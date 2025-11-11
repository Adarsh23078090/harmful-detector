import streamlit as st
import requests
from transformers import pipeline
from PIL import Image

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
# OCR via OCR.Space (works everywhere)
# ---------------------------------------------------
OCR_API_KEY = "helloworld"
def extract_text(image_path: str) -> str:
    url = "https://api.ocr.space/parse/image"
    with open(image_path, "rb") as f:
        files = {"file": f}
        data = {"apikey": OCR_API_KEY, "language": "eng"}
        try:
            r = requests.post(url, files=files, data=data, timeout=30)
            return r.json().get("ParsedResults", [{}])[0].get("ParsedText", "") or ""
        except:
            return ""

# ---------------------------------------------------
# HuggingFace Models (all guaranteed safe)
# ---------------------------------------------------
toxicity_model = pipeline(
    "text-classification",
    model="unitary/toxic-bert",
    device=-1
)

sentiment_model = pipeline(
    "text-classification",
    model="finiteautomata/bertweet-base-sentiment-analysis",
    device=-1
)

# ---------------------------------------------------
# Sightengine API
# ---------------------------------------------------
API_USER = st.secrets.get("SIGHTENGINE_USER", "PUT_USER_ID_HERE")
API_SECRET = st.secrets.get("SIGHTENGINE_SECRET", "PUT_SECRET_HERE")

def image_moderation(img_path: str) -> dict:
    url = "https://api.sightengine.com/1.0/check.json"
    with open(img_path, "rb") as f:
        files = {"media": f}
        params = {
            "models": "nudity,wad,offensive,faces,gore,weapon,violence",
            "api_user": API_USER,
            "api_secret": API_SECRET
        }
        try:
            res = requests.post(url, data=params, files=files, timeout=30)
            return res.json()
        except:
            return {}

# ---------------------------------------------------
# Fuse decisions safely
# ---------------------------------------------------
def fuse(text_res, senti_res, img_res):
    reasons = []
    text = text_res["raw"]

    # suicide keywords
    suicide_words = ["suicide", "kill myself", "end it", "die", "self harm", "cut myself", "no reason to live"]

    # sentiment
    if senti_res["label"].lower() == "negative" and any(w in text.lower() for w in suicide_words):
        reasons.append("Possible self-harm intent (negative sentiment + suicidal keywords).")

    # toxicity
    if text_res["toxic"]["label"].lower() == "toxic" and text_res["toxic"]["score"] > 0.75:
        reasons.append("Toxic / abusive language detected.")

    nudity = img_res.get("nudity", {}) or {}
    weapon = img_res.get("weapon", {}) or {}
    violence = img_res.get("violence", {}) or {}
    offensive = img_res.get("offensive", {}) or {}
    gore = img_res.get("gore", {}) or {}

    # image thresholds
    if nudity.get("raw", 0) > 0.50:
        reasons.append("Nudity detected.")
    if nudity.get("sexual_activity", 0) > 0.50:
        reasons.append("Sexual activity detected.")
    if weapon.get("prob", 0) > 0.60:
        reasons.append("Weapon detected.")
    if violence.get("prob", 0) > 0.60:
        reasons.append("Violence detected.")
    if offensive.get("prob", 0) > 0.60:
        reasons.append("Offensive / hate symbol detected.")
    if gore.get("prob", 0) > 0.50:
        reasons.append("Gore detected.")

    return ("OKAY" if not reasons else "BAD"), reasons

# ---------------------------------------------------
# Image saving (safe PNG)
# ---------------------------------------------------
def save_uploaded_image(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    temp_path = "temp.png"
    img.save(temp_path, "PNG")
    return temp_path

# ---------------------------------------------------
# UI
# ---------------------------------------------------
st.title("🚨 Harmful Content Detector")
uploaded_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    temp_path = save_uploaded_image(uploaded_file)
    st.image(temp_path, width=350)

    # OCR
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🔍 OCR Text")
    text = extract_text(temp_path)
    st.write(text if text.strip() else "_No text detected_")
    st.markdown("</div>", unsafe_allow_html=True)

    # TEXT ANALYSIS
    toxin = toxicity_model(text)[0] if text.strip() else {"label":"neutral","score":0}
    senti = sentiment_model(text)[0] if text.strip() else {"label":"neutral","score":0}
    text_res = {"toxic": toxin, "raw": text}

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("📘 Text Moderation")
    st.write("Toxicity:", toxin)
    st.write("Sentiment:", senti)
    st.markdown("</div>", unsafe_allow_html=True)

    # IMAGE ANALYSIS
    img_res = image_moderation(temp_path)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🖼 Image Moderation")
    st.write(img_res)
    st.markdown("</div>", unsafe_allow_html=True)

    # FINAL
    final, reasons = fuse(text_res, senti, img_res)
    st.markdown("---")
    st.subheader("🧾 Final Verdict")

    if final == "BAD":
        st.markdown("<div class='result-bad'>🚨 BAD</div>", unsafe_allow_html=True)
        for r in reasons:
            st.write("•", r)
    else:
        st.markdown("<div class='result-okay'>✅ OKAY</div>", unsafe_allow_html=True)
        st.write("Content is safe.")
