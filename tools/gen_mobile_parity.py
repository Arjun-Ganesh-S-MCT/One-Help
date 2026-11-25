"""Writes mobile/tests/parity.json using the REAL Python functions, so the JavaScript port can be
checked against them:  python tools/gen_mobile_parity.py  then  cd mobile && node --test"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from oru import complaint as C  # noqa: E402
from oru import labels  # noqa: E402

TODAY = date(2026, 11, 24)
PLANTVILLAGE = """Apple___Apple_scab Apple___Black_rot Apple___Cedar_apple_rust Apple___healthy Blueberry___healthy
Cherry_(including_sour)___Powdery_mildew Cherry_(including_sour)___healthy Corn_(maize)___Cercospora_leaf_spot_Gray_leaf_spot
Corn_(maize)___Common_rust_ Corn_(maize)___Northern_Leaf_Blight Corn_(maize)___healthy Grape___Black_rot Grape___Esca_(Black_Measles)
Grape___Leaf_blight_(Isariopsis_Leaf_Spot) Grape___healthy Orange___Haunglongbing_(Citrus_greening) Peach___Bacterial_spot Peach___healthy
Pepper,_bell___Bacterial_spot Pepper,_bell___healthy Potato___Early_blight Potato___Late_blight Potato___healthy Raspberry___healthy
Soybean___healthy Squash___Powdery_mildew Strawberry___Leaf_scorch Strawberry___healthy Tomato___Bacterial_spot Tomato___Early_blight
Tomato___Late_blight Tomato___Leaf_Mold Tomato___Septoria_leaf_spot Tomato___Spider_mites_Two-spotted_spider_mite Tomato___Target_Spot
Tomato___Tomato_Yellow_Leaf_Curl_Virus Tomato___Tomato_mosaic_virus Tomato___healthy""".split()
TEXTS = ["pothole on the road", "குப்பை அதிகம்", "no water since 3 days", "street light not working", "dog bite stray dogs",
         "drainage overflow near house", "power cut transformer", "", "something else entirely", "சாலை பள்ளம் மற்றும் குப்பை", "ROAD CRACK TAR"]


def letters():
    out = []
    for issue in C.issues():
        for area in ("chennai", "city", "village"):
            for lang in ("ta", "en"):
                for variant in range(3):
                    c = C.Complaint(
                        issue_id=issue["id"], area=area,
                        town="" if area == "chennai" and variant != 2 else " Tambaram " if variant else "Madurai",
                        address=" 12 Gandhi Street " if variant == 1 else "Gandhi Street, Chrompet",
                        landmark="near the temple" if variant == 2 else "",
                        name="A. Kumar", phone="" if variant == 0 else "98765 43210",
                        extra="" if variant != 1 else "It has been like this for a month.", has_photo=variant == 2)
                    out.append({"c": c.__dict__, "lang": lang, "letter": C.build_letter(c, lang, TODAY)})
    return out


def main():
    data = {
        "today": TODAY.isoformat(),
        "letters": letters(),
        "routes": [{"issue": i["id"], "area": a, "route": C.route(i["id"], a)} for i in C.issues() for a in ("chennai", "city", "village")],
        "suggest": [{"text": t, "id": C.suggest_issue(t)} for t in TEXTS],
        "labels": [{"raw": r, "reading": {"kind": x.kind, "crop": x.crop, "diseaseId": x.disease_id, "pretty": x.pretty}}
                   for r in PLANTVILLAGE for x in [labels.interpret(r)]],
    }
    dest = ROOT / "mobile" / "tests" / "parity.json"
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
    print(f"wrote {dest}: {len(data['letters'])} letters, {len(data['routes'])} routes, {len(data['labels'])} labels")


main()
