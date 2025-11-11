import streamlit as st
import cv2
import numpy as np
from transformers import pipeline
from PIL import Image
import requests
import os

# --------------------------------
# Streamlit Page Config
# --------------------------------
st.set_page_config(
    page_title="Harmful Content Detector",
    page_icon="🚨",
    layout="centered",
)

# --------------------------------
# Custom CSS
# --------------------------------
st.markdown("""
<style>

body {
    background-color: #f7f7f7;
}

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

# --------------------------------
# OCR using OCR.Space API
# --------------------------------
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

# --------------------------------
# HuggingFace Models
# --------------------------------
toxicity_model = pipeline(
    "text-classification",
    model="unitary/toxic-bert",
    device=-1,
    torch_dtype="float32"
)

suicide_model = pipeline(
    "text-classification",
    model="facebook/roberta-hate-speech-dynabench-r4-target",
    device=-1,
    torch_dtype="float32"
)

# --------------------------------
# Sightengine API
# --------------------------------
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

# --------------------------------
# Decision Fusion
# ------------------------------
