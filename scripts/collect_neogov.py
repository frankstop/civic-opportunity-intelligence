#!/usr/bin/env python3
"""Collect exam announcements / vacancies from agencies that publish on GovernmentJobs.com (NEOGOV).

NEOGOV hosts the official career pages of thousands of US counties, cities, towns and authorities
(e.g. Nassau County Civil Service: governmentjobs.com/careers/nassaucountyny).
Agencies are listed in data/neogov_agencies.json as {"slug": ..., "name": ..., "state": ..., "region": ...}.

Output: data/raw/neogov.json
"""
import html, json, re, sys, time, urllib.request, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
STAMP = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
TECH = re.compile(r"programmer|software|developer|data|database|information technology|\bIT\b|computer|"
                  r"cyber|systems analyst|application|\bGIS\b|geographic information|network|digital|"
                  r"technology|analytics|web", re.I)
HDR = {"User-Agent": "Mozilla/5.0 (civic-opportunity-tracker)", "X-Requested-With": "XMLHttpRequest"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=40) as r:
        return r.read().decode("utf-8", "ignore")


def clean(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def list_jobs(slug, max_pages=30):
    items, page = [], 1
    while page <= max_pages:
        s = get(f"https://www.governmentjobs.com/careers/home/index?agency={slug}&sort=PostingDate"
                f"&isDescendingSort=true&page={page}")
        found = re.findall(r'<li class="list-item"[^>]*data-job-id="(\d+)"(.*?)</li>', s, re.S)
        if not found:
            break
        for jid, body in found:
            a = re.search(r'href="([^"]+)"[^>]*>(.*?)</a>', body, re.S)
            items.append({"job_id": jid, "title": clean(a.group(2)) if a else "",
                          "url": "https://www.governmentjobs.com" + a.group(1) if a else None,
                          "summary": clean(re.search(r'list-entry">(.*?)</div>', body, re.S).group(1))
                          if 'list-entry"' in body else ""})
        if f"page={page + 1}" not in s:
            break
        page += 1
        time.sleep(0.4)
    return items


FIELDS = ["Salary", "Location", "Job Type", "Job Number", "Department", "Opening Date", "Closing Date",
          "Exam Date", "Fee"]


def detail(url):
    s = get(url)
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    t = re.sub(r"<(br|p|tr|li|h\d|div|dt|dd)[^>]*>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    lines = [re.sub(r"\s+", " ", x).strip() for x in t.split("\n")]
    lines = [x for x in lines if x]
    d = {}
    for i, x in enumerate(lines[:-1]):
        if x in FIELDS and x not in d:
            d[x] = lines[i + 1]
    body = "\n".join(lines)
    m = re.search(r"Minimum Qualifications(.*?)(?:Supplemental Information|Benefits|Agency\n|$)", body, re.S)
    d["min_quals"] = m.group(1).strip()[:2500] if m else ""
    m = re.search(r"ANNOUNCED FOR:?(.*?)(?:SALARY|Duties)", body, re.S)
    d["announced_for"] = m.group(1).strip()[:500] if m else ""
    m = re.search(r"(?:Duties|Description)\n(.*?)(?:Minimum Qualifications|Typical Work)", body, re.S)
    d["duties"] = m.group(1).strip()[:1200] if m else ""
    return d


def main():
    agencies = json.loads((ROOT / "data" / "neogov_agencies.json").read_text())
    only = set(sys.argv[1:])
    out = []
    for ag in agencies:
        if only and ag["slug"] not in only:
            continue
        try:
            items = list_jobs(ag["slug"])
        except Exception as e:
            print(f"!! {ag['slug']}: {e}", file=sys.stderr)
            continue
        tech = [i for i in items if TECH.search(i["title"])]
        print(f"{ag['slug']}: {len(items)} postings, {len(tech)} tech", file=sys.stderr)
        for i in tech:
            try:
                i.update(detail(i["url"]))
            except Exception as e:
                i["detail_error"] = str(e)
            i.update(agency=ag["name"], agency_slug=ag["slug"], state=ag["state"], region=ag.get("region", ""),
                     verified_at=STAMP)
            out.append(i)
            time.sleep(0.3)
        ag["last_count"] = len(items)
    (RAW / "neogov.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({"tech": len(out)}))


if __name__ == "__main__":
    main()
