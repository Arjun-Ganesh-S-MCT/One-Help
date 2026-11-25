"""Complaint logic: guess the problem, find the right office, write the letter.
No Qt in here so it is easy to test."""
import json
from dataclasses import dataclass
from datetime import date

from .paths import resource

_issues = None
_depts = None


def issues() -> list:
    global _issues
    if _issues is None:
        _issues = json.loads(resource("oru", "data", "issues.json").read_text("utf-8"))["issues"]
    return _issues


def departments() -> dict:
    global _depts
    if _depts is None:
        _depts = json.loads(resource("oru", "data", "departments.json").read_text("utf-8"))
    return _depts


def issue_by_id(issue_id: str) -> dict:
    return next(i for i in issues() if i["id"] == issue_id)


def suggest_issue(text: str):
    """Very simple keyword match (English + Tamil). Returns an issue id or None."""
    t = (text or "").lower()
    best, best_score = None, 0
    for it in issues():
        score = sum(1 for k in it["keywords"] if k.lower() in t)
        if score > best_score:
            best, best_score = it["id"], score
    return best


def route(issue_id: str, area: str) -> dict:
    """Which office should get this complaint? area = chennai | city | village"""
    d = departments()
    kind = d["issue_route"][issue_id]
    if kind == "power":
        block = d["authorities"]["power"]
    else:
        block = d["authorities"][area].get(kind) or d["authorities"][area]["local_body"]
    helplines = list(block["helplines"])
    if not helplines:
        helplines = [d["fallback_helpline"]]
    return {**block, "helplines": helplines}


@dataclass
class Complaint:
    issue_id: str
    area: str            # chennai | city | village
    town: str = ""
    address: str = ""
    landmark: str = ""
    name: str = ""
    phone: str = ""
    extra: str = ""
    has_photo: bool = False


def build_letter(c: Complaint, lang: str, today: date = None) -> str:
    today = today or date.today()
    block = route(c.issue_id, c.area)
    town = c.town.strip() or ("சென்னை" if lang == "ta" else "Chennai")
    to_block = block[lang].replace("{town}", town)
    issue = issue_by_id(c.issue_id)
    loc = c.landmark.strip() or c.address.strip()
    sentence = issue[f"sentence_{lang}"].replace("{loc}", loc)
    address_line = c.address.strip() + (", " + c.town.strip() if c.town.strip() else "")
    stamp = today.strftime("%d/%m/%Y")
    extra = c.extra.strip()
    phone = c.phone.strip()

    if lang == "ta":
        subject = f"{issue['name_ta']} தொடர்பான புகார்"
        lines = [
            "பெறுநர்:", to_block, "",
            "அனுப்புநர்:", c.name.strip(), address_line,
        ]
        if phone:
            lines.append(f"தொலைபேசி: {phone}")
        lines += [
            "", f"நாள்: {stamp}", "",
            f"பொருள்: {subject}", "",
            "மதிப்புமிகு ஐயா / அம்மா,", "",
            f"நான் {address_line} பகுதியில் வசிக்கிறேன். {sentence}. இதனால் பொதுமக்களுக்குப் பெரும் சிரமம் ஏற்படுகிறது."
            + (f" {extra}" if extra else ""),
            "",
            "எனவே, இந்தப் பிரச்சினையை விரைவில் நேரில் ஆய்வு செய்து சரிசெய்ய உரிய நடவடிக்கை எடுக்குமாறு பணிவுடன் கேட்டுக்கொள்கிறேன்."
            + (" பிரச்சினையின் புகைப்படம் இணைக்கப்பட்டுள்ளது." if c.has_photo else ""),
            "", "நன்றி.", "", "இப்படிக்கு,", c.name.strip(),
        ]
    else:
        subject = f"Complaint regarding {issue['name_en'].lower()}"
        lines = [
            "To,", to_block, "",
            "From,", c.name.strip(), address_line,
        ]
        if phone:
            lines.append(f"Phone: {phone}")
        lines += [
            "", f"Date: {stamp}", "",
            f"Subject: {subject}", "",
            "Respected Sir / Madam,", "",
            f"I am a resident of {address_line}. I would like to bring to your kind notice that {sentence}. "
            "This is causing great difficulty to the public."
            + (f" {extra}" if extra else ""),
            "",
            "I kindly request you to inspect the matter and take the necessary action at the earliest."
            + (" A photograph of the problem is attached." if c.has_photo else ""),
            "", "Thank you.", "", "Yours faithfully,", c.name.strip(),
        ]
    return "\n".join(lines)
