"""Rules that decide whether a posting belongs on the board and how to label it.

Everything here is pure functions over text so it can be unit-tested (tests/test_classify.py).
"""
import html
import re
from datetime import date, datetime

# ---------------------------------------------------------------- role type
STUDENT_TITLE = re.compile(
    r"\bintern(s|ship|ships)?\b|\bplacements?\b|year[- ]in[- ]industry|\bindustrial (year|trainee)|\bsandwich\b"
    r"|\bco-?op\b|\bsummer (student|engineer|analyst|programme|program)|vacation (scheme|student|placement)"
    r"|\bundergraduate\b|\bstudent\b|\bspring week\b|\binsight (programme|program|week|day)",
    re.I,
)
EXCLUDE_TITLE = re.compile(
    r"apprentice|\bph\.?d\b|doctoral|post-?doc|\bmba\b|\bmaster'?s? thesis|\bthesis\b|werkstudent|working student"
    r"|\bmanager\b|\bsenior\b|\bprincipal\b|\blead\b|\bdirector\b|\bhead of\b|placement (officer|coordinator|manager)"
    r"|student (services|recruitment|advisor|adviser|support)|\btutor\b|\bteacher\b",
    re.I,
)
PLACEMENT = re.compile(
    r"year[- ]in[- ]industry|industrial placement|industrial (year|trainee)|\bsandwich\b|placement year"
    r"|1[0-5][- ]?months?|\b(six|6)[- ]?months?|2027\s*[-/–]\s*(20)?28|\bco-?op\b|year[- ]long|one[- ]year (placement|internship)",
    re.I,
)
SUMMER = re.compile(r"\bsummer\b|vacation|\b(8|10|12)[- ]weeks?\b|\b(2|3) months?\b", re.I)
INSIGHT = re.compile(r"spring week|insight (programme|program|week|day)|discovery (day|week)", re.I)


def role_type(title: str, description: str = "") -> str | None:
    """Return 'placement', 'internship', 'insight', or None if not a student role."""
    if not STUDENT_TITLE.search(title) or EXCLUDE_TITLE.search(title):
        return None
    if INSIGHT.search(title):
        return "insight"
    if SUMMER.search(title):
        return "internship"
    if PLACEMENT.search(title):
        return "placement"
    # Title is ambiguous ("Engineering Intern", "Placement Student"): look at the first part of the description.
    head = description[:2500]
    if re.search(r"\bplacement\b", title, re.I):
        return "internship" if SUMMER.search(head) and not PLACEMENT.search(head) else "placement"
    if PLACEMENT.search(head) and not SUMMER.search(head):
        return "placement"
    return "internship"


# ---------------------------------------------------------------- discipline
DISCIPLINES = {
    "Mechanical": r"mechanical|mech\b|thermal|thermofluid|fluid|cfd|fea\b|stress|vibration|hvac|propulsion|powertrain|engine\b|turbine|design engineer",
    "Aerospace": r"aerospace|aeronautic|aerodynamic|aircraft|avionics|airframe|satellite|space|spacecraft|rocket|uav|drone|flight",
    "Electrical & Electronic": r"electrical|electronic|\beee\b|hardware|pcb|circuit|analog|analogue|asic|fpga|rf\b|semiconductor|silicon|chip|power electronics|firmware|embedded|photonic|optical",
    "Software & Data": r"software|developer|\bdata\b|machine learning|\bml\b|\bai\b|computer vision|cyber|cloud|devops|algorithm|computing",
    "Civil & Structural": r"civil|structural|geotechnical|transport planning|highways?|bridges?|rail\b|tunnel|construction|water engineer",
    "Chemical & Process": r"chemical|process engineer|chemistry|formulation|pharmaceutical|bioprocess|manufacturing science|process development",
    "Materials": r"materials|metallurg|composite|polymer|coatings?|additive",
    "Manufacturing & Quality": r"manufacturing|production|quality|industrial engineer|operations engineer|lean|supply chain|logistics|automation",
    "Robotics & Mechatronics": r"robot|mechatronic|autonom|control(s)? (systems? )?engineer|controls\b|perception|motion planning",
    "Biomedical": r"biomedical|medical device|medtech|clinical engineer|bioengineer|surgical|neuro",
    "Energy & Nuclear": r"energy|nuclear|renewable|wind|solar|battery|grid|hydrogen|fusion|electrification",
}
_DISC_RE = {k: re.compile(v, re.I) for k, v in DISCIPLINES.items()}
ENGINEERING_HINT = re.compile(
    r"engineer|engineering|technical|technolog|r&d|research|scientist|science|design|test|stem|analyst", re.I
)
NON_ENGINEERING = re.compile(
    r"finance|accounting|accountant|audit|\btax\b|\bhr\b|human resources|people team|marketing|sales|legal|\blaw\b|paralegal"
    r"|communications|\bpr\b|recruit|talent|procurement|purchasing|commercial|business development|customer service"
    r"|office|administrat|receptionist|events?\b|graphic design|brand|content|social media|copywrit"
    r"|\bpeople\b|customer|trade|affairs|pharmacovigilance|regulatory|clinical (research|development|scientist|affairs)"
    r"|community|engagement|policy|esg|sustainability analyst|treasury|investor|payroll|facilities|journalis",
    re.I,
)


