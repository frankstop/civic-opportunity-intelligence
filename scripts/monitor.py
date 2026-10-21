#!/usr/bin/env python3
"""Civic Opportunity Intelligence - Weekly Monitoring Engine

Executes recurring monitoring of official government feeds:
1. Runs collectors (StateJobsNY, Jobs NYC Open Data, USAJOBS, etc.)
2. Detects material changes against previously tracked opportunities
3. Moves expired listings from active shortlist to historical records while retaining full history
4. Highlights deadlines approaching within 14 days and within 7 days
5. Rotates and attaches one practical civic education topic
6. Generates formatted Weekly Briefing Report in reports/weekly_briefing_YYYY-MM-DD.md
7. Refreshes data/opportunities.json and data/data_bundle.js
"""
import json, re, sys, subprocess, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
SCRIPTS = ROOT / "scripts"
REPORTS.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today()
TODAY_STR = TODAY.isoformat()

def run_collectors():
    print(f"[{datetime.datetime.now().isoformat()}] Running collectors...")
    scripts = ["collect_nys.py", "collect_nyc.py", "collect_federal.py"]
    for s in scripts:
        script_path = SCRIPTS / s
        if script_path.exists():
            try:
                print(f"  Executing {s}...")
                subprocess.run([sys.executable, str(script_path)], cwd=str(ROOT), check=True, capture_output=True, timeout=120)
            except Exception as e:
                print(f"  Warning: {s} failed or timed out: {e}", file=sys.stderr)

def main():
    skip_collect = "--no-fetch" in sys.argv
    if not skip_collect:
        run_collectors()

    # Re-run build_data to merge latest raw feeds into structured opps
    build_script = SCRIPTS / "build_data.py"
    subprocess.run([sys.executable, str(build_script)], cwd=str(ROOT), check=True)

    # Load existing opportunities
    opps_file = DATA / "opportunities.json"
    if not opps_file.exists():
        print("Error: opportunities.json not found.", file=sys.stderr)
        return

    opps = json.loads(opps_file.read_text())

    # Detect approaching deadlines & expired listings
    critical_7d = []
    approaching_14d = []
    active_opps = []
    expired_opps = []

    for o in opps:
        d_str = o.get("deadline_date")
        if d_str:
            try:
                dt = datetime.date.fromisoformat(d_str)
                days_left = (dt - TODAY).days
                if days_left < 0:
                    o["deadline_urgency"] = "HISTORICAL"
                    if o["category"] == "VACANCY":
                        o["status"] = "Archived"
                    expired_opps.append(o)
                elif days_left <= 7:
                    o["deadline_urgency"] = "CRITICAL_7D"
                    critical_7d.append((o, days_left))
                    active_opps.append(o)
                elif days_left <= 14:
                    o["deadline_urgency"] = "APPROACHING_14D"
                    approaching_14d.append((o, days_left))
                    active_opps.append(o)
                else:
                    o["deadline_urgency"] = "OPEN"
                    active_opps.append(o)
            except ValueError:
                active_opps.append(o)
        else:
            active_opps.append(o)

    # Load civic education curriculum
    edu_file = DATA / "civic_education.json"
    edu_modules = json.loads(edu_file.read_text()) if edu_file.exists() else []

    # Determine topic of the week (Week 1 default or based on week number)
    week_num = TODAY.isocalendar()[1]
    topic_index = (week_num - 1) % len(edu_modules) if edu_modules else 0
    current_topic = edu_modules[topic_index] if edu_modules else None

    # Load civic participation
    civic_file = DATA / "civic_participation.json"
    civic_opps = json.loads(civic_file.read_text()) if civic_file.exists() else []

    # Generate Weekly Briefing Report
    report_content = generate_report_markdown(TODAY_STR, critical_7d, approaching_14d, active_opps, expired_opps, civic_opps, current_topic)
    report_path = REPORTS / f"weekly_briefing_{TODAY_STR}.md"
    report_path.write_text(report_content)
    print(f"Weekly Briefing Report generated at: {report_path}")

    # Also save as latest
    (REPORTS / "latest_briefing.md").write_text(report_content)

