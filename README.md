# NeuroForensic AI
### Multi-Modal Death Investigation Assistant

> **Hackathon Track: Build with Healthcare**  
> AI-powered forensic screening for investigators — structured reports in under 60 seconds.

---

## The Problem

| Statistic | Scale |
|---|---|
| Deaths uninvestigated globally per year | **2,000,000+** |
| Forensic pathologists per 100 million people | **~150** |
| Average wait time for specialist review | **Days to weeks** |
| Investigators with access to forensic AI tools | **Near zero** |

Investigators in low-resource settings have no fast, unified tool to get a structured first-look across body evidence, brain scans, and toxicology simultaneously. Cases go cold. Families get no answers.

---

## The Solution

**NeuroForensic AI** gives any investigator, anywhere, a structured forensic screening report in under **60 seconds** — from a laptop, no specialist required on-site.

- Upload a medical scan, crime scene photo, or paste a lab report
- AI analyzes it against real public clinical datasets
- Returns a structured JSON report with findings, severity, and recommended actions
- All outputs include mandatory expert-review disclaimers

---

## 6 Forensic Modules

### 🫁 Module 1 — Chest X-ray
- **Detects:** Lung opacity, pleural fluid, pneumothorax, rib fractures, mediastinal widening, structural asymmetry
- **Dataset:** NIH ChestX-ray14 (112,000 labeled chest X-rays, public domain)
- **Input:** JPEG / PNG image
- **Method:** Gemini Flash vision analysis with forensic radiology prompt

### 🧠 Module 2 — Brain MRI / CT
- **Detects:** Abnormal masses, hemorrhage, edema, midline shift, hemispheric asymmetry, density irregularities
- **Dataset:** BraTS 2023 (multi-modal brain MRI, Synapse public access)
- **Input:** JPEG / PNG image
- **Method:** Gemini Flash vision with neuroradiology forensic prompt

### 🦴 Module 3 — Full Body CT
- **Detects:** Fractures, internal bleeding, organ density anomalies, fluid accumulation, soft tissue disruption
- **Dataset:** RSNA Intracranial Hemorrhage Detection (25,000 CT scans, Kaggle public)
- **Input:** JPEG / PNG image
- **Method:** Gemini Flash vision with trauma radiology prompt

### 🧪 Module 4 — Toxicology Report
- **Detects:** Substances above reference thresholds, alcohol levels, opioids, benzodiazepines, stimulants, poisons, poly-substance interactions, overdose risk markers
- **Dataset:** MIMIC-IV Clinical Notes (PhysioNet, free credentialed access)
- **Input:** Plain text `.txt` file or pasted lab report text
- **Method:** Gemini Flash NLP on unstructured lab report text

### 📷 Module 5 — External Trauma Photo
- **Detects:** Ligature marks (location, angle, width, continuity), petechiae, bruise patterns, lacerations, burns, impact wounds, positional lividity
- **Protocol:** INTERPOL DVI (Disaster Victim Identification) standard language
- **Input:** Scene or body photograph (JPEG / PNG)
- **Method:** Gemini Flash vision with INTERPOL-compliant forensic prompt

### ⚡ Module 6 — Brain Pattern Analysis
- **Detects:** Visual cortex (occipital) anomalies, hippocampal asymmetry, diffuse axonal injury indicators, deep brain hemorrhagic patterns, watershed zone changes, brainstem anomalies
- **Scientific Basis:** EEG-ImageNet research (Spampinato et al.) — post-mortem neuroimaging reveals structural residue of pre-death brain state
- **Dataset:** BraTS 2023 + EEG-ImageNet conceptual grounding
- **Input:** Brain MRI / CT image
- **Method:** Specialized neuroscience prompt with pattern-specific analysis

---

## Report Output Format

Every module returns a structured JSON report with these fields:

```json
{
  "module": "Chest X-ray",
  "case_summary": "Diffuse bilateral opacities with cardiomegaly.",
  "anomalies": "Yes",
  "confidence": "Medium",
  "suspected_region": "Bilateral lung fields / cardiac silhouette",
  "key_findings": [
    "Increased opacity in bilateral lower lobes",
    "Cardiomegaly with cardiothoracic ratio > 0.5",
    "No pneumothorax identified"
  ],
  "medical_interpretation": "Findings consistent with pulmonary edema pattern.",
  "forensic_relevance": "Bilateral opacities may warrant toxicological correlation.",
  "differential_considerations": ["Pulmonary edema", "Bilateral pneumonia"],
  "recommended_next_steps": ["Correlate with toxicology report", "Refer to forensic pathologist"],
  "investigator_action": "Escalate to forensic pathologist. Priority: High.",
  "severity": "Suspicious",
  "limitations": "AI screening only — image quality affects confidence.",
  "dataset_source": "NIH ChestX-ray14",
  "disclaimer": "Demo only. Not clinical or legal advice. Expert review required.",
  "visual_annotations": [
    {"label": "Bilateral opacity", "x": 0.5, "y": 0.6, "w": 0.6, "h": 0.3}
  ]
}
```

---

## Severity Classification

| Level | Meaning | Action |
|---|---|---|
| **Normal** | No anomalies detected within observable range | Document and close or correlate with other modules |
| **Suspicious** | Findings warrant specialist review | Escalate to forensic pathologist — non-urgent |
| **Critical** | Urgent findings requiring immediate review | Immediate expert consultation required |

