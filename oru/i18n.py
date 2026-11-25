"""Tamil / English text. Tamil is the default language."""
from PyQt6.QtCore import QObject, pyqtSignal

STRINGS = {
    "app_name": ("ஒரு உதவி", "Oru Udhavi"),
    "tagline": ("உங்கள் ஊருக்கான ஒரு உதவி", "One help for your town"),
    "home_report": ("புகார் செய்ய", "Report a problem"),
    "home_report_sub": ("புகைப்படத்துடன் புகார் கடிதம் தயார் செய்யுங்கள்", "Get a complaint letter ready in minutes"),
    "home_crop": ("பயிர் நோய் பார்க்க", "Check my crop"),
    "home_crop_sub": ("நோய் அறிகுறியும் தீர்வும்", "Disease symptoms and remedies"),
    "home_history": ("என் புகார்கள்", "My complaints"),
    "home_history_sub": ("நான் செய்த புகார்களின் பட்டியல்", "Complaints I have made"),
    "home_emergency": ("அவசர எண்கள்", "Emergency numbers"),
    "home_chat": ("உதவியாளரிடம் பேசுங்கள்", "Talk to the helper"),
    "home_chat_sub": ("தமிழில் பேசலாம் அல்லது எழுதலாம்", "Speak or type your question"),
    "chat_title": ("உதவியாளர்", "Helper"),
    "chat_hello": ("வணக்கம்! நான் ஒரு உதவி. சாலை, குப்பை, தண்ணீர், மின்சாரம் போன்ற புகார்கள், மற்றும் பயிர் நோய்கள் பற்றி உதவுவேன். என்ன பிரச்சினை?",
                   "Hello! I am Oru Udhavi. I can help with complaints about roads, garbage, water, electricity and so on, and with crop diseases. What is the problem?"),
    "chat_placeholder": ("இங்கே எழுதுங்கள்…", "Type here…"),
    "chat_thinking": ("யோசிக்கிறேன்…", "Thinking…"),
    "chat_listening": ("கேட்கிறேன்… பேசி முடித்ததும் மைக்கை மீண்டும் அழுத்துங்கள்", "Listening… press the mic again when you finish"),
    "chat_recognising": ("புரிந்துகொள்கிறேன்…", "Understanding…"),
    "chat_speaking": ("பேசுகிறேன்…", "Speaking…"),
    "chat_voice_on": ("குரல் ஆன்", "Voice on"),
    "chat_voice_off": ("குரல் ஆஃப்", "Voice off"),
    "chat_new": ("புதிதாகத் தொடங்கு", "New chat"),
    "chat_open_form": ("புகார் படிவத்தைத் திற", "Open the complaint form"),
    "chat_key_title": ("உதவியாளர் அமைப்பு", "Helper setup"),
    "chat_setup": ("AI அமைப்பு", "AI setup"),
    "chat_setup_which": ("எந்த AI சேவை?", "Which AI service?"),
    "chat_setup_key": ("சாவியை இங்கே ஒட்டுங்கள் (API key)", "Paste the key here (API key)"),
    "chat_setup_get": ("இலவச சாவி கிடைக்கும் இடம்: {w}", "Get a key at: {w}"),
    "chat_setup_local": ("சாவி தேவையில்லை. இந்தக் கணினியில் Ollama ஓடிக்கொண்டிருக்க வேண்டும்.", "No key needed. Ollama must be running on this computer."),
    "chat_setup_save": ("சேமி", "Save"),
    "chat_err_bad_key": ("சாவி சரியில்லை. மீண்டும் முயற்சி செய்யுங்கள்.", "The key was not accepted. Please try again."),
    "chat_err_no_local": ("Ollama இந்தக் கணினியில் ஓடவில்லை. 'ollama serve' இயக்கி, மாடலைப் பதிவிறக்கியிருக்கிறீர்களா எனப் பாருங்கள்.", "Ollama is not running on this computer. Start it with 'ollama serve' and make sure the model is downloaded."),
    "chat_err_offline": ("இணைய இணைப்பு இல்லை. இணைப்பைச் சரிபார்த்து மீண்டும் முயலுங்கள்.", "No internet. Check the connection and try again."),
    "chat_err_busy": ("இப்போது அதிகக் கோரிக்கைகள் உள்ளன. சிறிது நேரம் கழித்து முயலுங்கள்.", "Too many requests right now. Please try again in a little while."),
    "chat_err_server": ("சேவையில் சிக்கல். மீண்டும் முயலுங்கள்.", "The service had a problem. Please try again."),
    "chat_err_no_mic": ("மைக்ரோஃபோன் கிடைக்கவில்லை.", "No microphone found."),
    "chat_err_mic_format": ("இந்த மைக்ரோஃபோன் வடிவம் ஆதரிக்கப்படவில்லை.", "This microphone format is not supported."),
    "chat_err_too_short": ("எதுவும் கேட்கவில்லை. மீண்டும் பேசுங்கள்.", "Nothing was heard. Please speak again."),
    "chat_err_not_understood": ("புரியவில்லை. மெதுவாக, தெளிவாகப் பேசுங்கள்.", "Could not understand. Please speak slowly and clearly."),
    "chat_err_tts": ("பதிலைப் படிக்க முடியவில்லை (இணையம் தேவை). எழுத்தில் படிக்கலாம்.", "Could not read the answer aloud (internet needed). You can read it on screen."),
    "chat_no_voice_in": ("பேச்சு அறிதல் நிறுவப்படவில்லை: pip install SpeechRecognition, மற்றும் sudo pacman -S flac", "Speech recognition is not installed: pip install SpeechRecognition, and sudo pacman -S flac"),
    "chat_no_voice_out": ("குரல் நிறுவப்படவில்லை: pip install gTTS", "Voice is not installed: pip install gTTS"),
    "back": ("பின்னால்", "Back"),
    "lang_button": ("English", "தமிழ்"),
    "report_title": ("புகார் செய்ய", "Report a problem"),
    "step1": ("1. என்ன பிரச்சினை?", "1. What is the problem?"),
    "step2": ("2. புகைப்படம் சேர்க்கவும்", "2. Add a photo"),
    "photo_choose": ("புகைப்படம் தேர்வு செய்க", "Choose a photo"),
    "photo_change": ("வேறு புகைப்படம்", "Change photo"),
    "photo_none": ("புகைப்படம் இல்லை (விருப்பம்)", "No photo (optional)"),
    "photo_dialog": ("புகைப்படத்தைத் தேர்வு செய்யுங்கள்", "Choose a photo"),
    "step3": ("3. எங்கே உள்ளது?", "3. Where is it?"),
    "area_chennai": ("சென்னை", "Chennai"),
    "area_city": ("வேறு நகரம் / பேரூராட்சி", "Another city or town"),
    "area_village": ("கிராமம் (ஊராட்சி)", "Village (panchayat)"),
    "town_label": ("ஊர் / நகரத்தின் பெயர்", "Name of your town or village"),
    "address_label": ("தெரு / பகுதி", "Street / area"),
    "landmark_label": ("அடையாளம் (எ.கா. கோயில் அருகில்)", "Landmark (e.g. near the temple)"),
    "step4": ("4. உங்கள் விவரம்", "4. Your details"),
    "name_label": ("உங்கள் பெயர்", "Your name"),
    "phone_label": ("தொலைபேசி எண்", "Phone number"),
    "extra_label": ("கூடுதல் விவரம் (விருப்பம்)", "More details (optional)"),
    "make_letter": ("புகார் கடிதம் தயார் செய்", "Make complaint letter"),
    "hint_suggest": ("இது '{x}' போல் தெரிகிறது. தேவையானால் மாற்றலாம்.", "This looks like '{x}'. You can change it."),
    "err_issue": ("பிரச்சினையைத் தேர்வு செய்யுங்கள்", "Please choose the problem"),
    "err_address": ("தெரு / பகுதியை எழுதுங்கள்", "Please write the street or area"),
    "err_town": ("ஊரின் பெயரை எழுதுங்கள்", "Please write the town name"),
    "err_name": ("உங்கள் பெயரை எழுதுங்கள்", "Please write your name"),
    "result_title": ("உங்கள் புகார்", "Your complaint"),
    "send_to": ("இங்கே அனுப்பவும்", "Send this to"),
    "helpline": ("உதவி எண்", "Helpline"),
    "no_helpline": ("இந்தப் பகுதிக்கு உதவி எண் இல்லை. நேரில் அலுவலகத்தில் கொடுக்கலாம்.", "No helpline listed for this area. You can hand the letter in at the office."),
    "letter_lang": ("கடிதத்தின் மொழி", "Letter language"),
    "copy": ("நகலெடு", "Copy letter"),
    "copied": ("நகலெடுக்கப்பட்டது", "Copied"),
    "save_file": ("கோப்பாகச் சேமி", "Save as file"),
    "saved_to": ("சேமிக்கப்பட்டது", "Saved"),
    "mark_sent": ("அனுப்பிவிட்டேன்", "I have sent it"),
    "sent_done": ("அனுப்பியதாகக் குறிக்கப்பட்டது", "Marked as sent"),
    "photo_note": ("அனுப்பும்போது உங்கள் புகைப்படத்தையும் சேர்க்க மறக்காதீர்கள்.", "Remember to attach your photo when you send it."),
    "history_title": ("என் புகார்கள்", "My complaints"),
    "history_empty": ("இன்னும் புகார் எதுவும் இல்லை", "No complaints yet"),
    "status_draft": ("தயார்", "Ready"),
    "status_sent": ("அனுப்பப்பட்டது", "Sent"),
    "view": ("பார்", "View"),
    "delete": ("நீக்கு", "Delete"),
    "crop_title": ("பயிர் நோய் பார்க்க", "Check my crop"),
    "crop_step1": ("1. பயிரைத் தேர்வு செய்யுங்கள்", "1. Choose your crop"),
    "crop_step2": ("2. நீங்கள் காணும் நோயைத் தேர்வு செய்யுங்கள்", "2. Choose the disease you see"),
    "crop_photo_title": ("புகைப்படம் மூலம் பார்க்க", "Check with a photo"),
    "crop_ai_unavailable": ("புகைப்பட சோதனை இன்னும் இந்தக் கணினியில் நிறுவப்படவில்லை. இப்போது கீழே உள்ள பட்டியலில் அறிகுறிகளைப் பார்த்துத் தேர்வு செய்யுங்கள்.", "Photo check is not installed on this computer yet. For now, pick the symptoms from the list below."),
    "crop_check": ("பரிசோதி", "Check"),
    "ai_result": ("இது '{x}' ஆக இருக்கலாம் ({p}%)", "This may be '{x}' ({p}%)"),
    "ai_not_sure": ("உறுதியாகச் சொல்ல முடியவில்லை. வேளாண் அலுவலரிடம் காட்டுங்கள்.", "Not sure. Please show it to an agriculture officer."),
    "ai_other": ("இது '{x}' போல் தெரிகிறது ({p}%). இந்தப் பயிர் / நோய் இன்னும் எங்கள் பட்டியலில் இல்லை.", "This looks like '{x}' ({p}%). This crop or disease is not in our library yet."),
    "ai_disclaimer": ("இது கணினியின் யூகம் மட்டுமே. உறுதி செய்ய வேளாண் அலுவலரிடம் காட்டுங்கள்.", "This is only the computer's guess. Show it to an agriculture officer to be sure."),
    "ai_healthy": ("செடி ஆரோக்கியமாகத் தெரிகிறது", "The plant looks healthy"),
    "symptoms": ("அறிகுறிகள்", "Symptoms"),
    "what_to_do": ("என்ன செய்யலாம்", "What you can do"),
    "prevention": ("வருமுன் காக்க", "How to prevent it"),
    "officer_note": ("நோய் அதிகமாக இருந்தால் அருகிலுள்ள வேளாண்மை விரிவாக்க மையத்தை அணுகுங்கள். கிசான் அழைப்பு மையம்: 1800 180 1551", "If the disease is severe, contact your nearest agriculture extension centre. Kisan Call Centre: 1800 180 1551"),
    "emergency_title": ("அவசர எண்கள்", "Emergency numbers"),
    "close": ("மூடு", "Close"),
}


class _Bus(QObject):
    changed = pyqtSignal()


bus = _Bus()
_lang = "ta"


def lang() -> str:
    return _lang


def set_lang(code: str) -> None:
    global _lang
    if code in ("ta", "en") and code != _lang:
        _lang = code
        bus.changed.emit()


def toggle() -> None:
    set_lang("en" if _lang == "ta" else "ta")


def tr(key: str, **kw) -> str:
    ta, en = STRINGS[key]
    s = ta if _lang == "ta" else en
    return s.format(**kw) if kw else s


def other(key: str) -> str:
    """The text in the language that is NOT selected (used for small subtitles)."""
    ta, en = STRINGS[key]
    return en if _lang == "ta" else ta


def pick(d: dict, base: str) -> str:
    """pick(issue, 'name') -> issue['name_ta'] or issue['name_en']"""
    return d[f"{base}_{_lang}"]
