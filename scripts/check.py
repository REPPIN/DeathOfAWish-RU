"""Usage: python check.py NN  -> validates ru/chunk_NN.json against chunks/chunk_NN.json"""
import json, os, re, sys
B = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8")
LEAD = re.compile(r"^\[(Lilli|Serah|Christian|PLAYERNAME|\?\?\?|NE)\]")
TOK = re.compile(r"\{[A-Z]+\}|\[PLAYERNAME\]|\[TVNUM\]|\bTARGET\b|<[^>]+>|\[\d VP\]")
def check(n):
    src = json.load(open(os.path.join(B, "chunks", f"chunk_{n}.json"), encoding="utf-8"))
    path = os.path.join(B, "ru", f"chunk_{n}.json")
    if not os.path.exists(path):
        return [f"missing file {path}"]
    try:
        ru = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [f"invalid JSON: {e}"]
    errs = []
    for it in src:
        k, en = it["key"], it["en"]
        if k not in ru:
            errs.append(f"{k}: missing"); continue
        v = ru[k]
        if not isinstance(v, str):
            errs.append(f"{k}: not a string"); continue
        if sorted(TOK.findall(en)) != sorted(TOK.findall(v)):
            errs.append(f"{k}: tokens differ {sorted(TOK.findall(en))} vs {sorted(TOK.findall(v))}")
        if en.count("\n") != v.count("\n"):
            errs.append(f"{k}: newline count {en.count(chr(10))} vs {v.count(chr(10))}")
        m = LEAD.match(en)
        if m and not v.startswith(m.group()):
            errs.append(f"{k}: speaker tag {m.group()} must stay at start")
        if en.strip() and not v.strip():
            errs.append(f"{k}: empty translation")
        if re.search(r"[A-Za-z]{4,}", en) and not re.search(r"[А-Яа-яЁё]", v) and en == v and len(en) > 12:
            errs.append(f"{k}: looks untranslated")
    extra = set(ru) - {i["key"] for i in src}
    if extra:
        errs.append(f"extra keys: {sorted(extra)[:10]}")
    return errs
if __name__ == "__main__":
    ids = sys.argv[1:] or [f[6:8] for f in sorted(os.listdir(os.path.join(B, "chunks")))]
    for n in ids:
        e = check(n)
        print(f"chunk_{n}: {'OK' if not e else str(len(e)) + ' problems'}")
        for x in e[:40]:
            print("  ", x)
