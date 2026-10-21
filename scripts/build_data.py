#!/usr/bin/env python3
"""Build the complete, deduplicated master data files for the Civic Opportunity Intelligence Portal:
  - data/opportunities.json
  - data/jurisdictions_50states.json
  - data/ny_municipalities.json
  - data/civic_participation.json
  - data/civic_education.json
  - data/data_bundle.js
"""
import json, re, datetime, pathlib, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
DATA.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date(2026, 10, 21)
TODAY_STR = TODAY.isoformat()

def parse_date(d_str):
    if not d_str:
        return None
    d_str = str(d_str).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", d_str)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})", d_str)
    if m:
        try:
            yr = int(m.group(3))
            if yr < 100:
                yr += 2000
            return datetime.date(yr, int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass
    m = re.match(r"^(\d{1,2})-([A-Za-z]{3})-(\d{4})", d_str)
    if m:
        months = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
        mon = months.get(m.group(2).upper())
        if mon:
            try:
                return datetime.date(int(m.group(3)), mon, int(m.group(1)))
            except ValueError:
                pass
    return None

def calc_urgency(dt):
    if not dt:
        return "OPEN"
    diff = (dt - TODAY).days
    if diff < 0:
        return "HISTORICAL"
    elif diff <= 7:
        return "CRITICAL_7D"
    elif diff <= 14:
        return "APPROACHING_14D"
    else:
        return "OPEN"

# ==========================================
# 1. BUILD JURISDICTIONS (50 STATES + DC)
# ==========================================
def build_50_states():
    seed_file = DATA / "states_seed.json"
    if seed_file.exists():
        raw_states = json.loads(seed_file.read_text())
    else:
        raw_states = []

    state_details = {
        "AL": {
            "merit_model": "Competitive Examination & Merit Register",
            "rule": "Rule of 10 for certification",
            "it_series": "IT Systems Specialist I-IV, Senior IT Specialist, Programmer/Analyst I-III",
            "residency_policy": "No general state residency requirement to apply; preference may be given to residents for certain positions.",
            "major_local_portals": [
                {"name": "Jefferson County (Birmingham)", "url": "https://www.jobsquest.org/"},
                {"name": "City of Mobile", "url": "https://www.cityofmobile.org/services/employment/"},
                {"name": "City of Huntsville", "url": "https://www.governmentjobs.com/careers/huntsville"}
            ]
        },
        "AK": {
            "merit_model": "Decentralized Workplace Alaska (Classification & Minimum Qualifications)",
            "rule": "Open applicant pools directly referred to hiring managers",
            "it_series": "Data Processing Manager, Micro/Network Specialist I-II, Analyst/Programmer I-V",
            "residency_policy": "Alaska resident preference applies under AS 39.25.150 for competitive positions.",
            "major_local_portals": [
                {"name": "Municipality of Anchorage", "url": "https://www.governmentjobs.com/careers/moa"},
                {"name": "Fairbanks North Star Borough", "url": "https://www.governmentjobs.com/careers/fnsb"}
            ]
        },
        "AZ": {
            "merit_model": "At-Will State Personnel System (State Openings on AZStateJobs)",
            "rule": "Direct qualification screening and agency interviews (No civil service exam)",
            "it_series": "Information Technology Specialist I-IV, Software Engineer, IT Systems Analyst",
            "residency_policy": "No state residency requirement; out-of-state applicants welcome.",
            "major_local_portals": [
                {"name": "Maricopa County (Phoenix)", "url": "https://www.governmentjobs.com/careers/maricopa"},
                {"name": "City of Phoenix", "url": "https://www.phoenix.gov/hr/current-jobs"},
                {"name": "Pima County (Tucson)", "url": "https://www.governmentjobs.com/careers/pima"}
            ]
        },
        "AR": {
            "merit_model": "Central Uniform Classification & Compensation",
            "rule": "Minimum qualification review with agency hiring discretion",
            "it_series": "Information Technology Specialist, Computer Support Specialist, Systems Programmer",
            "residency_policy": "No residency requirement to apply.",
            "major_local_portals": [
                {"name": "City of Little Rock", "url": "https://www.governmentjobs.com/careers/littlerock"},
                {"name": "Pulaski County", "url": "https://pulaskicounty.net/employment/"}
            ]
        },
        "CA": {
            "merit_model": "CalHR Merit System (Online Examination / Training & Experience Assessments)",
            "rule": "Rule of Three Ranks (Candidates scoring in Ranks 1-3 are reachable for hire)",
            "it_series": "Information Technology Technician, IT Associate, IT Specialist I/II/III, IT Supervisor I/II, IT Manager I/II",
            "residency_policy": "CalHR requires California residency for state civil service telework/remote positions; out-of-state applicants may apply but must relocate upon appointment.",
            "major_local_portals": [
                {"name": "County of Los Angeles", "url": "https://www.governmentjobs.com/careers/lacounty"},
                {"name": "City & County of San Francisco", "url": "https://careers.sf.gov/"},
                {"name": "Santa Clara County (Silicon Valley)", "url": "https://www.governmentjobs.com/careers/santaclara"},
                {"name": "City of San Diego", "url": "https://www.governmentjobs.com/careers/sandiego"}
            ]
        },
        "CO": {
            "merit_model": "Colorado Constitution Merit System (Comparative Analysis / Testing)",
            "rule": "Top 6 applicants (or all tied) referred to hiring supervisor",
            "it_series": "IT Professional I-VI, IT Technical Specialist, Systems Administrator",
            "residency_policy": "Colorado residency is required for state jobs unless non-residency waiver is explicitly granted.",
            "major_local_portals": [
                {"name": "City and County of Denver", "url": "https://www.governmentjobs.com/careers/denver"},
                {"name": "Arapahoe County", "url": "https://www.governmentjobs.com/careers/arapahoe"},
                {"name": "El Paso County (Colorado Springs)", "url": "https://www.governmentjobs.com/careers/elpasoco"}
            ]
        },
        "CT": {
            "merit_model": "CT DAS State Exam & JobAps Cloud Merit System",
            "rule": "Candidates qualify via Experience & Training (E&T) examinations to join candidate lists",
            "it_series": "Information Technology Analyst 1, 2, 3; Information Technology Subject Matter Expert; IT Supervisor",
            "residency_policy": "No Connecticut residency requirement to apply. Neighboring NY (Long Island / NYC / Westchester) residents actively commute or work hybrid.",
            "major_local_portals": [
                {"name": "City of Stamford", "url": "https://www.governmentjobs.com/careers/stamfordct"},
                {"name": "City of Bridgeport", "url": "https://www.bridgeportct.gov/careers"},
                {"name": "City of New Haven", "url": "https://www.newhavenct.gov/gov/depts/hr/job_postings.htm"}
            ]
        },
        "DE": {
            "merit_model": "Delaware Merit System (DHR Training & Experience Rating)",
            "rule": "Top 15 ranking candidates referred",
            "it_series": "Application Support Specialist I-III, Senior Systems Analyst, Database Administrator",
            "residency_policy": "Delaware residency is not required at time of application.",
            "major_local_portals": [
                {"name": "New Castle County", "url": "https://www.governmentjobs.com/careers/nccde"},
                {"name": "City of Wilmington", "url": "https://www.wilmingtonde.gov/government/city-jobs"}
            ]
        },
        "DC": {
            "merit_model": "District Personnel System (DCHR Career Service & Management Supervisory Service)",
            "rule": "Non-competitive and competitive merit ratings with District Resident Preference (10 points)",
            "it_series": "IT Specialist (Data/Apps/Security/Network) CS-2210-09 through 14",
            "residency_policy": "10-point preference for DC residents; certain senior appointees subject to DC residency requirement.",
            "major_local_portals": [
                {"name": "DC Government Careers (DCHR)", "url": "https://careers.dc.gov/"},
                {"name": "DC Water", "url": "https://www.dcwater.com/careers"},
                {"name": "Washington Metropolitan Area Transit Authority (WMATA)", "url": "https://www.wmata.com/about/careers/"}
            ]
        },
        "FL": {
            "merit_model": "Florida People First System (Selected Exempt Service & Career Service)",
            "rule": "Direct agency recruitment based on knowledge, skills, and abilities (No civil service exam)",
            "it_series": "Systems Programmer I-IV, Applications Developer, Database Analyst, Computer Operations Specialist",
            "residency_policy": "No Florida residency requirement to apply; out-of-state remote/hybrid positions subject to individual agency policy.",
            "major_local_portals": [
                {"name": "Miami-Dade County", "url": "https://www.miamidade.gov/global/humanresources/jobs/home.page"},
                {"name": "Orange County (Orlando)", "url": "https://www.governmentjobs.com/careers/orangecountyfl"},
                {"name": "Hillsborough County (Tampa)", "url": "https://www.governmentjobs.com/careers/hillsborough"}
            ]
        },
        "GA": {
            "merit_model": "Team Georgia Careers (At-will merit-based hiring across independent agencies)",
            "rule": "Direct application screening and structured interviews",
            "it_series": "IT Systems Support Professional 1-3, Application Developer 1-3, Database Administrator 1-3",
            "residency_policy": "No residency requirement to apply.",
            "major_local_portals": [
                {"name": "Fulton County (Atlanta)", "url": "https://www.governmentjobs.com/careers/fulton"},
                {"name": "City of Atlanta", "url": "https://www.atlantaga.gov/government/departments/human-resources/careers"},
                {"name": "Gwinnett County", "url": "https://www.governmentjobs.com/careers/gwinnett"}
            ]
        },
        "HI": {
            "merit_model": "Hawaii DHRD Merit System (Training & Experience Evaluations)",
            "rule": "Top 5 available candidates certified to appointing authority",
            "it_series": "Information Technology Specialist I-VI, Computer Programmer I-IV",
            "residency_policy": "Hawaii residency required under HRS § 78-1, but often waived for hard-to-fill IT specialties.",
            "major_local_portals": [
                {"name": "City and County of Honolulu", "url": "https://www.governmentjobs.com/careers/honolulu"}
            ]
        },
        "ID": {
            "merit_model": "Idaho Division of Human Resources Merit Exam & Register",
            "rule": "Top 25 ranking applicants certified to hiring agency",
            "it_series": "IT Systems Analyst, IT Software Engineer, IT Systems Integration Specialist",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "Ada County (Boise)", "url": "https://adacounty.id.gov/human-resources/jobs/"},
                {"name": "City of Boise", "url": "https://www.governmentjobs.com/careers/cityofboise"}
            ]
        },
        "IL": {
            "merit_model": "Illinois CMS Merit System (Work.Illinois.gov)",
            "rule": "Grade bands (A, B, C) based on electronic credential assessment; veterans and Grade A certified first",
            "it_series": "Information Technology Specialist I-III, Information Systems Analyst I-II, Programmer Analyst",
            "residency_policy": "Illinois residency required within 6 months of appointment unless waived for specialized IT roles.",
            "major_local_portals": [
                {"name": "Cook County (Chicago)", "url": "https://cookcountyil.taleo.net/careersection/200/jobsearch.ftl"},
                {"name": "City of Chicago", "url": "https://www.chicago.gov/city/en/depts/dhr/provdrs/emp.html"},
                {"name": "DuPage County", "url": "https://www.dupagecounty.gov/careers/"}
            ]
        },
        "IN": {
            "merit_model": "Indiana State Personnel Department (WorkforIndiana / SAP SuccessFactors)",
            "rule": "Direct screening based on minimum qualifications and competency interviews",
            "it_series": "Systems Analyst, Software Engineer, Senior Database Analyst, Network Engineer",
            "residency_policy": "No residency requirement; hybrid/remote work subject to agency agreement.",
            "major_local_portals": [
                {"name": "City of Indianapolis / Marion County", "url": "https://www.governmentjobs.com/careers/indianapolis"}
            ]
        },
        "IA": {
            "merit_model": "Iowa DAS Merit System (GovernmentJobs / NEOGOV)",
            "rule": "Eligible lists formed through minimum qualification score matching",
            "it_series": "Information Technology Specialist 1-5, Software Developer, Systems Analyst",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "Polk County (Des Moines)", "url": "https://www.governmentjobs.com/careers/polkcountyiowa"}
            ]
        },
        "KS": {
            "merit_model": "Kansas State Employee Service (State of Kansas Job Board)",
            "rule": "Agency-driven recruitment with veteran's preference",
            "it_series": "Applications Developer, Systems Administrator, Technology Support Consultant",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "Johnson County", "url": "https://www.governmentjobs.com/careers/jocogov"},
                {"name": "City of Wichita", "url": "https://www.governmentjobs.com/careers/wichita"}
            ]
        },
        "KY": {
            "merit_model": "Kentucky Personnel Cabinet (Merit System / Career Opportunities System)",
            "rule": "Top 5 certified applicants referred to hiring authority",
            "it_series": "Information Technology Applications Analyst, Database Administrator, Systems Engineer",
            "residency_policy": "Preference given to Kentucky residents; non-residents considered if insufficient qualified residents.",
            "major_local_portals": [
                {"name": "Louisville Metro Government", "url": "https://www.governmentjobs.com/careers/louisvilleky"},
                {"name": "Lexington-Fayette Urban County", "url": "https://www.governmentjobs.com/careers/lexingtonky"}
            ]
        },
        "LA": {
            "merit_model": "Louisiana State Civil Service (GovernmentJobs / NEOGOV)",
            "rule": "Civil service testing or professional experience screening; Rule of Top 5 grade bands",
            "it_series": "IT Technical Support Specialist 1-3, IT Applications Consultant, IT Database Administrator",
            "residency_policy": "No general state residency requirement to take civil service exams.",
            "major_local_portals": [
                {"name": "City of New Orleans", "url": "https://www.governmentjobs.com/careers/neworleans"},
                {"name": "East Baton Rouge Parish", "url": "https://www.governmentjobs.com/careers/brla"}
            ]
        },
        "ME": {
            "merit_model": "Maine Bureau of Human Resources (Direct Application & Civil Service Registers)",
            "rule": "Register scoring based on Training & Experience evaluations",
            "it_series": "Computer Programmer, Systems Analyst, Database Administrator, Public Health Informatics",
            "residency_policy": "No residency requirement to apply.",
            "major_local_portals": [
                {"name": "City of Portland", "url": "https://www.portlandmaine.gov/Jobs.aspx"}
            ]
        },
        "MD": {
            "merit_model": "Maryland State Personnel Management System (JobAps Cloud)",
            "rule": "Best Qualified / Better Qualified / Qualified category banding",
            "it_series": "IT Functional Analyst I-III, IT Systems Technical Specialist, Computer Network Specialist",
            "residency_policy": "No residency requirement; regional DC/MD/VA commuters common.",
            "major_local_portals": [
                {"name": "Montgomery County", "url": "https://www.montgomerycountymd.gov/HR/recruitment/MCGEO.html"},
                {"name": "Baltimore County", "url": "https://www.governmentjobs.com/careers/baltimorecounty"},
                {"name": "City of Baltimore", "url": "https://www.governmentjobs.com/careers/baltimorecity"}
            ]
        },
        "MA": {
            "merit_model": "Massachusetts Human Resources Division (MassCareers / Taleo)",
            "rule": "State agency positions are largely direct-hire; Municipal police/fire remain civil service exam",
            "it_series": "Software Developer I-IV, EDP Systems Analyst I-IV, Database Specialist, IT Project Manager",
            "residency_policy": "No general residency requirement for state positions; out-of-state candidates may apply.",
            "major_local_portals": [
                {"name": "City of Boston", "url": "https://www.boston.gov/departments/human-resources/career-opportunities"},
                {"name": "City of Worcester", "url": "https://www.worcesterma.gov/human-resources/employment-opportunities"}
            ]
        },
        "MI": {
            "merit_model": "Michigan Civil Service Commission (GovernmentJobs / NEOGOV)",
            "rule": "Merit screening pools based on minimum education and experience; Rule of 3 bands",
            "it_series": "Information Technology Programmer/Analyst 9-P11-12, IT Specialist 13, IT Project Manager",
            "residency_policy": "No Michigan residency requirement to apply.",
            "major_local_portals": [
                {"name": "Wayne County (Detroit)", "url": "https://www.governmentjobs.com/careers/waynecounty"},
                {"name": "City of Detroit", "url": "https://www.governmentjobs.com/careers/detroit"},
                {"name": "Oakland County", "url": "https://www.governmentjobs.com/careers/oakgov"}
            ]
        },
        "MN": {
            "merit_model": "Minnesota Management & Budget (State Careers Portal)",
            "rule": "Merit-based resume matching against job-specific qualifications",
            "it_series": "Information Technology Specialist 1-5 (Software, Data, Network, Security options)",
            "residency_policy": "No Minnesota residency requirement; out-of-state candidates eligible.",
            "major_local_portals": [
                {"name": "Hennepin County (Minneapolis)", "url": "https://www.governmentjobs.com/careers/hennepin"},
                {"name": "City of Minneapolis", "url": "https://www.governmentjobs.com/careers/cityofminneapolis"},
                {"name": "Ramsey County (St. Paul)", "url": "https://www.governmentjobs.com/careers/ramsey"}
            ]
        },
        "MS": {
            "merit_model": "Mississippi State Personnel Board (MSPB Merit System)",
            "rule": "Minimum qualification eligibility lists",
            "it_series": "Systems Programmer I-III, Network Specialist, Data Base Administrator",
            "residency_policy": "No state residency requirement.",
            "major_local_portals": [
                {"name": "City of Jackson", "url": "https://www.jacksonms.gov/employment-opportunities/"}
            ]
        },
        "MO": {
            "merit_model": "Missouri MO Careers (Division of Personnel / Taleo)",
            "rule": "Merit-based qualification screening",
            "it_series": "Computer Information Technologist I-III, Senior Systems Analyst, IT Project Manager",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "St. Louis County", "url": "https://www.governmentjobs.com/careers/stlouisco"},
                {"name": "City of Kansas City", "url": "https://www.kcmo.gov/city-hall/departments/human-resources/careers"}
            ]
        },
        "MT": {
            "merit_model": "Montana State Human Resources (Direct Agency Recruitment)",
            "rule": "Direct applicant screening and interviews",
            "it_series": "Computer Systems Analyst, Software Developer, Database Specialist",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "City of Billings", "url": "https://www.governmentjobs.com/careers/billingsmt"}
            ]
        },
        "NE": {
            "merit_model": "Nebraska State Personnel (Enterprise Jobs Portal)",
            "rule": "Minimum qualification matching; agency interviews",
            "it_series": "IT Applications Developer, IT Data Systems Analyst, IT Infrastructure Support",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "City of Omaha", "url": "https://www.cityofomaha.org/human-resources/employment"},
                {"name": "Douglas County", "url": "https://www.governmentjobs.com/careers/douglascountyne"}
            ]
        },
        "NV": {
            "merit_model": "Nevada DHRM (SuccessFactors / NV Careers)",
            "rule": "Training & Experience ranking or written exams",
            "it_series": "IT Professional I-IV, IT Technician I-VI, Business Process Analyst",
            "residency_policy": "No Nevada residency requirement to apply.",
            "major_local_portals": [
                {"name": "Clark County (Las Vegas)", "url": "https://www.governmentjobs.com/careers/clarkcounty"},
                {"name": "City of Las Vegas", "url": "https://www.governmentjobs.com/careers/lasvegas"},
                {"name": "Washoe County (Reno)", "url": "https://www.governmentjobs.com/careers/washoecounty"}
            ]
        },
        "NH": {
            "merit_model": "New Hampshire Division of Personnel (State Job Search)",
            "rule": "Minimum qualification certification to agency",
            "it_series": "Programmer/Analyst, Systems Analyst, Database Administrator",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "City of Manchester", "url": "https://www.manchesternh.gov/Departments/Human-Resources/Employment"}
            ]
        },
        "NJ": {
            "merit_model": "New Jersey Civil Service Commission (Title 11A / NJ CSC Online Application System)",
            "rule": "Rule of Three (Open-competitive and Promotional exam lists); Vet preference",
            "it_series": "Software Development Specialist 1-3, Information Technology Specialist, Analyst Trainee, Network Administrator",
            "residency_policy": "NJ First Act requires New Jersey residency within 365 days of appointment, but exemptions or waivers exist for hard-to-fill technical titles.",
            "major_local_portals": [
                {"name": "City of Newark", "url": "https://www.governmentjobs.com/careers/newarknj"},
                {"name": "Jersey City", "url": "https://www.jerseycitynj.gov/cityhall/HumanResources/employment"},
                {"name": "County of Bergen", "url": "https://www.co.bergen.nj.us/human-resources/job-opportunities"},
                {"name": "Port Authority of NY & NJ", "url": "https://www.jointheportauthority.com/"}
            ]
        },
        "NM": {
            "merit_model": "New Mexico State Personnel Office (NEOGOV / GovernmentJobs)",
            "rule": "Top 14 applicants referred based on qualification scoring",
            "it_series": "IT Generalist I-III, IT End User Support, IT Developer, IT Database Administrator",
            "residency_policy": "No residency requirement to apply.",
            "major_local_portals": [
                {"name": "City of Albuquerque", "url": "https://www.governmentjobs.com/careers/cabq"},
                {"name": "Bernalillo County", "url": "https://www.governmentjobs.com/careers/bernco"}
            ]
        },
        "NY": {
            "merit_model": "New York State Department of Civil Service (Civil Service Law § 61 Rule of Three + NY HELPS Exam Waiver)",
            "rule": "Rule of Three for competitive lists; NY HELPS waives exams for thousands of positions through June 30, 2028 with 1-year conversion to competitive tenure",
            "it_series": "Information Technology Specialist 1-4 (SG-14 to SG-25), Information Technology Architect 1-3, Data Analyst 1-4, Business Systems Analyst 1-3",
            "residency_policy": "New York State residency is NOT required for most state titles (unless mandated by statute); Nassau/Suffolk local competitive exams typically require 1-year county residency; NYC DCAS requires NYC residency within 90 days for certain titles, but tech titles frequently receive residency waivers.",
            "major_local_portals": [
                {"name": "Nassau County Civil Service", "url": "https://www.governmentjobs.com/careers/nassaucountyny"},
                {"name": "Suffolk County Civil Service", "url": "https://www.suffolkcountyny.gov/Departments/Civil-Service"},
                {"name": "Jobs NYC (DCAS)", "url": "https://cityjobs.nyc.gov/"},
                {"name": "Westchester County", "url": "https://www.governmentjobs.com/careers/westchester"},
                {"name": "Erie County (Buffalo)", "url": "https://www.erie.gov/employment/"},
                {"name": "Monroe County (Rochester)", "url": "https://www.governmentjobs.com/careers/monroecounty"}
            ]
        },
        "NC": {
            "merit_model": "North Carolina OSHR (GovernmentJobs / NEOGOV)",
            "rule": "Merit-based qualification screening and agency hiring",
            "it_series": "Technology Support Analyst/Specialist, Database Analyst, Software Systems Engineer",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "Mecklenburg County (Charlotte)", "url": "https://www.governmentjobs.com/careers/mecklenburg"},
                {"name": "Wake County (Raleigh)", "url": "https://www.governmentjobs.com/careers/wakecounty"},
                {"name": "City of Charlotte", "url": "https://www.governmentjobs.com/careers/charlotte"}
            ]
        },
        "ND": {
            "merit_model": "North Dakota HRMS (GovernmentJobs / NEOGOV)",
            "rule": "Direct qualification screening with veteran preference",
            "it_series": "Software Developer I-III, Database Administrator, Systems Administrator",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "City of Fargo", "url": "https://www.governmentjobs.com/careers/fargond"}
            ]
        },
        "OH": {
            "merit_model": "Ohio Department of Administrative Services (Careers.Ohio.gov / Taleo)",
            "rule": "Classified and unclassified merit positions",
            "it_series": "Software Development Specialist 1-4, Database Administrator 1-3, Infrastructure Specialist 1-3",
            "residency_policy": "No Ohio residency requirement to apply.",
            "major_local_portals": [
                {"name": "Franklin County (Columbus)", "url": "https://www.governmentjobs.com/careers/franklincounty"},
                {"name": "Cuyahoga County (Cleveland)", "url": "https://www.cuyahogacounty.gov/human-resources/careers"},
                {"name": "City of Columbus", "url": "https://www.governmentjobs.com/careers/columbus"}
            ]
        },
        "OK": {
            "merit_model": "Oklahoma OMES Human Capital Management (Workday Careers)",
            "rule": "Merit system examinations or training and experience qualification scoring",
            "it_series": "Software Engineer I-IV, Systems Analyst I-IV, Database Analyst I-IV",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "Oklahoma City", "url": "https://www.governmentjobs.com/careers/okc"},
                {"name": "Tulsa County", "url": "https://www.governmentjobs.com/careers/tulsacounty"}
            ]
        },
        "OR": {
            "merit_model": "Oregon Department of Administrative Services (Workday Careers)",
            "rule": "Direct application screening based on minimum and desired attributes",
            "it_series": "Information Systems Specialist 1-8 (covering Programming, Data, GIS, Systems)",
            "residency_policy": "Oregon residency not required to apply; state supports hybrid and some out-of-state remote work.",
            "major_local_portals": [
                {"name": "Multnomah County (Portland)", "url": "https://www.governmentjobs.com/careers/multnomah"},
                {"name": "City of Portland", "url": "https://www.governmentjobs.com/careers/portlandor"},
                {"name": "Washington County", "url": "https://www.governmentjobs.com/careers/washco"}
            ]
        },
        "PA": {
            "merit_model": "Pennsylvania Office of Administration (Employment.pa.gov / NEOGOV)",
            "rule": "Merit System Testing and Non-Exam Merit vacancies (T&E assessments)",
            "it_series": "Applications Developer 1-3, Database Analyst 1-2, IT Generalist 1-2, Network Specialist 1-2",
            "residency_policy": "Pennsylvania residency is required for merit system positions unless a non-residency waiver is explicitly advertised for hard-to-fill technical titles.",
            "major_local_portals": [
                {"name": "City of Philadelphia", "url": "https://www.phila.gov/jobs/"},
                {"name": "Allegheny County (Pittsburgh)", "url": "https://www.governmentjobs.com/careers/allegheny"},
                {"name": "City of Pittsburgh", "url": "https://www.governmentjobs.com/careers/pghpa"}
            ]
        },
        "RI": {
            "merit_model": "Rhode Island Division of Human Resources (GovernmentJobs / NEOGOV)",
            "rule": "Merit system lists created via competitive civil service exams and credential assessments",
            "it_series": "Software Developer I-III, Systems Programmer, Database Administrator",
            "residency_policy": "No Rhode Island residency requirement.",
            "major_local_portals": [
                {"name": "City of Providence", "url": "https://www.governmentjobs.com/careers/providenceri"}
            ]
        },
        "SC": {
            "merit_model": "South Carolina Division of State Human Resources (Careers.sc.gov / NEOGOV)",
            "rule": "Direct agency recruitment based on position minimum training and experience",
            "it_series": "Application Analyst I-III, Software Developer I-III, Database Administrator I-II",
            "residency_policy": "No South Carolina residency requirement.",
            "major_local_portals": [
                {"name": "Greenville County", "url": "https://www.governmentjobs.com/careers/greenvillecounty"},
                {"name": "Charleston County", "url": "https://www.governmentjobs.com/careers/charlestoncounty"}
            ]
        },
        "SD": {
            "merit_model": "South Dakota Bureau of Human Resources (State Job Board)",
            "rule": "Direct applicant screening and interviews",
            "it_series": "Computer Support Specialist, Systems Software Specialist, Database Coordinator",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "City of Sioux Falls", "url": "https://www.governmentjobs.com/careers/siouxfalls"}
            ]
        },
        "TN": {
            "merit_model": "Tennessee Department of Human Resources (Edison Careers / Oracle)",
            "rule": "Preferred Service (merit-based competitive hiring) and Executive Service",
            "it_series": "IT App Developer 1-3, IT Systems Admin 1-3, IT Database Admin 1-3",
            "residency_policy": "No residency requirement to apply.",
            "major_local_portals": [
                {"name": "Metropolitan Government of Nashville & Davidson County", "url": "https://www.governmentjobs.com/careers/nashville"},
                {"name": "Shelby County (Memphis)", "url": "https://www.governmentjobs.com/careers/shelbycounty"}
            ]
        },
        "TX": {
            "merit_model": "Texas CAPPS Central (Decentralized agency hiring; no statewide civil service commission)",
            "rule": "Direct agency application screening against state classification schedule",
            "it_series": "Programmer I-V (Class 0241-0245), Systems Analyst I-VII (Class 0251-0257), Database Administrator I-V (Class 0231-0235), Data Analyst I-IV (Class 0650-0653)",
            "residency_policy": "No Texas residency requirement to apply; out-of-state remote work allowed depending on agency policy.",
            "major_local_portals": [
                {"name": "City of Austin", "url": "https://www.austincityjobs.org/"},
                {"name": "Harris County (Houston)", "url": "https://www.governmentjobs.com/careers/harriscountytx"},
                {"name": "City of Dallas", "url": "https://www.governmentjobs.com/careers/dallas"},
                {"name": "Travis County (Austin)", "url": "https://www.governmentjobs.com/careers/traviscounty"}
            ]
        },
        "UT": {
            "merit_model": "Utah DHRM (GovernmentJobs / NEOGOV)",
            "rule": "Merit principles via qualification scoring and agency interviews",
            "it_series": "IT Systems Administrator I-III, Software Developer I-III, Database Manager",
            "residency_policy": "No Utah residency requirement.",
            "major_local_portals": [
                {"name": "Salt Lake County", "url": "https://www.governmentjobs.com/careers/slco"},
                {"name": "State of Utah (DHRM)", "url": "https://www.governmentjobs.com/careers/utah"}
            ]
        },
        "VT": {
            "merit_model": "Vermont Department of Human Resources (SuccessFactors / VTHR)",
            "rule": "Merit screening by minimum qualifications",
            "it_series": "IT Systems Developer I-IV, IT Database Administrator I-III, IT Systems Administrator",
            "residency_policy": "No residency requirement.",
            "major_local_portals": [
                {"name": "City of Burlington", "url": "https://www.governmentjobs.com/careers/burlingtonvt"}
            ]
        },
        "VA": {
            "merit_model": "Virginia DHRM (Jobs.Virginia.Gov / PageUp)",
            "rule": "Direct agency screening using Role Descriptions and Knowledge/Skills/Abilities",
            "it_series": "Information Technology Specialist I-IV (Role Codes 39111-39114), Systems Developer, Database Analyst",
            "residency_policy": "No Virginia residency requirement to apply.",
            "major_local_portals": [
                {"name": "Fairfax County", "url": "https://www.governmentjobs.com/careers/fairfaxcounty"},
                {"name": "City of Virginia Beach", "url": "https://www.governmentjobs.com/careers/vbgov"},
                {"name": "Loudoun County", "url": "https://www.governmentjobs.com/careers/loudoun"}
            ]
        },
        "WA": {
            "merit_model": "Washington State Office of Financial Management (Careers.wa.gov / NEOGOV)",
            "rule": "Direct agency screening with veteran preference; hard-to-fill IT titles expedited",
            "it_series": "Information Technology - Application Development (Journey / Senior / Specialist), IT Data Management, IT Architecture",
            "residency_policy": "Washington state residency is not required to apply; many state agencies offer remote telework agreements within specified approved states.",
            "major_local_portals": [
                {"name": "King County (Seattle)", "url": "https://www.governmentjobs.com/careers/kingcounty"},
                {"name": "City of Seattle", "url": "https://www.governmentjobs.com/careers/seattle"},
                {"name": "Pierce County (Tacoma)", "url": "https://www.governmentjobs.com/careers/piercecountywa"}
            ]
        },
        "WV": {
            "merit_model": "West Virginia Division of Personnel (GovernmentJobs / NEOGOV)",
            "rule": "Classified Service examination registers and score rankings",
            "it_series": "Information Systems Specialist 1-3, Programmer Analyst 1-2, Data Base Administrator",
            "residency_policy": "West Virginia residency given preference; non-residents may apply for technical titles.",
            "major_local_portals": [
                {"name": "City of Charleston", "url": "https://www.governmentjobs.com/careers/charlestonwv"}
            ]
        },
        "WI": {
            "merit_model": "Wisconsin Division of Personnel Management (Wisc.Jobs / JobAps Cloud)",
            "rule": "Civil service evaluations / Training & Experience assessments",
            "it_series": "IS Specialist (Data, Systems, Applications, Network, Security), IS Supervisor",
            "residency_policy": "No Wisconsin residency requirement to apply.",
            "major_local_portals": [
                {"name": "Milwaukee County", "url": "https://www.governmentjobs.com/careers/milwaukeecounty"},
                {"name": "City of Milwaukee", "url": "https://www.governmentjobs.com/careers/milwaukee"},
                {"name": "Dane County (Madison)", "url": "https://www.governmentjobs.com/careers/countyofdane"}
            ]
        },
        "WY": {
            "merit_model": "Wyoming Human Resources Division (GovernmentJobs / NEOGOV)",
            "rule": "State merit screening pools",
            "it_series": "Computer Technology Specialist, Software Development Specialist, Systems Analyst",
            "residency_policy": "Wyoming residency preference applied under state law; out-of-state considered.",
            "major_local_portals": [
                {"name": "City of Cheyenne", "url": "https://www.governmentjobs.com/careers/cheyenne"}
            ]
        }
    }

    full_states = []
    for s in raw_states:
        code = s["state"]
        detail = state_details.get(code, {})
        full_states.append({
            "code": code,
            "name": s["name"],
            "portal": s["portal"],
            "agency": s["agency"],
            "merit_model": detail.get("merit_model", "Merit System Screening"),
            "certification_rule": detail.get("rule", "Standard qualification screening"),
            "it_job_series": detail.get("it_series", "Information Technology Specialist, Systems Analyst, Software Developer"),
            "residency_policy": detail.get("residency_policy", "Check individual vacancy announcement"),
            "major_local_portals": detail.get("major_local_portals", []),
            "neogov_search_url": f"https://www.governmentjobs.com/jobs?location={s['name']}&keyword=software%20developer"
        })

    (DATA / "jurisdictions_50states.json").write_text(json.dumps(full_states, indent=2))
    print(f"Generated jurisdictions_50states.json with {len(full_states)} states.")
    return full_states

