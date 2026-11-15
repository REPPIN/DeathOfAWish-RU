"""Apply the Russian translation to a copy of Death of a Wish.

Usage:
    python scripts/patch.py "C:\\path\\to\\Death of a Wish"

The script never edits the original folder. It copies the game to
"<game folder> - RU" and patches the copy:
  * sharedassets0.assets: TextAsset Lucah_Localization_ES gets the Russian text,
    fonts xirod and Pokemon GB get Russo One (OFL, see fonts/).
  * level0: the language menu label "Español" becomes "Русский".

Requirements: Python 3.10+, UnityPy==1.25.4, TypeTreeGeneratorAPI.
"""
import glob
import io
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


def game_data_dir(game_dir):
    data = os.path.join(game_dir, "DeathOfAWish_Data")
    if not os.path.isdir(data):
        sys.exit(f"Not a Death of a Wish folder (no DeathOfAWish_Data): {game_dir}")
    return data


def load_translations():
    ru = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "ru", "chunk_*.json"))):
        with open(path, encoding="utf-8") as f:
            ru.update(json.load(f))
    return ru


def read_english_keys(data_dir):
    env = UnityPy.load(os.path.join(data_dir, "sharedassets0.assets"))
    for obj in env.objects:
        if obj.type.name == "TextAsset" and obj.read().m_Name == "Lucah_Localization_EN":
            items = json.loads(obj.read().m_Script.lstrip("\ufeff"))["items"]
            return [i["key"] for i in items]
    sys.exit("Lucah_Localization_EN not found in sharedassets0.assets")


def make_generator(data_dir):
    gen = TypeTreeGenerator(UNITY_VERSION)
    gen.load_local_game(os.path.dirname(data_dir))
    return gen


def patch_assets(data_dir, ru_text_json, font_bytes):
    path = os.path.join(data_dir, "sharedassets0.assets")
    env = UnityPy.load(path)
    env.typetree_generator = make_generator(data_dir)
    for obj in env.objects:
        if obj.type.name == "TextAsset" and obj.read().m_Name == "Lucah_Localization_ES":
            d = obj.read()
            d.m_Script = ru_text_json
            obj.set_raw_data(obj.save_typetree(d))
            print("  localization ES: Russian text written")
        elif obj.type.name == "Font" and obj.path_id in (21, 22):
            d = obj.read()
            d.m_FontData = font_bytes
            obj.set_raw_data(obj.save_typetree(d))
            print(f"  font id {obj.path_id}: replaced with Russo One")
    with open(path, "wb") as f:
        f.write(env.file.save())


def patch_language_label(data_dir):
    path = os.path.join(data_dir, "level0")
    env = UnityPy.load(path)
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
    if changed:
        with open(path, "wb") as f:
            f.write(env.file.save())
    print(f"  language label: {changed} changed")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    game = os.path.abspath(sys.argv[1])
    data = game_data_dir(game)
    copy = game.rstrip("\\/") + " - RU"
    if os.path.exists(copy):
        sys.exit(f"Target already exists, remove or rename it first: {copy}")

    print(f"Copying game to {copy}")
    shutil.copytree(game, copy)
    copy_data = game_data_dir(copy)

    ru = load_translations()
    en_keys = read_english_keys(copy_data)
    missing = [k for k in en_keys if k not in ru]
    extra = [k for k in ru if k not in en_keys]
    if missing or extra:
        sys.exit(f"Key mismatch with the game: {len(missing)} missing, {len(extra)} extra")
    text = json.dumps({"items": [{"key": k, "value": v} for k, v in ru.items()]},
                      ensure_ascii=False, indent=2)
    with open(os.path.join(ROOT, "fonts", "RussoOne-Regular.ttf"), "rb") as f:
        font = f.read()

    print("Patching sharedassets0.assets")
    patch_assets(copy_data, text, font)
    print("Patching level0")
    patch_language_label(copy_data)
    print(f"Done. Start the game from {copy} and choose 'Русский' in the language menu.")


if __name__ == "__main__":
    main()
