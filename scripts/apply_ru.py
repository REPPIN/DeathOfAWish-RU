import UnityPy, os, sys, json, glob
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
sys.stdout.reconfigure(encoding="utf-8")
B = r"C:\Users\REPPI\AppData\Local\Temp\opencode\dow"
D = r"C:\Games\Death of a Wish - RU\DeathOfAWish_Data"
FONT = open(os.path.join(B, "RussoOne.ttf"), "rb").read()

ru = {}
for p in sorted(glob.glob(os.path.join(B, "ru", "chunk_*.json"))):
    ru.update(json.load(open(p, encoding="utf-8")))
en = json.load(open(os.path.join(B, "orig", "Lucah_Localization_EN.json"), encoding="utf-8-sig"))["items"]
assert set(ru) == {i["key"] for i in en}, "key mismatch"
text = json.dumps({"items": [{"key": i["key"], "value": ru[i["key"]]} for i in en]}, ensure_ascii=False, indent=2)

gen = TypeTreeGenerator("2019.4.41f1")
gen.load_local_game(os.path.dirname(D))

path = os.path.join(D, "sharedassets0.assets")
env = UnityPy.load(path)
env.typetree_generator = gen
for obj in env.objects:
    if obj.type.name == "TextAsset" and obj.read().m_Name == "Lucah_Localization_ES":
        d = obj.read()
        d.m_Script = text
        obj.set_raw_data(obj.save_typetree(d))
        print("ES text written")
    if obj.type.name == "Font" and obj.path_id in (21, 22):
        d = obj.read()
        d.m_FontData = FONT
        obj.set_raw_data(obj.save_typetree(d))
        print("font", obj.path_id, "replaced")
data = env.file.save()
open(path, "wb").write(data)
print("saved", len(data))
