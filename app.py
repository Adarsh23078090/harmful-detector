import streamlit as st
import requests
from transformers import pipeline
from PIL import Image
import os

# ---------------------------------------------------
# Streamlit Page Config
# ---------------------------------------------------
st.set_page_config(
    page_title="Harmful Content Detector",
    page_icon="🚨",
    layout="centered",
)

# ---------------------------------------------------
# Custom CSS
# ---------------------------------------------------
st.markdown("""
<style>
.result-bad {
    padding: 12px;
    background-color: #ffcccc;
    border-left: 5px solid #d10000;
    border-radius: 5px;
    font-size: 18px;
}
.result-okay {
    padding: 12px;
    background-color: #ccffcc;
    border-left: 5px solid #008000;
    border-radius: 5px;
    font-size: 18px;
}
.section-card {
    background-color: white;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# OCR using OCR.Space API
# ---------------------------------------------------
OCR_API_KEY = "helloworld"   # Demo key

def extract_text(image_path):
    url = "https://api.ocr.space/parse/image"
    with open(image_path, "rb") as f:
        files = {"file": f}
        payload = {"apikey": OCR_API_KEY, "language": "eng"}
        r = requests.post(url, files=files, data=payload)
        try:
            return r.json()["ParsedResults"][0]["ParsedText"]
        except:
            return ""

# ---------------------------------------------------
# HuggingFace Models (clean dtype, no warnings)
# ---------------------------------------------------
toxicity_model = pipeline(
    "text-classification",
    model="unitary/toxic-bert",
    device=-1,
    dtype="float32"
)

suicide_model = pipeline(
    "text-classification",
    model="facebook/roberta-hate-speech-dynabench-r4-target",
    device=-1,
    dtype="float32"
)

# ---------------------------------------------------
# Sightengine API
# ---------------------------------------------------
API_USER = "872379412"
API_SECRET = "BggWDfoR2MtExba7FVjwepaznrxWejv6"

def image_moderation(img_path):
    url = "https://api.sightengine.com/1.0/check.json"
    files = {"media": open(img_path, "rb")}
    params = {
        "models": "nudity,wad,offensive,faces,gore,weapon,violence",
        "api_user": API_USER,
        "api_secret": API_SECRET
    }
    return requests.post(url, data=params, files=files).json()

# ---------------------------------------------------
# Decision Fusion
# ---------------------------------------------------
def fuse(text_res, img_res):
    reasons = []

    suicide_keywords = [
        "suicide","self-harm","kill","die","hurt","threat",
        "violent","abusive","harassment","hate"
    ]

    label = text_res["suicidal"]["label"].lower()
    if any(w in label for w in suicide_keywords) and text_res["suicidal"]["score"] > 0.45:
        reasons.append("Self-harm / Threatening language detected")

    if text_res["toxic"]["label"].lower() != "neutral" and text_res["toxic"]["score"] > 0.45:
        reasons.append("Toxic or abusive text detected")

    nudity = img_res.get("nudity", {})
    weapon = img_res.get("weapon", {})
    violence = img_res.get("violence", {})
    gore = img_res.get("gore", {})
    offensive = img_res.get("offensive", {})

    if nudity.get("sexual_activity", 0) > 0.25:
        reasons.append("Sexual activity detected")
    if nudity.get("sexual_display", 0) > 0.25:
        reasons.append("Sexual display detected")
    if nudity.get("raw", 0) > 0.3:
        reasons.append("Nudity detected")

    if weapon.get("prob", 0) > 0.4:
        reasons.append("Weapon detected")
    if violence.get("prob", 0) > 0.4:
        reasons.append("Violence detected")
    if gore.get("prob", 0) > 0.3:
        reasons.append("Gore detected")
    if offensive.get("prob", 0) > 0.4:
        reasons.append("Offensive / Hate symbol detected")

    return ("OKAY" if not reasons else "BAD"), reasons

# ---------------------------------------------------
# Safe Image Save (Avoid JPG errors)
# ---------------------------------------------------
def save_uploaded_image(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    temp_path = "temp.png"
    img.save(temp_path, format="PNG")
    return temp_path

# ---------------------------------------------------
# Streamlit UI
# ---------------------------------------------------
st.title("🚨 Harmful Content Detection System")
st.write("Upload → OCR → Text Moderation → Image Moderation → Verdict")

uploaded_file = st.file_uploader("Upload an image", type=["jpg","jpeg","png"])

if uploaded_file:

    # Save clean PNG
    temp_path = save_uploaded_image(uploaded_file)
    img = Image.open(temp_path)
    st.image(img, caption="Uploaded Image", width=350)

    # OCR
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🔍 OCR — Extracted Text")
    text = extract_text(temp_path)
    st.write(text if text.strip() else "*No text detected*")
    st.markdown("</div>", unsafe_allow_html=True)

    # TEXT MODERATION
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("📘 Text Moderation")

    text_res = {
        "toxic": toxicity_model(text)[0],
        "suicidal": suicide_model(text)[0]
    }

    st.write("**Toxicity:**", text_res["toxic"])
    st.progress(text_res["toxic"]["score"])

    st.write("**Self-harm Indicators:**", text_res["suicidal"])
    st.progress(text_res["suicidal"]["score"])
    st.markdown("</div>", unsafe_allow_html=True)

    # IMAGE MODERATION
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🖼 Image Moderation")

    img_res = image_moderation(temp_path)

    # Nudity
    if "nudity" in img_res:
        st.write("### Nudity / Sexual Content")
        for k, v in img_res["nudity"].items():
            st.write(f"{k}: {v:.2f}")
            st.progress(v)

    # Weapon
    weapon_prob = img_res.get("weapon", {}).get("prob", 0)
    if weapon_prob > 0:
        st.write("### Weapon:", weapon_prob)
        st.progress(weapon_prob)

    # Violence
    violence_prob = img_res.get("violence", {}).get("prob", 0)
    if violence_prob > 0:
        st.write("### Violence:", violence_prob)
        st.progress(violence_prob)

    # Gore
    gore_prob = img_res.get("gore", {}).get("prob", 0)
    if gore_prob > 0:
        st.write("### Gore:", gore_prob)
        st.progress(gore_prob)

    # Offensive symbols
    offensive_prob = img_res.get("offensive", {}).get("prob", 0)
    if offensive_prob > 0:
        st.write("### Offensive Symbols:", offensive_prob)
        st.progress(offensive_prob)

    st.markdown("</div>", unsafe_allow_html=True)

    # FINAL RESULT
    final, reasons = fuse(text_res, img_res)

    st.markdown("---")
    st.subheader("🧾 Final Verdict")

    if final == "BAD":
        st.markdown("<div class='result-bad'>🚨 BAD</div>", unsafe_allow_html=True)
        for r in reasons:
            st.write("• " + r)
    else:
        st.markdown("<div class='result-okay'>✅ OKAY</div>", unsafe_allow_html=True)
        st.write("Content is safe.")

    st.markdown("---")
