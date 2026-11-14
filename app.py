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
- v6 adds a persistent catalog on Cloudinary (free plan, no card):
  "Save to my catalog" uploads a design with the unsigned preset
  "home-designs" and the tag "home-designer"; the catalog below
  reads the public tag list, so saved designs survive closing and
  reopening the app. No API key or secret lives in this file.
"""
import base64
import random
import urllib.parse

import requests
import streamlit as st

st.set_page_config(page_title="AI Home Interior Designer", layout="centered")
st.title("🏠 AI Home Interior Designer")
st.caption("Starter scaffold — ₦0 text-to-image path. Your build, your code.")

# Cloudinary catalog settings (public values only — no secrets here).
CLOUD_NAME = "cdfmsqsp"
UPLOAD_PRESET = "home-designs"
CATALOG_TAG = "home-designer"
CLOUDINARY_UPLOAD_URL = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload"
CATALOG_LIST_URL = (
    f"https://res.cloudinary.com/{CLOUD_NAME}/image/list/{CATALOG_TAG}.json"
)


def _mime_for(image_bytes):
    """Guess the image type from the first bytes, for the upload."""
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return "image/jpeg"


def upload_to_catalog(image_bytes, style, room):
    """Upload one design to Cloudinary (unsigned preset) and return its URL."""
    mime = _mime_for(image_bytes)
    data_uri = (
        "data:" + mime + ";base64," + base64.b64encode(image_bytes).decode("ascii")
    )
    response = requests.post(
        CLOUDINARY_UPLOAD_URL,
        data={
            "file": data_uri,
            "upload_preset": UPLOAD_PRESET,
            "tags": CATALOG_TAG,
            "context": f"caption={style}: {room}",
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["secure_url"]


def fetch_catalog():
    """Read the public Cloudinary tag list. Returns a list of resources."""
    response = requests.get(CATALOG_LIST_URL, timeout=15)
    if response.status_code == 404:
        return []  # tag has no images yet
    response.raise_for_status()
    resources = response.json().get("resources", [])
    # Newest first, so the latest design is at the top.
    resources.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return resources


if "saved" not in st.session_state:
    st.session_state.saved = []
if "latest" not in st.session_state:
    st.session_state.latest = None

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

    st.session_state.latest = {
        "room": room.strip(),
        "style": style,
        "image": image_bytes,
        "catalog_url": None,
    }
    st.session_state.saved.append(
        {"room": room.strip(), "style": style, "image": image_bytes}
    )

latest = st.session_state.latest
if latest is not None:
    st.image(latest["image"], caption=f"{latest['style']} — generated from your description")
    st.success("Done. This is your scaffold — now make it yours.")
    st.download_button(
        "Download this design",
        data=latest["image"],
        file_name="my-design.png",
        mime="image/png",
    )
    if latest.get("catalog_url"):
        st.success(f"Saved to your catalog: {latest['catalog_url']}")
    elif st.button("Save to my catalog"):
        with st.spinner("Saving to your catalog..."):
            try:
                url = upload_to_catalog(
                    latest["image"], latest["style"], latest["room"]
                )
            except Exception as e:
                st.error(f"Could not save to catalog: {e}")
            else:
                latest["catalog_url"] = url
                st.success(f"Saved to your catalog: {url}")
                st.rerun()

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

st.divider()
st.subheader("My catalog (saved on Cloudinary)")
st.caption("Designs you saved stay here even after closing and reopening the app.")

try:
    catalog = fetch_catalog()
except Exception:
    st.write("Catalog could not load right now — check your connection and try again.")
else:
    if not catalog:
        st.write("Nothing in your catalog yet — generate a design and tap “Save to my catalog”.")
    else:
        st.write(f"{len(catalog)} design(s) in your catalog.")
        for item in catalog:
            caption = item.get("context", {}).get("custom", {}).get("caption") or item.get(
                "public_id", ""
            )
            st.image(item["secure_url"], caption=caption)
