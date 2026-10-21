#!/usr/bin/env python3
"""Collect federal software/data/IT postings from USAJOBS (official: usajobs.gov).

Uses the same public search endpoint the usajobs.gov website uses (no API key, no login).
Series: 2210 IT Management, 1550 Computer Science, 1560 Data Science.
If this endpoint changes, register a free key at developer.usajobs.gov and switch to data.usajobs.gov/api/search.

Output: data/raw/federal.json
"""
import json, re, urllib.request, datetime, pathlib, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
URL = "https://www.usajobs.gov/Search/ExecuteSearch"
STAMP = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
NY = re.compile(r"New York|Brooklyn|Bronx|Queens|Staten Island|Upton|Hauppauge|Garden City|Melville|"
                r"Islip|Uniondale|Mineola|Hempstead|Northport|Farmingdale|Brentwood|Jamaica|Yaphank|Plum Island", re.I)


def post(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_all(body):
    out, page = [], 1
    while True:
        d = post(dict(body, Page=str(page)))
        out += d.get("Jobs", [])
        pg = d.get("Pager", {})
        if not pg.get("HasNextPage"):
            return out
        page += 1
        time.sleep(0.5)


def norm(j, flags):
    hp = j.get("HiringPath")
    paths = [h.get("Code") for h in hp] if isinstance(hp, list) else re.findall(r"'Code': '([^']+)'", str(hp))
    cats = j.get("JobCategoryCode")
    series = [c.get("Code") for c in cats] if isinstance(cats, list) else re.findall(r"'Code': '(\d+)'", str(cats))
    loc = j.get("LocationDisplay", "")
    return {
        "id": j.get("DocumentID"), "control": j.get("PositionID"), "title": j.get("Title"),
        "agency": j.get("Agency"), "department": j.get("Department"), "salary": j.get("SalaryDisplay"),
        "grade": f"{j.get('JobGrade')}-{j.get('LowGrade')}" + (f"/{j.get('HighGrade')}" if j.get('HighGrade') != j.get('LowGrade') else ""),
        "location": loc, "dates": j.get("DateDisplay"), "closes": (j.get("PositionEndDate") or "")[:10],
        "opens": (j.get("PositionStartDate") or "")[:10], "schedule": j.get("WorkSchedule"),
        "work_type": j.get("WorkType"), "hiring_paths": paths, "series": series,
        "url": f"https://www.usajobs.gov/job/{j.get('DocumentID')}",
        "in_ny": bool(NY.search(loc)), "remote": bool(re.search(r"remote|Anywhere in the U", loc, re.I)),
        "location_negotiable": "Location Negotiable" in loc,
        "open_to_public": "public" in paths, "recent_grad_path": "graduates" in paths,
        "multi_location": bool(re.search(r"\+ ?\d+ location|Multiple|Various", loc, re.I)),
        "verified_at": STAMP,
    }


def main():
    series = ["2210", "1550", "1560"]
    jobs = {}
    for j in fetch_all({"JobCategoryCode": series}):
        jobs[j["DocumentID"]] = norm(j, set())
    # NOTE: the site's RemoteFilter parameter is ignored by this endpoint (verified 2026-10-21);
    # remote status is derived from the official location text instead (see norm()).
    for j in fetch_all({"JobCategoryCode": series, "HiringPath": ["graduates"]}):
        jobs.setdefault(j["DocumentID"], norm(j, set()))["recent_grad_path"] = True
    out = list(jobs.values())
    (RAW / "federal.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({"total": len(out), "ny": sum(x["in_ny"] for x in out), "remote": sum(x["remote"] for x in out),
                      "negotiable": sum(x["location_negotiable"] for x in out),
                      "public": sum(x["open_to_public"] for x in out),
                      "recent_grad": sum(x["recent_grad_path"] for x in out)}))


if __name__ == "__main__":
    main()