def disciplines(title: str, description: str = "") -> list[str]:
    """Tags from the title; falls back to the description only if the title names no discipline."""
    tags = [k for k, r in _DISC_RE.items() if r.search(title)]
    if tags:
        return tags
    head = description[:1500]
    scored = sorted(((len(r.findall(head)), k) for k, r in _DISC_RE.items()), reverse=True)
    return [k for n, k in scored[:2] if n >= 2]


def is_engineering(title: str, tags: list[str]) -> bool:
    if NON_ENGINEERING.search(title) and not re.search(r"engineer", title, re.I):
        return False
    return bool(tags) or bool(ENGINEERING_HINT.search(title))


# ---------------------------------------------------------------- location
UK_CITIES = (
    "London|Cambridge|Oxford|Bristol|Manchester|Birmingham|Edinburgh|Glasgow|Aberdeen|Leeds|Sheffield|Newcastle|Nottingham"
    "|Derby|Coventry|Leicester|Southampton|Portsmouth|Reading|Slough|Guildford|Brighton|Cardiff|Swansea|Belfast|Liverpool"
    "|Warrington|Stevenage|Harlow|Hatfield|Basingstoke|Farnborough|Filton|Preston|Warton|Barrow|Lincoln|Ipswich|Norwich|Milton Keynes"
    "|Luton|Swindon|Chippenham|Malmesbury|Hullavington|Gloucester|Cheltenham|Worcester|Wolverhampton|Stoke|Crewe|Chester"
    "|Ellesmere Port|Runcorn|Macclesfield|Stockport|Bolton|Hull|York|Durham|Sunderland|Middlesbrough|Teesside|Dundee|Inverness"
    "|Wrexham|Bridgend|Newport|Plymouth|Exeter|Bath|Poole|Bournemouth|Brough|Woking|Weybridge|Brentford|Uxbridge|Heathrow"
    "|Abingdon|Didcot|Culham|Harwell|Bicester|Silverstone|Brackley|Milton Park|Grove|Banbury|Gaydon|Solihull|Wellesbourne"
    "|Stafford|Lutterworth|Loughborough|Peterborough|Huntingdon|Chelmsford|Colchester|Basildon|Rochester|Maidstone|Crawley"
    "|Burton|Telford|Shrewsbury|Wotton-under-Edge|Stonehouse|Bracknell|Wokingham|High Wycombe|Hemel Hempstead|Watford|Welwyn"
)
UK = re.compile(
    rf"united kingdom|\bU\.?K\.?\b|\bGB\b|great britain|england|scotland|wales|northern ireland|\b({UK_CITIES})\b", re.I
)
NOT_UK = re.compile(r"cambridge,?\s*(ma|massachusetts)|london,?\s*(on|ontario|ky)|birmingham,?\s*(al|alabama)|"
                    r"new south wales|australia|canada|india|manchester,?\s*(nh|ct)|bristol,?\s*(ct|tn|va|pa)|oxford,?\s*(ms|oh)|reading,?\s*pa|\busa\b|united states", re.I)


def is_uk(location: str, country: str = "") -> bool:
    if country:
        return country.strip().lower() in {"gb", "uk", "united kingdom", "gbr", "great britain"}
    return bool(UK.search(location)) and not NOT_UK.search(location)


# ---------------------------------------------------------------- dates
MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
_DATE = (rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?((?:{MONTHS})[a-z]*),?\s+(20\d\d)"
         rf"|((?:{MONTHS})[a-z]*)\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(20\d\d)"
         r"|(\d{1,2})[/.](\d{1,2})[/.](20\d\d)")
DEADLINE = re.compile(
    rf"(?:closing date|application deadline|deadline|applications? (?:will )?close|closes?(?: on)?|apply by|open until|"
    rf"submit (?:your )?application by)\W{{0,25}}(?:[a-z]+day,?\s*)?(?:{_DATE})",
    re.I,
)


def _mk_date(groups) -> date | None:
    d1, m1, y1, m2, d2, y2, d3, m3, y3 = groups
    try:
        if d1:
            return datetime.strptime(f"{d1} {m1[:3]} {y1}", "%d %b %Y").date()
        if m2:
            return datetime.strptime(f"{d2} {m2[:3]} {y2}", "%d %b %Y").date()
        if d3:
            return date(int(y3), int(m3), int(d3))  # UK order dd/mm/yyyy
    except ValueError:
        return None
    return None


def find_deadline(text: str, today: date | None = None) -> str | None:
    """ISO date of the first plausible deadline mentioned in the text, else None."""
    today = today or date.today()
    for m in DEADLINE.finditer(text):
        d = _mk_date(m.groups())
        if d and today.replace(year=today.year - 1) < d < today.replace(year=today.year + 2):
            return d.isoformat()
    return None


def find_cycle(text: str) -> str | None:
    """Which recruitment cycle a role is for, e.g. '2027' or '2027/28'."""
    m = re.search(r"\b(20\d\d)\s*[-/–]\s*(20)?(\d\d)\b", text)
    if m and int(m.group(3)) == (int(m.group(1)) + 1) % 100:
        return f"{m.group(1)}/{m.group(3)}"
    m = re.search(r"\b(?:summer|starting|start(?:ing)? in|from|september|july|june)\s+(20\d\d)\b", text, re.I)
    return m.group(1) if m else None


# ---------------------------------------------------------------- text
_TAG = re.compile(r"<[^>]+>")


def html_to_text(s: str) -> str:
    s = html.unescape(html.unescape(s or ""))  # Greenhouse double-escapes content
    s = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", s, flags=re.I)
    return re.sub(r"[ \t\xa0]+", " ", _TAG.sub(" ", s)).strip()
