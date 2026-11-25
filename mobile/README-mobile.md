# Oru Udhavi – mobile app

Plain HTML/CSS/JS (no framework). Runs as a website, an installable PWA, or an Android APK (Capacitor).

## Try it now
    cd mobile && npm install && npm run serve      # open http://localhost:5173 on your phone/PC
Open it in Chrome on the phone and choose "Add to Home screen" – it installs like an app.

## Android APK
Push the repo to GitHub → Actions → "Android APK" → Run workflow → download `oru-udhavi-debug-apk`.
Or locally (needs Android Studio / SDK + JDK 17): `npm run sync && cd android && ./gradlew assembleDebug`.

## Crop photo check
Run `python tools/get_model.py` in the main project, then `mobile/tools/copy-model.sh`.
Without the model files the crop list of symptoms/remedies still works.

## Helper (AI chat)
Tap the gear → pick Gemini/Groq (free keys) → paste key. Key stays on the phone.
Voice answers work everywhere. Voice *input* uses the browser's speech recognition: good in Chrome, often missing inside the Android APK WebView – typing always works.

## Data
`npm run build:data` regenerates `www/js/data.js` from the Python data so Linux and mobile stay identical. `npm test` checks the JS against the Python results.

## Not verified yet
Real APK build, real phone voice, real AI keys, the ONNX model in the browser, and Tamil wording (needs a Tamil speaker's review).
