import streamlit as st
import requests
from PIL import Image

# ---------------------------------------------------
# CONFIG & CSS
# ---------------------------------------------------
st.set_page_config(page_title="Harmful Content Detector", page_icon="🚨")

st.markdown("""
<style>
.result-bad { padding:12px; background:#ffcccc; border-left:5px solid #d10000; border-radius:8px; font-size:18px; }
.result-okay { padding:12px; background:#ccffcc; border-left:5px solid #008000; border-radius:8px; font-size:18px; }
.section-card { background:white; padding:15px; margin:15px 0; border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,.1); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# OCR API
# ---------------------------------------------------
OCR_API_KEY = "helloworld"

def extract_text(img_path):
    url = "https://api.ocr.space/parse/image"
    with open(img_path, "rb") as f:
        files = {"file": f}
        data = {"apikey": OCR_API_KEY, "language": "eng"}
        try:
            res = requests.post(url, files=files, data=data).json()
            return res["ParsedResults"][0]["ParsedText"]
        except:
            return ""

# ---------------------------------------------------
# STRONG LOCAL TEXT FILTERS
# ---------------------------------------------------

PROFANITY = [
    "fuck","f**k","f---","shit","bitch","asshole","bastard","dick","pussy","slut",
    "whore","bollocks","crap","fucker","cunt"
]

HATE = [
    "kill you","kill yourself","kys","die","i will kill","murder you",
    "terrorist","racist","nazi","hitler","slave"
]

SELF_HARM = [
    "i want to die","i hate my life","i want to kill myself","end my life",
    "i want to disappear","suicidal","self harm","cut myself"
]

SEXUAL = [
    "nude","nudes","sex","boobs","tits","porn","fuck me","send nudes","horny"
]

# ---------------------------------------------------
# SIGHTENGINE IMAGE MODERATION
# ---------------------------------------------------
USER = "872379412"
SECRET = "BggWDfoR2MtExba7FVjwepaznrxWejv6"

def image_moderation(img_path):
    url = "https://api.sightengine.com/1.0/check.json"
    with open(img_path, 'rb') as f:
        files = {"media": f}
        params = {
            "models": "nudity,wad,offensive,gore,weapon,violence",
            "api_user": USER,
            "api_secret": SECRET,
        }
        try:
            return requests.post(url, data=params, files=files).json()
        except:
            return {}

# ---------------------------------------------------
# SAVE IMAGE
# ---------------------------------------------------
def save_uploaded_image(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode not in ("RGB","L"):
        img = img.convert("RGB")
    img.save("temp.png", "PNG")
    return "temp.png"

# ---------------------------------------------------
# TEXT SCORING
# ---------------------------------------------------
def analyze_text(raw_text):
    text = raw_text.lower()
    reasons = []

    if any(word in text for word in PROFANITY):
        reasons.append("Profanity detected.")

    if any(word in text for word in HATE):
        reasons.append("Hate or threatening language detected.")

    if any(word in text for word in SELF_HARM):
        reasons.append("Self-harm / suicidal expression detected.")

    if any(word in text for word in SEXUAL):
        reasons.append("Sexual/explicit text detected.")

    return reasons

# ---------------------------------------------------
# DECISION FUSION
# ---------------------------------------------------
def fuse(text_reasons, img_res):
    reasons = text_reasons.copy()

    nudity = img_res.get("nudity", {}) or {}
    if nudity.get("raw", 0) > 0.35:
        reasons.append("Nudity detected.")

    if nudity.get("sexual_activity", 0) > 0.25:
        reasons.append("Sexual activity in image.")

    if img_res.get("weapon", {}).get("prob", 0) > 0.4:
        reasons.append("Weapon detected.")

    if img_res.get("violence", {}).get("prob", 0) > 0.4:
        reasons.append("Violence detected.")

    if img_res.get("offensive", {}).get("prob", 0) > 0.4:
        reasons.append("Hate/offensive symbol detected.")

    if img_res.get("gore", {}).get("prob", 0) > 0.3:
        reasons.append("Gore detected.")

    final = "OKAY" if not reasons else "BAD"
    return final, reasons

# ---------------------------------------------------
# UI
# ---------------------------------------------------
st.title("🚨 Harmful Content Detection System")

uploaded = st.file_uploader("Upload image", type=["jpg","jpeg","png"])

if uploaded:
    temp_path = save_uploaded_image(uploaded)
    st.image(temp_path, width=350)

    # OCR
    text = extract_text(temp_path)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🔍 Extracted Text")
    st.write(text if text.strip() else "*No text found*")
    st.markdown("</div>", unsafe_allow_html=True)

    # TEXT ANALYSIS
    text_reasons = analyze_text(text)

    # IMAGE ANALYSIS
    img_res = image_moderation(temp_path)

    # FUSION
    final, reasons = fuse(text_reasons, img_res)

    st.subheader("Verdict")
    if final == "BAD":
        st.markdown("<div class='result-bad'>🚨 BAD</div>", unsafe_allow_html=True)
        for r in reasons:
            st.write("•", r)
    else:
        st.markdown("<div class='result-okay'>✅ OKAY</div>", unsafe_allow_html=True)
        st.write("Content is safe.")
