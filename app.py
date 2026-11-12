"""AI Home Interior Designer — starter scaffold (free path: text-to-image).

You describe the room + pick a style -> the app asks a free image
service for a fresh AI-generated design image. This is YOUR starting
point: extend it with style presets, a gallery, a download button,
or saved designs.

History (kept honest, for the project README):
- v1 used Hugging Face Inference Providers (FLUX.1-schnell). HF first
  retired that model on hf-inference ("410 Gone"), and on 2026-10-07
  removed free accounts' included monthly inference credit, so free
  calls to the remaining models now fail with "402 Payment Required".
- v2 therefore draws with Pollinations (image.pollinations.ai):
  free, no account, no token, no card. Everything else is unchanged.
- v5 adds a built-in Nigerian instruction (on by default): every
  design is guided toward a real Nigerian home — warm climate,
  local materials and fabrics — so the app solves a Nigerian
  problem without the user typing it every time.
"""
import random
import urllib.parse

import requests
import streamlit as st

st.set_page_config(page_title="AI Home Interior Designer", layout="centered")
st.title("🏠 AI Home Interior Designer")
st.caption("Starter scaffold — ₦0 text-to-image path. Your build, your code.")

if "saved" not in st.session_state:
    st.session_state.saved = []

# Built-in Nigerian instruction (v5): the system prompt baked into
# every generation. It steers the image toward a Nigerian home —
# tropical climate, local materials, local fabrics — and away from
# cold-climate features (fireplaces, radiators, heavy carpets).
NIGERIAN_GUIDE = (
    "Nigerian home in a warm tropical climate: warm earthy tones, "
    "local hardwood furniture, Ankara or Aso-Oke fabric accents, "
    "ceiling fan, large windows with sheer curtains for airflow and "
    "daylight, tiled floors, practical for heat and humidity, "
    "no fireplace, no radiator, no heavy carpet"
)

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
nigerian = st.checkbox("Nigerian home touches", value=True)

if st.button("Generate design", type="primary"):
    if not room.strip():
        st.warning("Describe your room first — the AI needs something to work with.")
        st.stop()
    prompt = f"Photorealistic interior design photo, sharp focus, high detail, well lit, {style.lower()} style: {room.strip()}"
    if nigerian:
        prompt = f"{prompt}. {NIGERIAN_GUIDE}"

    # Pollinations draws from a URL: the prompt goes in the address,
    # URL-encoded. A random seed means each tap draws a fresh design
    # instead of returning a cached copy of the same prompt.
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1, 999_999)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1280&height=960&seed={seed}&nologo=true"
    )

    with st.spinner("Asking the AI for your design..."):
        try:
            response = requests.get(url, timeout=180)
            response.raise_for_status()
            image_bytes = response.content
        except Exception as e:  # e.g. service busy or no network
            st.error(f"Generation failed: {e}")
            st.stop()

    st.image(image_bytes, caption=f"{style} — generated from your description")
    st.success("Done. This is your scaffold — now make it yours.")
    st.download_button(
        "Download this design",
        data=image_bytes,
        file_name="my-design.png",
        mime="image/png",
    )

    st.session_state.saved.append(
        {"room": room.strip(), "style": style, "image": image_bytes}
    )

st.divider()
st.subheader("My saved designs")

if not st.session_state.saved:
    st.write("Nothing saved yet — generate a design and it will appear here.")
else:
    for saved in reversed(st.session_state.saved):
        st.image(saved["image"], caption=f"{saved['style']}: {saved['room']}")
    if st.button("Clear saved designs"):
        st.session_state.saved = []
        st.rerun()
