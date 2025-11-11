import streamlit as st
import requests
from transformers import pipeline
from PIL import Image

# -----------------------------
# Streamlit Page Config & CSS
# -----------------------------
st.set_page_config(page_title="Harmful Content Detector", page_icon="🚨", layout="centered")
st.markdown("""
<style>
.result-bad { padding:12px; background:#ffcccc; border-left:5px solid #d10000; border-radius:8px; font-size:18px; }
.result-okay { padding:12px; background:#ccffcc; border-left:5px solid #008000; border-radius:8px; font-size:18px; }
.section-card { background:#fff; padding:16px; border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,.08); margin:16px 0; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# OCR via OCR.Space (no binary)
# -----------------------------
OCR_API_KEY = "helloworld"  # free demo key
def extract_text(image_path: str) -> str:
    url = "https://api.ocr.space/parse/image"
    with open(image_path, "rb") as f:
        files = {"file": f}
        data = {"apikey": OCR_API_KEY, "language": "eng"}
        try:
            r = requests.post(url, files=files, data=data, timeout=30)
            r.raise_for_status()
            j = r.json()
            return j.get("ParsedResults", [{}])[0].get("ParsedText", "") or ""
        except Exception:
            return ""

# -----------------------------
# Text models (CPU)
# -----------------------------
toxicity_model = pipeline("text-classification", model="unitary/toxic-bert", device=-1)
# Use a tiny, public self-harm classifier that works on Streamlit Cloud
suicide_model = pipeline("text-classification", model="mstz/self-harm", device=-1)

# -----------------------------
# Sightengine (read from secrets if available)
# -----------------------------
API_USER = st.secrets.get("SIGHTENGINE_USER", "").strip() or "PUT_USER_ID_HERE"
API_SECRET = st.secrets.get("SIGHTENGINE_SECRET", "").strip() or "PUT_SECRET_HERE"

def image_moderation(img_path: str) -> dict:
    url = "https://api.sightengine.com/1.0/check.json"
    with open(img_path, "rb") as f:
        files = {"media": f}
        params = {
            "models": "nudity,wad,offensive,faces,gore,weapon,violence",
            "api_user": API_USER,
            "api_secret": API_SECRET,
        }
        try:
            res = requests.post(url, data=params, files=files, timeout=30)
            res.raise_for_status()
            return res.json()
        except Exception:
            return {}

# -----------------------------
# Fusion logic (conservative)
# -----------------------------
def fuse(text_res: dict, img_res: dict):
    reasons = []

    # Text — self-harm (labels: "self-harm", "not-self-harm")
    if text_res["suicidal"]["label"].lower() == "self-harm" and text_res["suicidal"]["score"] > 0.70:
        reasons.append("Self-harm / suicidal intent detected.")

    # Text — toxicity (tight threshold to reduce false positives)
    if text_res["toxic"]["label"].lower() == "toxic" and text_res["toxic"]["score"] > 0.80:
        reasons.append("Toxic or abusive language detected.")

    nudity = img_res.get("nudity", {}) or {}
    weapon = img_res.get("weapon", {}) or {}
    violence = img_res.get("violence", {}) or {}
    gore = img_res.get("gore", {}) or {}
    offensive = img_res.get("offensive", {}) or {}

    # Image thresholds tuned to avoid false alarms
    if nudity.get("raw", 0) > 0.50: reasons.append("Nudity detected.")
    if nudity.get("sexual_activity", 0) > 0.50: reasons.append("Sexual activity detected.")
    if nudity.get("sexual_display", 0) > 0.50: reasons.append("Sexual display detected.")

    if weapon.get("prob", 0) > 0.60: reasons.append("Weapon detected.")
    if violence.get("prob", 0) > 0.60: reasons.append("Violence detected.")
    if gore.get("prob", 0) > 0.50: reasons.append("Gore detected.")
    if offensive.get("prob", 0) > 0.60: reasons.append("Offensive / hate symbol detected.")

    return ("OKAY" if not reasons else "BAD"), reasons

# -----------------------------
# Safe save (avoid JPEG RGBA)
# -----------------------------
def save_uploaded_image(uploaded_file) -> str:
    img = Image.open(uploaded_file)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    temp_path = "temp.png"
    img.save(temp_path, format="PNG")
    return temp_path

# -----------------------------
# UI
# -----------------------------
st.title("🚨 Harmful Content Detection System")
st.write("Upload → OCR → Text Moderation → Image Moderation → Verdict")

if not API_USER or not API_SECRET or "PUT_" in (API_USER + API_SECRET):
    st.warning("🔐 Add your Sightengine credentials in **Secrets**: `SIGHTENGINE_USER`, `SIGHTENGINE_SECRET`.", icon="⚠️")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # Save preview
    temp_path = save_uploaded_image(uploaded_file)
    st.image(temp_path, caption="Uploaded Image", width=350)

    # 1) OCR
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🔍 OCR — Extracted Text")
    text = extract_text(temp_path)
    st.write(text if text.strip() else "_No text detected_")
    st.markdown("</div>", unsafe_allow_html=True)

    # 2) Text moderation
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("📘 Text Moderation")

    if text.strip():
        tox = toxicity_model(text)[0]
        sui = suicide_model(text)[0]
    else:
        tox = {"label": "neutral", "score": 0.0}
        sui = {"label": "not-self-harm", "score": 0.0}

    text_res = {"toxic": tox, "suicidal": sui}

    st.write("**Toxicity**:", tox)
    st.progress(min(1.0, float(tox.get("score", 0.0))))
    st.write("**Self-harm**:", sui)
    st.progress(min(1.0, float(sui.get("score", 0.0))))
    st.markdown("</div>", unsafe_allow_html=True)

    # 3) Image moderation
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🖼 Image Moderation")
    img_res = image_moderation(temp_path)

    # Nudity (dictionary of scores)
    if isinstance(img_res.get("nudity"), dict):
        st.write("### Nudity / Sexual Content")
        for k, v in img_res["nudity"].items():
            try:
                val = float(v)
            except Exception:
                continue
            st.write(f"{k}: {val:.2f}")
            st.progress(min(1.0, val))

    # Single-prob fields (safe .get chain)
    for name in ["weapon", "violence", "gore", "offensive"]:
        prob = float(img_res.get(name, {}).get("prob", 0.0) or 0.0)
        if prob > 0:
            label = name.capitalize() if name != "offensive" else "Offensive Symbols"
            st.write(f"### {label}: {prob:.2f}")
            st.progress(min(1.0, prob))

    st.markdown("</div>", unsafe_allow_html=True)

    # 4) Final verdict
    final, reasons = fuse(text_res, img_res)
    st.markdown("---")
    st.subheader("🧾 Final Verdict")

    if final == "BAD":
        st.markdown("<div class='result-bad'>🚨 BAD</div>", unsafe_allow_html=True)
        if reasons:
            st.write("**Reasons:**")
            for r in reasons:
                st.write("•", r)
    else:
        st.markdown("<div class='result-okay'>✅ OKAY</div>", unsafe_allow_html=True)
        st.write("No harmful content detected.")
    st.markdown("---")
