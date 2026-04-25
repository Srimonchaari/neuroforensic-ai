# Pre-Autopsy Intelligence System

---

**Project Owner:** [shreyabalki](https://github.com/shreyabalki)

---

## Overview

NeuroForensic AI is a multi-modal forensic screening system that helps investigators perform rapid, structured first-pass analysis of forensic evidence. It accepts medical scan images, trauma photographs, and toxicology text reports, and returns structured JSON reports with findings, severity classification, and recommended next steps.

The system is designed for decision support only. It is not a diagnostic tool, not a legal evidence system, and does not determine cause of death. All outputs require review and validation by a qualified forensic specialist before any action is taken.

---

## Problem

| Challenge | Impact |
|---|---|
| Severe forensic expert shortage | ~150 forensic pathologists per 100 million people globally |
| Delayed case review | Days to weeks of wait time for specialist analysis; evidence degrades |
| Fragmented tooling | Medical imaging, toxicology, and trauma review handled by separate, disconnected tools |
| Low-resource access gap | Investigators in under-resourced regions have no accessible, lightweight forensic triage tools |
| Uninvestigated deaths | Over 2 million deaths go without forensic review annually |

---

## Solution

NeuroForensic AI addresses this gap with:

- **Multi-modal input support** — accepts medical images (JPEG/PNG) and unstructured text (lab reports)
- **Six independent forensic modules** — each with a tailored system prompt, schema, and accepted input type
- **Structured output format** — consistent JSON reports with severity, findings, confidence, and investigator actions
- **Fast screening** — full analysis in under 60 seconds per case
- **Consistent reporting** — standardised output structure across all modules and investigators
- **Mandatory expert review** — every report includes a built-in disclaimer and escalation guidance

---

## How It Works

```
1. Investigator selects a forensic module
        ↓
2. Uploads an image (JPEG/PNG) or pastes toxicology text
        ↓
3. Input is preprocessed
   - Images: resized to 512px max, compressed to JPEG 80%, base64-encoded
   - Text: passed directly as user-provided content
        ↓
4. Gemini Flash API performs multi-modal inference
   - Module-specific system prompt applied
   - Strict JSON output schema enforced
   - Hallucination-reduction constraints active
        ↓
5. System parses and validates the JSON response
   - Schema validation applied
   - Graceful fallback returned on parse failure
        ↓
6. UI renders structured report
   - Severity badge (Normal / Suspicious / Critical)
   - Key findings, interpretation, forensic relevance
   - Recommended next steps and investigator action
   - AI-annotated image with approximate bounding boxes
        ↓
7. Investigator reviews and escalates based on findings
```

---

## System Architecture

| Component | Technology |
|---|---|
| Application framework | Python 3.10+ with Streamlit |
| AI inference | Google Gemini 2.5 Flash (multimodal API) |
| Image preprocessing | Pillow (PIL) — resize, compress, encode |
| Annotation | Pillow ImageDraw — bounding boxes, labels |
| HTTP client | requests |
| Environment config | python-dotenv |
| Session persistence | JSON file (analysis_history.json) |
| Deployment | Streamlit Cloud or any Python host |

**No custom ML model is trained. No GPU infrastructure is required. All inference is performed through the Google Gemini API.**

---

## Modules

### 🫁 Chest X-ray
- **Input:** JPEG / PNG image
- **Screens for:** Lung opacity, pleural fluid, pneumothorax, rib fracture patterns, mediastinal widening, structural asymmetry
- **Reference source:** NIH ChestX-ray14 (112,120 labeled chest X-rays)

### 🧠 Brain MRI / CT
- **Input:** JPEG / PNG image
- **Screens for:** Abnormal masses, hemorrhage, edema, hemispheric asymmetry, midline shift indicators, density irregularities
- **Reference source:** BraTS 2023 (multi-modal brain MRI dataset)

### 🦴 Full Body CT
- **Input:** JPEG / PNG image
- **Screens for:** Fractures, internal bleeding indicators, organ density anomalies, soft tissue disruption, trauma patterns
- **Reference source:** RSNA Intracranial Hemorrhage (25,000 CT scans)

### 🧪 Toxicology Report
- **Input:** Plain text or `.txt` file
- **Screens for:** Substances above reference thresholds, alcohol markers, opioids, benzodiazepines, stimulants, overdose risk indicators, poly-substance interactions
- **Reference source:** MIMIC-IV Clinical Notes (PhysioNet)

### 📷 External Trauma
- **Input:** JPEG / PNG photograph
- **Screens for:** Visible injury patterns, bruising distribution, lacerations, burns, ligature-like marks, petechiae indicators
- **Protocol reference:** INTERPOL DVI (Disaster Victim Identification) standard

### ⚡ Deep Brain Screening
- **Input:** Brain MRI or CT image
- **Screens for:** Structural asymmetry, deep-region irregularities, white matter signal changes, occipital and parietal anomalies
- **Reference source:** BraTS 2023

---

## Model Strategy

This system does **not** train any custom deep learning model. There are no model weights, no training pipelines, and no GPU requirements.

All AI inference is performed through the **Google Gemini 2.5 Flash API** using a pre-trained multimodal model. Output behaviour is controlled entirely through:

- **Module-specific system prompts** — forensic domain instructions per module
- **Strict JSON output schemas** — enforced 14-field report structure
- **Hallucination-reduction rules** — prohibit disease naming, cause-of-death claims, and fabricated patient details
- **Mandatory disclaimer field** — expert-review requirement included in every response

This approach allows rapid iteration, zero compute cost, and deployment on any machine with internet access.

---

## Data Sources

| Dataset | Module | Scale | Access |
|---|---|---|---|
| NIH ChestX-ray14 | Chest X-ray | 112,120 images | Public domain |
| BraTS 2023 | Brain MRI / CT, Deep Brain | Multi-modal MRI | Free academic |
| RSNA Hemorrhage | Full Body CT | 25,000 CT scans | Kaggle public |
| MIMIC-IV | Toxicology | 300,000+ records | PhysioNet credentialed |
| INTERPOL DVI | External Trauma | Protocol standard | Public standard |
| EEG-ImageNet | Deep Brain | EEG + visual pairs | Research |

> These sources are used for grounding, reference, prompt design, and expected output structure. They are **not** used to retrain a custom model. Only public or credentialed datasets are referenced. No private patient data is stored.

---

## Data Collection & Processing

- **User-provided input only** — the system processes only what the investigator explicitly uploads or enters
- **No automatic data collection** — no scraping, no passive monitoring, no background tracking
- **No long-term storage** — uploaded images and case content are not retained after the session ends
- **No personal or biometric data stored** — no patient identifiers, demographics, or case metadata retained by the app
- **Third-party inference** — inputs are sent to Google Gemini API; review Google's API data handling policies for applicable protections

---

## Output Format

Every module returns a structured JSON response with the following fields:

| Field | Description |
|---|---|
| `module` | Name of the forensic module used |
| `case_summary` | One-sentence overview of key findings |
| `findings` / `key_findings` | Array of 1–4 observable signals |
| `severity` | `Normal`, `Suspicious`, or `Critical` |
| `confidence` | `Low`, `Medium`, or `High` |
| `suspected_region` | Specific anatomical area of concern |
| `medical_interpretation` | Brief interpretation of findings |
| `forensic_relevance` | Relevance to death investigation context |
| `differential_considerations` | Possible alternative explanations |
| `recommended_next_steps` | Actions for the investigator |
| `investigator_action` | One-sentence escalation guidance |
| `limitations` | Constraints applicable to this analysis |
| `disclaimer` | Mandatory expert-review statement |
| `visual_annotations` | Approximate bounding box coordinates |

---

## Target Users

- **Field investigators** — on-scene, time-critical forensic triage
- **Law enforcement teams** — structured case prioritization and escalation
- **Forensic analysts** — pre-autopsy first-pass screening
- **Disaster response teams** — multi-case triage support in mass casualty events
- **Low-resource healthcare systems** — accessible screening without specialist infrastructure

---

## Limitations

- The system is not a diagnostic tool and does not determine cause of death
- Outputs are not legally authoritative and cannot be used as legal evidence
- Input quality directly affects the reliability of findings — blurry or low-resolution images reduce confidence
- The AI may miss or misinterpret subtle findings; specialist expertise cannot be replicated through prompt engineering
- Toxicology analysis depends on the completeness and clarity of the submitted report
- The Deep Brain Screening module performs structural image analysis only and is not a clinically validated neuro-forensic tool
- Expert validation is mandatory before any output is acted upon

---

## Ethics & Safety

- **No cause-of-death determination** — the system cannot and does not infer why someone died
- **No medical diagnosis** — findings are observable signals, not clinical conclusions
- **No legal conclusions** — outputs do not constitute evidence and carry no legal weight
- **No automated final decisions** — a qualified human expert must review all outputs before any action is taken
- **Cautious language enforced** — all outputs use hedged language: "consistent with", "suggests", "warrants review"
- **Hallucination constraints** — prompts prohibit AI from naming diseases, inventing demographics, or claiming certainty

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/shreyabalki/neuroforensic-ai
cd neuroforensic-ai

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env
# Edit .env and set:
# GEMINI_API_KEY=your_key_here

# 5. Download demo samples (optional)
python download_samples.py

# 6. Run the application
streamlit run app.py
```

The app will be available at **http://localhost:8501**

**Streamlit Cloud deployment:** Add `GEMINI_API_KEY` to your app's Secrets in the Streamlit Cloud dashboard.

---

## Project Structure

```
neuroforensic-ai/
├── app.py                    ← Main Streamlit application
├── download_samples.py       ← Downloads and creates demo sample files
├── requirements.txt          ← Python dependencies
├── .env.example              ← API key configuration template
├── analysis_history.json     ← Persistent session history (auto-generated)
├── docs/
│   └── index.html            ← Landing page (GitHub Pages)
├── agents/
│   ├── forensic_agent.md     ← Per-module AI behaviour rules
│   ├── output_agent.md       ← Report rendering rules
│   └── neuro_agent.md        ← Brain module rules
└── samples/
    ├── chest_normal.jpg
    ├── chest_suspicious.jpg
    ├── chest_critical.jpg
    ├── brain_normal.jpg
    ├── brain_suspicious.jpg
    ├── body_normal.jpg
    ├── body_trauma.jpg
    ├── tox_normal.txt
    ├── tox_suspicious.txt
    └── tox_critical.txt
```

---

## Disclaimer

> AI screening only. NeuroForensic AI requires expert validation and must not be used as a standalone medical, legal, or cause-of-death decision system.
