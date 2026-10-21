# Public Service & Civic Opportunity Intelligence

[![Daily Civic Opportunity Intelligence Monitor](https://github.com/frankstop/civic-opportunity-intelligence/actions/workflows/daily-civic-monitor.yml/badge.svg)](https://github.com/frankstop/civic-opportunity-intelligence/actions/workflows/daily-civic-monitor.yml)

A persistent research, monitoring, and intelligence platform designed to eliminate the information gap surrounding government technology employment, civil-service examination systems, municipal procurement, and civic participation.

Focused on **Long Island (Nassau & Suffolk Counties)**, **New York City**, **New York State**, and **Federal Government (USAJOBS)**, accompanied by a comprehensive **50-State Civil Service Directory**.

---

## Candidate Profile & Qualification Context
- **Education:** Bachelor of Science in Computer & Information Science (Conferred August 2025).
- **Experience:** ~5 years professional technical experience (Python, SQL, JavaScript/TypeScript, APIs, Databases, Automation, Systems Integration, IT Ops).
- **Target Geography:** Long Island, NYC, Hybrid, Remote, New York State.
- **Key Pathways:**
  - **NYS NY HELPS:** Direct appointment to competitive SG-18 and SG-23 titles without examination through June 30, 2028.
  - **Federal Recent Graduates (5 CFR 362):** 2-year statutory hiring authority active through August 2027.
  - **NYC Non-Competitive IT:** Year-round appointment for IT Project Specialist and City Research Scientist titles.
  - **Long Island Continuous Registers:** Ongoing training-and-experience registers for Programmer Analyst and IT Specialist titles in Nassau and Suffolk Counties.

---

## Core Intelligence Tracks

### Track 1: Government Technology Careers
- **New York State (NY HELPS):** ITS 2 (SG-18, $65k–$82k) and ITS 3 (SG-23, $84k–$106k) direct vacancies.
- **New York City (DCAS & Agencies):** DCAS open exams, OTI, NYPD, DOT, DEP direct and provisional tech vacancies.
- **Long Island Municipalities:** Nassau County Civil Service, Suffolk County Civil Service, all 13 Long Island Towns, 2 Cities, and Villages.
- **Public Authorities & National Labs:** Metropolitan Transportation Authority (MTA/LIRR), Brookhaven National Laboratory (BNL), Port Authority of NY & NJ (PANYNJ), LIPA, Suffolk County Water Authority (SCWA).
- **Higher Education:** SUNY Stony Brook, Farmingdale State, SUNY Old Westbury, CUNY.
- **Federal Government (USAJOBS):** Series 2210 (IT Management / Software / Data), Series 1550 (Computer Science), and Recent Graduates Pathways with NY-NJ 37.24% locality pay.
- **50-State Directory:** Merit models (Rule of Three, Banded, Direct Classification), IT job series, remote policies, and municipal portals across all 50 states + D.C.

### Track 2: Civic Participation & Public Opportunities
- **Civic Tech Volunteering:** BetaNYC Civic Innovation Lab, U.S. Digital Response (USDR), OWASP Long Island & NYC.
- **Municipal Technology Committees:** Suffolk County Legislature IT & Diversity Committee, Nassau County Legislature, NYC Council Committee on Technology.
- **Open Data & APIs:** NYS Open Data Socrata API, NYC Open Data, MTA Developer real-time GTFS-RT APIs.
- **Public Procurements & RFPs:** NYS Contract Reporter (bids $50k+ and discretionary purchases), NYC PASSPort, BidNet Direct.
- **Government Training Programs:** CISA Learning / FedVTE, NYSDOL Coursera workforce certifications.

### Track 3: Practical Civic Education Curriculum
1. **Topic 1:** Civil Service Examinations, The Rule of Three & NY HELPS (NYS Civil Service Law § 61).
2. **Topic 2:** How Local Governments Hire Software Developers (Civil Service vs. Direct Appointment).
3. **Topic 3:** Municipal Technology Procurement, RFPs & Public Contracts (State Finance Law § 163).
4. **Topic 4:** How Residents Participate in Public Hearings & Meetings (Open Meetings Law, POL Art. 7).
5. **Topic 5:** How to Read a Municipal Budget (General Fund, Capital Budget, NYS 2% Tax Cap).
6. **Topic 6:** How Public Records Requests Work (NYS FOIL, POL Art. 6 & Federal FOIA).
7. **Topic 7:** Division of Government Responsibilities on Long Island (State, County, Town, Village, Special District).

---

## Automated Daily Monitoring Workflow (GitHub Actions)

This repository executes an automated cloud audit every day at **13:00 UTC (9:00 AM EDT / America/New_York)** via GitHub Actions:
- **Workflow File:** [`.github/workflows/daily-civic-monitor.yml`](.github/workflows/daily-civic-monitor.yml)
- **Engine Script:** [`scripts/monitor.py`](scripts/monitor.py)
- **Actions Performed:**
  1. Queries authoritative government endpoints (StateJobsNY, Jobs NYC Open Data, USAJOBS).
  2. Detects material changes against previously tracked opportunities.
  3. Moves expired listings from the active shortlist to historical records while preserving history.
  4. Flags critical deadlines approaching within 7 days and within 14 days.
  5. Rotates and attaches the practical civic education module.
  6. Compiles updated datasets (`data/opportunities.json`, `data/data_bundle.js`) and generates the weekly briefing report (`reports/latest_briefing.md`).
  7. Automatically commits updated records and deploys to GitHub Pages.

---

## Directory Structure

```
.
├── .github/
│   └── workflows/
│       └── daily-civic-monitor.yml    # Daily GitHub Actions workflow
├── data/
│   ├── raw/                           # Raw JSON/HTML feeds from official endpoints
│   ├── opportunities.json             # 203 structured, deduplicated opportunities
│   ├── jurisdictions_50states.json    # Complete 50-state + D.C. civil service directory
│   ├── ny_municipalities.json         # Long Island Towns, Cities, Villages, Authorities
│   ├── civic_participation.json       # 13 verified Track 2 initiatives
│   ├── civic_education.json           # 7 practical civic education modules
│   └── data_bundle.js                 # Unified browser dataset (window.CIVIC_DATA)
├── reports/
│   ├── latest_briefing.md             # Most recent briefing report
│   └── weekly_briefing_2026-10-21.md  # Timestamped audit report
├── scripts/
│   ├── collect_nys.py                 # Scrapes & parses StateJobsNY vacancies
│   ├── collect_nyc.py                 # Queries NYC Open Data Socrata APIs
│   ├── collect_federal.py             # Queries USAJOBS Series 2210 & Recent Grads
│   ├── collect_neogov.py              # Queries Nassau & Suffolk municipal feeds
│   ├── build_data.py                  # Deduplicates, assesses match, compiles bundle
│   └── monitor.py                     # Daily audit engine, deadline filter, changelog
├── index.html                         # Modern semantic single-page web portal
├── styles.css                         # Light-dark CSS tokens, responsive-table cards
├── app.js                             # Interactive client logic, dialog light-dismiss
└── README.md                          # Repository documentation
```

---

## Running Locally

To run the audit locally:
```bash
# Clone the repository
git clone https://github.com/frankstop/civic-opportunity-intelligence.git
cd civic-opportunity-intelligence

# Run the monitoring audit
python3 scripts/monitor.py

# Open the portal
open index.html
```
No external Python dependencies or pip packages are required (built strictly with the Python standard library).
