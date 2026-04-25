"""
NeuroForensic AI — Multi-Modal Death Investigation Assistant
============================================================
Author: Aman
Track: Build with Healthcare
AI Provider: Google Gemini 1.5 Flash (vision + text)

Modules:
  1. Chest X-ray       — lung opacity, fluid, structural anomaly
  2. Brain MRI / CT    — tumor, lesion, mass, midline shift
  3. Full Body CT      — trauma, bleeding, fractures
  4. Toxicology Report — poisoning via NLP on lab report text
  5. External Trauma   — hanging, strangulation, blunt force (scene photo)
  6. Brain Pattern     — neurological trauma patterns (EEG-ImageNet grounded)

Grounded by: CLAUDE.md, agents/forensic_agent.md,
             agents/output_agent.md, agents/neuro_agent.md
"""

import streamlit as st
import requests as http
import base64
import json
import os
import time
import io
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image as PILImage

load_dotenv()

MODEL      = "gemini-2.0-flash"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent"
)

def _get_api_key() -> str | None:
    """Read Gemini API key: Streamlit secrets → env var → sidebar input."""
    for candidate in [
        lambda: st.secrets.get("GEMINI_API_KEY", ""),
        lambda: os.getenv("GEMINI_API_KEY", ""),
        lambda: st.session_state.get("gemini_api_key", ""),
    ]:
        try:
            key = (candidate() or "").strip()
            if key:
                return key
        except Exception:
            pass
    return None


def _verify_key(key: str) -> tuple[bool, str]:
    """Ping Gemini with a minimal request to validate the key."""
    try:
        r = http.post(
            GEMINI_URL,
            params={"key": key},
            json={"contents": [{"parts": [{"text": "Hi"}]}],
                  "generationConfig": {"maxOutputTokens": 5}},
            timeout=10,
        )
        if r.ok:
            return True, "Key verified."
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        msg = body.get("error", {}).get("message", r.text[:120])
        return False, msg
    except Exception as e:
        return False, str(e)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NeuroForensic AI",
    page_icon="🧠",
    layout="centered"
)

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_OUTPUT_TOKENS = 1024
VALID_SEVERITIES  = ["Normal", "Suspicious", "Critical"]
VALID_CONFIDENCES = ["Low", "Medium", "High"]

SEVERITY_COLORS = {
    "Normal":     {"bg": "#E1F5EE", "text": "#0F6E56", "label": "No Anomalies Detected"},
    "Suspicious": {"bg": "#FAEEDA", "text": "#633806", "label": "Review Recommended"},
    "Critical":   {"bg": "#FCEBEB", "text": "#791F1F", "label": "Urgent Review Required"},
}

# ── System prompts (from agents/forensic_agent.md) ────────────────────────────
BASE_RULES = (
    "Output ONLY valid JSON, no markdown. Describe only what is visually/textually "
    "observable. Never diagnose, name diseases, or state cause of death. "
    "Always recommend expert review."
)

