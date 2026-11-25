# Oru Udhavi: native Android app (Kotlin + Jetpack Compose)

A real Android app (not a web view): Kotlin, Jetpack Compose, the phone's own text-to-speech, speech recognition, phone dialer, share sheet and on-phone ONNX model.

## Get the APK (no Android Studio needed)
1. Put the repo on GitHub.  2. Actions → **Native Android APK** → Run workflow.  3. Download `oru-udhavi-native-debug-apk`, copy to the phone, open it (allow "install unknown apps").

Or open the `android-native` folder in Android Studio and press Run.

## Crop photo check
Run `python tools/get_model.py`, then copy `models/crop_model.onnx` and `models/crop_labels.json` into `app/src/main/assets/models/` and rebuild. Without them the symptom list and remedies still work.

## AI helper
Gear icon → choose Gemini or Groq (free keys) → paste the key. Stored only on the phone. Voice input opens Google's own speech dialog.

## Same data and logic as the other apps
`node tools/gen_data.mjs` regenerates `assets/data.json` from the shared data. `ParityTest` checks that the Kotlin letters, routes, suggestions and crop-label rules are identical to the Python app.

## Status
Logic (Data.kt, Logic.kt, Ai.kt, Store.kt) is compiled and verified against the Python results on a computer.
The screens (Compose) were written without being compiled or run, because the Android build tools are not available where this was written. Expect to fix small compile errors on the first CI run.
