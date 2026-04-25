# NeuroForensic AI
## Multi-Modal Death Investigation Assistant

> **Healthcare Hackathon Project** — Built by Aman

---

## What It Solves

Over **2 million deaths go uninvestigated globally every year**.
There are only **150 forensic pathologists per 100 million people**.

NeuroForensic AI gives any investigator, anywhere in the world,
a structured forensic screening report in under **60 seconds** —
from a laptop, with no specialist required on-site.

---

## The 6 Modules

| Module | Detects | Dataset |
|---|---|---|
| Chest X-ray | Lung opacity, fluid, structural anomalies | NIH ChestX-ray14 (112,000 images) |
| Brain MRI / CT | Tumor, lesion, mass, midline shift | BraTS 2023 |
| Full Body CT | Trauma, internal bleeding, fractures | RSNA Hemorrhage (25,000 scans) |
| Toxicology Report | Poisoning via NLP on lab report text | MIMIC-IV Clinical Notes |
| External Trauma Photo | Hanging, strangulation, blunt force | INTERPOL DVI Protocol |
| Brain Pattern Analysis | Neurological trauma patterns (EEG-grounded) | BraTS 2023 + EEG-ImageNet |

---

## Tech Stack

- **AI:** OpenAI GPT-4o (vision + text)
- **UI:** Streamlit (Python)
- **Language:** Python 3.9+

---

## Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/neuroforensic-ai
cd neuroforensic-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your OpenAI API key
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-your-key-here

# 4. Download demo samples
python download_samples.py

# 5. Run the app
streamlit run app.py
```

Open: http://localhost:8501

---

## Project Structure

```
neuroforensic-ai/
  app.py                  ← Main Streamlit app (all 6 modules)
  CLAUDE.md               ← AI grounding document (prevents hallucination)
  README.md               ← This file
  requirements.txt
  .env.example
  agents/
    forensic_agent.md     ← Per-module AI behavior + system prompts
    output_agent.md       ← Report card rendering rules
    neuro_agent.md        ← Brain pattern module science + rules
  samples/                ← Demo images and text files
  download_samples.py     ← Fetch demo images from public sources
```

---

## Dataset Sources

1. **NIH ChestX-ray14** — nihcc.app.box.com/v/ChestXray-NIHCC
2. **BraTS 2023** — synapse.org/#!Synapse:syn51156910
3. **RSNA Hemorrhage** — kaggle.com/c/rsna-intracranial-hemorrhage-detection
4. **MIMIC-IV** — physionet.org/content/mimiciv
5. **EEG-ImageNet** — github.com/perceivelab/eeg_visual_classification
6. **INTERPOL DVI** — interpol.int/How-we-work/Forensics/DVI

---

## Ethical Statement

This tool is a **decision-support prototype** only.
- Does NOT replace qualified forensic pathologists
- Does NOT determine cause of death
- Does NOT generate legally admissible evidence
- Uses only public domain anonymized datasets
- Every report includes a mandatory expert review disclaimer

---

## Future Scope

- Mobile app for on-scene investigators
- Fine-tuned forensic model on anonymized case data
- WHO Digital Health initiative deployment
- INTERPOL DVI integration
- Full EEG-to-image live signal integration (BCI hardware)

---

## Author

**Aman** | Healthcare AI Hackathon 2024
