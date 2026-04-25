# CLAUDE.md — NeuroForensic AI
## Multi-Modal Death Investigation Assistant

---

## Project Identity
- **Title:** NeuroForensic AI — Multi-Modal Death Investigation Assistant
- **Track:** Build with Healthcare
- **Author:** Aman
- **AI Provider:** OpenAI API (GPT-4o with vision)
- **Type:** Decision-support forensic screening prototype
- **Stack:** Python, Streamlit, OpenAI API

---

## What This System Solves

Over 2 million deaths go uninvestigated globally every year.
There are only 150 forensic pathologists per 100 million people.
Investigators have no fast, unified tool to get a structured first-look
across body evidence, brain scans, and toxicology simultaneously.

NeuroForensic AI gives any investigator, anywhere, a structured
forensic screening report in under 60 seconds — from a laptop,
with no specialist required on-site.

---

## What This System IS
- AI-powered forensic screening tool for investigators
- Accepts: medical scan images, scene photos, toxicology text
- Returns: structured forensic report with severity + findings + action
- Grounded in 5 real public clinical datasets
- Follows INTERPOL DVI forensic protocol language
- Decision-support tool — NOT a replacement for expert review

## What This System IS NOT
- NOT a clinical diagnostic tool
- NOT a legal evidence generator
- NOT a cause-of-death determiner
- NOT trained on private patient data
- NOT a replacement for forensic pathologists
- NOT fine-tuned — uses GPT-4o vision via prompt engineering

---

## The 6 Modules

### Module 1 — Chest X-ray
- Detects: lung opacity, fluid, structural asymmetry, rib irregularities
- Dataset: NIH ChestX-ray14 (112,000 images, public domain)
- Input: JPEG/PNG image
- API method: GPT-4o vision (image + text)

### Module 2 — Brain MRI / CT
- Detects: tumor mass, lesion, hemispheric asymmetry, midline shift
- Dataset: BraTS 2023 (synapse.org, free academic access)
- Input: JPEG/PNG image
- API method: GPT-4o vision

### Module 3 — Full Body CT
- Detects: internal bleeding, organ irregularities, fractures, soft tissue disruption
- Dataset: RSNA Intracranial Hemorrhage (25,000 CT scans, Kaggle)
- Input: JPEG/PNG image
- API method: GPT-4o vision

### Module 4 — Toxicology Report
- Detects: elevated compounds, multi-substance flags, out-of-range markers
- Dataset: MIMIC-IV clinical notes (PhysioNet, free credentialed access)
- Input: Plain text paste or .txt file
- API method: GPT-4o text (NLP)

### Module 5 — External Trauma Photo
- Detects: ligature mark patterns, bruising distribution, impact wounds, petechiae
- Protocol: INTERPOL DVI (Disaster Victim Identification) standards
- Input: Scene/body photograph (JPEG/PNG)
- API method: GPT-4o vision

### Module 6 — Brain Pattern Analysis (NeuroForensic)
- Detects: hypoxic injury patterns, visual cortex anomalies, hippocampal asymmetry,
  diffuse axonal injury indicators, hemorrhagic deep brain patterns
- Scientific basis: EEG-ImageNet research (brain signal + visual pattern correlation)
- Dataset: BraTS 2023 + EEG-ImageNet conceptual grounding
- Input: Brain MRI/CT image
- API method: GPT-4o vision with specialized neuroscience prompt

---

## Strict Output Contract (ALL Modules)

OpenAI MUST return ONLY valid JSON. No preamble. No explanation. No markdown fences.

```json
{
  "module": "Chest X-ray",
  "anomalies_detected": true,
  "findings": [
    "Increased opacity in right lower lobe",
    "Asymmetry in bilateral lung fields"
  ],
  "region": "Chest / Pulmonary",
  "severity": "Suspicious",
  "investigator_action": "Refer to forensic pathologist. Priority: Medium.",
  "confidence": "Medium",
  "dataset_source": "NIH ChestX-ray14",
  "disclaimer": "AI screening only. All findings require expert forensic review."
}
```

### Field Constraints
| Field | Type | Allowed Values |
|---|---|---|
| module | string | Exact module name |
| anomalies_detected | boolean | true / false |
| findings | array | 1-4 strings, [] if none |
| region | string | Anatomical label |
| severity | string | "Normal" / "Suspicious" / "Critical" |
| investigator_action | string | One sentence, no diagnosis |
| confidence | string | "Low" / "Medium" / "High" |
| dataset_source | string | Named public dataset |
| disclaimer | string | Always present |

---

## Hallucination Prevention Rules

1. NEVER name specific diseases, syndromes, or disorders
2. NEVER state or imply cause of death
3. NEVER invent patient demographics (age, name, gender)
4. NEVER claim certainty — use "consistent with", "suggests", "warrants review"
5. NEVER output text outside the JSON schema
6. NEVER skip the disclaimer field
7. ONLY describe what is visually or textually observable
8. IF image is unclear → severity: Normal, confidence: Low, note image quality
9. IF input is not a medical/forensic image → return findings: ["Input does not appear to be a valid forensic sample"]

---

## Ethical Guardrails
- Disclaimer shown on every report card, no exceptions
- No image storage or logging
- Demo uses public domain datasets only
- Footer states "For demonstration purposes only" on every page
- System prompt explicitly prohibits cause-of-death statements

---

## File Structure
```
neuroforensic-ai/
  app.py                    ← main Streamlit application
  CLAUDE.md                 ← this file
  README.md                 ← GitHub readme
  requirements.txt          ← pip dependencies
  .env.example              ← API key template
  agents/
    forensic_agent.md       ← per-module AI behavior rules
    output_agent.md         ← report card rendering rules
    neuro_agent.md          ← brain pattern module rules
  samples/
    chest_normal.jpg
    chest_suspicious.jpg
    chest_critical.jpg
    brain_normal.jpg
    brain_suspicious.jpg
    body_normal.jpg
    body_trauma.jpg
    tox_normal.txt
    tox_suspicious.txt
  static/
    style.css               ← custom UI styles
  download_samples.py       ← fetch demo images
```

---

## Dataset References (Proof of Real Data)
1. NIH ChestX-ray14 — nihcc.app.box.com/v/ChestXray-NIHCC
2. BraTS 2023 — synapse.org/#!Synapse:syn51156910
3. RSNA Hemorrhage — kaggle.com/c/rsna-intracranial-hemorrhage-detection
4. MIMIC-IV — physionet.org/content/mimiciv
5. EEG-ImageNet — github.com/perceivelab/eeg_visual_classification
6. INTERPOL DVI — interpol.int/How-we-work/Forensics/DVI