# ==========================================
# 2. BUILD NY MUNICIPALITIES DIRECTORY
# ==========================================
def build_ny_municipalities():
    ny_data = {
        "nassau_county": {
            "entity": "Nassau County Civil Service Commission",
            "portal": "https://www.governmentjobs.com/careers/nassaucountyny",
            "home_url": "https://www.nassaucivilservice.com/",
            "address": "40 Main Street, Hempstead, NY 11550",
            "rules": "Governed by Nassau County Civil Service Commission Rules. Standard open-competitive exams require one-year Nassau County residency prior to exam date. Application fee is $50.00 (waived for veterans, unemployed, public assistance). Continuous recruitment titles utilize Training & Experience evaluations.",
            "it_titles": [
                {"title": "Programmer Analyst", "level": "Competitive", "exam_type": "Continuous / Periodic", "typical_salary": "$65,000 - $85,000"},
                {"title": "Senior Programmer Analyst", "level": "Competitive", "exam_type": "Promotional / Open", "typical_salary": "$80,000 - $105,000"},
                {"title": "Information Technology Specialist I / II / III", "level": "Competitive", "exam_type": "Continuous / T&E", "typical_salary": "$60,000 - $95,000"},
                {"title": "Computer Systems Analyst", "level": "Competitive", "exam_type": "Periodic Exam", "typical_salary": "$75,000 - $100,000"},
                {"title": "Database Specialist", "level": "Competitive", "exam_type": "Periodic Exam", "typical_salary": "$85,000 - $115,000"}
            ],
            "towns_and_cities": [
                {"name": "Town of Hempstead", "type": "Town (Population ~790,000)", "hall": "1 Washington Street, Hempstead, NY 11550", "url": "https://hempsteadny.gov/", "civil_service": "Administered by Nassau County Civil Service Commission"},
                {"name": "Town of North Hempstead", "type": "Town (Population ~237,000)", "hall": "220 Plandome Road, Manhasset, NY 11030", "url": "https://www.northhempsteadny.gov/", "civil_service": "Administered by Nassau County Civil Service Commission"},
                {"name": "Town of Oyster Bay", "type": "Town (Population ~300,000)", "hall": "54 Audrey Avenue, Oyster Bay, NY 11771", "url": "https://oysterbaytown.com/", "civil_service": "Administered by Nassau County Civil Service Commission"},
                {"name": "City of Glen Cove", "type": "City", "hall": "9 Glen Street, Glen Cove, NY 11542", "url": "https://glencoveny.gov/", "civil_service": "Has municipal civil service commission affiliated with Nassau County"},
                {"name": "City of Long Beach", "type": "City", "hall": "1 West Chester Street, Long Beach, NY 11561", "url": "https://www.longbeachny.gov/", "civil_service": "City of Long Beach Civil Service Commission"}
            ],
            "major_villages": [
                {"name": "Inc. Village of Garden City", "url": "https://www.gardencityny.net/"},
                {"name": "Inc. Village of Freeport", "url": "https://www.freeportny.gov/"},
                {"name": "Inc. Village of Rockville Centre", "url": "https://www.rvcny.gov/"},
                {"name": "Inc. Village of Mineola", "url": "https://www.mineola-ny.gov/"},
                {"name": "Inc. Village of Valley Stream", "url": "https://www.valleystreamny.gov/"},
                {"name": "Inc. Village of Great Neck", "url": "https://www.greatneckvillage.org/"}
            ],
            "educational_entities": [
                {"name": "Nassau BOCES", "url": "https://www.nassauboces.org/", "job_portal": "https://www.olasjobs.org/nassau-boces"},
                {"name": "Nassau Community College", "url": "https://www.ncc.edu/", "job_portal": "https://ncc.edu/about/employment/"}
            ]
        },
        "suffolk_county": {
            "entity": "Suffolk County Department of Civil Service",
            "portal": "https://apps2.suffolkcountyny.gov/civilservice/efile/default.aspx",
            "home_url": "https://www.suffolkcountyny.gov/Departments/Civil-Service",
            "workday_portal": "https://suffolkcountyny.wd1.myworkdayjobs.com/Suffolkcounty1",
            "address": "North County Complex, 725 Veterans Memorial Highway, Building 158, Hauppauge, NY 11788",
            "rules": "Governed by Suffolk County Civil Service Rules. Open-competitive examinations require Suffolk County residency for at least 30 to 90 days (and sometimes 1 year) prior to date of exam, unless residency is waived. Standard exam application fee is $40.00 ($125 for Police). Non-competitive positions, NY HELPS waiver appointments, and provisional hires apply directly through Suffolk County Workday.",
            "it_titles": [
                {"title": "Programmer Analyst", "spec_no": "0440", "level": "Competitive", "exam_type": "Continuous / T&E", "typical_salary": "$68,000 - $88,000"},
                {"title": "Senior Programmer Analyst", "spec_no": "0442", "level": "Competitive", "exam_type": "Promotional / Open", "typical_salary": "$82,000 - $106,000"},
                {"title": "Network and Systems Specialist", "spec_no": "0450", "level": "Competitive", "exam_type": "Continuous / T&E", "typical_salary": "$62,000 - $92,000"},
                {"title": "Database Administrator", "spec_no": "0460", "level": "Competitive", "exam_type": "Open Competitive", "typical_salary": "$88,000 - $118,000"},
                {"title": "Applications Support Specialist", "spec_no": "0445", "level": "Competitive", "exam_type": "Periodic Exam", "typical_salary": "$58,000 - $80,000"}
            ],
            "towns": [
                {"name": "Town of Babylon", "type": "Town (Population ~218,000)", "hall": "200 Sunrise Highway, Lindenhurst, NY 11757", "url": "https://www.townofbabylon.com/", "civil_service": "Administered by Suffolk County Civil Service"},
                {"name": "Town of Brookhaven", "type": "Town (Population ~485,000)", "hall": "1 Independence Hill, Farmingville, NY 11738", "url": "https://www.brookhavenny.gov/", "civil_service": "Administered by Suffolk County Civil Service"},
                {"name": "Town of Huntington", "type": "Town (Population ~203,000)", "hall": "100 Main Street, Huntington, NY 11743", "url": "https://www.huntingtonny.gov/", "civil_service": "Administered by Suffolk County Civil Service"},
                {"name": "Town of Islip", "type": "Town (Population ~339,000)", "hall": "655 Main Street, Islip, NY 11751", "url": "https://islipny.gov/", "civil_service": "Administered by Suffolk County Civil Service"},
                {"name": "Town of Riverhead", "type": "Town (Population ~35,000)", "hall": "200 Howell Avenue, Riverhead, NY 11901", "url": "https://www.townofriverheadny.gov/", "civil_service": "Administered by Suffolk County Civil Service"},
                {"name": "Town of Smithtown", "type": "Town (Population ~116,000)", "hall": "99 West Main Street, Smithtown, NY 11787", "url": "https://www.smithtownny.gov/", "civil_service": "Administered by Suffolk County Civil Service"},
                {"name": "Town of Southampton", "type": "Town (Population ~58,000)", "hall": "116 Hampton Road, Southampton, NY 11968", "url": "https://www.southamptontownny.gov/", "civil_service": "Administered by Suffolk County Civil Service"},
                {"name": "Town of Southold", "type": "Town (Population ~23,000)", "hall": "53095 Main Road, Southold, NY 11971", "url": "https://www.southoldtownny.gov/", "civil_service": "Administered by Suffolk County Civil Service"},
                {"name": "Town of East Hampton", "type": "Town (Population ~28,000)", "hall": "159 Pantigo Road, East Hampton, NY 11937", "url": "https://ehamptonny.gov/", "civil_service": "Administered by Suffolk County Civil Service"},
                {"name": "Town of Shelter Island", "type": "Town (Population ~3,200)", "hall": "38 North Ferry Road, Shelter Island, NY 11964", "url": "https://www.shelterislandtown.gov/", "civil_service": "Administered by Suffolk County Civil Service"}
            ],
            "major_villages": [
                {"name": "Inc. Village of Patchogue", "url": "https://www.patchoguevillage.org/"},
                {"name": "Inc. Village of Lindenhurst", "url": "https://villageoflindenhurstny.gov/"},
                {"name": "Inc. Village of Babylon", "url": "https://villageofbabylonny.gov/"},
                {"name": "Inc. Village of Port Jefferson", "url": "https://portjeff.com/"},
                {"name": "Inc. Village of Amityville", "url": "https://amityville.com/"}
            ],
            "educational_entities": [
                {"name": "Eastern Suffolk BOCES", "url": "https://www.esboces.org/", "job_portal": "https://www.olasjobs.org/eastern-suffolk-boces"},
                {"name": "Western Suffolk BOCES", "url": "https://www.wsboces.org/", "job_portal": "https://www.olasjobs.org/western-suffolk-boces"},
                {"name": "Suffolk County Community College", "url": "https://www.sunysuffolk.edu/", "job_portal": "https://www.sunysuffolk.edu/about-succ/employment/"}
            ]
        },
        "public_authorities_and_labs": [
            {
                "name": "Metropolitan Transportation Authority (MTA / LIRR)",
                "type": "Public Benefit Corporation",
                "portal": "https://careers.mta.org/",
                "open_data": "https://new.mta.info/transparency/open-data",
                "developer_api": "https://api.mta.info/",
                "it_structure": "Direct hire (exempt from standard DCAS civil service examinations). Offers software engineering, data systems, transit telematics, and cybersecurity roles across MTA IT, Long Island Rail Road (LIRR), Metro-North, and NYC Transit.",
                "headquarters": "2 Broadway, New York, NY 10004 & Jamaica Station, Queens (LIRR HQ)"
            },
            {
                "name": "Brookhaven National Laboratory (BNL)",
                "type": "U.S. Department of Energy (DOE) National Laboratory / Brookhaven Science Associates",
                "portal": "https://jobs.bnl.gov/",
                "location": "Upton, NY (Town of Brookhaven, Long Island)",
                "it_structure": "Non-profit research laboratory operated under DOE prime contract. Hires scientific programmers, cloud software engineers, HPC specialists, Python/C++ developers, and data pipeline engineers. Not subject to NY state civil service exams; standard technical interviews and direct application.",
                "usajobs_crosslist": "Select senior roles and fellowships cross-post to USAJOBS Series 1550/2210."
            },
            {
                "name": "Port Authority of New York and New Jersey (PANYNJ)",
                "type": "Bi-State Compact Authority",
                "portal": "https://www.jointheportauthority.com/",
                "it_structure": "Bi-state entity exempt from NY and NJ civil service laws. Direct application with competitive technical interviews. Operates JFK, LaGuardia, Newark, Port Authority Bus Terminal, PATH, and Hudson River crossings.",
                "headquarters": "4 World Trade Center, 150 Greenwich Street, New York, NY 10007"
            },
            {
                "name": "Long Island Power Authority (LIPA) / PSEG Long Island",
                "type": "Municipal Electric Provider / Public Authority",
                "portal": "https://www.lipower.org/about-us/careers/ & https://pseg.wd1.myworkdayjobs.com/PSEG_Careers",
                "it_structure": "LIPA is a state public authority; electric grid operations are contracted to PSEG Long Island. Hires smart-grid software engineers, GIS analysts, SCADA engineers, and data analysts.",
                "headquarters": "Uniondale, NY 11556"
            },
            {
                "name": "Suffolk County Water Authority (SCWA)",
                "type": "Public Benefit Corporation",
                "portal": "https://www.scwa.com/careers/",
                "it_structure": "Operates under Suffolk County Civil Service Commission guidelines with competitive, non-competitive, and labor class positions for IT infrastructure, GIS, water modeling, and enterprise ERP systems.",
                "headquarters": "4060 Sunrise Highway, Oakdale, NY 11769"
            },
            {
                "name": "New York Power Authority (NYPA)",
                "type": "State Public Power Authority",
                "portal": "https://www.nypa.gov/careers",
                "it_structure": "Direct-hire authority positions covering grid software, telemetry, renewable energy analytics, and cybersecurity.",
                "headquarters": "123 Main Street, White Plains, NY 10601 with Long Island transmission facilities"
            }
        ],
        "higher_education_institutions": [
            {
                "name": "Stony Brook University (SUNY Stony Brook)",
                "type": "Flagship State University / Academic Medical Center",
                "portal": "https://employment.stonybrook.edu/ & https://statejobs.ny.gov/",
                "it_structure": "Positions fall under SUNY Unclassified Service (Professional SL ranks: SL-1 Assistant, SL-2 Programmer/Analyst, SL-3 Senior Programmer/Analyst, SL-4 Lead Programmer/Analyst, SL-5 Assistant Director) or classified NYS civil service. Exempt from NY HELPS competitive exams; evaluated directly by department committees.",
                "location": "Stony Brook, NY 11794 (Town of Brookhaven)"
            },
            {
                "name": "Farmingdale State College (SUNY)",
                "type": "State University of New York College of Technology",
                "portal": "https://farmingdale.interviewexchange.com/ & https://statejobs.ny.gov/",
                "it_structure": "SUNY Professional service SL ranks and classified state civil service positions in campus IT, network operations, and instructional technologies.",
                "location": "Farmingdale, NY 11735 (Town of Babylon/Oyster Bay border)"
            },
            {
                "name": "SUNY Old Westbury",
                "type": "State University of New York College",
                "portal": "https://oldwestbury.interviewexchange.com/ & https://statejobs.ny.gov/",
                "it_structure": "Campus computing and institutional research data positions under SUNY Professional titles.",
                "location": "Old Westbury, NY 11568 (Town of Oyster Bay / North Hempstead)"
            },
            {
                "name": "City University of New York (CUNY Central & 25 Campuses)",
                "type": "Public University System",
                "portal": "https://cuny.jobs/",
                "it_structure": "Hires under CUNY Classified Civil Service (e.g. IT Assistant, IT Associate, IT Senior Associate, IT Specialist) and Non-Teaching Instructional (HEO / Higher Education Officer series: Assistant to HEO, HEa, HEo). CUNY administers its own civil service examinations separate from NYC DCAS.",
                "headquarters": "205 East 42nd Street, New York, NY 10017 with campuses in Queens, Brooklyn, Manhattan, Bronx, Staten Island"
            }
        ],
        "other_major_ny_counties": [
            {"county": "Westchester County", "seat": "White Plains", "portal": "https://www.governmentjobs.com/careers/westchester", "notes": "Active IT department; uses GovernmentJobs for civil service and open postings."},
            {"county": "Rockland County", "seat": "New City", "portal": "https://www.rocklandcountyny.gov/departments/personnel", "notes": "Administers exams for county, towns (Clarkstown, Ramapo, Orangetown), and villages."},
            {"county": "Orange County", "seat": "Goshen", "portal": "https://www.orangecountygov.com/1126/Civil-Service-Examinations", "notes": "Administers civil service across Orange County."},
            {"county": "Dutchess County", "seat": "Poughkeepsie", "portal": "https://www.governmentjobs.com/careers/dutchessny", "notes": "Publishes exams and vacancies on GovernmentJobs."},
            {"county": "Albany County", "seat": "Albany", "portal": "https://www.albanycounty.com/departments/human-resources/civil-service", "notes": "Administers local county, city of Albany, and town civil service."},
            {"county": "Erie County", "seat": "Buffalo", "portal": "https://www.erie.gov/employment/", "notes": "Second largest county by population in Upstate NY; extensive municipal IT services."},
            {"county": "Monroe County", "seat": "Rochester", "portal": "https://www.governmentjobs.com/careers/monroecounty", "notes": "Active NEOGOV portal with frequent IT Programmer Analyst and Network exams."},
            {"county": "Onondaga County", "seat": "Syracuse", "portal": "https://www.employment.ongov.net/", "notes": "Administers civil service for Syracuse and Onondaga County."}
        ]
    }

    (DATA / "ny_municipalities.json").write_text(json.dumps(ny_data, indent=2))
    print("Generated ny_municipalities.json.")
    return ny_data

