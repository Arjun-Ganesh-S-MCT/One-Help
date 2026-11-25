# Crop photo-check model

The app works without a model (it then shows the symptom library only). To turn on
"Check with a photo", this folder needs two files:

- `crop_model.onnx`  – image classifier (input `1x3x224x224` float32, output = class scores)
- `crop_labels.json` – class names plus the image settings the model expects

## Easiest: convert the ready-made PlantVillage model

```bash
source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r tools/requirements-model.txt
python tools/get_model.py        # downloads from Hugging Face and writes both files here
python main.py                   # "Check my crop" now shows the photo check
```
Then `git add models/ && git commit -m "Add crop model"` so the GitHub build includes it
(the .onnx is about 9 MB).

The default model is `linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification`
(MobileNetV2, 38 PlantVillage classes, ~95% accuracy reported by its author, licence listed as "other":
check it before you publish). Use `--source <id or folder>` for another Hugging Face model.

## What it can and cannot do

- It knows tomato and potato diseases that are in `oru/data/remedies.json`; for those, the app opens the remedy page.
- For other crops it knows (apple, grape, corn, ...) the app only names what it sees and says the crop is not in the library yet.
- It has **no rice or banana** classes. Those need a model fine-tuned on rice / banana leaf photos
  (see `tools/get_model.py` for how a model is converted; train it in Google Colab, then convert the same way).
- Below 60% confidence the app says "Not sure". PlantVillage photos are taken in a lab, so real field photos are harder.
