"""AI Home Interior Designer — starter scaffold (free path: text-to-image).

You describe the room + pick a style -> the app asks Hugging Face for a
fresh AI-generated design image. This is YOUR starting point: extend it
with style presets, a gallery, prompt history, or (later, paid) photo
restyling via image-to-image.

Free-path facts (verified 2026-10-11):
- HF Inference Providers gives free accounts $0.10/month credit
  (subject to change) — enough to build and test.
- Text-to-image is covered; image-to-image (photo restyling) is not.
- Call it with InferenceClient(provider="hf-inference", ...).
"""
import os

import streamlit as st
from huggingface_hub import InferenceClient

st.set_page_config(page_title="AI Home Interior Designer", layout="centered")
st.title("🏠 AI Home Interior Designer")
st.caption("Starter scaffold — ₦0 text-to-image path. Your build, your code.")

HF_TOKEN = st.secrets.get("HF_TOKEN", os.environ.get("HF_TOKEN"))

STYLES = [
    "Modern minimalist",
    "Scandinavian",
    "Contemporary Nigerian",
    "Rustic farmhouse",
    "Luxury hotel",
    "Japandi",
]

room = st.text_area(
    "Describe your room",
    placeholder="e.g. A small bedroom, 3m by 4m, one window on the left, white walls...",
)
style = st.selectbox("Pick a style", STYLES)

# Fast text-to-image model that works on the free tier.
MODEL = "black-forest-labs/FLUX.1-schnell"

if st.button("Generate design", type="primary"):
    if not HF_TOKEN:
        st.error("No Hugging Face token found. Follow SETUP.md step 2, then come back.")
        st.stop()
    if not room.strip():
        st.warning("Describe your room first — the AI needs something to work with.")
        st.stop()

    prompt = f"Photorealistic interior design photo, {style.lower()} style: {room.strip()}"

    with st.spinner("Asking the AI for your design..."):
        try:
            client = InferenceClient(provider="hf-inference", api_key=HF_TOKEN)
            image = client.text_to_image(prompt, model=MODEL)  # returns a PIL Image
        except Exception as e:  # e.g. credit exhausted or bad token
            st.error(f"Generation failed: {e}")
            st.stop()

    st.image(image, caption=f"{style} — generated from your description")
    st.success("Done. This is your scaffold — now make it yours.")
