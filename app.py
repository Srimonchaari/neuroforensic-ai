"""
Forensic AI — Multi-Modal Death Investigation Assistant
============================================================
Author: Aman | Track: Build with Healthcare | AI: Gemini Flash
Decision-support forensic screening prototype — not for clinical or legal use.
"""

import streamlit as st
import requests as http
import base64
import json
import os
import re
import time
import io
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image as PILImage, ImageDraw, ImageFont

load_dotenv()

MODEL      = "gemini-2.5-flash"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent"
)

# ─────────────────────────────────────────────────────────────────────────────
# API key helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_api_key() -> str | None:
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
        body = (r.json() if r.headers.get("content-type", "").startswith("application/json") else {})
        return False, body.get("error", {}).get("message", r.text[:120])
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Persistent history — stored in local JSON file, survives refresh
# ─────────────────────────────────────────────────────────────────────────────
HISTORY_FILE = Path("analysis_history.json")


def _load_history() -> list:
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text())
    except Exception:
        pass
    return []


def _save_history(history: list) -> None:
    try:
        HISTORY_FILE.write_text(json.dumps(history, indent=2))
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Page config  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Forensic AI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS design system
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Layout ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stDeployButton"] { display: none !important; }
[data-testid="stToolbarActions"] { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; max-width: 780px; }