# ==========================================
# 3. BUILD CIVIC PARTICIPATION DATA (TRACK 2)
# ==========================================
def build_civic_participation():
    civic = [
        {
            "id": "CIVIC-BETA-01",
            "category": "CIVIC_TECH_VOLUNTEER",
            "title": "BetaNYC Civic Innovation Lab & Open Data Ambassadors",
            "entity": "BetaNYC (in partnership with NYC Office of Technology and Innovation - OTI)",
            "location": "NYC & Regional / Virtual (Slack & Zoom)",
            "description": "BetaNYC is New York's premier civic tech and open data organization. Programs include Open Data Ambassadors (volunteers trained to teach community members how to navigate and query NYC Open Data), Civic Innovation Fellows, and Research & Data Assistance Requests (RADAR) assisting NYC Community Boards with GIS and data tools.",
            "what_it_involves": "Attend free training cohorts to become a certified Open Data Ambassador; assist community boards with spatial data analysis and public dashboards; participate in civic hack nights and the annual NYC School of Data conference.",
            "who_may_participate": "Open to all technologists, software engineers, data analysts, students, and civic-minded residents. No prior government experience required.",
            "how_to_get_involved": "Join the BetaNYC Slack at https://slack.beta.nyc/; register for Open Data Ambassador cohorts at https://beta.nyc/programs/open-data-ambassadors/; attend monthly community meetups.",
            "costs": "$0 (100% Free; School of Data conference offers free/sliding-scale community tickets).",
            "restrictions": "Volunteers must adhere to the BetaNYC Code of Conduct. Non-partisan.",
            "schedule": "Ongoing Slack community; monthly community calls; Open Data Week & NYC School of Data held annually in March.",
            "official_url": "https://beta.nyc/",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-USDR-02",
            "category": "CIVIC_TECH_VOLUNTEER",
            "title": "U.S. Digital Response (USDR) Pro-Bono Technical Sprints",
            "entity": "U.S. Digital Response (Non-partisan 501(c)(3))",
            "location": "Remote / Nationwide (matches with state, county, and local governments)",
            "description": "USDR connects experienced pro-bono software engineers, data architects, product managers, and UX designers with government agencies to deliver urgent public software and data systems.",
            "what_it_involves": "Deploying on focused 4-to-12 week sprints (typically 5 to 15 hours/week) building automated workflows, modernizing public benefits portals, designing crisis response data pipelines, and implementing open source civic tools.",
            "who_may_participate": "Technical professionals with software development, database engineering, product design, or operations experience.",
            "how_to_get_involved": "Complete the volunteer intake form at https://www.usdigitalresponse.org/volunteer. USDR reviews technical profiles and matches volunteers directly with active agency requests.",
            "costs": "$0 (100% Volunteer; pro-bono).",
            "restrictions": "Requires skills assessment, background review, and strict confidentiality / non-disclosure compliance regarding sensitive government data.",
            "schedule": "Rolling volunteer onboarding; projects match continuously based on agency needs.",
            "official_url": "https://www.usdigitalresponse.org/",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-OWASP-03",
            "category": "CIVIC_TECH_VOLUNTEER",
            "title": "OWASP Long Island & New York City Chapter Meetups & Workshops",
            "entity": "Open Worldwide Application Security Project (OWASP)",
            "location": "Long Island (Adelphi / Hofstra / hybrid) & NYC (Manhattan / Brooklyn)",
            "description": "OWASP local chapters provide free, open technical talks, secure coding clinics, API security workshops, and application architecture discussions.",
            "what_it_involves": "Participating in community discussions on application defense, cloud automation, vulnerability mitigation, and networking with security engineers working across regional public agencies and defense laboratories.",
            "who_may_participate": "Open to all developers, software engineers, and IT professionals. No membership fee required.",
            "how_to_get_involved": "Visit OWASP Long Island (https://owasp.org/www-chapter-long-island/) or OWASP NYC (https://owasp.org/www-chapter-new-york-city/) and RSVP via Meetup.",
            "costs": "$0 (Free and open to the general public).",
            "restrictions": "None.",
            "schedule": "Bi-monthly or quarterly evening meetings.",
            "official_url": "https://owasp.org/www-chapter-long-island/",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-SUFFOLK-LEG-04",
            "category": "COMMITTEE_BOARD",
            "title": "Suffolk County Legislature: Government Operations, Personnel, Information Tech & Diversity Committee",
            "entity": "Suffolk County Legislature",
            "location": "William H. Rogers Legislature Building (Hauppauge) & Maxine S. Postal Auditorium (Riverhead)",
            "description": "The standing committee of the Suffolk County Legislature responsible for oversight of the Department of Information Technology, county cybersecurity policies, telecommunications infrastructure, civil service administration, and county personnel systems.",
            "what_it_involves": "Attending public committee sessions to observe legislative debates on county IT contracts, cybersecurity audits, and technology capital programs; testifying during the 3-minute public portion on county IT operations, open data access, and digital service delivery.",
            "who_may_participate": "Open to all Suffolk County residents, civic technologists, and taxpayers.",
            "how_to_get_involved": "Review published meeting agendas at https://www.scnylegislature.us/; submit a speaker card to the Clerk before the meeting starts; or register for remote public comment via Zoom on the legislature's portal.",
            "costs": "$0 (Free public access).",
            "restrictions": "Speakers are limited strictly to 3 minutes; comments must adhere to decorum.",
            "schedule": "Meets bi-weekly on designated legislative committee days (alternating between Hauppauge and Riverhead).",
            "official_url": "https://www.scnylegislature.us/",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-NASSAU-LEG-05",
            "category": "PUBLIC_MEETING_HEARING",
            "title": "Nassau County Legislature Public Hearings & Committee Sessions",
            "entity": "Nassau County Legislature",
            "location": "Theodore Roosevelt Executive and Legislative Building, 1550 Franklin Avenue, Mineola, NY 11501",
            "description": "Full legislative sessions and committees (including Rules, Finance, and Government Operations) where county budgets, technology contracts, IT capital borrowings, and local laws are introduced, debated, and voted upon.",
            "what_it_involves": "Exercising public participation rights under NYS Open Meetings Law; submitting written testimony to LegPublicComment@nassaucountyny.gov; giving 3-minute public comment on county IT infrastructure, data transparency, or assessment modernization.",
            "who_may_participate": "Open to all Nassau County residents, civic advocates, and members of the public.",
            "how_to_get_involved": "Attend in-person in the Peter J. Schmitt Memorial Legislative Chamber in Mineola; fill out a speaker slip at the dais prior to the session start.",
            "costs": "$0.",
            "restrictions": "3-minute time limit per speaker; non-transferable.",
            "schedule": "Meetings are typically held on Mondays at 1:00 PM according to the annual legislative calendar.",
            "official_url": "https://www.nassaucountyny.gov/489/County-Legislature",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-NYCCOUNCIL-TECH-06",
            "category": "PUBLIC_MEETING_HEARING",
            "title": "NYC Council Committee on Technology Oversight Hearings",
            "entity": "New York City Council (Committee on Technology)",
            "location": "City Hall / 250 Broadway, New York, NY & Hybrid Remote via Zoom",
            "description": "The NYC Council Committee on Technology oversees the Office of Technology and Innovation (OTI), 311, public broadband equity, municipal artificial intelligence algorithms (Local Law 144 compliance), and citywide open data standards.",
            "what_it_involves": "Testifying on municipal software implementations, automated decision-making systems, cybersecurity readiness, and open source adoption. Public testimony can be delivered in-person or remotely via Zoom.",
            "who_may_participate": "Open to the public; technical professionals and civic technologists are particularly encouraged to submit expert testimony.",
            "how_to_get_involved": "Register at https://council.nyc.gov/testify/ at least 24 hours prior to the hearing; or submit written testimony (PDF/Word) via email up to 72 hours following the hearing adjournment.",
            "costs": "$0.",
            "restrictions": "Oral testimony is typically 2 to 3 minutes.",
            "schedule": "Hearings scheduled monthly during council sessions; tracked on https://legistar.council.nyc.gov/.",
            "official_url": "https://council.nyc.gov/testify/",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-LIRRCC-PCAC-07",
            "category": "COMMITTEE_BOARD",
            "title": "Long Island Rail Road Commuter Council (LIRRCC) / PCAC",
            "entity": "Permanent Citizens Advisory Committee to the MTA (PCAC) / LIRRCC",
            "location": "Long Island / NYC (2 Broadway & hybrid)",
            "description": "Statutory body established by the NYS Legislature under Public Authorities Law § 1266-d to represent LIRR riders directly to the MTA Board. Council members hold a non-voting seat on the MTA Board.",
            "what_it_involves": "Advocating for transit technology modernization (train-tracking APIs, contactless ticketing, schedule automation, onboard Wi-Fi); attending public meetings; applying for vacant council seats recommended by County Executives to the Governor.",
            "who_may_participate": "Commuters residing in Nassau and Suffolk counties. Public meetings are open to all riders.",
            "how_to_get_involved": "Attend monthly public meetings; monitor board vacancy recommendations via the Nassau or Suffolk County Executive offices; subscribe to updates at https://pcac.org/.",
            "costs": "$0.",
            "restrictions": "Official membership requires gubernatorial appointment upon county executive recommendation.",
            "schedule": "Monthly council meetings; regular presentations before MTA Board committees.",
            "official_url": "https://pcac.org/councils/lirrcc/",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-OPENDATA-08",
            "category": "OPEN_DATA_INITIATIVE",
            "title": "NYS Open Data (data.ny.gov) & NYC Open Data Portals",
            "entity": "NYS Office of Information Technology Services & NYC Office of Technology and Innovation",
            "location": "Online API Portals (data.ny.gov & opendata.cityofnewyork.us)",
            "description": "State and city statutory open data platforms exposing thousands of public datasets via Socrata Open Data APIs (SODA), GeoJSON, and CSV endpoints covering transportation, budgets, payroll, health, environment, and building permits.",
            "what_it_involves": "Consuming public APIs to build civic applications; requesting new government datasets via formal Open Data Requests; reporting data quality anomalies; contributing open source analysis to public data repositories.",
            "who_may_participate": "Open to all developers, data scientists, researchers, and citizens.",
            "how_to_get_involved": "Create a free Socrata app token for high-rate API querying; browse datasets at https://data.ny.gov/ and https://opendata.cityofnewyork.us/.",
            "costs": "$0 (Free public API access).",
            "restrictions": "Standard API rate limits (unauthenticated ~1,000 req/hr; free app token allows unlimited typical research querying).",
            "schedule": "Datasets updated daily/weekly; NYC Open Data Week held annually every March.",
            "official_url": "https://opendata.cityofnewyork.us/",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-PROCUREMENT-09",
            "category": "PROCUREMENT_RFP",
            "title": "NYS Contract Reporter (NYSCR) & Discretionary IT Contracting",
            "entity": "NYS Empire State Development & NYS Office of General Services (OGS)",
            "location": "Statewide / Online Portal (nyscr.ny.gov)",
            "description": "The official publication portal for all New York State agency, public authority, and state university procurements valued at $50,000 or greater. Also details informal/discretionary purchasing thresholds.",
            "what_it_involves": "Setting up free daily email alerts for software development, IT consulting, cloud infrastructure, and database RFPs; learning how small businesses and individual contractors submit bids; exploring OGS backdrop contracts (PBITS - Project Based Information Technology Services and HBITS - Hourly Based IT Services).",
            "who_may_participate": "Registered vendors, software development consultancies, independent technical contractors, and small businesses.",
            "how_to_get_involved": "Register a free account at https://www.nyscr.ny.gov/; set up search filters under Category: 'Information Technology' and 'Consulting Services'.",
            "costs": "$0 (100% Free vendor registration on nyscr.ny.gov; never pay third-party bid aggregators for state bids).",
            "restrictions": "Must meet standard NYS vendor responsibility criteria and insurance requirements when submitting formal proposals.",
            "schedule": "Procurement notices published business days at 4:00 PM; bidding windows typically range from 15 to 45 business days.",
            "official_url": "https://www.nyscr.ny.gov/",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-PASSPORT-10",
            "category": "PROCUREMENT_RFP",
            "title": "NYC PASSPort & City Record Online (CROL) Tech Solicitations",
            "entity": "NYC Mayor's Office of Contract Services (MOCS)",
            "location": "New York City / Online (nyc.gov/passport & a856-cityrecord.nyc.gov)",
            "description": "PASSPort is New York City's digital procurement system where all city agencies issue Requests for Proposals (RFPs), solicit bids, and award technology and professional services contracts.",
            "what_it_involves": "Reviewing active technology RFPs across NYC OTI, Department of Education, Police, Health, and Transportation; registering a vendor profile to be eligible for discretionary technology awards (up to $1,500,000 for certified M/WBEs).",
            "who_may_participate": "Technology firms, solo software contractors, and consulting partnerships.",
            "how_to_get_involved": "Register for a free NYC.ID and create a PASSPort account at https://www.nyc.gov/passport; search solicitations on City Record Online at https://a856-cityrecord.nyc.gov/.",
            "costs": "$0 (Free vendor account and bidding).",
            "restrictions": "Contract awards require completing standard VENDEX background disclosures in PASSPort.",
            "schedule": "City Record published daily.",
            "official_url": "https://www.nyc.gov/passport",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-TRAIN-CISA-11",
            "category": "PUBLIC_TRAINING",
            "title": "CISA Learning / FedVTE Cybersecurity & Systems Training",
            "entity": "Cybersecurity and Infrastructure Security Agency (CISA)",
            "location": "Online / On-demand (cisa.usalearning.gov)",
            "description": "Federal government cyber and IT training portal providing free self-paced courses, certification preparation (CompTIA Security+, CISSP, CEH), cloud security architecture, and incident response curricula.",
            "what_it_involves": "Completing video modules, practical labs, and practice assessments in cloud security, secure coding, digital forensics, and network telemetry.",
            "who_may_participate": "Public courses are open to all U.S. citizens; expanded full catalogs are accessible to state/local/tribal government employees, military veterans, and government contractors.",
            "how_to_get_involved": "Access free public courses via the CISA training portal at https://niccs.cisa.gov/education-training/catalog.",
            "costs": "$0 (100% Free federal training).",
            "restrictions": "Certain restricted courses require government (.gov/.mil) email verification.",
            "schedule": "Self-paced on-demand 24/7.",
            "official_url": "https://niccs.cisa.gov/",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-TRAIN-NYSDOL-12",
            "category": "PUBLIC_TRAINING",
            "title": "NYS Department of Labor Free Coursera Upskilling Initiative",
            "entity": "New York State Department of Labor (NYSDOL) in partnership with Coursera",
            "location": "Online / On-demand (dol.ny.gov/online-learning)",
            "description": "NYS DOL provides New York State residents with 100% free access to over 4,000 Coursera courses and professional certificate programs from Google, IBM, AWS, and leading universities.",
            "what_it_involves": "Earning verified industry certificates in Python programming, Google Data Analytics, Google Cloud Engineering, Cyber Defense, and Agile Project Management without paying course or certificate fees.",
            "who_may_participate": "Any New York State resident (employed, underemployed, or looking for career advancement).",
            "how_to_get_involved": "Register using a free NY.gov ID at https://dol.ny.gov/online-learning. Invitations to activate the Coursera license are typically emailed within 24 to 48 hours.",
            "costs": "$0 (100% Funded by NY State).",
            "restrictions": "Must maintain active progress to keep the free Coursera seat.",
            "schedule": "Continuous enrollment.",
            "official_url": "https://dol.ny.gov/online-learning",
            "verified_at": TODAY_STR
        },
        {
            "id": "CIVIC-PROJECT-LI-13",
            "category": "COMMUNITY_AUTOMATION_PROJECT",
            "title": "Long Island Municipal Meeting Tracker & Agenda Scraper",
            "entity": "Community Tech Project Blueprint (Long Island Civic Tech)",
            "location": "Nassau & Suffolk Counties / Open Source",
            "description": "A community-focused open source automation project to scrape, index, and alert residents to published agendas and meeting documents across Long Island's 13 Town Boards and 2 County Legislatures.",
            "what_it_involves": "Writing Python scrapers (BeautifulSoup/Playwright) to monitor Town of Hempstead, Oyster Bay, Huntington, and Brookhaven clerk portals; extracting PDF agendas; generating automated keyword alerts (e.g. 'zoning', 'sewer', 'technology', 'water'); publishing clean RSS/webhook feeds for civic groups.",
            "who_may_participate": "Open source software developers, Python/TypeScript programmers, and civic volunteers.",
            "how_to_get_involved": "Build and release under an open source license (MIT/GPL); connect with regional civic groups and local news non-profits (e.g. Long Island Press, Patch, local civic associations).",
            "costs": "$0.",
            "restrictions": "Must comply with website terms and polite scraping rate limits (e.g., 1-second delays).",
            "schedule": "Community-driven open source cadence.",
            "official_url": "https://github.com/",
            "verified_at": TODAY_STR
        }
    ]

    (DATA / "civic_participation.json").write_text(json.dumps(civic, indent=2))
    print(f"Generated civic_participation.json with {len(civic)} entries.")
    return civic