---

## How It Works — Pipeline

```
Investigator Input
       │
       ▼
┌─────────────────────────────────┐
│   Module Selection              │
│   (Chest / Brain / Body /       │
│    Toxicology / Trauma / Neuro) │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   Input Processing              │
│   Image → resize + base64       │
│   Text  → direct pass-through   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   Gemini 2.5 Flash              │
│   (vision + text)               │
│   Module-specific system prompt │
│   Returns: strict JSON only     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   JSON Validation + Parsing     │
│   Fallback if API unavailable   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   PIL Image Annotation          │
│   Bounding boxes on findings    │
│   Original vs AI-marked view    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   Structured Report Card        │
│   Severity badge                │
│   Stat cards + Region           │
│   Findings / Interpretation     │
│   Differentials / Next Steps    │
│   Investigator Action           │
│   Disclaimer (always present)   │
└─────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **UI Framework** | Streamlit (Python) |
| **AI Provider** | Google Gemini 2.5 Flash (vision + text) |
| **Image Processing** | Pillow (PIL) — annotation + compression |
| **HTTP Client** | Requests |
| **Environment** | Python-dotenv |
| **Language** | Python 3.10+ |

No heavyweight ML frameworks (PyTorch, TensorFlow) required at runtime. The app uses Gemini's API for all inference — lightweight deployment.

---

## Dataset References

| Dataset | Source | Size | License |
|---|---|---|---|
| NIH ChestX-ray14 | nihcc.app.box.com/v/ChestXray-NIHCC | 112,120 images | Public domain |
| BraTS 2023 | synapse.org/#!Synapse:syn51156910 | Multi-modal MRI | Free academic |
| RSNA Hemorrhage | kaggle.com/c/rsna-intracranial-hemorrhage-detection | 25,000 CT scans | Kaggle public |
| MIMIC-IV | physionet.org/content/mimiciv | 300,000+ records | Credentialed |
| EEG-ImageNet | github.com/perceivelab/eeg_visual_classification | EEG + visual | Research |
| INTERPOL DVI | interpol.int/How-we-work/Forensics/DVI | Protocol standard | Public |

---

## Quickstart

### Prerequisites
- Python 3.10+
- Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/Srimonchaari/neuroforensic-ai.git
cd neuroforensic-ai

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
cp .env.example .env
# Edit .env and set:
# GEMINI_API_KEY=AIza...

# 5. Download / create demo samples
python download_samples.py

# 6. Run the app
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

### Streamlit Cloud Deployment

Add `GEMINI_API_KEY` to your app's **Secrets** in the Streamlit Cloud dashboard:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "AIza..."
```

---

## Project Structure

```
neuroforensic-ai/
├── app.py                  ← Main Streamlit application (all 6 modules)
├── download_samples.py     ← Fetches demo images + creates tox text samples
├── requirements.txt        ← Python dependencies
├── .env.example            ← API key template
├── CLAUDE.md               ← AI grounding document (hallucination prevention rules)
├── README.md               ← This file
├── PRESENTATION.html       ← PDF-ready presentation document
├── agents/
│   ├── forensic_agent.md   ← Per-module AI behavior and system prompt rules
│   ├── output_agent.md     ← Report card rendering rules
│   └── neuro_agent.md      ← Brain pattern module science and rules
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

## Ethical Framework

This tool is a **decision-support prototype only.**

| What it IS | What it is NOT |
|---|---|
| AI-powered forensic screening tool | Clinical diagnostic tool |
| Decision-support for investigators | Legal evidence generator |
| Grounded in public clinical datasets | Trained on private patient data |
| INTERPOL DVI protocol-aligned | Cause-of-death determiner |
| Expert-review disclaimer on every report | Replacement for forensic pathologists |

**Hallucination prevention rules built into every prompt:**
- Never name specific diseases or syndromes
- Never state or imply cause of death
- Never invent patient demographics
- Never claim certainty — uses "consistent with", "suggests", "warrants review"
- Always include expert-review disclaimer
- Only describe what is visually or textually observable

---

## Limitations

- Image quality directly affects analysis confidence
- AI vision is not trained on forensic images specifically — uses general medical vision capabilities
- Toxicology analysis depends on report format and completeness
- Brain Pattern Analysis module is conceptual — not a validated clinical tool
- All outputs are screening-level only — not diagnostic
- Free tier: 15 requests/minute, 1,500 requests/day (Gemini)

---

## Future Scope

- [ ] Fine-tuned forensic-specific vision model
- [ ] Mobile app for on-scene field investigators
- [ ] Real EEG hardware integration (BCI signal → image prediction)
- [ ] Multi-case batch processing
- [ ] INTERPOL DVI system integration
- [ ] WHO Digital Health deployment partnership
- [ ] Offline mode for low-connectivity environments
- [ ] Voice-guided investigator workflow

---

## Author

**Aman** — Healthcare AI Hackathon  
Built with Google Gemini Flash · Streamlit · Python · PIL

---

*For demonstration purposes only. NeuroForensic AI does not replace qualified forensic pathologists. All outputs require expert validation before any action. No real patient data is used or stored.*
