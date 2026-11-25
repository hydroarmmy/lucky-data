"""ดึงผลชุดรายวันงวดใหม่จากหน้าประวัติของ Kapook แล้วเพิ่มลง data/daily.json
ถ้าดึงไม่ได้ ให้กรอกเองใน data/daily_manual.json รูปแบบ [{"d": "2026-11-25", "s": "123456"}]"""
import json, datetime, re, html, urllib.request, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "data"
DATA = ROOT / "daily.json"
MANUAL = ROOT / "daily_manual.json"
URL = "https://lottery.kapook.com/laolottery/history/1"
MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
          "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
DATE_RE = re.compile(r"งวดประจำวันที่\s*(\d{1,2})\s*(" + "|".join(MONTHS) + r")\s*(\d{4})")


def parse_page(text):
    """คืน {วันที่: เลข 6 ตัว} จากข้อความหน้าเว็บ (ตัด tag ออกก่อน)"""
    plain = html.unescape(re.sub(r"<[^>]+>", " ", text))
    plain = re.sub(r"\s+", " ", plain)
    out = {}
    matches = list(DATE_RE.finditer(plain))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(plain)
        chunk = plain[m.end():end]
        nums = re.findall(r"(?<!\d)(\d{6})(?!\d)", chunk)
        if not nums:
            continue
        six = nums[0]
        # ตรวจซ้ำ: ในตารางต้องมีเลข 4 ตัวท้ายที่ตรงกับเลข 6 ตัว
        if not re.search(r"(?<!\d)" + six[-4:] + r"(?!\d)", chunk[chunk.find(six) + 6:]):
            continue
        d = datetime.date(int(m.group(3)) - 543, MONTHS.index(m.group(2)) + 1, int(m.group(1)))
        out.setdefault(d.isoformat(), six)
    return out


def valid(day, six):
    d = datetime.date.fromisoformat(day)
    return d.weekday() < 5 and d <= datetime.date.today() and len(six) == 6 and six.isdigit()


def main():
    daily = json.loads(DATA.read_text(encoding="utf-8"))
    known = {r["d"] for r in daily}
    found = {}
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            found = parse_page(r.read().decode("utf-8", "replace"))
    except Exception as e:
        print(f"fetch failed: {e!r}", file=sys.stderr)
    if MANUAL.exists():
        for r in json.loads(MANUAL.read_text(encoding="utf-8")):
            found[r["d"]] = r["s"]           # ข้อมูลที่กรอกเองมาก่อนเสมอ
    added = [{"d": d, "s": s, "f": s[-4:]} for d, s in sorted(found.items()) if d not in known and valid(d, s)]
    if added:
        daily = sorted(daily + added, key=lambda r: r["d"])
        DATA.write_text(json.dumps(daily, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print("parsed:", len(found), "added:", [r["d"] for r in added])


if __name__ == "__main__":
    main()
