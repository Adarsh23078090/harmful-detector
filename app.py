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
# OCR.Space API (No tesseract needed)
# ---------------------------------------------------
OCR_API_KEY = "helloworld"

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
# HuggingFace Models (fixed dtype, correct model)
# ---------------------------------------------------
toxicity_model = pipeline(
    "text-classification",
    model="unitary/toxic-bert",
    device=-1,
    dtype="float32"
)

suicide_model = pipeline(
    "text-classification",
    model="michellejieli/self-harm",   # REAL suicide model
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
# Decision Fusion (fixed for correctness)
# ---------------------------------------------------
def fuse(text_res, img_res):
    reasons = []

    # TEXT — Suicide model (fixed)
    if text_res["suicidal"]["label"] in ["self-harm", "suicidal"] and text_res["suicidal"]["score"] > 0.7:
        reasons.append("Self-harm or suicidal intent detected")

    # TEXT — Toxic model (fixed)
    if text_res["toxic"]["label"].lower() == "toxic" and text_res["toxic"]["score"] > 0.8:
        reasons.append("Toxic or abusive language detected")

    # IMAGE — Extract scores
    nudity = img_res.get("nudity", {})
    weapon = img_res.get("weapon", {})
    violence = img_res.get("violence", {})
    gore = img_res.get("gore", {})
    offensive = img_res.get("offensive", {})

    # Thresholds tuned to avoid false positives
    if nudity.get("raw", 0) > 0.5:
        reasons.append("Nudity detected")
    if nudity.get("sexual_activity", 0) > 0.5:
        reasons.append("Sexual activity detected")
    if nudity.get("sexual_display", 0) > 0.5:
        reasons.append("Sexual display detected")

    if weapon.get("prob", 0) > 0.6:
        reasons.append("Weapon detected")
    if violence.get("prob", 0) > 0.6:
        reasons.append("Violence detected")
    if gore.get("prob", 0) > 0.5:
        reasons.append("Gore detected")
    if offensive.get("prob", 0) > 0.6:
        reasons.append("Offensive or hate symbols detected")

    return ("OKAY" if not reasons else "BAD"), reasons


# ---------------------------------------------------
# Safe Image Save
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

    temp_path = save_uploaded_image(uploaded_file)
    img = Image.open(temp_path)
    st.image(img, caption="Uploaded Image", width=350)

    # ------------------ OCR ------------------
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🔍 OCR — Extracted Text")

    text = extract_text(temp_path)
    st.write(text if text.strip() else "*No text detected*")
    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ TEXT MODERATION ------------------
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("📘 Text Moderation")

    # If blank text, do NOT classify
    if text.strip() == "":
        text_res = {
            "toxic": {"label": "neutral", "score": 0.0},
            "suicidal": {"label": "neutral", "score": 0.0}
        }
    else:
        text_res = {
            "toxic": toxicity_model(text)[0],
            "suicidal": suicide_model(text)[0]
        }

    st.write("**Toxicity:**", text_res["toxic"])
    st.progress(text_res["toxic"]["score"])

    st.write("**Self-harm Indicators:**", text_res["suicidal"])
    st.progress(text_res["suicidal"]["score"])
    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ IMAGE MODERATION ------------------
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🖼 Image Moderation")

    img_res = image_moderation(temp_path)

    # Nudity
    if "nudity" in img_res:
        st.write("### Nudity & Sexual Content")
        for k, v in img_res["nudity"].items():
            st.write(f"{k}: {v:.2f}")
            st.progress(v)

    # Weapon
    if "weapon" in img_res:
        prob = img_res["weapon"]["prob"]
        st.write("### Weapon:", prob)
        st.progress(prob)

    # Violence
    if "violence" in img_res:
        prob = img_res["violence"]["prob"]
        st.write("### Violence:", prob)
        st.progress(prob)

    # Gore
    if "gore" in img_res:
        prob = img_res["gore"]["prob"]
        st.write("### Gore:", prob)
        st.progress(prob)

    # Offensive
    if "offensive" in img_res:
        prob = img_res["offensive"]["prob"]
        st.write("### Hate / Offensive Symbols:", prob)
        st.progress(prob)

    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ FINAL RESULT ------------------
    final, reasons = fuse(text_res, img_res)

    st.markdown("---")
    st.subheader("🧾 Final Verdict")

    if final == "BAD":
        st.markdown("<div class='result-bad'>🚨 BAD</div>", unsafe_allow_html=True)
        for r in reasons:
            st.write("•", r)
    else:
        st.markdown("<div class='result-okay'>✅ OKAY</div>", unsafe_allow_html=True)
        st.write("Content appears safe.")

    st.markdown("---")
