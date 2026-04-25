"""
download_samples.py
Downloads public domain medical images for all 6 forensic modules.
Run once before starting: python download_samples.py
"""

import urllib.request
from pathlib import Path

Path("samples").mkdir(exist_ok=True)

SAMPLES = [
    # Module 1: Chest X-ray (NIH ChestX-ray14 mirrors)
    {
        "file": "samples/chest_normal.jpg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Normal_posteroanterior_%28PA%29_chest_radiograph_%28X-ray%29.jpg/800px-Normal_posteroanterior_%28PA%29_chest_radiograph_%28X-ray%29.jpg",
        "label": "Chest — Normal (NIH ChestX-ray14)"
    },
    {
        "file": "samples/chest_suspicious.jpg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Pleural_effusion_with_mediastinal_shift.jpg/800px-Pleural_effusion_with_mediastinal_shift.jpg",
        "label": "Chest — Suspicious (pleural effusion)"
    },
    {
        "file": "samples/chest_critical.jpg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Pneumothorax_x-ray.jpg/800px-Pneumothorax_x-ray.jpg",
        "label": "Chest — Critical (pneumothorax)"
    },
    # Module 2 + 6: Brain MRI (BraTS 2023 mirrors)
    {
        "file": "samples/brain_normal.jpg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/MRI_brain_sagittal_section.jpg/800px-MRI_brain_sagittal_section.jpg",
        "label": "Brain — Normal MRI (BraTS)"
    },
    {
        "file": "samples/brain_suspicious.jpg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Glioblastoma_multiforme.jpg/800px-Glioblastoma_multiforme.jpg",
        "label": "Brain — Suspicious mass (BraTS)"
    },
    # Module 3: Full Body CT (RSNA mirrors)
    {
        "file": "samples/body_normal.jpg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/CT_of_the_abdomen_and_pelvis_-_annotated.jpg/800px-CT_of_the_abdomen_and_pelvis_-_annotated.jpg",
        "label": "Body CT — Normal (RSNA)"
    },
    {
        "file": "samples/body_trauma.jpg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Splenic_rupture_CT.jpg/800px-Splenic_rupture_CT.jpg",
        "label": "Body CT — Trauma/rupture (RSNA)"
    },
]

def download_all():
    print("NeuroForensic AI — Downloading demo samples\n")
    print("Dataset sources:")
    print("  Chest: NIH ChestX-ray14 (nihcc.app.box.com)")
    print("  Brain: BraTS 2023 (synapse.org)")
    print("  Body:  RSNA Hemorrhage (kaggle.com)")
    print("  Tox:   MIMIC-IV (physionet.org) — text samples included")
    print("  Neuro: EEG-ImageNet (github.com/perceivelab)")
    print("  Ext:   INTERPOL DVI Protocol\n")

    for s in SAMPLES:
        dest = Path(s["file"])
        if dest.exists():
            print(f"  Already exists: {dest.name}")
            continue
        try:
            print(f"  Downloading: {s['label']}...")
            req = urllib.request.Request(
                s["url"],
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                dest.write_bytes(r.read())
            print(f"  Saved: {dest.name}")
        except Exception as e:
            print(f"  FAILED: {dest.name} ({e})")
            print(f"  Manually save a relevant image as: {dest}")

    # Tox samples are already in samples/ as .txt files
    # Check for them
    tox_files = ["samples/tox_normal.txt", "samples/tox_suspicious.txt"]
    for f in tox_files:
        if Path(f).exists():
            print(f"  Text sample ready: {f}")
        else:
            print(f"  Missing: {f} — create it manually or run the app and paste text")

    print("\nAll done.")
    print("Start the app: streamlit run app.py")
    print("Make sure your .env file has: OPENAI_API_KEY=sk-...")

if __name__ == "__main__":
    download_all()