SYSTEM_PROMPTS = {

    "Chest X-ray": f"""You are a forensic screening assistant analyzing a CHEST X-RAY image.
{BASE_RULES}
Look for: lung opacity, pleural fluid, structural asymmetry,
rib irregularities, mediastinal widening, unusual densities.

Return ONLY this JSON:
{{
  "module": "Chest X-ray",
  "anomalies_detected": true or false,
  "findings": ["observation 1", "observation 2"],
  "region": "Chest / Pulmonary",
  "severity": "Normal" or "Suspicious" or "Critical",
  "investigator_action": "one sentence",
  "confidence": "Low" or "Medium" or "High",
  "dataset_source": "NIH ChestX-ray14",
  "disclaimer": "AI screening only. All findings require expert forensic review."
}}""",

    "Brain MRI / CT": f"""You are a forensic screening assistant analyzing a BRAIN MRI or CT SCAN image.
{BASE_RULES}
Look for: abnormal masses, lesions, hemispheric asymmetry,
midline shift, density irregularities, structural disruption.

Return ONLY this JSON:
{{
  "module": "Brain MRI / CT",
  "anomalies_detected": true or false,
  "findings": ["observation 1", "observation 2"],
  "region": "Brain / Neurological",
  "severity": "Normal" or "Suspicious" or "Critical",
  "investigator_action": "one sentence",
  "confidence": "Low" or "Medium" or "High",
  "dataset_source": "BraTS 2023",
  "disclaimer": "AI screening only. All findings require expert forensic review."
}}""",

    "Full Body CT": f"""You are a forensic screening assistant analyzing a FULL BODY CT SCAN image.
{BASE_RULES}
Look for: internal bleeding indicators, organ density anomalies,
skeletal fractures, fluid in abnormal regions, soft tissue disruption.

Return ONLY this JSON:
{{
  "module": "Full Body CT",
  "anomalies_detected": true or false,
  "findings": ["observation 1", "observation 2"],
  "region": "Full Body / Trauma",
  "severity": "Normal" or "Suspicious" or "Critical",
  "investigator_action": "one sentence",
  "confidence": "Low" or "Medium" or "High",
  "dataset_source": "RSNA Hemorrhage Dataset",
  "disclaimer": "AI screening only. All findings require expert forensic review."
}}""",

    "Toxicology Report": f"""You are a forensic screening assistant analyzing a TOXICOLOGY LAB REPORT text.
{BASE_RULES}
Look for: substances above reference thresholds, multi-substance
flags, out-of-range chemical markers, abnormal compound levels.
Reference substances by lab notation only — not common names.

Return ONLY this JSON:
{{
  "module": "Toxicology Report",
  "anomalies_detected": true or false,
  "findings": ["observation 1", "observation 2"],
  "region": "Toxicology / Chemical",
  "severity": "Normal" or "Suspicious" or "Critical",
  "investigator_action": "one sentence",
  "confidence": "Low" or "Medium" or "High",
  "dataset_source": "MIMIC-IV Clinical Notes",
  "disclaimer": "AI screening only. All findings require expert forensic review."
}}""",

    "External Trauma Photo": f"""You are a forensic screening assistant analyzing a CRIME SCENE
or BODY PHOTOGRAPH for external trauma indicators.
Follow INTERPOL DVI (Disaster Victim Identification) protocol language.
{BASE_RULES}
Look for:
- Ligature marks: location, angle (horizontal vs angled), width, continuity
- Petechiae: presence in eyes or face
- Bruise patterns: shape, distribution, finger spacing, nail impressions
- Impact wounds: shape, edge character, single vs scattered distribution
- Positional indicators: lividity pattern consistency

Return ONLY this JSON:
{{
  "module": "External Trauma Photo",
  "anomalies_detected": true or false,
  "findings": ["observation 1", "observation 2"],
  "region": "External / Surface",
  "severity": "Normal" or "Suspicious" or "Critical",
  "investigator_action": "one sentence",
  "confidence": "Low" or "Medium" or "High",
  "dataset_source": "INTERPOL DVI Protocol",
  "disclaimer": "AI screening only. All findings require expert forensic review."
}}""",

    "Brain Pattern Analysis": f"""You are a forensic neuroscience screening assistant.
Analyze this BRAIN MRI or CT for neurological trauma patterns.

Scientific basis: EEG-ImageNet research demonstrates that brain
activity patterns in the visual cortex, hippocampus, and prefrontal
regions are consistent and decodable. Post-mortem neuroimaging
reveals structural residue of what the brain experienced before death.
{BASE_RULES}
Look specifically for:
- Visual cortex (occipital lobe) density or structural anomalies
- Hippocampal asymmetry or volume irregularity
- Prefrontal region density changes
- Watershed zone patterns (border-zone ischemia)
- Diffuse axonal injury indicators across white matter
- Deep brain hemorrhagic pattern distribution
- Brainstem compression or density anomalies

Return ONLY this JSON:
{{
  "module": "Brain Pattern Analysis",
  "anomalies_detected": true or false,
  "findings": ["observation 1", "observation 2"],
  "region": "Brain / Neurological Pattern",
  "severity": "Normal" or "Suspicious" or "Critical",
  "investigator_action": "one sentence",
  "confidence": "Low" or "Medium" or "High",
  "dataset_source": "BraTS 2023 + EEG-ImageNet",
  "disclaimer": "AI screening only. All findings require expert forensic review."
}}""",
}

