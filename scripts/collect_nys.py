#!/usr/bin/env python3
"""Collect NYS StateJobs vacancies (official: statejobs.ny.gov) and filter technical roles.

Output: data/raw/nys_tech.json  (list of dicts, one per vacancy)
Only data present on the official page is recorded. Nothing is inferred here.
"""
import html, json, re, sys, urllib.request, datetime, pathlib

BASE = "https://statejobs.ny.gov/public/"
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

TECH = re.compile(
    r"information technology|\bIT\b|programm|software|developer|data (analyst|scien|engineer|base)|"
    r"database|systems analyst|application|computer|cyber|\bGIS\b|geographic information|"
    r"web |digital|technology|analytics|automation|engineer.*(software|data)",
    re.I,
)
EXCLUDE = re.compile(r"teacher|nurse|correction officer|food service|maintenance|therapy aide", re.I)
# Long Island / NYC / downstate-adjacent counties get priority
PRIORITY_COUNTIES = {"Nassau", "Suffolk", "New York", "Kings", "Queens", "Bronx", "Richmond",
                     "Westchester", "Rockland"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (civic-opportunity-tracker)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "ignore")


def clean(x: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def parse_table(s: str):
    out = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", s, re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) < 7:
            continue
        m = re.search(r'href="(vacancyDetailsView\.cfm\?id=\d+)"', cells[1])
        out.append({
            "item": clean(cells[0]), "title": clean(cells[1]), "grade": clean(cells[2]),
            "posted": clean(cells[3]), "deadline": clean(cells[4]), "agency": clean(cells[5]),
            "county": clean(cells[6]), "url": BASE + m.group(1) if m else None,
        })
    return out


def parse_detail(s: str) -> dict:
    """Pull labelled fields from a vacancy detail page (label/value pairs)."""
    d = {}
    for lab, val in re.findall(r'<span class="leftCol">(.*?)</span>\s*<span class="rightCol">(.*?)</span>', s, re.S):
        d[clean(lab).rstrip(":")] = clean(val)
    if not d:  # fallback layout: <dt>/<dd> or th/td
        for lab, val in re.findall(r"<(?:th|dt)[^>]*>(.*?)</(?:th|dt)>\s*<(?:td|dd)[^>]*>(.*?)</(?:td|dd)>", s, re.S):
            d[clean(lab).rstrip(":")] = clean(val)
    return d


def main(detail=True):
    s = fetch(BASE + "vacancyTable.cfm")
    (RAW / "nys_vacancies.html").write_text(s)
    rows = parse_table(s)
    tech = [r for r in rows if TECH.search(r["title"]) and not EXCLUDE.search(r["title"])]
    print(f"total vacancies: {len(rows)}  tech-matched: {len(tech)}", file=sys.stderr)
    if detail:
        for r in tech:
            try:
                r["detail"] = parse_detail(fetch(r["url"]))
            except Exception as e:  # keep row; mark detail missing
                r["detail_error"] = str(e)
    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    for r in tech:
        r["verified_at"] = stamp
        r["priority_region"] = r["county"] in PRIORITY_COUNTIES
    (RAW / "nys_tech.json").write_text(json.dumps(tech, indent=1))
    print(json.dumps({"total": len(rows), "tech": len(tech)}))


if __name__ == "__main__":
    main(detail="--no-detail" not in sys.argv)
