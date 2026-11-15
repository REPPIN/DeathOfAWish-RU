import UnityPy, os, sys
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
sys.stdout.reconfigure(encoding="utf-8")
D = r"C:\Games\Death of a Wish - RU\DeathOfAWish_Data"
gen = TypeTreeGenerator("2019.4.41f1")
gen.load_local_game(os.path.dirname(D))
path = os.path.join(D, "level0")
env = UnityPy.load(path)
env.typetree_generator = gen
n = 0
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    try:
        t = obj.read_typetree()
    except Exception:
        continue
    if t.get("m_Text") == "Español":
        t["m_Text"] = "Русский"
        obj.set_raw_data(obj.save_typetree(t))
        n += 1
        print("renamed", obj.path_id)
if n:
    data = env.file.save()
    open(path, "wb").write(data)
    print("saved", len(data), "changed", n)
else:
    print("nothing found")
