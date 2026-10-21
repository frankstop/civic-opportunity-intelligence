#!/usr/bin/env python3
"""Collect NYC government tech opportunities from official NYC Open Data (Socrata) datasets.

Datasets (all published by NYC DCAS / OTI on data.cityofnewyork.us):
  kpav-sd4t  Jobs NYC Postings              -> vacancies
  4ptz-hmtc  Annual Examination Schedule     -> exam announcements (DCAS)
  vx8i-nprf  Civil Service List (Active)     -> eligible lists (aggregated; NO personal names stored)

Outputs: data/raw/nyc_jobs.json, nyc_exams.json, nyc_lists.json
"""
import json, re, urllib.parse, urllib.request, datetime, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
API = "https://data.cityofnewyork.us/resource/{}.json"
NOW = datetime.datetime.now().astimezone()
STAMP = NOW.isoformat(timespec="seconds")

TECH_TITLE = re.compile(
    r"computer|software|programm|developer|data|database|information technology|\bIT\b|cyber|"
    r"systems? (analyst|engineer)|application|\bGIS\b|geographic|digital|web|devops|cloud|"
    r"machine learning|\bAI\b|analytics|automation|technology",
    re.I,
)


def q(dataset, **params):
    url = API.format(dataset) + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "civic-opportunity-tracker"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def jobs():
    rows = q("kpav-sd4t", **{
        "$where": "job_category like '%Technology%' OR upper(civil_service_title) like '%COMPUTER%' "
                  "OR upper(civil_service_title) like '%DATA%' OR upper(business_title) like '%DEVELOPER%' "
                  "OR upper(business_title) like '%SOFTWARE%' OR upper(business_title) like '%DATA%'",
        "$limit": 5000,
    })
    by_id = {}
    for r in rows:
        jid = r["job_id"]
        # Same job appears as Internal + External; prefer External (open to the public)
        if jid not in by_id or r.get("posting_type") == "External":
            by_id[jid] = r
    out = []
    for r in by_id.values():
        out.append({
            "job_id": r["job_id"], "agency": r.get("agency"), "business_title": r.get("business_title"),
            "civil_service_title": r.get("civil_service_title"), "title_code": r.get("title_code_no"),
            "title_classification": r.get("title_classification"), "level": r.get("level"),
            "posting_type": r.get("posting_type"), "category": r.get("job_category"),
            "career_level": r.get("career_level"), "salary_from": r.get("salary_range_from"),
            "salary_to": r.get("salary_range_to"), "salary_frequency": r.get("salary_frequency"),
            "location": r.get("work_location"), "posted": r.get("posting_date", "")[:10],
            "post_until": r.get("post_until"), "updated": r.get("posting_updated", "")[:10],
            "min_quals": r.get("minimum_qual_requirements", ""), "preferred": r.get("preferred_skills", ""),
            "residency": r.get("residency_requirement", ""), "to_apply": r.get("to_apply", ""),
            "description": (r.get("job_description") or "")[:1500],
            "url": f"https://cityjobs.nyc.gov/job/{r['job_id']}",
            "verified_at": STAMP,
        })
    return out


def exams():
    rows = q("4ptz-hmtc", **{"$limit": 50000, "$order": "application_period_end_date DESC"})
    out, seen = [], set()
    for r in rows:
        end = r.get("application_period_end_date", "")[:10]
        if not end or end < (NOW - datetime.timedelta(days=400)).date().isoformat():
            continue  # keep ~13 months of history to show "recently missed"
        key = (r.get("exam_number"), r.get("exam_title"), r.get("application_period_start"), end)
        if key in seen:  # dataset contains duplicate rows
            continue
        seen.add(key)
        out.append({
            "exam_number": r.get("exam_number"), "title": r.get("exam_title"),
            "type": r.get("open_competitive_promotion"),
            "app_start": r.get("application_period_start", "")[:10], "app_end": end,
            "tech": bool(TECH_TITLE.search(r.get("exam_title", ""))), "verified_at": STAMP,
        })
    return out


def lists():
    """Aggregate active eligible lists by (exam, title, agency). Personal names are never read into output."""
    where = " OR ".join(f"upper(list_title_desc) like '%{w}%'" for w in
                        ["COMPUTER", "DATA", "SOFTWARE", "IT ", "INFORMATION", "CYBER", "SYSTEMS", "GIS",
                         "TECHNOLOG", "PROGRAM"])
    rows = q("vx8i-nprf", **{
        "$select": "exam_no,list_no,list_title_desc,list_title_code,list_agency_desc,established_date,"
                   "anniversary_date,extension_date",
        "$where": where, "$limit": 200000,
    })
    agg = collections.OrderedDict()
    for r in rows:
        if not TECH_TITLE.search(r.get("list_title_desc", "")):
            continue
        k = (r.get("exam_no"), r.get("list_title_desc"), r.get("list_agency_desc"))
        a = agg.setdefault(k, {
            "exam_no": k[0], "title": k[1], "list_agency": k[2], "title_code": r.get("list_title_code"),
            "established": (r.get("established_date") or "")[:10],
            "anniversary": (r.get("anniversary_date") or "")[:10],
            "extension": (r.get("extension_date") or "")[:10], "eligibles": 0, "verified_at": STAMP,
        })
        a["eligibles"] += 1
    return list(agg.values())


if __name__ == "__main__":
    j, e, l = jobs(), exams(), lists()
    (RAW / "nyc_jobs.json").write_text(json.dumps(j, indent=1))
    (RAW / "nyc_exams.json").write_text(json.dumps(e, indent=1))
    (RAW / "nyc_lists.json").write_text(json.dumps(l, indent=1))
    print(json.dumps({"jobs": len(j), "exams_recent": len(e), "tech_exams": sum(x["tech"] for x in e),
                      "tech_lists": len(l)}))
