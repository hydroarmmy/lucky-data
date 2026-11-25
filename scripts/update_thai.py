"""ดึงผลสลากกินแบ่งรัฐบาลงวดใหม่จากคลัง vicha-w/thai-lotto-archive แล้วเพิ่มลง data/draws.json
ปลอดภัย: เพิ่มเฉพาะงวดที่ผ่านการตรวจรูปแบบครบ ไม่แก้งวดเดิม"""
import json, datetime, urllib.request, urllib.error, sys, pathlib

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "draws.json"
RAW = "https://raw.githubusercontent.com/vicha-w/thai-lotto-archive/master/lottonumbers/{}.txt"
KEYS = [("NEAR_FIRST", "nf", 2), ("SECOND", "p2", 5), ("THIRD", "p3", 10), ("FOURTH", "p4", 50), ("FIFTH", "p5", 100)]


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def parse(day, text):
    t = {}
    for line in text.splitlines()[1:]:
        k, _, v = line.partition(" ")
        t[k] = v.split()
    first = t["FIRST"][0]
    rec = {"d": day, "f": first, "t2": t["TWO"][0]}
    if "THREE_FIRST" in t:
        rec["f3"] = t["THREE_FIRST"]
    rec["l3"] = t.get("THREE_LAST") or t.get("THREE")
    # ตรวจรูปแบบรางวัลหลัก
    assert len(first) == 6 and first.isdigit(), "FIRST"
    assert len(rec["t2"]) == 2 and rec["t2"].isdigit(), "TWO"
    assert all(len(x) == 3 and x.isdigit() for x in rec.get("f3", []) + rec["l3"]), "THREE"
    f = int(first)
    rec["nf"] = [f"{(f - 1) % 1000000:06d}", f"{(f + 1) % 1000000:06d}"]   # คำนวณเอง กันข้อมูลคลังเพี้ยน
    for k, j, n in KEYS[1:]:
        v = t.get(k, [])
        if len(v) == n and all(len(x) == 6 and x.isdigit() for x in v):
            rec[j] = v                       # รางวัลที่ 2–5 ใส่เฉพาะที่ครบและถูกรูปแบบ
    return rec


def main():
    draws = json.loads(DATA.read_text(encoding="utf-8"))
    known = {r["d"] for r in draws}
    last = max(datetime.date.fromisoformat(d) for d in known)
    today = datetime.date.today()
    added = []
    d = last + datetime.timedelta(days=1)
    while d <= today:
        text = fetch(RAW.format(d.isoformat()))
        if text and d.isoformat() not in known:
            try:
                added.append(parse(d.isoformat(), text))
            except Exception as e:  # ข้อมูลยังไม่ครบหรือรูปแบบผิด: ข้ามไว้ รอบหน้าลองใหม่
                print(f"skip {d}: {e!r}", file=sys.stderr)
        d += datetime.timedelta(days=1)
    if added:
        draws = sorted(draws + added, key=lambda r: r["d"])
        DATA.write_text(json.dumps(draws, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print("added:", [r["d"] for r in added])


if __name__ == "__main__":
    main()