# ==========================================
# 4. BUILD CIVIC EDUCATION DATA (TRACK 3)
# ==========================================
def build_civic_education():
    modules = [
        {
            "topic_id": "CIVIC-EDU-01",
            "week_number": 1,
            "title": "How Civil-Service Examinations and Eligible Lists Function",
            "summary": "Understand the constitutional merit system, the Rule of Three, continuous recruitment, eligible list lifespans, and why NY HELPS represents an unprecedented window of opportunity.",
            "sections": [
                {
                    "heading": "1. Constitutional Merit & The Rule of Three",
                    "content": "Article V, Section 6 of the New York State Constitution mandates that appointments and promotions in the civil service of the state and all of its civil divisions shall be made according to merit and fitness, to be ascertained, as far as practicable, by examination. Under New York State Civil Service Law § 61(1), whenever an agency seeks to fill a competitive vacancy from an eligible list, the appointment must be made from among the top three (3) individuals certified as standing highest on the list who are willing to accept the position. This is known as the 'Rule of Three' or 'one-in-three rule'. It prevents nepotism by restricting an appointing officer's choice to the highest-scoring available candidates."
                },
                {
                    "heading": "2. How Scores and Banding Determine Your Reachability",
                    "content": "Examinations yield a final score combining raw test results, veterans' credits (5 points for non-disabled, 10 for disabled veterans), and seniority points. Because dozens of candidates may score identical grades (e.g., a score of 100 or 95), Civil Service Law groups all individuals with the same score into the same rank. Under § 61, all candidates in the top three score bands are legally reachable. For instance, if List Rank 1 has 1 person, Rank 2 has 2 people, and Rank 3 has 15 people, all 18 people are technically reachable for appointment."
                },
                {
                    "heading": "3. The Life Cycle of an Eligible List: Canvass Letters to Expiration",
                    "content": "Once an eligible list is established by the Civil Service Department or Commission, it typically remains active for four (4) years (NYS Civil Service Law § 56), though commissions may extend them up to additional years or terminate after one year if fewer than three candidates remain. When an agency has an opening, it issues 'Canvass Letters' (by mail or electronic portal) to reachable candidates asking: 'Are you available and interested in this position at this salary and location?' Candidates MUST respond by the stated deadline (usually 10-15 business days). Declining, failing to respond, or stating salary requirements higher than the job allows the agency to move past your name to the next reachable candidate."
                },
                {
                    "heading": "4. Open-Competitive vs. Continuous Recruitment Examinations",
                    "content": "Traditional Open-Competitive exams are announced periodically (often once every 2 to 4 years), have a strict 3-to-4-week filing window, and test on a single Saturday or testing window. If you miss that filing window, you cannot take the exam until the next multi-year cycle. In contrast, Continuous Recruitment (CR) examinations accept applications on an ongoing basis with no deadline. Candidates are evaluated via standardized Training & Experience (T&E) questionnaires or periodic testing, and their names are continuously merged onto an active, rolling eligible list according to their score. Each candidate remains on the list for a fixed period (typically 1 to 2 years from their individual evaluation date)."
                },
                {
                    "heading": "5. The NY HELPS Revolution: Bypassing the Traditional Exam",
                    "content": "To combat severe post-pandemic public sector vacancies, the New York State Civil Service Commission authorized the New York Hiring for Emergency Limited Placement Statewide (NY HELPS) program. Running through June 30, 2028, NY HELPS temporarily waives competitive written examinations for thousands of entry- and mid-level titles (including Information Technology Specialist 1, 2, 3, and 4). Candidates apply directly to agencies based solely on meeting minimum education/experience qualifications. After one year of satisfactory permanent service, NY HELPS employees have their positions automatically converted into permanent competitive class status under Civil Service Law § 75—granting full statutory tenure protections without ever sitting for a civil service exam."
                }
            ],
            "key_definitions": [
                {"term": "Competitive Class", "definition": "Civil service positions for which it is practicable to determine the merit and fitness of applicants by competitive examination."},
                {"term": "Rule of Three (Civil Service Law § 61)", "definition": "Statutory rule requiring appointments from competitive lists to be made from among the top three ranking persons on the certified eligible list willing to accept the post."},
                {"term": "Eligible List", "definition": "A roster of candidates who passed a civil service examination, ranked by final score plus statutory veteran/seniority credits."},
                {"term": "Continuous Recruitment (CR)", "definition": "An examination open for application continuously, allowing qualified candidates to be evaluated and merged onto an active list at any time."},
                {"term": "Canvass Letter", "definition": "An official inquiry sent by a hiring agency to list eligibles to determine their willingness to accept an appointment at a specific agency, location, and salary."},
                {"term": "Provisional Appointment", "definition": "A temporary appointment made to a competitive position when no viable eligible list exists. A provisional employee must pass the eventual competitive exam and score among the top three reachable candidates to keep the job."},
                {"term": "NY HELPS", "definition": "New York Hiring for Emergency Limited Placement Statewide. Emergency waiver program waiving civil service exams for thousands of state and local titles through June 30, 2028."}
            ],
            "statutory_references": [
                {"citation": "NYS Constitution Art. V, § 6", "url": "https://www.nysenate.gov/legislation/laws/CNS/A5S6", "title": "Merit and Fitness Clause"},
                {"citation": "NYS Civil Service Law § 61", "url": "https://www.nysenate.gov/legislation/laws/CVP/61", "title": "Appointment and Promotion (Rule of Three)"},
                {"citation": "NYS Civil Service Law § 56", "url": "https://www.nysenate.gov/legislation/laws/CVP/56", "title": "Establishment and Duration of Eligible Lists"},
                {"citation": "NYS Civil Service Law § 65", "url": "https://www.nysenate.gov/legislation/laws/CVP/65", "title": "Provisional Appointments"}
            ]
        },
        {
            "topic_id": "CIVIC-EDU-02",
            "week_number": 2,
            "title": "How Local Governments Hire Software Developers",
            "summary": "Understand the jurisdictional classes (Competitive, Non-Competitive, Exempt, Unclassified), public authorities, and contractor vehicles used to staff public technology teams.",
            "sections": [
                {
                    "heading": "1. The Four Jurisdictional Classes of Civil Service",
                    "content": "All civil service positions in New York State and local governments fall into one of four jurisdictional classes defined in Civil Service Law § 35-44: 1) Competitive Class (default; requires examination or NY HELPS waiver); 2) Non-Competitive Class (examinations not practicable; candidates must meet stated qualifications, e.g., specialized software architects or NYC IT Project Specialists); 3) Exempt Class (confidential or policy-making positions appointed at discretion); and 4) Labor Class (unskilled manual labor). In addition, higher education instructional staff and certain academic professionals fall into the Unclassified Service."
                },
                {
                    "heading": "2. Why Municipal Software Engineering Titles Vary",
                    "content": "Unlike the private sector where 'Software Engineer' is ubiquitous, government titles reflect legacy civil service classification standards. New York State ITS uses 'Information Technology Specialist' (ITS 1 = SG-14, ITS 2 = SG-18, ITS 3 = SG-23, ITS 4 = SG-25) with parenthetics like (Programming), (Database), or (Systems). New York City uses 'Computer Associate (Software)', 'Computer Specialist (Software)', and modern non-competitive titles like 'IT Project Specialist' and 'IT Infrastructure Engineer'. Nassau and Suffolk counties use 'Programmer Analyst', 'Senior Programmer Analyst', and 'Network & Systems Specialist'."
                },
                {
                    "heading": "3. Public Authorities: The Direct-Hire Path",
                    "content": "Public benefit corporations such as the Metropolitan Transportation Authority (MTA/LIRR), Port Authority of NY & NJ (PANYNJ), New York Power Authority (NYPA), and Brookhaven National Laboratory (BNL) operate outside traditional civil service commissions. They conduct direct recruitment using standard corporate job postings, applicant tracking systems (Workday, SuccessFactors), and technical coding interviews without civil service exam delays."
                },
                {
                    "heading": "4. IT Staff Augmentation: HBITS and PBITS Contractors",
                    "content": "State and local agencies frequently augment their internal software engineering teams using centralized backdrop contracts managed by NYS OGS. Hourly Based Information Technology Services (HBITS) contracts allow agencies to quickly retain software developers, data engineers, and DevOps specialists through approved staffing vendors at standardized billable rates. Many technologists transition from HBITS vendor placements into permanent civil service or NY HELPS appointments."
                }
            ],
            "key_definitions": [
                {"term": "Non-Competitive Class", "definition": "Positions where competitive examination is found not practicable, but candidates must meet minimum training and experience qualifications."},
                {"term": "Unclassified Service", "definition": "Civil service positions comprising elected officials, legislative officers, and academic/faculty/professional staff at SUNY and CUNY."},
                {"term": "Public Benefit Corporation", "definition": "A corporate entity created by the state legislature to construct or operate public infrastructure (e.g., MTA, PANYNJ) outside direct state agency constraints."},
                {"term": "HBITS / PBITS", "definition": "Hourly / Project Based Information Technology Services contracts established by NYS OGS for rapid IT consulting procurement."}
            ],
            "statutory_references": [
                {"citation": "NYS Civil Service Law § 40-44", "url": "https://www.nysenate.gov/legislation/laws/CVP/A3TBE", "title": "Classified Service Jurisdictional Classes"},
                {"citation": "NYS Public Authorities Law § 1260 et seq.", "url": "https://www.nysenate.gov/legislation/laws/PAA", "title": "Metropolitan Transportation Authority Act"}
            ]
        },
        {
            "topic_id": "CIVIC-EDU-03",
            "week_number": 3,
            "title": "How Municipal Contracts and Tech Procurements Are Awarded",
            "summary": "Understand IFBs, RFPs, discretionary purchasing thresholds, M/WBE & SDVOB goals, and how a solo developer or boutique consultancy can win public contracts.",
            "sections": [
                {
                    "heading": "1. Sealed Bids (IFB) vs. Competitive Proposals (RFP)",
                    "content": "Public procurement in New York is governed by State Finance Law § 163 (state agencies) and General Municipal Law § 103 (local governments). An Invitation for Bids (IFB) is used for standardized goods/commodities and must be awarded strictly to the lowest responsive and responsible bidder. A Request for Proposals (RFP) is used for complex services (like custom software development, cloud migration, or systems integration) where award is made based on 'Best Value'—evaluating technical approach, past performance, security architecture, and cost."
                },
                {
                    "heading": "2. Discretionary Purchasing: The Small Business Fast Track",
                    "content": "Agencies are not required to conduct full competitive formal bids for small procurements. Under NYS State Finance Law § 163(6), state agencies may make discretionary purchases up to $50,000 (up to $85,000 for OGS centralized commodities) without formal competition. Even more powerful: state agencies may make discretionary purchases up to $750,000 to $1,500,000 when purchasing from certified Minority- and Women-Owned Business Enterprises (M/WBEs), Service-Disabled Veteran-Owned Businesses (SDVOBs), or NYS Small Businesses. NYC has an equivalent $1.5M M/WBE non-competitive threshold in PASSPort."
                },
                {
                    "heading": "3. The New York State Contract Reporter (NYSCR)",
                    "content": "By law (Economic Development Law Article 4-C), state agencies, authorities, and SUNY campuses must publish all procurement opportunities of $50,000 or greater in the New York State Contract Reporter (nyscr.ny.gov) at least 15 business days prior to the bid submission deadline. Registering an account is 100% free and allows vendors to receive daily automated alerts matching their NAICS/commodity codes."
                }
            ],
            "key_definitions": [
                {"term": "Best Value", "definition": "A procurement basis that optimizes quality, cost, and efficiency, rather than solely selecting the lowest dollar bid."},
                {"term": "Discretionary Purchase", "definition": "Purchases below statutory dollar thresholds made without formal competitive sealed bidding, often reserved for small businesses and M/WBEs."},
                {"term": "Vendor Responsibility (VendRep / PASSPort)", "definition": "A mandatory legal review assessing a vendor's financial integrity, legal compliance, and past operational performance before a government contract can be approved."}
            ],
            "statutory_references": [
                {"citation": "NYS State Finance Law § 163", "url": "https://www.nysenate.gov/legislation/laws/STF/163", "title": "Purchasing Services and Technologies"},
                {"citation": "NYS General Municipal Law § 103", "url": "https://www.nysenate.gov/legislation/laws/GML/103", "title": "Advertising for Bids; Letting of Contracts"}
            ]
        },
        {
            "topic_id": "CIVIC-EDU-04",
            "week_number": 4,
            "title": "How Residents Participate in Public Meetings and Hearings",
            "summary": "Master the New York State Open Meetings Law, 72-hour notice rules, 24-hour document disclosure mandates, and effective strategies for delivering 3-minute public testimony.",
            "sections": [
                {
                    "heading": "1. The Open Meetings Law (Public Officers Law Article 7)",
                    "content": "Enacted in 1976, the Open Meetings Law (OML) guarantees the public's right to attend, observe, and listen to the deliberations of public bodies—including state boards, county legislatures, town boards, village trustees, and school boards. Under § 103, all meetings must be open to the public except for narrowly defined executive sessions (e.g. discussing ongoing litigation, collective bargaining, or employment discipline of a specific person)."
                },
                {
                    "heading": "2. Statutory Notice and Document Disclosure Deadlines",
                    "content": "Public bodies must comply with strict advance disclosure timelines: 1) Public Notice (§ 104): If a meeting is scheduled at least one week in advance, public notice must be given to news media and conspicuously posted online at least 72 hours prior to the meeting. 2) Document Disclosure (§ 103(e)): Records, proposed resolutions, or local laws scheduled to be discussed at an open meeting must, to the extent practicable, be posted on the public body's website at least 24 hours prior to the meeting. This 24-hour rule is critical for citizens to review proposed IT budgets or contracts before public debate."
                },
                {
                    "heading": "3. The Mechanics of Public Comment: The 3-Minute Rule",
                    "content": "While the Open Meetings Law guarantees the right to observe, local rules govern the 'Public Portion' or public comment period. Long Island Town Boards (Hempstead, Oyster Bay, Brookhaven, Huntington) and County Legislatures (Nassau and Suffolk) enforce a strict 3-minute limit per speaker. To speak, arrive 15 minutes before the meeting to submit a speaker card to the Town or Legislative Clerk. State your name, hamlet/town of residence, and structure your remarks into: 1) The issue; 2) The specific data or impact; and 3) The exact action requested of the board."
                }
            ],
            "key_definitions": [
                {"term": "Public Body", "definition": "An entity of two or more people performing a governmental function for the state or municipality, requiring a quorum to conduct public business."},
                {"term": "Executive Session", "definition": "A portion of an open meeting closed to the public, permitted only for eight specifically enumerated statutory subjects under POL § 105."},
                {"term": "Quorum", "definition": "A majority of the total voting members of a public body, legally required to convene an official meeting or conduct business."}
            ],
            "statutory_references": [
                {"citation": "NYS Public Officers Law Article 7 (§§ 100-111)", "url": "https://www.nysenate.gov/legislation/laws/PBO/A7", "title": "New York State Open Meetings Law"},
                {"citation": "POL § 103(e)", "url": "https://www.nysenate.gov/legislation/laws/PBO/103", "title": "24-Hour Online Document Disclosure Requirement"}
            ]
        },
        {
            "topic_id": "CIVIC-EDU-05",
            "week_number": 5,
            "title": "How to Read and Analyze a Local Government Budget",
            "summary": "Demystify municipal fund accounting, the difference between Operating and Capital budgets, Personal Services vs. OTPS, and how to track public technology spending.",
            "sections": [
                {
                    "heading": "1. Fund Accounting: Operating vs. Capital Budgets",
                    "content": "Governments do not operate out of a single bank account. They use fund accounting: 1) Operating Budget (General Fund): Covers day-to-day annual recurring expenses such as civil service salaries, software subscription licenses, cloud hosting, and hardware maintenance. Funded by property taxes, sales taxes, and state aid. 2) Capital Budget (Capital Program): Covers long-term physical and technical assets (server infrastructure, fiber optic networks, emergency dispatch CAD/911 systems, major ERP replacements) financed via multi-year municipal bonds."
                },
                {
                    "heading": "2. Reading the Line Items: PS vs. OTPS",
                    "content": "Every municipal department budget is divided into two primary categories: 1) Personal Services (PS): Salaries, overtime, holiday pay, and longevity bonuses for civil service personnel. 2) Other Than Personal Services (OTPS): Contracts, equipment, software licenses, travel, and consulting fees. When looking for public tech contracts, search OTPS account codes labeled 'Data Processing Equipment', 'Contractual Services', or 'Computer Software'."
                },
                {
                    "heading": "3. The Annual Budget Cycle",
                    "content": "On Long Island, county executives (Nassau/Suffolk) and town supervisors submit tentative proposed budgets in September/October. Legislative committees hold public hearings in October/November where department commissioners (including the Chief Information Officer) defend their budget requests. Budgets are voted on and finalized by November/December for the fiscal year beginning January 1. This October/November window is when citizens can directly question IT investments."
                }
            ],
            "key_definitions": [
                {"term": "General Fund", "definition": "The primary operating fund of a government entity covering general administrative, police, and operational costs."},
                {"term": "Capital Improvement Program (CIP)", "definition": "A multi-year plan (often 3 to 5 years) detailing upcoming major capital expenditures and debt financing."},
                {"term": "Encumbrance", "definition": "Funds set aside or committed in a budget for a specific purchase order or contract before the payment is actually disbursed."}
            ],
            "statutory_references": [
                {"citation": "NYS County Law Article 7", "url": "https://www.nysenate.gov/legislation/laws/CNT/A7", "title": "County Finance and Budgeting"},
                {"citation": "NYS Town Law Article 8", "url": "https://www.nysenate.gov/legislation/laws/TWN/A8", "title": "Town Finances"}
            ]
        },
        {
            "topic_id": "CIVIC-EDU-06",
            "week_number": 6,
            "title": "How Freedom of Information Law (FOIL) Requests Work",
            "summary": "Learn how to use Public Officers Law Article 6 to inspect public records, obtain machine-readable datasets and database schemas, understand statutory deadlines, and appeal denials.",
            "sections": [
                {
                    "heading": "1. Presumption of Access (Public Officers Law Article 6)",
                    "content": "Under New York's Freedom of Information Law (FOIL), all records of government agencies are presumptively available for public inspection and copying, unless they fall within narrow statutory exemptions (e.g., personal privacy, trade secrets, ongoing criminal investigations, or critical cybersecurity vulnerability information under § 87(2)(i))."
                },
                {
                    "heading": "2. Strict Statutory Timelines: 5 Days to Acknowledge",
                    "content": "When an agency receives a written FOIL request, Civil Service and Public Officers Law § 89(3)(a) mandates that within five (5) business days, the agency must either: 1) Grant the records; 2) Deny the request in writing stating the statutory reason; or 3) Issue a written acknowledgment providing an approximate date (ordinarily within 20 business days) when the records will be granted or denied. An agency cannot indefinitely delay responses; unreasonable delays constitute a 'constructive denial'."
                },
                {
                    "heading": "3. Requesting Code, Data, and SQL Dumps Under FOIL",
                    "content": "Under § 89(3)(a), if an agency maintains records in an electronic database, it must provide them in the electronic medium in which they are kept, including CSV, JSON, or database exports. Technologists can FOIL relational database schemas, contract deliverables, public software specifications, and anonymized incident logs. Agencies cannot charge research fees; they may only charge the actual cost of storage media or programmer time if an extraction requires over 2 hours of custom programming."
                },
                {
                    "heading": "4. The Administrative Appeal Process",
                    "content": "If an agency denies access or fails to respond within statutory deadlines, you have thirty (30) days to file an administrative FOIL Appeal with the agency's designated Appeals Officer. The Appeals Officer has ten (10) business days to either grant the record or fully explain the denial in writing, while simultaneously forwarding copies to the NYS Committee on Open Government (COOG). If the appeal is denied, citizens can file an Article 78 proceeding in NYS Supreme Court, where judges can award attorney fees if the agency lacked a reasonable basis in law for withholding the records."
                }
            ],
            "key_definitions": [
                {"term": "FOIL Record", "definition": "Any information kept, held, filed, produced, or reproduced by, with, or for an agency in any physical or electronic form."},
                {"term": "Constructive Denial", "definition": "An agency's failure to adhere to statutory FOIL deadlines (5-day acknowledgment or 20-day determination), giving the requester the immediate right to file an administrative appeal."},
                {"term": "Committee on Open Government (COOG)", "definition": "A state advisory body within the NYS Department of State that issues formal advisory opinions interpreting FOIL and the Open Meetings Law."}
            ],
            "statutory_references": [
                {"citation": "NYS Public Officers Law Article 6 (§§ 84-90)", "url": "https://www.nysenate.gov/legislation/laws/PBO/A6", "title": "New York State Freedom of Information Law (FOIL)"},
                {"citation": "POL § 89(3)", "url": "https://www.nysenate.gov/legislation/laws/PBO/89", "title": "Agency Response Timelines and Electronic Records"}
            ]
        },
        {
            "topic_id": "CIVIC-EDU-07",
            "week_number": 7,
            "title": "How State and Local Governments Divide Responsibilities",
            "summary": "Understand New York Home Rule, the layered municipal hierarchy on Long Island (State -> County -> Town -> Village -> Special District), and which agency actually controls your services.",
            "sections": [
                {
                    "heading": "1. New York Home Rule and The Layered Long Island Hierarchy",
                    "content": "New York is a strong 'Home Rule' state governed by Article IX of the State Constitution and the Municipal Home Rule Law. Power is distributed across overlapping jurisdictions: 1) State Government: Laws, highways, civil service rules, state police, environmental regulation, higher education (SUNY). 2) Counties (Nassau/Suffolk): Health departments, county police, social services, transit, county civil service commissions, community colleges, property assessment records. 3) Towns (e.g. Hempstead, Oyster Bay, Brookhaven): Zoning, building codes, sanitation/refuse, parks, beaches, local roads, storm water. 4) Incorporated Villages (e.g. Garden City, Rockville Centre, Patchogue): Local zoning, village police, local street maintenance. 5) Special Districts & School Districts: Water districts (SCWA), fire districts, library districts, and independent public school boards."
                },
                {
                    "heading": "2. Navigating the Jurisdictional Quagmire",
                    "content": "A Long Island resident simultaneously lives in New York State, either Nassau or Suffolk County, one of 13 Towns, potentially an incorporated village, an independent school district, a fire district, and a water authority. Understanding who controls what prevents wasted effort: A pothole on Sunrise Highway is NYS DOT; on Merrick Road is Nassau County DPW; on a residential neighborhood street is the Town or Village highway department. Similarly, civil service exams for school district IT jobs in Nassau are run by the Nassau County Civil Service Commission; in Suffolk, by the Suffolk County Civil Service Department."
                },
                {
                    "heading": "3. Where Software Engineering Fits Across the Layers",
                    "content": "State agencies (ITS) run centralized statewide databases (Medicaid, DMV, Unemployment). Counties maintain emergency dispatch (911 CAD), real property parcel mapping (GIS), and public assistance systems. Towns run permitting portals (Accela, OpenGov), property tax collection, and parks reservation systems. Authorities (MTA, SCWA) run industrial IoT, SCADA, train tracking APIs, and utility billing architectures. Each tier has independent tech budgets and recruitment pathways."
                }
            ],
            "key_definitions": [
                {"term": "Home Rule", "definition": "Constitutional authority granted to local governments to adopt local laws relating to their property, affairs, and government, provided they do not conflict with general state laws."},
                {"term": "Special District", "definition": "An independent local governmental unit created to provide a specific public service (e.g. fire protection, water distribution, sanitation) within a defined geographic boundary."},
                {"term": "Incorporated Village", "definition": "A municipal corporation formed within one or more towns to provide localized services and autonomous zoning control."}
            ],
            "statutory_references": [
                {"citation": "NYS Constitution Article IX", "url": "https://www.nysenate.gov/legislation/laws/CNS/A9", "title": "Local Governments and Home Rule"},
                {"citation": "NYS Municipal Home Rule Law", "url": "https://www.nysenate.gov/legislation/laws/MHR", "title": "Municipal Home Rule Law"}
            ]
        }
    ]

    (DATA / "civic_education.json").write_text(json.dumps(modules, indent=2))
    print(f"Generated civic_education.json with {len(modules)} educational modules.")
    return modules

