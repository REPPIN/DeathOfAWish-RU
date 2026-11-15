"""Install the Russian translation into a Death of a Wish folder.

Usage:
    python scripts/patch.py "C:\\path\\to\\Death of a Wish"

Original files are saved to "<game folder>\\backup" the first time the script runs.
Every later run patches the saved originals again, so it can be run repeatedly.
To restore the game, copy the two files from "backup" back into DeathOfAWish_Data.

Changes:
  * DeathOfAWish_Data/sharedassets0.assets
      - TextAsset Lucah_Localization_ES gets the Russian text;
      - font xirod is replaced by Stalinist One, font Pokemon GB by Press Start 2P (both OFL).
  * DeathOfAWish_Data/level0
      - the language menu label "Español" becomes "Русский".

Requirements: Python 3.10+, UnityPy==1.25.4, TypeTreeGeneratorAPI.
"""
import glob
import json
import os
import shutil
import sys

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNITY_VERSION = "2019.4.41f1"
ORIGINAL_ES_LABEL = "Español"
NEW_ES_LABEL = "Русский"
FONT_REPLACEMENTS = {
    21: os.path.join(ROOT, "fonts", "StalinistOne-Regular.ttf"),  # xirod
    22: os.path.join(ROOT, "fonts", "PressStart2P-Regular.ttf"),  # Pokemon GB
}
BACKUP_FILES = ["sharedassets0.assets", "level0"]


def game_data_dir(game_dir):
    data = os.path.join(game_dir, "DeathOfAWish_Data")
    if not os.path.isdir(data):
        sys.exit(f"Not a Death of a Wish folder (no DeathOfAWish_Data): {game_dir}")
    return data


def prepare_backup(game_dir, data_dir):
    backup = os.path.join(game_dir, "backup")
    if not os.path.isdir(backup):
        os.makedirs(backup)
        for name in BACKUP_FILES:
            shutil.copy2(os.path.join(data_dir, name), os.path.join(backup, name))
        print(f"Original files saved to {backup}")
    for name in BACKUP_FILES:
        if not os.path.isfile(os.path.join(backup, name)):
            sys.exit(f"Backup is incomplete, missing: {os.path.join(backup, name)}")
    return backup


def load_translations():
    ru = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "ru", "chunk_*.json"))):
        with open(path, encoding="utf-8") as f:
            ru.update(json.load(f))
    return ru


def read_english_keys(assets_path):
    env = UnityPy.load(assets_path)
    for obj in env.objects:
        if obj.type.name == "TextAsset" and obj.read().m_Name == "Lucah_Localization_EN":
            items = json.loads(obj.read().m_Script.lstrip("\ufeff"))["items"]
            return [i["key"] for i in items]
    sys.exit("Lucah_Localization_EN not found in sharedassets0.assets")


def make_generator(data_dir):
    gen = TypeTreeGenerator(UNITY_VERSION)
    gen.load_local_game(os.path.dirname(data_dir))
    return gen


def patch_assets(src, dst, data_dir, ru_text_json):
    env = UnityPy.load(src)
    env.typetree_generator = make_generator(data_dir)
    for obj in env.objects:
        if obj.type.name == "TextAsset" and obj.read().m_Name == "Lucah_Localization_ES":
            d = obj.read()
            d.m_Script = ru_text_json
            obj.set_raw_data(obj.save_typetree(d))
            print("  localization ES: Russian text written")
        elif obj.type.name == "Font" and obj.path_id in FONT_REPLACEMENTS:
            d = obj.read()
            with open(FONT_REPLACEMENTS[obj.path_id], "rb") as f:
                d.m_FontData = f.read()
            obj.set_raw_data(obj.save_typetree(d))
            print(f"  font id {obj.path_id}: replaced")
    data = env.file.save()
    with open(dst, "wb") as f:
        f.write(data)


def patch_language_label(src, dst, data_dir):
    env = UnityPy.load(src)
    env.typetree_generator = make_generator(data_dir)
    changed = 0
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        if tree.get("m_Text") == ORIGINAL_ES_LABEL:
            tree["m_Text"] = NEW_ES_LABEL
            obj.set_raw_data(obj.save_typetree(tree))
            changed += 1
    if changed != 1:
        sys.exit(f"Expected one language label '{ORIGINAL_ES_LABEL}', found {changed}")
    data = env.file.save()
    with open(dst, "wb") as f:
        f.write(data)
    print("  language label: changed")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    game = os.path.abspath(sys.argv[1])
    data = game_data_dir(game)
    backup = prepare_backup(game, data)

    ru = load_translations()
    en_keys = read_english_keys(os.path.join(data, "sharedassets0.assets"))
    missing = [k for k in en_keys if k not in ru]
    extra = [k for k in ru if k not in en_keys]
    if missing or extra:
        sys.exit(f"Key mismatch with the game: {len(missing)} missing, {len(extra)} extra")
    text = json.dumps({"items": [{"key": k, "value": v} for k, v in ru.items()]},
                      ensure_ascii=False, indent=2)

    for name in BACKUP_FILES:
        shutil.copy2(os.path.join(backup, name), os.path.join(data, name))
    print("Restored originals from backup, then patching in place")
    patch_assets(os.path.join(data, "sharedassets0.assets"),
                 os.path.join(data, "sharedassets0.assets"), data, text)
    patch_language_label(os.path.join(data, "level0"), os.path.join(data, "level0"), data)
    print("Done. Start DeathOfAWish.exe and choose 'Русский' in the language menu.")


if __name__ == "__main__":
    main()