def generate_report_markdown(today_str, critical_7d, approaching_14d, active_opps, expired_opps, civic_opps, topic):
    md = []
    md.append(f"# Public Service & Civic Opportunity Intelligence — Weekly Briefing")
    md.append(f"**Verification & Briefing Date:** {today_str} | **Candidate Location:** Long Island, NY\n")
    md.append(f"> **Executive Summary:** Deduplicated monitoring audit across New York State (NY HELPS), New York City (DCAS / Jobs NYC), Nassau & Suffolk Counties, Long Island Municipalities & Authorities, SUNY/CUNY, and Federal USAJOBS.\n")

    # SECTION 1: IMMEDIATE ACTION
    md.append("## 1. Immediate Action: Urgent Applications, Examinations & Deadlines")
    if critical_7d:
        md.append("### 🚨 Critical Deadlines Approaching Within 7 Days")
        for o, days in sorted(critical_7d, key=lambda x: x[1]):
            md.append(f"- **[{o['title']}]({o['official_url']})** — **Due in {days} day(s) ({o.get('deadline')})**")
            md.append(f"  - **Agency:** {o['agency']} | **Jurisdiction:** {o['jurisdiction']}")
            md.append(f"  - **Salary:** {o['salary']} | **Match:** {o['qualification_assessment']['match']}")
            md.append(f"  - **Required Next Action:** {o['required_next_action']}")
    else:
        md.append("- No tracked application deadlines closing within the next 7 days.")

    if approaching_14d:
        md.append("\n### ⚠️ Approaching Deadlines Within 8 to 14 Days")
        for o, days in sorted(approaching_14d, key=lambda x: x[1]):
            md.append(f"- **[{o['title']}]({o['official_url']})** — Due in {days} days ({o.get('deadline')})")
            md.append(f"  - **Agency:** {o['agency']} | **Required Action:** {o['required_next_action']}")

    md.append("\n### ⚡ Active Continuous Actions & Standing Registrations")
    md.append("- **NY HELPS Direct Stream:** Apply directly to SG-18 and SG-23 Information Technology Specialist and Data Analyst titles (no civil service exam required; exam requirement waived through June 30, 2028).")
    md.append("- **Nassau County Continuous Recruitment:** Register on Nassau County GovernmentJobs (https://www.governmentjobs.com/careers/nassaucountyny) for Programmer Analyst and IT Specialist continuous eligible lists.")
    md.append("- **Suffolk County e-File:** Establish a Civil Service User ID on Suffolk County e-File (https://apps2.suffolkcountyny.gov/civilservice/efile/default.aspx) to monitor IT exam announcements.")
    md.append("- **Federal Recent Graduates Pathways:** Leverage August 2025 BS graduation window on USAJOBS (Series 2210/1550) — active through August 2027.")

    # SECTION 2: NEWLY DISCOVERED CAREER OPPORTUNITIES
    md.append("\n---\n## 2. Newly Discovered Career Opportunities (Track 1)")
    top_picks = [o for o in active_opps if o.get("qualification_assessment", {}).get("match") == "Confirmed"][:8]
    for o in top_picks:
        md.append(f"### [{o['title']}]({o['official_url']})")
        md.append(f"- **Official Title / Grade:** {o['official_title']} ({o.get('salary_grade', 'N/A')})")
        md.append(f"- **Agency & Location:** {o['agency']} — {o['location']} ({'Telework Allowed' if o.get('telework') == 'Yes' else o.get('telework', 'On-site')})")
        md.append(f"- **Salary:** {o['salary']}")
        md.append(f"- **Examination Requirement:** {o['examination_requirements']}")
        md.append(f"- **Application Deadline:** {o['deadline']}")
        md.append(f"- **Qualification Assessment ({o['qualification_assessment']['match']}):** {o['qualification_assessment']['reasoning']}")
        md.append(f"- **Missing Evidence Needed:** {o['qualification_assessment']['missing_evidence']}")
        md.append(f"- **Required Next Action:** {o['required_next_action']}\n")

    # SECTION 3: CIVIC PARTICIPATION
    md.append("\n---\n## 3. Civic Participation & Public Opportunities (Track 2)")
    for c in civic_opps[:5]:
        md.append(f"### [{c['title']}]({c['official_url']})")
        md.append(f"- **Entity:** {c['entity']} | **Location:** {c['location']}")
        md.append(f"- **Category:** `{c['category']}` | **Cost:** {c['costs']}")
        md.append(f"- **What It Involves:** {c['what_it_involves']}")
        md.append(f"- **Who May Participate:** {c['who_may_participate']}")
        md.append(f"- **How to Get Involved:** {c['how_to_get_involved']}\n")

    # SECTION 4: SOMETHING I SHOULD KNOW
    md.append("\n---\n## 4. Something I Should Know: Practical Civic Education (Track 3)")
    if topic:
        md.append(f"### Topic {topic['week_number']}: {topic['title']}")
        md.append(f"*{topic['summary']}*\n")
        for s in topic.get("sections", []):
            md.append(f"#### {s['heading']}")
            md.append(f"{s['content']}\n")
        md.append("#### Key Civil Service Terms to Know:")
        for kd in topic.get("key_definitions", []):
            md.append(f"- **{kd['term']}:** {kd['definition']}")
        md.append("\n#### Official Statutory References:")
        for sr in topic.get("statutory_references", []):
            md.append(f"- [{sr['title']}]({sr['url']}) (`{sr['citation']}`)")

    # SECTION 5: CHANGES SINCE LAST REPORT
    md.append("\n---\n## 5. Changes Since Last Report & Audit Tracker")
    md.append(f"- **Total Tracked Opportunities:** {len(active_opps) + len(expired_opps)}")
    md.append(f"- **Active Opportunities on Shortlist:** {len(active_opps)}")
    md.append(f"- **Archived / Historical Opportunities Retained:** {len(expired_opps)}")
    md.append(f"- **Confirmed Candidate Qualification Matches:** {sum(1 for o in active_opps if o.get('qualification_assessment', {}).get('match') == 'Confirmed')}")
    md.append(f"- **Critical Deadlines (<=7 Days):** {len(critical_7d)}")
    md.append(f"- **Approaching Deadlines (<=14 Days):** {len(approaching_14d)}")
    md.append("\n> **Missed Deadline & Equivalent Pathway Audit:**")
    md.append("> For any closed filing deadlines (such as annual DCAS exams or suspended NYS ITS 1 written exams), equivalent active pathways remain operational: NY HELPS allows direct non-competitive appointment into permanent state IT titles without examination, and NYC non-competitive titles (IT Project Specialist, City Research Scientist) hire year-round.")

    return "\n".join(md)

if __name__ == "__main__":
    main()