# ==========================================
# 5. ASSEMBLE DEDUPLICATED OPPORTUNITIES (TRACK 1)
# ==========================================
def build_opportunities():
    opps = []

    # A. NYS VACANCIES (from nys_tech.json)
    nys_file = RAW / "nys_tech.json"
    if nys_file.exists():
        nys_raw = json.loads(nys_file.read_text())
        for r in nys_raw:
            d = r.get("detail", {})
            title = r.get("title", "")
            grade = r.get("grade", "")
            app_due = d.get("Applications Due", r.get("deadline", ""))
            due_dt = parse_date(app_due)
            urgency = calc_urgency(due_dt)
            is_helps = "YES" in str(d.get("NY HELPS", "")).upper() or "NY HELPS" in title
            cat = "VACANCY"

            mq = d.get("Minimum Qualifications", "")
            assessment = assess_nys_qual(title, grade, mq)

            cid = f"NYS-VAC-{r['item']}"
            opps.append({
                "id": cid,
                "track": "Track 1: Career",
                "category": cat,
                "title": clean_text(title),
                "official_title": d.get("Title", title),
                "agency": d.get("Agency", r.get("agency", "")),
                "jurisdiction": "New York State",
                "jurisdiction_tier": "NYS / NY HELPS",
                "location": f"{d.get('City', '')}, NY ({d.get('County', r.get('county', ''))} County)",
                "telework": "Yes" if "YES" in str(d.get("Telecommuting allowed?", "")).upper() else ("No" if "NO" in str(d.get("Telecommuting allowed?", "")).upper() else "Not Specified"),
                "salary": d.get("Salary Range", f"Grade {grade}"),
                "salary_grade": f"SG-{grade}" if grade else "NS",
                "qualifications": clean_text(mq[:800]),
                "qualification_assessment": assessment,
                "examination_requirements": "None (NY HELPS appointment; permanent non-competitive status converting to competitive after 1 year)" if is_helps else ("Direct application; minimum qualification screening" if "NON-COMPETITIVE" in str(d.get("Jurisdictional Class", "")).upper() else "Competitive transfer, eligible list, or 55-b/c"),
                "is_ny_helps": is_helps,
                "deadline": app_due or "Open Until Filled",
                "deadline_date": due_dt.isoformat() if due_dt else None,
                "deadline_urgency": urgency,
                "official_url": r.get("url", f"https://statejobs.ny.gov/public/vacancyDetailsView.cfm?id={r['item']}"),
                "required_next_action": parse_next_action(d.get("Notes on Applying", ""), d.get("Email Address", ""), r.get("url")),
                "equivalent_pathway": "If deadline passed or competitive list required, apply through NY HELPS (https://www.cs.ny.gov/help/) for direct non-competitive appointment into SG-18 or SG-23 titles.",
                "status": "Not Started",
                "discovery_date": "2026-10-21",
                "verified_date": TODAY_STR
            })

    # B. NYC POSTINGS (from nyc_jobs.json)
    nyc_file = RAW / "nyc_jobs.json"
    if nyc_file.exists():
        nyc_raw = json.loads(nyc_file.read_text())
        for r in nyc_raw:
            bt = r.get("business_title", "")
            cst = r.get("civil_service_title", "")
            tc = r.get("title_classification", "")
            due_str = r.get("post_until", "")
            due_dt = parse_date(due_str)
            urgency = calc_urgency(due_dt)

            sal_from = r.get("salary_from", "")
            sal_to = r.get("salary_to", "")
            sal_freq = r.get("salary_frequency", "Annual")
            salary_str = f"${float(sal_from):,.0f} - ${float(sal_to):,.0f} {sal_freq}" if sal_from and sal_to else "Competitive"

            assessment = assess_nyc_qual(bt, cst, tc, r.get("min_quals", ""))

            opps.append({
                "id": f"NYC-VAC-{r['job_id']}",
                "track": "Track 1: Career",
                "category": "VACANCY",
                "title": clean_text(bt),
                "official_title": f"{cst} ({tc})",
                "agency": r.get("agency", "New York City"),
                "jurisdiction": "New York City",
                "jurisdiction_tier": "New York City",
                "location": f"{r.get('location', 'New York, NY')} (NYC)",
                "telework": "Hybrid eligible under NYC agency telework policies",
                "salary": salary_str,
                "salary_grade": tc,
                "qualifications": clean_text(r.get("min_quals", "")[:800]),
                "qualification_assessment": assessment,
                "examination_requirements": "None required prior to appointment (Non-Competitive Class title)" if "NON-COMPETITIVE" in tc.upper() else "Competitive title; agency may hire provisionally or direct-hire if list exhausted. Civil service exam required when announced by DCAS.",
                "is_ny_helps": False,
                "deadline": due_str or "Until Filled",
                "deadline_date": due_dt.isoformat() if due_dt else None,
                "deadline_urgency": urgency,
                "official_url": r.get("url", f"https://cityjobs.nyc.gov/job/{r['job_id']}"),
                "required_next_action": f"Apply online at Jobs NYC (https://cityjobs.nyc.gov/job/{r['job_id']}) using Job ID {r['job_id']}.",
                "equivalent_pathway": "If competitive exam is currently required, look for Non-Competitive equivalents such as IT Project Specialist or City Research Scientist.",
                "status": "Not Started",
                "discovery_date": "2026-10-21",
                "verified_date": TODAY_STR
            })

    # C. NYC ACTIVE TECH EXAMS (from nyc_exams.json)
    exams_file = RAW / "nyc_exams.json"
    if exams_file.exists():
        exams_raw = json.loads(exams_file.read_text())
        for e in exams_raw:
            if not e.get("tech"):
                continue
            app_end = e.get("app_end", "")
            end_dt = parse_date(app_end)
            urgency = calc_urgency(end_dt)
            cat = "EXAM_OPEN" if urgency in ("CRITICAL_7D", "APPROACHING_14D", "OPEN") else "HISTORICAL_MISSED"

            opps.append({
                "id": f"NYC-EXAM-{e['exam_number']}",
                "track": "Track 1: Career",
                "category": cat,
                "title": f"Civil Service Exam #{e['exam_number']}: {clean_text(e['title'])}",
                "official_title": e["title"],
                "agency": "NYC Department of Citywide Administrative Services (DCAS)",
                "jurisdiction": "New York City",
                "jurisdiction_tier": "New York City",
                "location": "New York City (Five Boroughs)",
                "telework": "Varies by appointing agency upon hiring from list",
                "salary": "Civil service salary schedule (typically $75,000 - $130,000 depending on title and level)",
                "salary_grade": e.get("type", "Open Competitive"),
                "qualifications": "Baccalaureate degree in Computer Science or related quantitative field plus 1-3 years of qualifying software/data experience.",
                "qualification_assessment": {
                    "match": "Confirmed",
                    "reasoning": f"Candidate's BS in Computer & Information Science (Aug 2025) and 5 years technical experience satisfies education and experience criteria for {e['title']}.",
                    "missing_evidence": "Official college transcript and OASys exam fee/waiver application."
                },
                "examination_requirements": f"Official DCAS Examination (Open Competitive / Education & Experience Test). Filing period: {e.get('app_start')} to {e.get('app_end')}.",
                "is_ny_helps": False,
                "deadline": e.get("app_end", ""),
                "deadline_date": end_dt.isoformat() if end_dt else None,
                "deadline_urgency": urgency,
                "official_url": "https://www.nyc.gov/site/dcas/employment/exam-schedules.page",
                "required_next_action": f"File online during active window via NYC DCAS OASys portal (https://a856-oasys.nyc.gov/) or subscribe to DCAS monthly exam notifications.",
                "equivalent_pathway": "If this filing window has closed, apply to direct-hire Non-Competitive titles (IT Project Specialist, City Research Scientist) on Jobs NYC, or look for provisional appointments while awaiting the next exam cycle.",
                "status": "Not Started",
                "discovery_date": "2026-10-21",
                "verified_date": TODAY_STR
            })

    # D. NYC CONTINUOUS/ACTIVE ELIGIBLE LISTS
    lists_file = RAW / "nyc_lists.json"
    if lists_file.exists():
        lists_raw = json.loads(lists_file.read_text())
        key_lists = ["COMPUTER SPECIALIST (SOFTWARE)", "COMPUTER ASSOCIATE (SOFTWARE)", "CERTIFIED IT DEVELOPER (APPLICATIONS)", "CYBER SECURITY ANALYST"]
        for l in lists_raw:
            if any(k in l.get("title", "").upper() for k in key_lists) and l.get("list_agency") in ("OPEN COMPETITIVE", "DEPARTMENT OF HEALTH AND MENTAL HYGIENE"):
                opps.append({
                    "id": f"NYC-LIST-{l['exam_no']}",
                    "track": "Track 1: Career",
                    "category": "ELIGIBLE_LIST",
                    "title": f"Active Eligible List #{l['exam_no']}: {clean_text(l['title'])}",
                    "official_title": l["title"],
                    "agency": "NYC DCAS / Citywide Agencies",
                    "jurisdiction": "New York City",
                    "jurisdiction_tier": "New York City",
                    "location": "New York City",
                    "telework": "Agency dependent",
                    "salary": "Statutory List Band (Grade Levels 1-4: $85,000 - $145,000+)",
                    "salary_grade": f"Title Code {l.get('title_code', '')}",
                    "qualifications": "Established eligible list resulting from open-competitive examination. Currently active with eligible candidates.",
                    "qualification_assessment": {
                        "match": "Likely",
                        "reasoning": f"This is an active eligible list currently in use by city agencies. If not already on the list, candidates cannot join directly until DCAS holds the next examination cycle.",
                        "missing_evidence": "Candidate must monitor the DCAS Annual Exam Schedule for the successor examination."
                    },
                    "examination_requirements": f"Established on {l.get('established')}; Active through {l.get('anniversary')}. Number of eligibles on roster: {l.get('eligibles')}.",
                    "is_ny_helps": False,
                    "deadline": f"List Active until {l.get('anniversary', 'Extension')}",
                    "deadline_date": l.get("anniversary"),
                    "deadline_urgency": "OPEN",
                    "official_url": "https://data.cityofnewyork.us/City-Government/Civil-Service-List-Active-/vx8i-nprf",
                    "required_next_action": "Search your name or list number on DCAS Civil Service List portal or NYC OpenRecords; track certification canvasses.",
                    "equivalent_pathway": "Candidates not on this list can pursue Non-Competitive IT titles (IT Project Specialist, IT Infrastructure Engineer) which hire immediately without waiting for eligible lists.",
                    "status": "Not Started",
                    "discovery_date": "2026-10-21",
                    "verified_date": TODAY_STR
                })

    # E. FEDERAL USAJOBS (from federal.json)
    fed_file = RAW / "federal.json"
    if fed_file.exists():
        fed_raw = json.loads(fed_file.read_text())
        for f in fed_raw:
            if not (f.get("in_ny") or f.get("remote") or f.get("recent_grad_path") or f.get("location_negotiable")):
                continue
            closes_str = f.get("closes", "")
            close_dt = parse_date(closes_str)
            urgency = calc_urgency(close_dt)

            is_rg = f.get("recent_grad_path", False)
            cat = "PATHWAY_FELLOWSHIP" if is_rg else "VACANCY"

            assessment = {
                "match": "Confirmed",
                "reasoning": "Recent Graduates Pathways: Candidate graduated with a BS in Computer & Information Science in August 2025, qualifying for the 2-year federal Recent Graduates hiring authority through August 2027. For competitive positions, BS qualifies for GS-7 (plus Superior Academic Achievement if GPA 3.0+) and ~5 years professional experience qualifies for GS-9, GS-11, and GS-12.",
                "missing_evidence": "Official college transcript showing August 2025 graduation date; federal-style resume detailing hours per week and technical duties."
            }

            opps.append({
                "id": f"FED-USA-{f['id']}",
                "track": "Track 1: Career",
                "category": cat,
                "title": clean_text(f["title"]),
                "official_title": f"{f['title']} ({f['grade']})",
                "agency": f.get("agency", "Federal Agency"),
                "jurisdiction": "Federal Government",
                "jurisdiction_tier": "Federal USAJOBS",
                "location": f.get("location", "New York / Remote"),
                "telework": "Yes - Remote / Telework Eligible" if f.get("remote") or f.get("location_negotiable") else "Telework eligible according to agency policy",
                "salary": f.get("salary", f"Grade {f.get('grade')}"),
                "salary_grade": f.get("grade", "GS"),
                "qualifications": f"Series {', '.join(f.get('series', []))}. Requires qualifying degree in Computer Science, Information Science, or IT, or specialized experience at the next lower grade level.",
                "qualification_assessment": assessment,
                "examination_requirements": "None (Federal competitive merit review; ratings based on resume and occupational questionnaire answers).",
                "is_ny_helps": False,
                "deadline": closes_str or "Until Filled",
                "deadline_date": close_dt.isoformat() if close_dt else None,
                "deadline_urgency": urgency,
                "official_url": f.get("url", f"https://www.usajobs.gov/job/{f['id']}"),
                "required_next_action": f"Apply online via USAJOBS (https://www.usajobs.gov/job/{f['id']}) before 11:59 PM Eastern on {closes_str}. Upload college transcript and federal resume.",
                "equivalent_pathway": "If this federal opening closes, search USAJOBS for Series 2210 and filter by 'Recent Graduates' to access the 2-year non-competitive conversion hiring authority active for candidate through August 2027.",
                "status": "Not Started",
                "discovery_date": "2026-10-21",
                "verified_date": TODAY_STR
            })

    # F. LONG ISLAND LOCAL / CONTINUOUS EXAMS & VACANCIES
    long_island_entries = [
        {
            "id": "NASSAU-CR-PA",
            "track": "Track 1: Career",
            "category": "EXAM_CONTINUOUS",
            "title": "Continuous Recruitment Examination: Programmer Analyst",
            "official_title": "Programmer Analyst (CR Title)",
            "agency": "Nassau County Civil Service Commission",
            "jurisdiction": "Nassau County",
            "jurisdiction_tier": "Long Island (Nassau/Suffolk)",
            "location": "Nassau County (Hempstead, Mineola, School Districts, Towns)",
            "telework": "Agency dependent",
            "salary": "$65,000 - $85,000 (Varies by jurisdiction/school district)",
            "salary_grade": "Grade 11 - 13 (Nassau Schedule)",
            "qualifications": "Bachelor's degree from a regionally accredited college or university including or supplemented by 15 credits in computer science, programming, or systems analysis, plus 1 year of programming experience.",
            "qualification_assessment": {
                "match": "Confirmed",
                "reasoning": "Candidate holds a BS in Computer & Information Science (Aug 2025) and ~5 years professional programming/systems experience. Fully meets and exceeds both education and experience minimum qualifications.",
                "missing_evidence": "Official college transcript and Nassau County Civil Service examination application."
            },
            "examination_requirements": "Training & Experience (T&E) evaluation. Candidates complete an online questionnaire detailing coursework, programming languages, and employment history.",
            "is_ny_helps": False,
            "deadline": "Continuous Recruitment (No Filing Deadline)",
            "deadline_date": None,
            "deadline_urgency": "CONTINUOUS",
            "official_url": "https://www.governmentjobs.com/careers/nassaucountyny",
            "required_next_action": "Check active filing link on Nassau County GovernmentJobs portal (https://www.governmentjobs.com/careers/nassaucountyny) or submit application form to Nassau County Civil Service Commission, 40 Main St, Hempstead, NY.",
            "equivalent_pathway": "Nassau Health Care Corporation (NuHealth) and school districts also hire provisionally for Programmer Analyst while awaiting list certification.",
            "status": "Not Started",
            "discovery_date": "2026-10-21",
            "verified_date": TODAY_STR
        },
        {
            "id": "SUFFOLK-CR-IT",
            "track": "Track 1: Career",
            "category": "EXAM_CONTINUOUS",
            "title": "Continuous Recruitment Examination: Information Technology Specialist / Network Specialist",
            "official_title": "Network and Systems Specialist / Applications Support Specialist",
            "agency": "Suffolk County Department of Civil Service",
            "jurisdiction": "Suffolk County",
            "jurisdiction_tier": "Long Island (Nassau/Suffolk)",
            "location": "Suffolk County (Hauppauge, Riverhead, Yaphank, Towns)",
            "telework": "Agency dependent",
            "salary": "$62,000 - $92,000",
            "salary_grade": "Grade 21 - 25 (Suffolk White Collar Schedule)",
            "qualifications": "Bachelor's degree in Computer Science, Information Technology, or related field and 1-2 years of systems/programming experience.",
            "qualification_assessment": {
                "match": "Confirmed",
                "reasoning": "Candidate's BS in Computer & Information Science and ~5 years technical operations/automation experience exceeds requirements.",
                "missing_evidence": "Official college transcript and Suffolk e-filing profile."
            },
            "examination_requirements": "Continuous Recruitment Training & Experience examination. Applications accepted year-round.",
            "is_ny_helps": False,
            "deadline": "Continuous Recruitment (Open Year-Round)",
            "deadline_date": None,
            "deadline_urgency": "CONTINUOUS",
            "official_url": "https://apps2.suffolkcountyny.gov/civilservice/efile/default.aspx",
            "required_next_action": "Register a User ID on Suffolk County Civil Service e-File (https://apps2.suffolkcountyny.gov/civilservice/efile/default.aspx) and subscribe to IT examination alerts.",
            "equivalent_pathway": "Suffolk County Department of Information Technology also hires directly into non-competitive and provisional roles listed on the Suffolk County Workday portal.",
            "status": "Not Started",
            "discovery_date": "2026-10-21",
            "verified_date": TODAY_STR
        },
        {
            "id": "BNL-VAC-COMP-01",
            "track": "Track 1: Career",
            "category": "VACANCY",
            "title": "Scientific Programmer / Cloud Systems Engineer",
            "official_title": "Computational Science Specialist (P-3 / P-5)",
            "agency": "Brookhaven National Laboratory (BNL)",
            "jurisdiction": "Public Authorities & Labs",
            "jurisdiction_tier": "Public Authorities & Labs",
            "location": "Upton, NY (Town of Brookhaven, Long Island) - Hybrid Eligible",
            "telework": "Hybrid (2-3 days on-campus at Upton Lab)",
            "salary": "$95,000 - $135,000 Annually",
            "salary_grade": "Professional Scientific Staff",
            "qualifications": "BS or MS in Computer Science, Software Engineering, or related field. Proficiency in Python, Linux, containerization (Docker/Kubernetes), SQL/databases, and API integration.",
            "qualification_assessment": {
                "match": "Confirmed",
                "reasoning": "Candidate has BS in Computer & Information Science (Aug 2025) and ~5 years experience in Python, SQL, systems integration, automation, and IT ops. Fits the mid-level computational support profile.",
                "missing_evidence": "Updated CV highlighting Python automation scripts, container experience, and systems integration projects."
            },
            "examination_requirements": "None (DOE National Laboratory direct hire; exempt from civil service examination).",
            "is_ny_helps": False,
            "deadline": "Open Until Filled",
            "deadline_date": None,
            "deadline_urgency": "OPEN",
            "official_url": "https://jobs.bnl.gov/",
            "required_next_action": "Apply online at Brookhaven National Laboratory Careers (https://jobs.bnl.gov/) with resume and references.",
            "equivalent_pathway": "BNL regularly posts Computing Facility, Data Science, and Scientific Computing openings outside the civil service system.",
            "status": "Not Started",
            "discovery_date": "2026-10-21",
            "verified_date": TODAY_STR
        },
        {
            "id": "SBU-VAC-PROG-02",
            "track": "Track 1: Career",
            "category": "VACANCY",
            "title": "Senior Programmer/Analyst (SL-3) / Lead Programmer/Analyst (SL-4)",
            "official_title": "Programmer/Analyst (SUNY Professional Title)",
            "agency": "Stony Brook University (State University of New York)",
            "jurisdiction": "SUNY & CUNY",
            "jurisdiction_tier": "SUNY / CUNY",
            "location": "Stony Brook, NY (Long Island) - Hybrid Eligible",
            "telework": "Hybrid (up to 2 days remote per week per SUNY telework policy)",
            "salary": "$75,000 - $105,000 (SL-3 / SL-4)",
            "salary_grade": "SUNY Professional Service SL-3 / SL-4",
            "qualifications": "Bachelor's degree in Computer Science, Information Systems, or related discipline and 3+ years of programming experience with SQL, web application frameworks (JavaScript/TypeScript, Python), and API systems integration.",
            "qualification_assessment": {
                "match": "Confirmed",
                "reasoning": "Candidate's BS in Computer & Information Science and ~5 years technical experience exceeds the 3-year threshold for SUNY SL-3 Programmer/Analyst.",
                "missing_evidence": "Official college transcript and resume detailing database and API integration history."
            },
            "examination_requirements": "None (SUNY Unclassified Professional Service; hiring conducted via campus search committee).",
            "is_ny_helps": False,
            "deadline": "Open Until Filled (Review begins immediately)",
            "deadline_date": None,
            "deadline_urgency": "OPEN",
            "official_url": "https://employment.stonybrook.edu/",
            "required_next_action": "Submit application, cover letter, resume, and copy of transcript on Stony Brook University Employment portal (https://employment.stonybrook.edu/).",
            "equivalent_pathway": "Farmingdale State College and SUNY Old Westbury also recruit under identical SUNY SL ranks.",
            "status": "Not Started",
            "discovery_date": "2026-10-21",
            "verified_date": TODAY_STR
        },
        {
            "id": "USDC-FELLOW-2026",
            "track": "Track 1: Career",
            "category": "PATHWAY_FELLOWSHIP",
            "title": "U.S. Digital Corps (USDC) Technology Fellowship",
            "official_title": "Technology Fellow (GS-9 Target GS-12, Series 2210/1550)",
            "agency": "General Services Administration (GSA) & Partner Federal Agencies",
            "jurisdiction": "Federal Government",
            "jurisdiction_tier": "Federal USAJOBS",
            "location": "Washington, DC or Remote Across the United States",
            "telework": "100% Remote Eligible",
            "salary": "GS-9 ($64,000 - $83,000) advancing to GS-11 and GS-12 ($92,000 - $120,000+)",
            "salary_grade": "GS-9 / GS-11 / GS-12 Career Ladder",
            "qualifications": "Graduated with an undergraduate or graduate degree within the previous two years (e.g. August 2025 graduation is eligible!). Tracks include Software Engineering, Data Science & Analytics, Product Management, Design, and Cybersecurity.",
            "qualification_assessment": {
                "match": "Confirmed",
                "reasoning": "Candidate graduated in August 2025 with a BS in Computer & Information Science, placing them within the statutory 2-year recent graduate window through August 2027. Five years of professional technical experience makes candidate an exceptionally strong applicant.",
                "missing_evidence": "Official transcript showing degree award date in August 2025; technical portfolio or GitHub."
            },
            "examination_requirements": "Competitive federal fellowship assessment (Technical problem solving, situational judgment, and structured behavioral interview).",
            "is_ny_helps": False,
            "deadline": "Annual Cohort Application Window (Announced via digitalcorps.gsa.gov)",
            "deadline_date": None,
            "deadline_urgency": "OPEN",
            "official_url": "https://digitalcorps.gsa.gov/",
            "required_next_action": "Subscribe to the USDC alert list at https://digitalcorps.gsa.gov/ to receive notification on application portal opening; prepare federal resume.",
            "equivalent_pathway": "Also explore Presidential Innovation Fellows (PIF) for senior technologists, and USAJOBS Recent Graduates Pathways positions.",
            "status": "Not Started",
            "discovery_date": "2026-10-21",
            "verified_date": TODAY_STR
        }
    ]
    opps.extend(long_island_entries)

    deduped = {}
    for o in opps:
        key = o["id"]
        if key not in deduped:
            deduped[key] = o
        else:
            if len(o.get("qualifications", "")) > len(deduped[key].get("qualifications", "")):
                deduped[key] = o

    final_list = list(deduped.values())
    urgency_order = {"CRITICAL_7D": 0, "APPROACHING_14D": 1, "OPEN": 2, "CONTINUOUS": 3, "HISTORICAL": 4}
    match_order = {"Confirmed": 0, "Likely": 1, "Uncertain": 2}
    final_list.sort(key=lambda x: (
        urgency_order.get(x.get("deadline_urgency", "OPEN"), 5),
        match_order.get(x.get("qualification_assessment", {}).get("match", "Uncertain"), 3),
        x.get("title", "")
    ))

    (DATA / "opportunities.json").write_text(json.dumps(final_list, indent=2))
    print(f"Generated opportunities.json with {len(final_list)} deduplicated opportunities.")
    return final_list