/* ═══════════════════════════════════════════════════════
   HERO  — always dark gradient, works on any theme
═══════════════════════════════════════════════════════ */
.nf-hero {
    background: linear-gradient(135deg, #0D1B2A 0%, #1B2A4A 60%, #0D2137 100%);
    padding: 28px 32px 22px;
    border-radius: 16px;
    margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.07);
}
.nf-hero-title { color:#FFF; font-size:28px; font-weight:800; letter-spacing:-0.5px; margin:0 0 4px; line-height:1.2; }
.nf-hero-sub   { color:rgba(255,255,255,0.58); font-size:13px; margin:0 0 14px; }
.nf-hero-chips { display:flex; gap:8px; flex-wrap:wrap; }
.nf-chip {
    background: rgba(255,255,255,0.10);
    color: rgba(255,255,255,0.80);
    padding: 3px 11px; border-radius: 20px;
    font-size: 11px; font-weight: 500; letter-spacing: 0.3px;
    border: 1px solid rgba(255,255,255,0.15);
}

/* ═══════════════════════════════════════════════════════
   STEP HEADER
═══════════════════════════════════════════════════════ */
.nf-step { display:flex; align-items:center; gap:12px; margin:28px 0 14px; }
.nf-step-num {
    background: #1565C0; color: #fff;
    width:30px; height:30px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:13px; font-weight:800; flex-shrink:0;
    box-shadow: 0 2px 6px rgba(21,101,192,0.40);
}
.nf-step-label { font-size:17px; font-weight:700; color:var(--text-color); letter-spacing:-0.2px; }

/* ═══════════════════════════════════════════════════════
   MODULE CARD
═══════════════════════════════════════════════════════ */
.nf-module-card {
    background: rgba(21,101,192,0.07);
    border: 1px solid rgba(21,101,192,0.25);
    border-left: 4px solid #1565C0;
    border-radius: 10px;
    padding: 14px 18px; margin: 8px 0 16px;
    display:flex; align-items:flex-start; gap:14px;
}
.nf-module-icon { font-size:30px; line-height:1; }
.nf-module-name { font-size:15px; font-weight:700; color:#1565C0; margin:0 0 3px; }
.nf-module-desc { font-size:13px; color:var(--text-color); opacity:0.75; margin:0 0 5px; }
.nf-module-ds   { font-size:11px; color:var(--text-color); opacity:0.45; font-style:italic; margin:0; }

/* ═══════════════════════════════════════════════════════
   SEVERITY BANNER — semi-transparent tints, readable on
   both light and dark backgrounds
═══════════════════════════════════════════════════════ */
.nf-severity {
    display:flex; align-items:center; gap:10px;
    padding:12px 20px; border-radius:10px;
    font-weight:700; font-size:16px;
    width:100%; box-sizing:border-box; margin-bottom:14px;
}
.sev-normal     { background:rgba(46,125,50,0.12);   color:#2E7D32; border:1.5px solid rgba(46,125,50,0.35); }
.sev-suspicious { background:rgba(230,81,0,0.12);    color:#BF360C; border:1.5px solid rgba(230,81,0,0.35); }
.sev-critical   { background:rgba(183,28,28,0.12);   color:#B71C1C; border:1.5px solid rgba(183,28,28,0.35); }

/* dark-mode: lighten severity text so it reads on dark bg */
[data-theme="dark"] .sev-normal     { color:#81C784; background:rgba(46,125,50,0.18);  border-color:rgba(46,125,50,0.45); }
[data-theme="dark"] .sev-suspicious { color:#FFB74D; background:rgba(230,81,0,0.18);   border-color:rgba(230,81,0,0.45); }
[data-theme="dark"] .sev-critical   { color:#E57373; background:rgba(183,28,28,0.18);  border-color:rgba(183,28,28,0.45); }

/* ═══════════════════════════════════════════════════════
   REPORT TITLE ROW
═══════════════════════════════════════════════════════ */
.nf-report-title { font-size:20px; font-weight:800; color:var(--text-color); margin:0; }
.nf-report-mod   { font-size:13px; color:var(--text-color); opacity:0.50; margin-left:8px; }
.nf-report-ds    { font-size:11px; color:var(--text-color); opacity:0.40; margin:4px 0 10px; }

/* ═══════════════════════════════════════════════════════
   CASE SUMMARY
═══════════════════════════════════════════════════════ */
.nf-summary {
    background: rgba(21,101,192,0.06);
    border-left: 3px solid #1565C0;
    padding: 10px 16px; border-radius: 0 8px 8px 0;
    font-size: 13.5px; color: var(--text-color);
    opacity: 0.85; font-style: italic;
    margin: 6px 0 16px; line-height: 1.6;
}

/* ═══════════════════════════════════════════════════════
   STAT CARDS
═══════════════════════════════════════════════════════ */
.nf-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin:10px 0; }
.nf-stat {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 10px; padding:13px 14px; text-align:center;
}
.stat-label {
    font-size:10px; font-weight:700; text-transform:uppercase;
    letter-spacing:0.9px; color:var(--text-color);
    opacity:0.45; margin-bottom:5px;
}
.stat-value { font-size:19px; font-weight:800; color:var(--text-color); }

/* ═══════════════════════════════════════════════════════
   REGION
═══════════════════════════════════════════════════════ */
.nf-region {
    background: rgba(21,101,192,0.07);
    border: 1px solid rgba(21,101,192,0.22);
    border-radius: 8px; padding:8px 14px;
    font-size:13px; color:var(--text-color);
    margin:10px 0 18px;
    white-space:normal; overflow-wrap:anywhere; word-break:break-word;
}
.nf-region b { color:#1565C0; }

/* ═══════════════════════════════════════════════════════
   CONTENT CARDS
═══════════════════════════════════════════════════════ */
.nf-card {
    background: var(--background-color);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 12px; padding:16px 18px; margin:8px 0;
    box-shadow: 0 1px 5px rgba(0,0,0,0.05);
}
[data-theme="dark"] .nf-card {
    background: var(--secondary-background-color);
    border-color: rgba(255,255,255,0.08);
    box-shadow: none;
}
.nf-card-title {
    font-size:10px; font-weight:700; text-transform:uppercase;
    letter-spacing:0.9px; color:var(--text-color); opacity:0.45; margin-bottom:10px;
}

/* ═══════════════════════════════════════════════════════
   FINDING ITEMS
═══════════════════════════════════════════════════════ */
.nf-finding {
    display:flex; align-items:flex-start; gap:10px;
    padding:7px 0; border-bottom:1px solid rgba(128,128,128,0.10);
    font-size:13.5px; color:var(--text-color); line-height:1.55;
}
.nf-finding:last-child { border-bottom:none; padding-bottom:0; }
.nf-dot { width:7px; height:7px; border-radius:50%; margin-top:6px; flex-shrink:0; }
.dot-normal     { background:#43A047; }
.dot-suspicious { background:#EF6C00; }
.dot-critical   { background:#C62828; }

/* ═══════════════════════════════════════════════════════
   TWO-COLUMN GRID
═══════════════════════════════════════════════════════ */
.nf-two-col { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:8px 0; }
.nf-two-col .nf-card { margin:0; }

/* ═══════════════════════════════════════════════════════
   INVESTIGATOR ACTION CARD
═══════════════════════════════════════════════════════ */
.nf-action {
    background: rgba(21,101,192,0.08);
    border: 1px solid rgba(21,101,192,0.30);
    border-radius: 10px; padding:14px 18px; margin:12px 0;
}
.nf-action-label {
    font-size:10px; font-weight:700; text-transform:uppercase;
    letter-spacing:0.9px; color:#1565C0; margin-bottom:6px;
}
.nf-action-text { font-size:14px; font-weight:600; color:var(--text-color); line-height:1.5; }

[data-theme="dark"] .nf-action-label { color:#90CAF9; }

/* ═══════════════════════════════════════════════════════
   DISCLAIMER
═══════════════════════════════════════════════════════ */
.nf-disclaimer {
    background: rgba(249,168,37,0.10);
    border: 1px solid rgba(249,168,37,0.45);
    border-radius: 8px; padding:10px 14px;
    font-size:12px; color:var(--text-color);
    opacity:0.85; margin:10px 0 2px; line-height:1.5;
}
[data-theme="dark"] .nf-disclaimer { opacity:1; }

/* ═══════════════════════════════════════════════════════
   IMAGE PANEL
═══════════════════════════════════════════════════════ */
.nf-img-panel { text-align:center; }
.nf-img-label {
    font-size:10px; font-weight:700; text-transform:uppercase;
    letter-spacing:0.9px; color:var(--text-color); opacity:0.45;
    margin-bottom:6px; display:block;
}
.nf-img-caption { font-size:11px; color:var(--text-color); opacity:0.40; font-style:italic; margin-top:4px; }

/* ═══════════════════════════════════════════════════════
   FOOTER
═══════════════════════════════════════════════════════ */
.nf-footer {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 10px; padding:14px 18px;
    font-size:11px; color:var(--text-color); opacity:0.70;
    text-align:center; margin-top:28px; line-height:1.7;
}

/* ═══════════════════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════════════════ */
.nf-sidebar-title {
    font-size:10px; font-weight:700; text-transform:uppercase;
    letter-spacing:0.9px; color:var(--text-color); opacity:0.45; margin:14px 0 8px;
}
.nf-api-badge {
    padding:7px 12px; border-radius:8px;
    font-size:12px; font-weight:600; text-align:center; margin:4px 0 10px;
}
.api-ok   { background:rgba(46,125,50,0.12);  color:#2E7D32; border:1px solid rgba(46,125,50,0.30); }
.api-none { background:rgba(230,81,0,0.12);   color:#BF360C; border:1px solid rgba(230,81,0,0.30); }
[data-theme="dark"] .api-ok   { color:#81C784; border-color:rgba(46,125,50,0.40); }
[data-theme="dark"] .api-none { color:#FFB74D; border-color:rgba(230,81,0,0.40); }

.nf-hist-card {
    background: var(--background-color);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 8px; padding:8px 10px; margin:5px 0; font-size:12px;
}
[data-theme="dark"] .nf-hist-card { background:var(--secondary-background-color); border-color:rgba(255,255,255,0.08); }
.nf-hist-mod  { font-weight:600; color:var(--text-color); }
.nf-hist-time { font-size:10px; color:var(--text-color); opacity:0.45; }
.nf-hist-tags { margin-top:4px; display:flex; gap:5px; flex-wrap:wrap; }
.nf-hist-tag  { font-size:10px; padding:2px 7px; border-radius:10px; font-weight:500; }

.tag-normal     { background:rgba(46,125,50,0.12);  color:#2E7D32; }
.tag-suspicious { background:rgba(230,81,0,0.12);   color:#BF360C; }
.tag-critical   { background:rgba(183,28,28,0.12);  color:#B71C1C; }
[data-theme="dark"] .tag-normal     { color:#81C784; background:rgba(46,125,50,0.20); }
[data-theme="dark"] .tag-suspicious { color:#FFB74D; background:rgba(230,81,0,0.20); }
[data-theme="dark"] .tag-critical   { color:#E57373; background:rgba(183,28,28,0.20); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
MAX_OUTPUT_TOKENS = 4096
VALID_SEVERITIES  = ["Normal", "Suspicious", "Critical"]
VALID_CONFIDENCES = ["Low", "Medium", "High"]

ANNO_COLOR = {
    "Normal":     (0, 200, 83),
    "Suspicious": (255, 109, 0),
    "Critical":   (213, 0, 0),
}

SEV_CLASS  = {"Normal": "sev-normal", "Suspicious": "sev-suspicious", "Critical": "sev-critical"}
SEV_ICON   = {"Normal": "✓", "Suspicious": "⚠", "Critical": "🔴"}
SEV_LABEL  = {"Normal": "No Anomalies Detected", "Suspicious": "Review Recommended", "Critical": "Urgent Review Required"}
DOT_CLASS  = {"Normal": "dot-normal", "Suspicious": "dot-suspicious", "Critical": "dot-critical"}

# ─────────────────────────────────────────────────────────────────────────────
# Module metadata
# ─────────────────────────────────────────────────────────────────────────────
MODULE_META = {
    "Chest X-ray": {
        "icon": "🫁",
        "input_type": "image",
        "description": "Detects lung opacity, fluid, structural anomalies",
        "dataset": "NIH ChestX-ray14 — 112,000 images",
        "samples": {
            "Normal chest scan":     "samples/chest_normal.jpg",
            "Suspicious chest scan": "samples/chest_suspicious.jpg",
            "Critical chest scan":   "samples/chest_critical.jpg",
        },
    },
    "Brain MRI / CT": {
        "icon": "🧠",
        "input_type": "image",
        "description": "Detects tumors, lesions, mass effect, midline shift",
        "dataset": "BraTS 2023 — multi-modal brain MRI",
        "samples": {
            "Normal brain scan":     "samples/brain_normal.jpg",
            "Suspicious brain scan": "samples/brain_suspicious.jpg",
        },
    },
    "Full Body CT": {
        "icon": "🦴",
        "input_type": "image",
        "description": "Detects trauma, internal bleeding, organ injuries, fractures",
        "dataset": "RSNA Hemorrhage — 25,000 CT scans",
        "samples": {
            "Normal body CT": "samples/body_normal.jpg",
            "Trauma body CT": "samples/body_trauma.jpg",
        },
    },
    "Toxicology Report": {
        "icon": "🧪",
        "input_type": "text",
        "description": "Detects drug levels, toxic substances via lab report NLP",
        "dataset": "MIMIC-IV Clinical Notes (PhysioNet)",
        "samples": {
            "Normal tox report":     "samples/tox_normal.txt",
            "Suspicious tox report": "samples/tox_suspicious.txt",
            "Critical tox report":   "samples/tox_critical.txt",
        },
    },
    "External Trauma Photo": {
        "icon": "📷",
        "input_type": "image",
        "description": "Detects ligature marks, bruising, wounds from scene photos",
        "dataset": "INTERPOL DVI Protocol Standards",
        "samples": {},
    },
    "Deep Brain Screening": {
        "icon": "⚡",
        "input_type": "image",
        "description": "Deep structural screening of brain MRI/CT for forensic trauma patterns",
        "dataset": "BraTS 2023 — multi-modal brain MRI",
        "samples": {
            "Normal brain scan":     "samples/brain_normal.jpg",
            "Suspicious brain scan": "samples/brain_suspicious.jpg",
        },
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# System prompts
# ─────────────────────────────────────────────────────────────────────────────
_BASE_RULES = (
    "Output ONLY valid JSON — no markdown fences, no preamble. "
    "Describe only what is visually or textually observable. "
    "Never diagnose diseases or state cause of death. "
    "Always include expert-review disclaimer. This is a demo only."
)


def _schema(module: str, dataset: str) -> str:
    return (
        "{\n"
        f'  "module": "{module}",\n'
        '  "case_summary": "one sentence overview of key finding",\n'
        '  "anomalies": "Yes" or "No",\n'
        '  "anomalies_detected": true or false,\n'
        '  "confidence": "Low" or "Medium" or "High",\n'
        '  "suspected_region": "specific anatomical area or region",\n'
        '  "key_findings": ["finding 1", "finding 2", "finding 3"],\n'
        '  "medical_interpretation": "brief interpretation of the findings",\n'
        '  "forensic_relevance": "relevance to death investigation context",\n'
        '  "differential_considerations": ["possibility 1", "possibility 2"],\n'
        '  "recommended_next_steps": ["step 1", "step 2"],\n'
        '  "investigator_action": "one sentence action recommendation",\n'
        '  "severity": "Normal" or "Suspicious" or "Critical",\n'
        '  "region": "broad anatomical label",\n'
        '  "findings": ["finding 1", "finding 2"],\n'
        '  "limitations": "brief limitations note for this analysis",\n'
        f'  "dataset_source": "{dataset}",\n'
        '  "disclaimer": "Demo only. Not clinical or legal advice. Expert review required.",\n'
        '  "visual_annotations": [\n'
        '    {"label": "region label", "x": 0.50, "y": 0.50, "w": 0.20, "h": 0.15}\n'
        "  ]\n"
        "}"
    )


SYSTEM_PROMPTS = {
    "Chest X-ray": (
        f"Forensic screening assistant — CHEST X-RAY image.\n{_BASE_RULES}\n"
        "Look for: lung opacity, consolidation, pleural fluid, pneumothorax, "
        "rib fractures, mediastinal widening, asymmetric densities.\n"
        "Return ONLY:\n" + _schema("Chest X-ray", "NIH ChestX-ray14")
    ),
    "Brain MRI / CT": (
        f"Forensic screening assistant — BRAIN MRI or CT SCAN.\n{_BASE_RULES}\n"
        "Look for: abnormal masses, hemorrhage, edema, midline shift, "
        "hemispheric asymmetry, density irregularities, structural disruption.\n"
        "Return ONLY:\n" + _schema("Brain MRI / CT", "BraTS 2023")
    ),
    "Full Body CT": (
        f"Forensic screening assistant — FULL BODY CT SCAN.\n{_BASE_RULES}\n"
        "Look for: fractures, organ density anomalies, internal bleeding indicators, "
        "fluid in abnormal regions, soft tissue disruption, lung findings.\n"
        "Return ONLY:\n" + _schema("Full Body CT", "RSNA Hemorrhage Dataset")
    ),
    "Toxicology Report": (
        f"Forensic screening assistant — TOXICOLOGY LAB REPORT text.\n{_BASE_RULES}\n"
        "Look for: substances above reference thresholds, alcohol, opioids, "
        "benzodiazepines, stimulants, poisons, poly-substance interactions, "
        "overdose risk markers. Reference by lab notation only.\n"
        "Return ONLY:\n" + _schema("Toxicology Report", "MIMIC-IV Clinical Notes")
    ),
    "External Trauma Photo": (
        f"Forensic screening assistant — EXTERNAL TRAUMA PHOTO.\n{_BASE_RULES}\n"
        "Follow INTERPOL DVI (Disaster Victim Identification) protocol language.\n"
        "Look for: ligature marks (location, angle, width), petechiae, bruise "
        "patterns (shape, distribution), lacerations, burns, impact wounds, "
        "positional lividity indicators.\n"
        "Return ONLY:\n" + _schema("External Trauma Photo", "INTERPOL DVI Protocol")
    ),
    "Deep Brain Screening": (
        f"Forensic neuroradiology assistant — BRAIN MRI or CT structural screening.\n{_BASE_RULES}\n"
        "Look for: deep white matter signal changes, hippocampal volume asymmetry, "
        "occipital and parietal cortex density anomalies, watershed zone hypodensity, "
        "diffuse axonal injury indicators, brainstem compression or density changes, "
        "deep nuclei hemorrhagic foci, ventricular asymmetry.\n"
        "Return ONLY:\n" + _schema("Deep Brain Screening", "BraTS 2023")
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Fallback result
# ─────────────────────────────────────────────────────────────────────────────

def _make_fallback(module: str) -> dict:
    return {
        "module": module,
        "case_summary": "API unavailable — demo fallback result shown.",
        "anomalies": "No",
        "anomalies_detected": False,
        "confidence": "Low",
        "suspected_region": "N/A",
        "key_findings": ["API unavailable — check your Gemini key or quota and retry."],
        "medical_interpretation": "Analysis could not be completed. API not reachable.",
        "forensic_relevance": "No analysis available at this time.",
        "differential_considerations": ["Manual expert review required"],
        "recommended_next_steps": ["Verify API key at aistudio.google.com", "Retry analysis"],
        "investigator_action": "Check API key validity and retry, or consult a forensic specialist.",
        "severity": "Normal",
        "region": module,
        "findings": ["API unavailable — demo fallback result."],
        "limitations": "API not reachable for this request.",
        "dataset_source": MODULE_META[module]["dataset"],
        "disclaimer": "Demo only. Not clinical or legal advice. Expert review required.",
        "visual_annotations": [],
    }

# ─────────────────────────────────────────────────────────────────────────────
# Image annotation — PIL only
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_annotations(module: str) -> list:
    defaults = {
        "Chest X-ray":           [{"label": "Possible opacity",  "x": 0.50, "y": 0.55, "w": 0.30, "h": 0.25}],
        "Brain MRI / CT":        [{"label": "Suspected lesion",  "x": 0.45, "y": 0.45, "w": 0.25, "h": 0.20}],
        "Full Body CT":          [{"label": "Abnormal density",  "x": 0.50, "y": 0.50, "w": 0.30, "h": 0.20}],
        "External Trauma Photo": [{"label": "Visible injury",    "x": 0.50, "y": 0.40, "w": 0.35, "h": 0.25}],
        "Deep Brain Screening":[{"label": "Structural anomaly", "x": 0.45, "y": 0.45, "w": 0.25, "h": 0.20}],
    }
    return defaults.get(module, [{"label": "Region of interest", "x": 0.5, "y": 0.5, "w": 0.25, "h": 0.20}])


def annotate_image(image_bytes: bytes, result: dict, module: str) -> bytes:
    img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)
    iw, ih = img.size
    severity = result.get("severity", "Normal")
    color = ANNO_COLOR.get(severity, (255, 109, 0))
    annotations = result.get("visual_annotations") or []
    if not annotations and severity != "Normal":
        annotations = _fallback_annotations(module)
    try:
        font = ImageFont.load_default(size=14)
    except TypeError:
        font = ImageFont.load_default()
    for ann in annotations:
        label = ann.get("label", "Region of interest")
        cx = float(ann.get("x", 0.5))
        cy = float(ann.get("y", 0.5))
        bw = float(ann.get("w", 0.2))
        bh = float(ann.get("h", 0.15))
        x1 = max(0, int((cx - bw / 2) * iw))
        y1 = max(0, int((cy - bh / 2) * ih))
        x2 = min(iw, int((cx + bw / 2) * iw))
        y2 = min(ih, int((cy + bh / 2) * ih))
        for t in range(3):
            draw.rectangle([x1 - t, y1 - t, x2 + t, y2 + t], outline=color)
        label_w = len(label) * 8 + 6
        label_top = max(0, y1 - 20)
        draw.rectangle([x1, label_top, x1 + label_w, y1], fill=color)
        draw.text((x1 + 3, label_top + 2), label, fill=(255, 255, 255), font=font)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────────────────────
# Rate limiting + Gemini API
# ─────────────────────────────────────────────────────────────────────────────
MIN_CALL_INTERVAL = 6


@st.cache_resource
def _rate_state() -> dict:
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
        bar.progress((i + 1) / steps, text=f"Ready in {max(0, int(wait - (i + 1) * 0.1))}s…")
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


def run_image_agent(image_bytes: bytes, module: str) -> dict:
    b64, mime = _compress_image(image_bytes)
    payload = _build_payload(
        SYSTEM_PROMPTS[module],
        [{"inline_data": {"mime_type": mime, "data": b64}}, {"text": "Return JSON only."}],
    )
    return _parse(_gemini_post(payload))


def run_text_agent(report_text: str, module: str) -> dict:
    payload = _build_payload(
        SYSTEM_PROMPTS[module],
        [{"text": f"Analyze this lab report:\n\n{report_text}\n\nReturn JSON only."}],
    )
    return _parse(_gemini_post(payload))


def _parse(raw: str) -> dict:
    raw = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    obj = re.search(r"\{.*\}", raw, re.DOTALL)
    if obj:
        try:
            return json.loads(obj.group())
        except json.JSONDecodeError:
            pass
    raise json.JSONDecodeError("No valid JSON found in model response", raw, 0)

# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_result(result: dict) -> bool:
    for k in ("module", "severity", "confidence", "disclaimer"):
        if k not in result:
            return False
    if result["severity"] not in VALID_SEVERITIES:
        return False
    if result["confidence"] not in VALID_CONFIDENCES:
        return False
    return True

# ─────────────────────────────────────────────────────────────────────────────
# Report renderer — production card layout
# ─────────────────────────────────────────────────────────────────────────────

def render_report(result: dict):
    severity   = result.get("severity", "Normal")
    sev_cls    = SEV_CLASS.get(severity, "sev-normal")
    sev_icon   = SEV_ICON.get(severity, "●")
    sev_lbl    = SEV_LABEL.get(severity, severity)
    dot_cls    = DOT_CLASS.get(severity, "dot-normal")

    # ── Severity banner
    st.markdown(f"""
    <div class="nf-severity {sev_cls}">
        <span style="font-size:22px;line-height:1">{sev_icon}</span>
        <span>{sev_lbl}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Report title + dataset
    module_name = result.get("module", "")
    dataset_src = result.get("dataset_source", "Unknown")
    st.markdown(f"""
    <div style="margin:0 0 4px">
        <span class="nf-report-title">Forensic Screening Report</span>
        <span class="nf-report-mod">{module_name}</span>
    </div>
    <div class="nf-report-ds">Dataset grounding: <strong>{dataset_src}</strong></div>
    """, unsafe_allow_html=True)

    # ── Case summary
    if result.get("case_summary"):
        st.markdown(
            f'<div class="nf-summary">📋 {result["case_summary"]}</div>',
            unsafe_allow_html=True,
        )

    # ── Stat cards (Anomalies · Confidence · Severity)
    anomaly_val = result.get("anomalies") or ("Yes" if result.get("anomalies_detected") else "No")
    confidence  = result.get("confidence", "—")
    st.markdown(f"""
    <div class="nf-stats">
        <div class="nf-stat">
            <div class="stat-label">Anomalies</div>
            <div class="stat-value">{anomaly_val}</div>
        </div>
        <div class="nf-stat">
            <div class="stat-label">Confidence</div>
            <div class="stat-value">{confidence}</div>
        </div>
        <div class="nf-stat">
            <div class="stat-label">Severity</div>
            <div class="stat-value">{severity}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Region (full-width, no truncation)
    region_val = result.get("suspected_region") or result.get("region", "Unknown")
    st.markdown(
        f'<div class="nf-region"><b>Region:</b> {region_val}</div>',
        unsafe_allow_html=True,
    )

    # ── Key findings card
    findings = result.get("key_findings") or result.get("findings", [])
    if not findings:
        findings = ["No significant findings detected in this sample."]
    items_html = "".join(
        f'<div class="nf-finding">'
        f'<span class="nf-dot {dot_cls}"></span>'
        f'<span>{f}</span></div>'
        for f in findings
    )
    st.markdown(f"""
    <div class="nf-card">
        <div class="nf-card-title">🔍 Key Findings</div>
        {items_html}
    </div>
    """, unsafe_allow_html=True)

    # ── Interpretation + Forensic Relevance (two-column)
    interp    = result.get("medical_interpretation", "")
    relevance = result.get("forensic_relevance", "")
    if interp or relevance:
        st.markdown(f"""
        <div class="nf-two-col">
            <div class="nf-card">
                <div class="nf-card-title">🩺 Medical Interpretation</div>
                <div style="font-size:13.5px;color:#333;line-height:1.6">{interp or "—"}</div>
            </div>
            <div class="nf-card">
                <div class="nf-card-title">🔎 Forensic Relevance</div>
                <div style="font-size:13.5px;color:#333;line-height:1.6">{relevance or "—"}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Differentials + Next Steps (collapsible, side by side)
    differentials = result.get("differential_considerations", [])
    next_steps    = result.get("recommended_next_steps", [])
    if differentials or next_steps:
        col_l, col_r = st.columns(2)
        with col_l:
            if differentials:
                with st.expander("🔀 Differential Considerations"):
                    for d in differentials:
                        st.markdown(f"- {d}")
        with col_r:
            if next_steps:
                with st.expander("📋 Recommended Next Steps"):
                    for s in next_steps:
                        st.markdown(f"- {s}")

    # ── Investigator action card
    action = result.get("investigator_action", "")
    if action:
        st.markdown(f"""
        <div class="nf-action">
            <div class="nf-action-label">🎯 Investigator Action Required</div>
            <div class="nf-action-text">{action}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Limitations note
    limitations = result.get("limitations", "")
    if limitations:
        st.caption(f"⚡ Analysis limitations: {limitations}")

    # ── Disclaimer
    disclaimer = result.get("disclaimer", "AI screening only. Expert forensic review required.")
    st.markdown(
        f'<div class="nf-disclaimer">⚠️ <strong>Disclaimer:</strong> {disclaimer}</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────────────────────────
if "selected_module" not in st.session_state:
    st.session_state.selected_module = list(MODULE_META.keys())[0]
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = _load_history()

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 Forensic AI")

    # API status
    key = _get_api_key()
    st.markdown('<div class="nf-sidebar-title">API Status</div>', unsafe_allow_html=True)
    if key:
        st.markdown(
            f'<div class="nf-api-badge api-ok">🟢 Key loaded &nbsp;·&nbsp; <code>{key[:8]}…</code></div>',
            unsafe_allow_html=True,
        )
        if st.button("Verify key", use_container_width=True):
            with st.spinner("Testing…"):
                ok, msg = _verify_key(key)
            st.success("Key valid!") if ok else st.error(f"Rejected: {msg}")
    else:
        st.markdown(
            '<div class="nf-api-badge api-none">🔴 No API key set</div>',
            unsafe_allow_html=True,
        )
        entered = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIza…",
            help="Free key at aistudio.google.com",
        )
        if entered:
            st.session_state["gemini_api_key"] = entered.strip()
            st.rerun()
        st.caption("Get a free key at **aistudio.google.com** — no credit card needed.")

    # Rate limit status
    st.markdown('<div class="nf-sidebar-title">Rate Limit</div>', unsafe_allow_html=True)
    remaining = max(0, int(MIN_CALL_INTERVAL - (time.time() - _rate_state()["last_call"])))
    if remaining > 0:
        st.warning(f"Next call ready in {remaining}s")
    else:
        st.success("Ready to analyze")
    st.caption(f"Free tier: 15 req/min · 1,500 req/day · App enforces {MIN_CALL_INTERVAL}s gap")

    # Analysis history
    st.markdown('<div class="nf-sidebar-title">Analysis History</div>', unsafe_allow_html=True)
    if st.session_state.analysis_history:
        col_clr, col_cnt = st.columns([2, 1])
        with col_cnt:
            st.caption(f"{len(st.session_state.analysis_history)} saved")
        with col_clr:
            if st.button("🗑 Clear", use_container_width=True):
                st.session_state.analysis_history = []
                _save_history([])
                st.session_state.pop("history_result", None)
                st.rerun()

        for i, entry in enumerate(st.session_state.analysis_history):
            icon    = MODULE_META.get(entry["module"], {}).get("icon", "🔬")
            sev     = entry.get("severity", "Normal")
            tag_cls = {"Normal": "tag-normal", "Suspicious": "tag-suspicious",
                       "Critical": "tag-critical"}.get(sev, "tag-normal")
            summary = entry.get("case_summary", "")
            st.markdown(f"""
            <div class="nf-hist-card">
                <div class="nf-hist-mod">{icon} {entry['module']}</div>
                <div class="nf-hist-time">{entry['timestamp']} · {entry['filename']}</div>
                <div class="nf-hist-tags">
                    <span class="nf-hist-tag {tag_cls}">{sev}</span>
                    <span class="nf-hist-tag" style="background:rgba(128,128,128,0.12);color:#555">{entry['confidence']}</span>
                </div>
                {f'<div style="font-size:11px;color:#888;margin-top:4px;font-style:italic">{summary[:70]}…</div>' if summary else ""}
            </div>
            """, unsafe_allow_html=True)
            if entry.get("result"):
                if st.button("📂 Load case", key=f"load_{i}", use_container_width=True):
                    st.session_state["history_result"] = entry["result"]
                    st.session_state.selected_module   = entry["module"]
                    for k in ("last_result", "last_cache_key", "annotated_image"):
                        st.session_state.pop(k, None)
                    st.rerun()
    else:
        st.caption("No analyses yet — results persist across refreshes.")

# ─────────────────────────────────────────────────────────────────────────────
# API key hard stop
# ─────────────────────────────────────────────────────────────────────────────
if not _get_api_key():
    st.markdown("""
    <div class="nf-hero">
        <div class="nf-hero-title">🧠 Forensic AI</div>
        <div class="nf-hero-sub">Enter your Gemini API key in the sidebar to begin.</div>
    </div>
    """, unsafe_allow_html=True)
    st.info("👈 Add your free Gemini API key in the sidebar to start forensic screening.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Hero header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nf-hero">
    <div class="nf-hero-title">🧠 Forensic AI</div>
    <div class="nf-hero-sub">Multi-Modal Death Investigation Assistant · Healthcare Track · Hackathon Demo</div>
    <div class="nf-hero-chips">
        <span class="nf-chip">6 Forensic Modules</span>
        <span class="nf-chip">Gemini Flash Vision</span>
        <span class="nf-chip">INTERPOL DVI Protocol</span>
        <span class="nf-chip">Demo Only — Not Clinical</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Module selector
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nf-step">
    <div class="nf-step-num">1</div>
    <div class="nf-step-label">Select forensic module</div>
</div>
""", unsafe_allow_html=True)

module_names = list(MODULE_META.keys())
cols = st.columns(3)
for i, name in enumerate(module_names):
    meta = MODULE_META[name]
    if cols[i % 3].button(
        f"{meta['icon']} {name}",
        use_container_width=True,
        type="primary" if st.session_state.selected_module == name else "secondary",
    ):
        if st.session_state.selected_module != name:
            st.session_state.selected_module = name
            for k in ("last_result", "last_cache_key", "annotated_image"):
                st.session_state.pop(k, None)

selected_module = st.session_state.selected_module
meta = MODULE_META[selected_module]

st.markdown(f"""
<div class="nf-module-card">
    <div class="nf-module-icon">{meta['icon']}</div>
    <div>
        <div class="nf-module-name">{selected_module}</div>
        <div class="nf-module-desc">{meta['description']}</div>
        <div class="nf-module-ds">Dataset: {meta['dataset']}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Input
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nf-step">
    <div class="nf-step-num">2</div>
    <div class="nf-step-label">Provide evidence</div>
</div>
""", unsafe_allow_html=True)

input_bytes     = None
input_text      = None
input_ready     = False
selected_sample = "none"

if meta["input_type"] == "image":
    sample_options = {"Upload my own image": None}
    sample_options.update(meta["samples"])

    selected_sample = st.selectbox(
        "Choose a demo sample or upload your own:",
        list(sample_options.keys()),
        key=f"sample_sel_{selected_module}",
    )

    if selected_sample == "Upload my own image":
        uploaded = st.file_uploader(
            f"Upload scan / scene photo (JPEG or PNG) — will be analyzed as **{selected_module}**",
            type=["jpg", "jpeg", "png"],
            key=f"uploader_{selected_module}",
        )
        if uploaded:
            input_bytes     = uploaded.read()
            selected_sample = uploaded.name
            st.markdown('<div class="nf-img-panel"><span class="nf-img-label">Uploaded Image</span></div>', unsafe_allow_html=True)
            st.image(input_bytes, use_container_width=True)
            input_ready = True
    else:
        path = Path(sample_options[selected_sample])
        if path.exists():
            input_bytes = path.read_bytes()
            st.markdown(f'<div class="nf-img-panel"><span class="nf-img-label">{selected_sample}</span></div>', unsafe_allow_html=True)
            st.image(input_bytes, use_container_width=True)
            input_ready = True
        else:
            st.warning(
                f"Sample not found: `{path}`\n\n"
                "Run `python download_samples.py` or choose **Upload my own image**."
            )

else:  # Toxicology text
    all_text_opts = {"Paste your own report": None}
    all_text_opts.update(meta["samples"])

    selected_sample = st.selectbox(
        "Choose a demo report or paste your own:",
        list(all_text_opts.keys()),
        key=f"sample_sel_{selected_module}",
    )

    if selected_sample != "Paste your own report":
        path = Path(all_text_opts[selected_sample])
        if path.exists():
            input_text = path.read_text()
            preview = input_text[:2000] + ("…" if len(input_text) > 2000 else "")
            st.code(preview, language="text")
            input_ready = True
        else:
            st.warning(
                f"Sample not found: `{path}`\n\n"
                "Run `python download_samples.py` to create demo text files."
            )

    if not input_ready:
        input_text = st.text_area(
            "Paste toxicology report text:",
            height=200,
            placeholder=(
                "Ethanol: 0.32 g/dL  [Reference < 0.08]  ** ELEVATED **\n"
                "Acetaminophen: 240 mcg/mL  [Reference < 20]  ** CRITICAL **"
            ),
            key=f"paste_{selected_module}",
        )
        if input_text and input_text.strip():
            selected_sample = "Pasted report"
            input_ready = True

# ─────────────────────────────────────────────────────────────────────────────
# Cache key
# ─────────────────────────────────────────────────────────────────────────────
if input_bytes is not None:
    _content_hash = hash(input_bytes) & 0xFFFFFFFF
elif input_text is not None:
    _content_hash = hash(input_text) & 0xFFFFFFFF
else:
    _content_hash = 0

_cache_key = f"{selected_module}|{selected_sample}|{_content_hash}"

# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Run analysis
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nf-step">
    <div class="nf-step-num">3</div>
    <div class="nf-step-label">Run forensic screening</div>
</div>
""", unsafe_allow_html=True)

if st.button("🔬 Analyze Now", type="primary", disabled=not input_ready, use_container_width=True):
    st.session_state.pop("history_result", None)
    if st.session_state.get("last_cache_key") != _cache_key:
        with st.spinner(f"Running {selected_module} analysis…"):
            try:
                if meta["input_type"] == "image":
                    result = run_image_agent(input_bytes, selected_module)
                else:
                    result = run_text_agent(input_text, selected_module)

                st.session_state["last_result"]    = result
                st.session_state["last_cache_key"] = _cache_key

                if meta["input_type"] == "image" and input_bytes:
                    try:
                        ann = annotate_image(input_bytes, result, selected_module)
                        st.session_state["annotated_image"] = ann
                    except Exception:
                        st.session_state.pop("annotated_image", None)

                history_entry = {
                    "timestamp":    datetime.now().strftime("%H:%M:%S"),
                    "module":       selected_module,
                    "filename":     selected_sample,
                    "anomalies":    result.get("anomalies") or ("Yes" if result.get("anomalies_detected") else "No"),
                    "confidence":   result.get("confidence", "Unknown"),
                    "severity":     result.get("severity", "Normal"),
                    "suspected_region": result.get("suspected_region") or result.get("region", "Unknown"),
                    "case_summary": result.get("case_summary", ""),
                    "result":       result,
                }
                st.session_state.analysis_history.insert(0, history_entry)
                if len(st.session_state.analysis_history) > 20:
                    st.session_state.analysis_history = st.session_state.analysis_history[:20]
                _save_history(st.session_state.analysis_history)

            except json.JSONDecodeError as e:
                st.error(f"Model returned non-JSON: {e.doc[:300]}")
                st.session_state["last_result"]    = _make_fallback(selected_module)
                st.session_state["last_cache_key"] = _cache_key
            except Exception as e:
                err = str(e)
                if "api_key" in err.lower() or "403" in err:
                    st.error("Invalid API key. Check at aistudio.google.com.")
                elif "429" in err or "quota" in err.lower() or "rate" in err.lower():
                    st.error("Rate limit exceeded. Wait 60s then retry. Daily cap resets at midnight UTC.")
                else:
                    st.error(f"Analysis failed: {err}")
                st.session_state["last_result"]    = _make_fallback(selected_module)
                st.session_state["last_cache_key"] = _cache_key

# ─────────────────────────────────────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────────────────────────────────────
_from_history = bool(st.session_state.get("history_result"))
_fresh        = (st.session_state.get("last_result")
                 and st.session_state.get("last_cache_key") == _cache_key)

if _from_history or _fresh:
    result  = st.session_state["history_result"] if _from_history else st.session_state["last_result"]
    ann_img = None if _from_history else st.session_state.get("annotated_image")

    if _from_history:
        st.info("📂 Loaded from history — re-run analysis to generate new annotations.")

    # Image comparison panel
    if ann_img and meta["input_type"] == "image" and input_bytes:
        st.markdown("<br>", unsafe_allow_html=True)
        col_orig, col_ann = st.columns(2)
        with col_orig:
            st.markdown('<div class="nf-img-panel"><span class="nf-img-label">Original</span></div>', unsafe_allow_html=True)
            st.image(input_bytes, use_container_width=True)
        with col_ann:
            st.markdown('<div class="nf-img-panel"><span class="nf-img-label">AI Markers</span></div>', unsafe_allow_html=True)
            st.image(ann_img, use_container_width=True)
        st.markdown(
            '<div class="nf-img-caption" style="text-align:center">⚠ Annotations are AI-estimated approximations for demo triage only.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if validate_result(result):
        render_report(result)
    else:
        st.error("Unexpected report format. Raw output:")
        st.json(result)

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nf-footer">
    <strong>Forensic AI</strong> — For demonstration purposes only.<br>
    Does not replace qualified forensic pathologists. All outputs require expert validation.<br>
    No real patient data used or stored.<br>
    <span style="color:#AAB">Datasets: NIH ChestX-ray14 · BraTS 2023 · RSNA · MIMIC-IV · INTERPOL DVI</span>
</div>
""", unsafe_allow_html=True)
