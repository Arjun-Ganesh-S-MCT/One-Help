# Oru Udhavi (ஒரு உதவி) – "One Help"

A simple Tamil / English desktop app for everyday people in Tamil Nadu.

1. **Report a problem** – pick the problem (road, garbage, drain, street light, water, electricity, stray animals),
   add a photo, say where it is, and the app tells you **which office to contact** and writes a
   **ready-to-send complaint letter** in Tamil or English. Letters are saved in *My complaints*.
2. **Check my crop** – choose tomato, potato, rice or banana and read the symptoms, what to do and how to prevent
   common diseases, in Tamil or English. Photo check with a ready-made AI model: run `python tools/get_model.py` once (see `models/README.md`).
3. **Talking helper** – chat in Tamil or English by typing or speaking; it answers aloud. Uses an online AI service.
4. **Emergency numbers** – 112, police, ambulance, fire, women, child, Kisan Call Centre.

Starts with a small splash window (the intro video at its own size, click to skip), then opens the app.

## Run on Arch Linux

```bash
sudo pacman -S python git
git clone <your-repo-url> oru-udhavi && cd oru-udhavi
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py                 # with splash
python main.py --no-splash     # skip splash while developing
python -m pytest -q tests      # run tests (needs: pip install pytest onnx)
```
### Talking helper (free AI)

```bash
sudo pacman -S flac            # needed once, for the microphone
```
Open **Talk to the helper** -> **AI setup** and pick one:

| Choice | Cost | Notes |
|---|---|---|
| Google Gemini | free key, no card (aistudio.google.com) | Best Tamil. Free limits and model names change, check the site. |
| Groq | free key (console.groq.com) | Very fast; Tamil is weaker. |
| Ollama | free, runs on your PC, no key, works offline | `sudo pacman -S ollama && ollama serve`, then `ollama pull qwen2.5:7b`. Needs ~8 GB RAM; Tamil is basic. |
| Claude | paid key | Optional. |

- Keys are saved in `~/.config/oru-udhavi/config.json` (or use env `GEMINI_API_KEY`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`).
- If a model name stops working, set `ORU_MODEL=<new name>`.
- Voice **in** = Google speech recognition, voice **out** = Google text-to-speech (gTTS), both free but need internet.
  Without them (or without a microphone) the chat still works by typing.
- The AI never makes up phone numbers: it looks them up in `oru/data/departments.json` through tools.
  Free/small models sometimes skip the lookup, so keep the "confirm the number" habit.

Your complaints are saved in `~/.local/share/oru-udhavi/complaints.db`.

## Build + release with GitHub Actions

```bash
git init && git add . && git commit -m "Oru Udhavi v0.1"
git branch -M main
git remote add origin git@github.com:<you>/oru-udhavi.git
git push -u origin main        # tests + Linux build run automatically (Actions tab -> artifact)
git tag v0.1.0 && git push origin v0.1.0   # also publishes oru-udhavi-linux-x86_64.tar.gz as a GitHub Release
```
Install a downloaded build: `tar xzf oru-udhavi-linux-x86_64.tar.gz && cd oru-udhavi && ./install-local.sh`
(`build.sh` puts the installer inside the folder for you).

## Project layout

```
main.py                 start the app
oru/app.py              window + splash start-up, fonts
oru/complaint.py        problem -> office -> letter (no UI code, tested)
oru/assistant.py        talking helper brain (online AI + lookups, no UI code, tested)
oru/voice.py            microphone + spoken replies
oru/crop.py             disease library + optional ONNX photo check
oru/labels.py           maps the model's class names to our remedy library
oru/store.py            saves complaints (SQLite)
oru/i18n.py             all Tamil / English text
oru/data/*.json         problems, offices + helplines, crop diseases  <- edit these, no code needed
oru/ui/                 screens, theme, splash
assets/                 icon, banner, splash.mp4
packaging/              build script, .desktop file, installer
tools/get_model.py      downloads + converts the ready-made plant-disease model
tests/                  tests for the logic
```

## Before you show it to others

- **Helplines**: 1913 (Chennai Corporation), 1916 (Metrowater drinking water), 044 4567 4567 (Metrowater) and
  94987 94987 / 1912 (Minnagam power) were confirmed in news/guide articles on 2026-10-21; the CM helpline 1100 and the
  all-India emergency numbers are widely published but re-check them. Other towns have no number listed, so the app
  shows the CM helpline and the local office name. Fix anything in `oru/data/departments.json`.
- **Tamil text** (letters, remedies) was written by an AI assistant: have a Tamil speaker and, for the crop advice, an
  agriculture officer read it. The remedies give no pesticide names or doses on purpose.
- The Splash plays the video's sound at 50% volume; change `volume` in `oru/ui/splash.py` or mute it.


## Mobile app
See `mobile/README-mobile.md` (website / installable PWA / Android APK built by GitHub Actions: `.github/workflows/android.yml`).
Both apps share one data source: edit `oru/data/*.json` and `oru/i18n.py`, then run `python tools/gen_mobile_data.py`.

## Design
Both apps use the tactile (skeuomorphic) design: ivory 60%, ink + sand 30%, red 10% (only the main action and lamps).
Check the Linux screens with `python tools/shoot_linux.py` (writes PNGs to `screenshots-linux/`).