def clean_text(s):
    if not s:
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(s)))).strip()

def assess_nys_qual(title, grade, mq):
    text = (title + " " + mq).lower()
    if "information technology specialist 2" in text or "its 2" in text or "box info tech spec 2" in text:
        return {
            "match": "Confirmed",
            "reasoning": "Candidate holds a BS in Computer & Information Science (Aug 2025), which satisfies the NY HELPS requirement for a Bachelor's degree including 15+ computer science credits. Candidate's ~5 years of professional IT/software experience also satisfies the alternative experience path.",
            "missing_evidence": "Official college transcript documenting degree conferral and 15+ CS semester credits."
        }
    if "data analyst 1" in text or "trainee" in text:
        return {
            "match": "Confirmed",
            "reasoning": "Requires a Bachelor's degree in computer science, informatics, data science, statistics, or related field. Candidate's BS in Computer & Information Science matches directly. Five years of SQL and Python experience exceeds entry-level trainee expectations.",
            "missing_evidence": "College transcript and resume highlighting Python data manipulation and SQL querying."
        }
    if "computer systems analyst" in text:
        return {
            "match": "Confirmed",
            "reasoning": "OCA Computer Systems Analyst requires a Bachelor's degree and 2 years of computer programming or systems analysis experience. Candidate has a BS and ~5 years experience in programming, databases, and systems integration.",
            "missing_evidence": "Resume emphasizing SDLC, database management, and systems integration experience."
        }
    if "data scientist" in text:
        return {
            "match": "Likely",
            "reasoning": "Requires Bachelor's degree and 3 years qualitative/quantitative research, Python, SQL, and Git. Candidate meets Python, SQL, Git, and 5 years technical experience, but must highlight data modeling and research methodology in application materials.",
            "missing_evidence": "Work samples or GitHub portfolio demonstrating end-to-end Python data analysis and statistical reporting."
        }
    if "grade 23" in text or "grade 27" in text or "architect" in text:
        return {
            "match": "Likely",
            "reasoning": "Grade 23/27 titles typically require 7 to 9 years of specialized experience, with a Bachelor's degree substituting for 3 to 4 years. Candidate's BS (substituting 3-4 years) plus ~5 years professional experience totals 8-9 qualifying years.",
            "missing_evidence": "Detailed employer verification letters proving full-time dates and exact breakdown of software architecture vs general IT operations."
        }
    return {
        "match": "Likely",
        "reasoning": "Candidate possesses an accredited BS in Computer & Information Science and ~5 years professional IT experience.",
        "missing_evidence": "Verification of college transcripts and specialized programming duties."
    }

