import streamlit as st
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pdf2image
import io
import cv2
import numpy as np
import re
import os
# Set Tesseract path on Windows; on other OS, ensure tesseract is in PATH.
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# For non-Windows users: Install Tesseract and ensure it's in your system PATH.
# cspell:ignore Selectbox selectbox deskew denoise Denoise Denoising Deskew fromarray Tesseract confs textlens onmouseover onmouseout

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TextLens OCR",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:        #0f0f0f;
    --surface:   #181818;
    --surface2:  #222222;
    --border:    #2e2e2e;
    --accent:    #e8d5b0;
    --accent2:   #c9a96e;
    --text:      #f0ece4;
    --muted:     #888880;
    --success:   #6fcf97;
    --warn:      #f2994a;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}

[data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
}

[data-testid="stHeader"] { background: transparent !important; }

/* hide default streamlit chrome */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* ── Hero header ── */
.hero {
    padding: 3rem 0 1.5rem;
    text-align: center;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(2.4rem, 5vw, 4rem);
    letter-spacing: -0.02em;
    color: var(--accent);
    margin: 0;
    line-height: 1.1;
}
.hero-title em {
    font-style: italic;
    color: var(--accent2);
}
.hero-sub {
    font-size: 0.95rem;
    color: var(--muted);
    margin-top: 0.5rem;
    font-weight: 300;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent2) !important;
}
[data-testid="stFileUploader"] label {
    color: var(--muted) !important;
    font-size: 0.85rem !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--accent) !important;
    color: #0f0f0f !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 2rem !important;
    letter-spacing: 0.02em !important;
    transition: background 0.15s, transform 0.1s !important;
    width: 100%;
}
.stButton > button:hover {
    background: var(--accent2) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Toggle (radio as pills) ── */
[data-testid="stRadio"] > div {
    background: var(--surface2);
    border-radius: 10px;
    padding: 4px;
    display: flex;
    gap: 4px;
    border: 1px solid var(--border);
}
[data-testid="stRadio"] label {
    flex: 1;
    text-align: center;
    padding: 6px 14px;
    border-radius: 7px;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    color: var(--muted) !important;
    transition: all 0.15s;
}
[data-testid="stRadio"] [data-checked="true"] {
    background: var(--accent);
    color: #0f0f0f !important;
}

/* ── Text output area ── */
.output-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.83rem;
    line-height: 1.75;
    color: var(--text);
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 520px;
    overflow-y: auto;
}
.output-box::-webkit-scrollbar { width: 6px; }
.output-box::-webkit-scrollbar-track { background: var(--surface2); border-radius: 3px; }
.output-box::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── Stats bar ── */
.stats-bar {
    display: flex;
    gap: 1.5rem;
    padding: 0.8rem 1.2rem;
    background: var(--surface2);
    border-radius: 10px;
    border: 1px solid var(--border);
    margin-bottom: 1rem;
}
.stat-item { display: flex; flex-direction: column; }
.stat-val {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: var(--accent);
    line-height: 1;
}
.stat-lbl {
    font-size: 0.7rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 2px;
}

/* ── Section labels ── */
.section-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin-bottom: 0.5rem;
    font-weight: 500;
}

/* ── Page chip ── */
.page-chip {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: var(--muted);
    margin: 0.2rem;
    cursor: pointer;
}
.page-chip.active {
    background: var(--accent);
    color: #0f0f0f;
    border-color: var(--accent);
    font-weight: 600;
}

/* ── Confidence badge ── */
.conf-high { color: var(--success); font-size: 0.75rem; }
.conf-low  { color: var(--warn);    font-size: 0.75rem; }

/* ── Divider ── */
.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.5rem 0;
}