# ── Module metadata ───────────────────────────────────────────────────────────
MODULE_META = {
    "Chest X-ray": {
        "icon": "🫁", "input_type": "image",
        "description": "Detects lung opacity, fluid, structural anomalies",
        "dataset": "NIH ChestX-ray14 — 112,000 images",
        "samples": {
            "Normal chest scan":     "samples/chest_normal.jpg",
            "Suspicious chest scan": "samples/chest_suspicious.jpg",
            "Critical chest scan":   "samples/chest_critical.jpg",
        }
    },
    "Brain MRI / CT": {
        "icon": "🧠", "input_type": "image",
        "description": "Detects tumors, lesions, mass, midline shift",
        "dataset": "BraTS 2023 — multi-modal brain MRI",
        "samples": {
            "Normal brain scan":     "samples/brain_normal.jpg",
            "Suspicious brain scan": "samples/brain_suspicious.jpg",
        }
    },
    "Full Body CT": {
        "icon": "🦴", "input_type": "image",
        "description": "Detects trauma, internal bleeding, fractures",
        "dataset": "RSNA Hemorrhage — 25,000 CT scans",
        "samples": {
            "Normal body CT":  "samples/body_normal.jpg",
            "Trauma body CT":  "samples/body_trauma.jpg",
        }
    },
    "Toxicology Report": {
        "icon": "🧪", "input_type": "text",
        "description": "Detects poisoning via lab report NLP analysis",
        "dataset": "MIMIC-IV Clinical Notes (PhysioNet)",
        "samples": {
            "Normal tox report":     "samples/tox_normal.txt",
            "Suspicious tox report": "samples/tox_suspicious.txt",
        }
    },
    "External Trauma Photo": {
        "icon": "📷", "input_type": "image",
        "description": "Detects hanging, strangulation, blunt force from scene photos",
        "dataset": "INTERPOL DVI Protocol Standards",
        "samples": {
            "Upload a scene photo": None,
        }
    },
    "Brain Pattern Analysis": {
        "icon": "⚡", "input_type": "image",
        "description": "Neurological trauma patterns — EEG-ImageNet grounded",
        "dataset": "BraTS 2023 + EEG-ImageNet (Spampinato et al.)",
        "samples": {
            "Normal brain scan":     "samples/brain_normal.jpg",
            "Suspicious brain scan": "samples/brain_suspicious.jpg",
        }
    },
}

# ── Gemini Agents ─────────────────────────────────────────────────────────────
MIN_CALL_INTERVAL = 6  # seconds — enforces ~10 RPM, well under free-tier 15 RPM


@st.cache_resource
def _rate_state() -> dict:
    # Survives page reloads within the same server process
    return {"last_call": 0.0}


def _rate_limit_wait():
    state = _rate_state()
    wait = MIN_CALL_INTERVAL - (time.time() - state["last_call"])
    if wait <= 0:
        return
    steps = int(wait * 10)
    bar = st.progress(0.0, text=f"Ready in {int(wait)}s…")
    for i in range(steps):
        time.sleep(0.1)
        bar.progress((i + 1) / steps, text=f"Ready in {max(0, int(wait - (i+1)*0.1))}s…")
    bar.empty()


def _do_post(payload: dict) -> http.Response:
    return http.post(
        GEMINI_URL,
        params={"key": _get_api_key()},
        json=payload,
        timeout=30,
    )


def _gemini_post(payload: dict) -> str:
    _rate_limit_wait()
    _rate_state()["last_call"] = time.time()

    r = _do_post(payload)

    if r.status_code == 429:
        # Retry after a full 65-second window
        for remaining in range(65, 0, -1):
            time.sleep(1)
            if remaining % 10 == 0:
                st.toast(f"Rate limit — retrying in {remaining}s…")
        _rate_state()["last_call"] = time.time()
        r = _do_post(payload)

    if not r.ok:
        try:
            msg = r.json()["error"]["message"]
        except Exception:
            msg = r.text[:200]
        raise RuntimeError(f"{r.status_code}: {msg}")

    candidates = r.json().get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates — try again.")
    return candidates[0]["content"]["parts"][0]["text"]