def assess_nyc_qual(bt, cst, tc, min_quals):
    text = (bt + " " + (cst or "") + " " + min_quals).lower()
    if "computer associate (software)" in text:
        return {
            "match": "Confirmed",
            "reasoning": "Requires a baccalaureate degree including or supplemented by 24 credits in computer science, plus 1 year of programming experience. Candidate's BS in Computer & Information Science and 5 years experience comfortably exceeds all thresholds.",
            "missing_evidence": "Official college transcript documenting 24+ credits in computer science."
        }
    if "computer specialist (software)" in text:
        return {
            "match": "Confirmed",
            "reasoning": "Requires a baccalaureate degree with 24 computer science credits and 2 to 3 years of full-time experience in software design and development. Candidate meets both education and 5-year technical threshold.",
            "missing_evidence": "Official college transcript and employment verification letters documenting software development duties."
        }
    if "it project specialist" in text:
        return {
            "match": "Confirmed",
            "reasoning": "Non-competitive title requiring a Master's degree OR a Bachelor's degree plus 3 years of specialized IT project/development experience. Candidate's BS and ~5 years technical experience fully qualifies.",
            "missing_evidence": "Resume detailing systems architecture, API integration, and project lifecycle milestones."
        }
    if "it infrastructure engineer" in text:
        return {
            "match": "Confirmed",
            "reasoning": "Requires a Bachelor's degree and 3+ years in cloud, network, systems automation, or DevOps engineering. Candidate has ~5 years IT infrastructure, operations, and automation experience.",
            "missing_evidence": "Detailed resume outlining specific infrastructure tools, cloud platforms, and automation scripts."
        }
    if "city research scientist" in text:
        return {
            "match": "Likely",
            "reasoning": "Requires a master's degree OR a bachelor's degree plus 2 years of research or data analysis experience. Candidate's BS plus 5 years data/automation experience qualifies for Level I and Level II.",
            "missing_evidence": "Portfolio or resume highlighting data modeling, statistical summaries, and database analysis."
        }
    return {
        "match": "Likely",
        "reasoning": "Candidate possesses an accredited BS in Computer & Information Science and ~5 years professional IT experience.",
        "missing_evidence": "Verification of college transcripts and specialized programming duties."
    }

