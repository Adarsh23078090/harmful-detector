import streamlit as st
import requests
from PIL import Image
import os

# ---------------------------------------------------
# Streamlit Page Config & CSS
# ---------------------------------------------------
st.set_page_config(page_title="Harmful Content Detector", page_icon="🚨", layout="centered")
st.markdown("""
<style>
.result-bad { padding:12px; background:#ffcccc; border-left:5px solid #d10000; border-radius:8px; font-size:18px; }
.result-okay { padding:12px; background:#ccffcc; border-left:5px solid #008000; border-radius:8px; font-size:18px; }
.section-card { background:#fff; padding:16px; border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,.08); margin:16px 0; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# APIs
# ---------------------------------------------------
OCR_API_KEY = "helloworld"    # free OCR.Space demo key
DEEPAI_KEY = "quickstart-QUdJIGlzIGNvbWluZy4uLi4K"  # public free key

SIGHT_USER = "872379412"
SIGHT_SECRET = "BggWDfoR2MtExba7FVjwepaznrxWejv6"

# ---------------------------------------------------
# OCR API
# ---------------------------------------------------
def extract_text(image_path):
    url = "https://api.ocr.space/parse/image"
    with open(image_path, "rb") as f:
        files = {"file": f}
        data = {"apikey": OCR_API_KEY, "language": "eng"}
        try:
            r = requests.post(url, files=files, data=data).json()
            return r["ParsedResults"][0]["ParsedText"]
        except:
            return ""

# ---------------------------------------------------
# DeepAI Toxicity
# ---------------------------------------------------
def check_toxicity(text):
    url = "https://api.deepai.org/api/toxicity"
    headers = {"api-key": DEEPAI_KEY}
    try:
        r = requests.post(url, data={"text": text}, headers=headers).json()
        return float(r.get("output", 0))
    except:
        return 0

# ---------------------------------------------------
# DeepAI Sentiment
# ---------------------------------------------------
def check_sentiment(text):
    url = "https://api.deepai.org/api/sentiment-analysis"
    headers = {"api-key": DEEPAI_KEY}
    try:
        r = requests.post(url, data={"text": text}, headers=headers).json()
        out = r.get("output", ["neutral"])
        return out[0].lower()
    except:
        return "neutral"

# ---------------------------------------------------
# Sightengine Image Moderation
# ---------------------------------------------------
def image_moderation(img_path):
    url = "https://api.sightengine.com/1.0/check.json"
    with open(img_path, "rb") as f:
        files = {"media": f}
        params = {
            "models": "nudity,wad,offensive,faces,gore,weapon,violence",
            "api_user": SIGHT_USER,
            "api_secret": SIGHT_SECRET,
        }
        try:
            return requests.post(url, data=params, files=files).json()
        except:
            return {}

# ---------------------------------------------------
# Save Uploaded Image
# ---------------------------------------------------
def save_uploaded_image(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode not in ("RGB","L"):
        img = img.convert("RGB")
    img.save("temp.png", "PNG")
    return "temp.png"

# ---------------------------------------------------
# Decision Fusion
# ---------------------------------------------------
def fuse(text, tox, sentiment, img):
    reasons = []

    if tox > 0.6:
        reasons.append("Toxic language detected.")

    if sentiment == "negative":
        reasons.append("Negative/sad emotional tone detected.")

    nudity = img.get("nudity", {}) or {}
    if nudity.get("raw", 0) > 0.5:
        reasons.append("Nudity detected.")

    weapon = img.get("weapon", {}) or {}
    if weapon.get("prob", 0) > 0.6:
        reasons.append("Weapon detected.")

    violence = img.get("violence", {}) or {}
    if violence.get("prob", 0) > 0.6:
        reasons.append("Violence detected.")

    offensive = img.get("offensive", {}) or {}
    if offensive.get("prob", 0) > 0.6:
        reasons.append("Hate/offensive symbol detected.")

    gore = img.get("gore", {}) or {}
    if gore.get("prob", 0) > 0.5:
        reasons.append("Gore detected.")

    return ("OKAY" if not reasons else "BAD", reasons)

# ---------------------------------------------------
# UI
# ---------------------------------------------------
st.title("🚨 Harmful Content Detector")

uploaded_file = st.file_uploader("Upload an image", type=["jpg","jpeg","png"])

if uploaded_file:
    temp_path = save_uploaded_image(uploaded_file)
    st.image(temp_path, width=350)

    # OCR
    text = extract_text(temp_path)

    # TEXT ANALYSIS
    tox = check_toxicity(text)
    sentiment = check_sentiment(text)

    # IMAGE ANALYSIS
    img_res = image_moderation(temp_path)

    # FINAL DECISION
    final, reasons = fuse(text, tox, sentiment, img_res)

    st.markdown("---")
    st.subheader("Final Verdict")

    if final == "BAD":
        st.markdown("<div class='result-bad'>🚨 BAD</div>", unsafe_allow_html=True)
        for r in reasons:
            st.write("•", r)
    else:
        st.markdown("<div class='result-okay'>✅ OKAY</div>", unsafe_allow_html=True)
        st.write("Content is safe.")