/* ── Select / text area overrides ── */
.stSelectbox > div > div {
    background: var(--surface2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
}
textarea, [data-testid="stTextArea"] textarea {
    background: var(--surface) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.83rem !important;
    border-radius: 12px !important;
}

/* expander */
[data-testid="stExpander"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary {
    color: var(--muted) !important;
    font-size: 0.82rem !important;
}

/* progress */
[data-testid="stProgress"] > div > div {
    background: var(--accent2) !important;
    border-radius: 4px !important;
}

/* columns gap */
[data-testid="column"] { padding: 0 0.6rem !important; }

/* alert */
.stAlert {
    background: var(--surface2) !important;
    border-color: var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def preprocess_image(pil_img: Image.Image) -> Image.Image:
    """Apple-like preprocessing: deskew, denoise, sharpen, contrast boost."""
    img = pil_img.convert("RGB")
    arr = np.array(img)

    # Denoise
    arr = cv2.fastNlMeansDenoisingColored(arr, None, 7, 7, 7, 21)

    # Convert to grayscale for deskew
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Deskew
    coords = np.column_stack(np.where(gray < 200))
    if len(coords) > 100:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) < 15:
            h, w = gray.shape
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            arr = cv2.warpAffine(arr, M, (w, h),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)

    result = Image.fromarray(arr)

    # Sharpen + contrast
    result = result.filter(ImageFilter.SHARPEN)
    result = ImageEnhance.Contrast(result).enhance(1.4)
    result = ImageEnhance.Sharpness(result).enhance(1.6)

    return result


def run_ocr(pil_img: Image.Image, lang: str) -> tuple[str, float]:
    """Run Tesseract, return (text, confidence 0-100)."""
    processed = preprocess_image(pil_img)
    data = pytesseract.image_to_data(
        processed, lang=lang,
        output_type=pytesseract.Output.DICT
    )
    confs = [int(c) for c in data["conf"] if str(c).lstrip("-").isdigit() and int(c) >= 0]
    avg_conf = round(sum(confs) / len(confs), 1) if confs else 0.0
    text = pytesseract.image_to_string(processed, lang=lang)
    return text.strip(), avg_conf


def text_to_markdown(text: str) -> str:
    """Heuristic: short ALL-CAPS or short lines → headings; lists preserved."""
    lines = text.splitlines()
    md_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            md_lines.append("")
            continue
        # ALL CAPS short line → H2
        if stripped.isupper() and len(stripped) < 60 and len(stripped) > 3:
            md_lines.append(f"## {stripped.title()}")
        # Short line ending with colon → H3
        elif stripped.endswith(":") and len(stripped) < 50:
            md_lines.append(f"### {stripped}")
        # Bullet heuristic
        elif re.match(r"^[-•*·]\s", stripped):
            md_lines.append(f"- {stripped[2:].strip()}")
        elif re.match(r"^\d+[.)]\s", stripped):
            md_lines.append(stripped)
        else:
            md_lines.append(stripped)
    return "\n".join(md_lines)


def get_available_langs() -> list[str]:
    try:
        raw = pytesseract.get_languages(config="")
        return [l for l in raw if l != "osd"]
    except Exception:
        return ["eng"]


def load_pdf_pages(file_bytes: bytes) -> list[Image.Image]:
    return pdf2image.convert_from_bytes(file_bytes, dpi=200)


# ── Session state ─────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = []       # list of {page, text, conf}
if "active_page" not in st.session_state:
    st.session_state.active_page = 0
if "output_fmt" not in st.session_state:
    st.session_state.output_fmt = "Plain Text"

# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
  <p class="hero-title">Text<em>Lens</em></p>
  <p class="hero-sub">OCR · Images &amp; PDFs · Offline &amp; Free</p>
</div>
""", unsafe_allow_html=True)

# ── Controls row ──────────────────────────────────────────────────────────────
col_upload, col_opts = st.columns([2, 1], gap="large")

with col_upload:
    st.markdown('<div class="section-label">Upload file</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drop an image or PDF here",
        type=["png", "jpg", "jpeg", "webp", "bmp", "tiff", "pdf"],
        label_visibility="collapsed"
    )

with col_opts:
    st.markdown('<div class="section-label">Language</div>', unsafe_allow_html=True)
    langs = get_available_langs()
    lang_labels = {
        "eng": "English", "fil": "Filipino", "jpn": "Japanese",
        "chi_sim": "Chinese (Simplified)", "chi_tra": "Chinese (Traditional)",
        "fra": "French", "deu": "German", "spa": "Spanish",
        "ita": "Italian", "por": "Portuguese", "ara": "Arabic",
    }
    display_langs = [lang_labels.get(l, l) for l in langs]
    lang_sel_display = st.selectbox("Language", display_langs, label_visibility="collapsed")
    lang_sel = langs[display_langs.index(lang_sel_display)]

    st.markdown('<div class="section-label" style="margin-top:1rem">Output format</div>', unsafe_allow_html=True)
    fmt = st.radio("Format", ["Plain Text", "Markdown"], horizontal=True,
                   label_visibility="collapsed",
                   index=["Plain Text", "Markdown"].index(st.session_state.output_fmt))
    st.session_state.output_fmt = fmt

st.markdown('<hr class="divider"/>', unsafe_allow_html=True)

# ── Extract button + processing ───────────────────────────────────────────────
if uploaded:
    left, mid, right = st.columns([1, 1, 1])
    with mid:
        extract_btn = st.button("⟳  Extract Text", use_container_width=True)

    if extract_btn:
        st.session_state.results = []
        st.session_state.active_page = 0
        is_pdf = uploaded.name.lower().endswith(".pdf")
        file_bytes = uploaded.read()

        with st.spinner(""):
            progress = st.progress(0, text="Preparing…")

            if is_pdf:
                pages = load_pdf_pages(file_bytes)
                total = len(pages)
                for i, page_img in enumerate(pages):
                    progress.progress((i + 1) / total,
                                      text=f"Processing page {i+1} of {total}…")
                    text, conf = run_ocr(page_img, lang_sel)
                    st.session_state.results.append({
                        "page": i + 1,
                        "image": page_img,
                        "text": text,
                        "conf": conf,
                    })
            else:
                progress.progress(0.3, text="Preprocessing image…")
                img = Image.open(io.BytesIO(file_bytes))
                progress.progress(0.6, text="Running OCR…")
                text, conf = run_ocr(img, lang_sel)
                progress.progress(1.0, text="Done!")
                st.session_state.results.append({
                    "page": 1,
                    "image": img,
                    "text": text,
                    "conf": conf,
                })
            progress.empty()

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.results:
    results = st.session_state.results
    active = st.session_state.active_page
    current = results[active]

    # Stats bar
    total_words = sum(len(r["text"].split()) for r in results)
    total_chars = sum(len(r["text"]) for r in results)
    avg_conf    = round(sum(r["conf"] for r in results) / len(results), 1)
    conf_color  = "conf-high" if avg_conf >= 70 else "conf-low"

    st.markdown(f"""
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-val">{len(results)}</span>
        <span class="stat-lbl">{"Pages" if len(results) > 1 else "Page"}</span>
      </div>
      <div class="stat-item">
        <span class="stat-val">{total_words:,}</span>
        <span class="stat-lbl">Words</span>
      </div>
      <div class="stat-item">
        <span class="stat-val">{total_chars:,}</span>
        <span class="stat-lbl">Characters</span>
      </div>
      <div class="stat-item">
        <span class="stat-val {conf_color}">{avg_conf}%</span>
        <span class="stat-lbl">Confidence</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Page selector (if multi-page)
    if len(results) > 1:
        st.markdown('<div class="section-label">Pages</div>', unsafe_allow_html=True)
        page_cols = st.columns(min(len(results), 10))
        for i, r in enumerate(results):
            with page_cols[i % 10]:
                if st.button(f"Pg {r['page']}", key=f"pg_{i}",
                             use_container_width=True):
                    st.session_state.active_page = i
                    st.rerun()
        st.markdown('<hr class="divider"/>', unsafe_allow_html=True)

    # Two-column layout: preview | text
    col_img, col_text = st.columns([1, 1], gap="large")

    with col_img:
        st.markdown('<div class="section-label">Preview</div>', unsafe_allow_html=True)
        st.image(current["image"], use_container_width=True)

    with col_text:
        st.markdown('<div class="section-label">Extracted Text</div>', unsafe_allow_html=True)
        display_text = (text_to_markdown(current["text"])
                        if st.session_state.output_fmt == "Markdown"
                        else current["text"])

        no_text_html = '<span style="color:var(--muted)">No text detected on this page.</span>'
        output_content = display_text if display_text else no_text_html
        st.markdown(f'<div class="output-box">{output_content}</div>',
                    unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Download / copy
        dl_col, copy_col = st.columns(2)

        ext = "md" if st.session_state.output_fmt == "Markdown" else "txt"
        all_text = "\n\n---\n\n".join(
            f"[Page {r['page']}]\n{text_to_markdown(r['text']) if st.session_state.output_fmt == 'Markdown' else r['text']}"
            for r in results
        )

        with dl_col:
            st.download_button(
                label=f"↓  Download .{ext}",
                data=all_text,
                file_name=f"textlens_output.{ext}",
                mime="text/plain",
                use_container_width=True,
            )

        with copy_col:
            st.download_button(
                label="⎘  Copy as File",
                data=display_text,
                file_name="copied_text.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # Low confidence warning
        if current["conf"] < 60:
            st.markdown(f"""
            <div style="margin-top:1rem; padding:0.7rem 1rem; background:var(--surface2);
                        border-left:3px solid var(--warn); border-radius:8px;
                        font-size:0.8rem; color:var(--warn);">
            ⚠ Low confidence ({current['conf']}%) — image may be blurry, skewed, or low resolution.
            Try a clearer scan for better results.
            </div>
            """, unsafe_allow_html=True)

else:
    if not uploaded:
        st.markdown("""
        <div style="text-align:center; padding:3rem 0; color:var(--muted);">
          <div style="font-size:3rem; margin-bottom:1rem;">🔍</div>
          <div style="font-size:0.9rem; letter-spacing:0.05em; text-transform:uppercase;">
            Upload an image or PDF to begin
          </div>
          <div style="font-size:0.78rem; margin-top:0.5rem; color:#555">
            JPG · PNG · WEBP · BMP · TIFF · PDF
          </div>
        </div>
        """, unsafe_allow_html=True)