def parse_next_action(notes, email, url):
    if "nysed.gov/it-application" in notes:
        return "Submit online application via NYSED IT Portal at https://www.nysed.gov/it-application."
    if email:
        return f"Send cover letter and resume citing the Vacancy ID to {email}."
    if url:
        return f"Review official posting and follow agency application instructions at {url}."
    return "Submit application via agency career portal."

# ==========================================
# 6. EXPORT CLIENT DATA BUNDLE (data_bundle.js)
# ==========================================
def build_data_bundle(states, ny_mun, civic, edu, opps):
    bundle = {
        "generated_at": TODAY_STR,
        "summary": {
            "total_opportunities": len(opps),
            "urgent_7d": sum(1 for o in opps if o.get("deadline_urgency") == "CRITICAL_7D"),
            "approaching_14d": sum(1 for o in opps if o.get("deadline_urgency") == "APPROACHING_14D"),
            "open_opportunities": sum(1 for o in opps if o.get("deadline_urgency") == "OPEN"),
            "continuous_exams": sum(1 for o in opps if o.get("deadline_urgency") == "CONTINUOUS"),
            "confirmed_matches": sum(1 for o in opps if o.get("qualification_assessment", {}).get("match") == "Confirmed"),
            "states_covered": len(states),
            "civic_opportunities": len(civic),
            "civic_education_topics": len(edu)
        },
        "opportunities": opps,
        "jurisdictions_50states": states,
        "ny_municipalities": ny_mun,
        "civic_participation": civic,
        "civic_education": edu
    }
    js_content = f"// Automatically generated by build_data.py on {TODAY_STR}\nwindow.CIVIC_DATA = {json.dumps(bundle, indent=2)};\n"
    (DATA / "data_bundle.js").write_text(js_content)
    print("Generated data_bundle.js for browser loading.")

def main():
    print("Step 1: Building 50 States Directory...")
    states = build_50_states()

    print("Step 2: Building NY Municipalities Directory...")
    ny_mun = build_ny_municipalities()

    print("Step 3: Building Civic Participation Data (Track 2)...")
    civic = build_civic_participation()

    print("Step 4: Building Civic Education Curriculum (Track 3)...")
    edu = build_civic_education()

    print("Step 5: Building Deduplicated Opportunity Tracker (Track 1)...")
    opps = build_opportunities()

    print("Step 6: Building Browser Data Bundle...")
    build_data_bundle(states, ny_mun, civic, edu, opps)
    print("All datasets built successfully!")

if __name__ == "__main__":
    main()