def _compress_image(image_bytes: bytes, max_px: int = 512) -> tuple[str, str]:
    """Returns (base64_string, mime_type) resized to max_px."""
    img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((max_px, max_px), PILImage.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode(), "image/jpeg"


def _build_payload(system_prompt: str, parts: list) -> dict:
    return {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": parts}],
        "generationConfig": {
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }


def run_image_agent(image_bytes: bytes, media_type: str, module: str) -> dict:
    b64, mime = _compress_image(image_bytes)
    payload = _build_payload(
        SYSTEM_PROMPTS[module],
        [
            {"inline_data": {"mime_type": mime, "data": b64}},
            {"text": "Return JSON only."},
        ],
    )
    return _parse(_gemini_post(payload))


def run_text_agent(report_text: str, module: str) -> dict:
    payload = _build_payload(
        SYSTEM_PROMPTS[module],
        [{"text": f"Analyze:\n\n{report_text}\n\nReturn JSON only."}],
    )
    return _parse(_gemini_post(payload))


def _parse(raw: str) -> dict:
    import re
    raw = raw.strip()
    # Strip markdown fences (```json ... ``` or ``` ... ```)
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1)
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Fall back: extract first {...} block from anywhere in the text
    obj = re.search(r"\{.*\}", raw, re.DOTALL)
    if obj:
        try:
            return json.loads(obj.group())
        except json.JSONDecodeError:
            pass
    raise json.JSONDecodeError("No valid JSON found in model response", raw, 0)


# ── Validation (from output_agent.md) ────────────────────────────────────────
def validate_result(result: dict) -> bool:
    required = [
        "module", "anomalies_detected", "findings", "region",
        "severity", "investigator_action", "confidence",
        "dataset_source", "disclaimer"
    ]
    for k in required:
        if k not in result:
            return False
    if result["severity"] not in VALID_SEVERITIES:
        return False
    if result["confidence"] not in VALID_CONFIDENCES:
        return False
    if not isinstance(result["findings"], list):
        return False
    return True


# ── Report card renderer (from output_agent.md) ───────────────────────────────
def render_report(result: dict):
    severity = result.get("severity", "Normal")
    c = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["Normal"])

    st.markdown(f"""
    <div style='background:{c["bg"]};color:{c["text"]};padding:8px 18px;
    border-radius:8px;display:inline-block;font-weight:500;
    font-size:14px;margin-bottom:16px'>{c["label"]}</div>
    """, unsafe_allow_html=True)

    st.subheader(f"Forensic Screening Report — {result.get('module','')}")
    st.caption(f"Dataset grounding: **{result.get('dataset_source','Unknown')}**")
    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Anomalies",  "Yes" if result.get("anomalies_detected") else "No")
    col2.metric("Confidence", result.get("confidence", "Unknown"))
    col3.metric("Region",     result.get("region", "Unknown"))

    st.divider()
    st.markdown("**Findings**")
    findings = result.get("findings", [])
    if findings:
        for f in findings:
            st.markdown(f"- {f}")
    else:
        st.markdown("- No visual anomalies detected in this sample.")

    st.divider()
    st.markdown("**Investigator Action**")
    st.info(result.get("investigator_action", "No action specified."))
    st.warning(
        f"⚠ {result.get('disclaimer','AI screening only. Expert forensic review required.')}"
    )


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("NeuroForensic AI")
st.caption("Multi-Modal Death Investigation Assistant | Healthcare Track | Hackathon Demo")
st.caption("Decision-support prototype — not for clinical or legal use.")
st.divider()

# ── Sidebar — API key entry ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Configuration")
    key = _get_api_key()
    if not key:
        entered = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIza...",
            help="Free key at aistudio.google.com — no credit card needed",
        )
        if entered:
            st.session_state["gemini_api_key"] = entered.strip()
            st.rerun()
        st.info(
            "Get a free key at **aistudio.google.com**\n\n"
            "Or add to `.env` file:\n"
            "```\nGEMINI_API_KEY=AIza...\n```"
        )
    else:
        st.success(f"Key loaded: `{key[:8]}...`")
        if st.button("Verify key", use_container_width=True):
            with st.spinner("Testing key…"):
                ok, msg = _verify_key(key)
            if ok:
                st.success("Key is valid!")
            else:
                st.error(f"Key rejected: {msg}")

    st.divider()
    st.markdown("**Gemini free tier limits**")
    st.caption("15 req/min · 1,500 req/day · No credit card")
    st.caption(f"App enforces {MIN_CALL_INTERVAL}s between calls.")

    remaining = max(0, int(MIN_CALL_INTERVAL - (time.time() - _rate_state()["last_call"])))
    if remaining > 0:
        st.warning(f"Next call ready in {remaining}s")
    else:
        st.success("Ready to analyze")

# API key hard stop
if not _get_api_key():
    st.warning("Enter your Gemini API key in the sidebar to continue.")
    st.stop()

# ── Module selector ───────────────────────────────────────────────────────────
st.subheader("Step 1 — Select forensic module")

module_names = list(MODULE_META.keys())
if "selected_module" not in st.session_state:
    st.session_state.selected_module = module_names[0]

cols = st.columns(3)
for i, name in enumerate(module_names):
    meta = MODULE_META[name]
    if cols[i % 3].button(
        f"{meta['icon']} {name}",
        use_container_width=True,
        type="primary" if st.session_state.selected_module == name else "secondary"
    ):
        st.session_state.selected_module = name

selected_module = st.session_state.selected_module
meta = MODULE_META[selected_module]

st.info(
    f"**{meta['icon']} {selected_module}** — {meta['description']}\n\n"
    f"Dataset: *{meta['dataset']}*"
)
st.divider()

# ── Input section ─────────────────────────────────────────────────────────────
st.subheader("Step 2 — Provide evidence")

input_bytes  = None
input_text   = None
media_type   = "image/jpeg"
input_ready  = False

if meta["input_type"] == "image":
    sample_options = {k: v for k, v in meta["samples"].items() if v is not None}
    sample_options = {"Upload my own image": None, **sample_options}
    selected_sample = st.selectbox("Choose a demo sample or upload:", list(sample_options.keys()))

    if selected_sample == "Upload my own image":
        uploaded = st.file_uploader(
            "Upload scan or scene photo (JPEG or PNG)",
            type=["jpg", "jpeg", "png"]
        )
        if uploaded:
            input_bytes = uploaded.read()
            media_type  = "image/png" if uploaded.name.endswith(".png") else "image/jpeg"
            st.image(input_bytes, caption="Uploaded image", use_container_width=True)
            input_ready = True
    else:
        path = Path(sample_options[selected_sample])
        if path.exists():
            input_bytes = path.read_bytes()
            st.image(input_bytes, caption=selected_sample, use_container_width=True)
            input_ready = True
        else:
            st.warning(
                f"Sample not found: `{path}`\n\n"
                "Run `python download_samples.py` to download demo images, "
                "or upload your own above."
            )

else:  # Toxicology text
    sample_options = {k: v for k, v in meta["samples"].items()}
    selected_sample = st.selectbox("Choose a demo report or paste your own:", list(sample_options.keys()))

    if selected_sample and Path(meta["samples"].get(selected_sample, "")).exists():
        input_text = Path(meta["samples"][selected_sample]).read_text()
        st.code(input_text, language="text")
        input_ready = True
    else:
        input_text = st.text_area(
            "Paste toxicology report text:",
            height=220,
            placeholder="e.g.\nEthanol: 0.32 g/dL [Reference < 0.08] ** ELEVATED **\nAcetaminophen: 240 mcg/mL [Reference < 20] ** CRITICAL **"
        )
        if input_text and input_text.strip():
            input_ready = True

# ── Run analysis ──────────────────────────────────────────────────────────────
st.divider()
st.subheader("Step 3 — Run forensic screening")

# Build a cache key from the current input so changing input invalidates the cache
_cache_key = f"{selected_module}::{selected_sample if 'selected_sample' in dir() else ''}::{hash(input_bytes or b'') if input_bytes else hash(input_text or '')}"

if st.button("Analyze Now", type="primary", disabled=not input_ready):
    if st.session_state.get("last_cache_key") != _cache_key:
        with st.spinner(f"Running {selected_module} analysis..."):
            try:
                if meta["input_type"] == "image":
                    result = run_image_agent(input_bytes, media_type, selected_module)
                else:
                    result = run_text_agent(input_text, selected_module)
                st.session_state["last_result"] = result
                st.session_state["last_cache_key"] = _cache_key
            except json.JSONDecodeError as e:
                st.error(f"Gemini returned non-JSON: {e.doc[:300]}")
            except Exception as e:
                err = str(e)
                if "api_key" in err.lower() or "permission" in err.lower() or "403" in err:
                    st.error("Invalid Gemini API key. Check your key at aistudio.google.com.")
                elif "429" in err or "quota" in err.lower() or "rate" in err.lower():
                    st.error("Rate limit exceeded after retry. Wait 60s then click Analyze Again. If it keeps failing, you may have hit the 1500 req/day cap — resets at midnight UTC.")
                else:
                    st.error(err)

if st.session_state.get("last_result") and st.session_state.get("last_cache_key") == _cache_key:
    result = st.session_state["last_result"]
    if validate_result(result):
        render_report(result)
    else:
        st.error("Report generation failed: unexpected format. Please retry.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "For demonstration purposes only. "
    "NeuroForensic AI does not replace qualified forensic pathologists. "
    "All outputs require expert validation before any action. "
    "No real patient data is used or stored. | "
    "Datasets: NIH ChestX-ray14, BraTS 2023, RSNA, MIMIC-IV, EEG-ImageNet, INTERPOL DVI."
)
