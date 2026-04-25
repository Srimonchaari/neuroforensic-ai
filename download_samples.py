"""
download_samples.py — Downloads REAL public-domain medical images for NeuroForensic AI.

Sources (all verified accessible):
  Chest X-ray: ieee8023/covid-chestxray-dataset (GitHub, CC BY 4.0)
  Brain MRI:   nipy/nibabel fMRI test data — real 128×96 brain scan (MIT)
  Body CT:     ieee8023/covid-chestxray-dataset axial CT subset (CC BY 4.0)
  Toxicology:  Text samples already in samples/ (MIMIC-IV reference format)

Usage:
  pip install requests nibabel numpy Pillow
  python download_samples.py
"""

import os
import tempfile
import time
from pathlib import Path

import requests
from PIL import Image

Path("samples").mkdir(exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
})

MIN_BYTES = 10_000
CHEST_BASE = "https://raw.githubusercontent.com/ieee8023/covid-chestxray-dataset/master/images/"

DIRECT_IMAGES = [
    # ── Chest X-ray (PA view, real clinical images, CC BY 4.0) ──────────────
    (
        "samples/chest_normal.jpg",
        CHEST_BASE + "F051E018-DAD1-4506-AD43-BE4CA29E960B.jpeg",
        "Chest X-ray — Normal PA view",
        "ieee8023/covid-chestxray-dataset · No Finding · CC BY 4.0",
    ),
    (
        "samples/chest_suspicious.jpg",
        CHEST_BASE + "covid-19-pneumonia-15-PA.jpg",
        "Chest X-ray — Bilateral pneumonia (suspicious)",
        "ieee8023/covid-chestxray-dataset · Pneumonia/Viral · CC BY 4.0",
    ),
    (
        "samples/chest_critical.jpg",
        CHEST_BASE + "covid-19-pneumonia-12.jpg",
        "Chest X-ray — Severe bilateral pneumonia (critical)",
        "ieee8023/covid-chestxray-dataset · Pneumonia/Viral · CC BY 4.0",
    ),
    # ── Full Body CT (axial thoracic CT, CC BY 4.0) ──────────────────────────
    (
        "samples/body_normal.jpg",
        CHEST_BASE + "jkms-35-e79-g001-l-d.jpg",
        "Body CT — Axial thoracic CT",
        "ieee8023/covid-chestxray-dataset · Axial CT · CC BY 4.0",
    ),
    (
        "samples/body_trauma.jpg",
        CHEST_BASE + "1-s2.0-S0929664620300449-gr3_lrg-a.jpg",
        "Body CT — Axial CT with ground-glass opacity",
        "ieee8023/covid-chestxray-dataset · Axial CT · CC BY 4.0",
    ),
]


def download_image(dest, url, label, source):
    path = Path(dest)
    if path.exists() and path.stat().st_size > MIN_BYTES:
        print(f"  Already exists: {dest}")
        return True
    print(f"  Downloading: {label} ...")
    try:
        r = SESSION.get(url, timeout=30)
        r.raise_for_status()
        if len(r.content) < MIN_BYTES:
            print(f"  FAILED: response too small ({len(r.content)} bytes)")
            return False
        path.write_bytes(r.content)
        print(f"  Saved: {dest}  ({path.stat().st_size // 1024} KB)")
        print(f"         Source: {source}")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def download_brain_mri():
    """
    Downloads real brain fMRI NIfTI (128×96 px) from nipy/nibabel test data
    and extracts two JPEG slices — one normal mid-slice, one deeper slice.
    """
    normal_path = Path("samples/brain_normal.jpg")
    suspicious_path = Path("samples/brain_suspicious.jpg")

    if (normal_path.exists() and suspicious_path.exists()
            and normal_path.stat().st_size > MIN_BYTES
            and suspicious_path.stat().st_size > MIN_BYTES):
        print("  Already exists: samples/brain_normal.jpg")
        print("  Already exists: samples/brain_suspicious.jpg")
        return True

    try:
        import nibabel as nib
        import numpy as np
    except ImportError:
        print("  FAILED: nibabel/numpy not installed.")
        print("  Run: pip install nibabel numpy")
        return False

    url = "https://raw.githubusercontent.com/nipy/nibabel/master/nibabel/tests/data/example4d.nii.gz"
    print("  Downloading: Brain fMRI NIfTI (nipy/nibabel, real 128×96 scan) ...")
    try:
        r = SESSION.get(url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  FAILED fetching NIfTI: {e}")
        return False

    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as f:
        f.write(r.content)
        tmp = f.name

    try:
        img = nib.load(tmp)
        data = img.get_fdata()          # shape (128, 96, 24, 2)
        vol = data[:, :, :, 0]         # first volume

        def save_slice(arr, out_path):
            arr = arr.astype(float)
            arr -= arr.min()
            if arr.max() > 0:
                arr /= arr.max()
            pil = Image.fromarray((arr * 255).astype("uint8")).convert("L")
            pil = pil.resize((400, 400), Image.LANCZOS)
            pil.save(out_path, "JPEG", quality=90)

        mid = vol.shape[2] // 2
        save_slice(vol[:, :, mid].T,       normal_path)
        save_slice(vol[:, :, mid + 4].T,   suspicious_path)

        print(f"  Saved: samples/brain_normal.jpg   — real fMRI slice z={mid}")
        print(f"  Saved: samples/brain_suspicious.jpg — real fMRI slice z={mid+4}")
        print("         Source: nipy/nibabel test data · MIT license")
        return True
    except Exception as e:
        print(f"  FAILED processing NIfTI: {e}")
        return False
    finally:
        os.unlink(tmp)


TOX_SAMPLES = {
    "samples/tox_normal.txt": """\
SYNTHETIC DEMO TOXICOLOGY REPORT — NOT REAL PATIENT DATA
Case ID: DEMO-TOX-001
Specimen Type: Postmortem Blood, Central (femoral)

============================================================
TOXICOLOGY PANEL RESULTS
============================================================

VOLATILE COMPOUNDS
  Ethanol:              < 0.01 g/dL   [Reference < 0.08 g/dL]   WITHIN NORMAL LIMITS

DRUGS OF ABUSE SCREEN
  Opioids (Screen):     Negative       [Reference: Negative]      WITHIN NORMAL LIMITS
  Benzodiazepines:      Negative       [Reference: Negative]      WITHIN NORMAL LIMITS
  Cocaine Metabolite:   Not detected   [Reference: Not detected]  WITHIN NORMAL LIMITS
  Amphetamines:         Negative       [Reference: Negative]      WITHIN NORMAL LIMITS

THERAPEUTIC DRUGS
  Acetaminophen:        7.4 mcg/mL    [Reference < 20 mcg/mL]   WITHIN NORMAL LIMITS
  Salicylate:           < 2.0 mg/dL   [Reference < 30 mg/dL]    WITHIN NORMAL LIMITS

CARBON MONOXIDE
  Carboxyhemoglobin:    1.1%          [Reference < 5%]           WITHIN NORMAL LIMITS

============================================================
INTERPRETATION
============================================================

No toxic substances detected above established reference thresholds.
No evidence of drug intoxication or toxic exposure at time of death.

Analyst: DEMO SYSTEM | Lab: DEMO FORENSIC TOXICOLOGY LABORATORY
This is SYNTHETIC demo data for AI screening demonstration only.
""",

    "samples/tox_suspicious.txt": """\
SYNTHETIC DEMO TOXICOLOGY REPORT — NOT REAL PATIENT DATA
Case ID: DEMO-TOX-002
Specimen Type: Postmortem Blood, Central + Peripheral

============================================================
TOXICOLOGY PANEL RESULTS
============================================================

VOLATILE COMPOUNDS
  Ethanol:              0.21 g/dL    [Reference < 0.08 g/dL]    ** ELEVATED **

DRUGS OF ABUSE SCREEN / CONFIRMATORY
  Opioids (Screen):     POSITIVE
    Morphine (GC-MS):   180 ng/mL   [Reference < 20 ng/mL]      ** ELEVATED **
  Benzodiazepines:      POSITIVE
    Diazepam (GC-MS):   420 ng/mL   [Reference < 200 ng/mL]     ** ELEVATED **
  Cocaine Metabolite:   Not detected                             WITHIN NORMAL LIMITS
  Amphetamines:         Negative                                 WITHIN NORMAL LIMITS

THERAPEUTIC DRUGS
  Acetaminophen:        14.5 mcg/mL  [Reference < 20 mcg/mL]   WITHIN NORMAL LIMITS
  Salicylate:           8.1 mg/dL    [Reference < 30 mg/dL]    WITHIN NORMAL LIMITS

CARBON MONOXIDE
  Carboxyhemoglobin:    3.1%         [Reference < 5%]           WITHIN NORMAL LIMITS

============================================================
INTERPRETATION
============================================================

Multiple substance interaction detected. Combined CNS depressant effect
from concurrent alcohol + opioids (morphine) + benzodiazepine (diazepam).
Confirmatory GC-MS performed. Expert forensic review strongly recommended.

Analyst: DEMO SYSTEM | Lab: DEMO FORENSIC TOXICOLOGY LABORATORY
This is SYNTHETIC demo data for AI screening demonstration only.
""",

    "samples/tox_critical.txt": """\
SYNTHETIC DEMO TOXICOLOGY REPORT — NOT REAL PATIENT DATA
Case ID: DEMO-TOX-003
Specimen Type: Postmortem Blood (Central + Peripheral) + Vitreous Humor + Urine

============================================================
TOXICOLOGY PANEL RESULTS — CRITICAL FLAGS PRESENT
============================================================

VOLATILE COMPOUNDS
  Ethanol:              0.38 g/dL    [Reference < 0.08 g/dL]    ** CRITICAL — UPPER LETHAL RANGE **

DRUGS OF ABUSE SCREEN / CONFIRMATORY
  Opioids:              POSITIVE
    Fentanyl (LC-MS):   24 ng/mL    [Reference < 2 ng/mL]      ** CRITICAL — LETHAL RANGE **
    Norfentanyl:        9 ng/mL     [Active metabolite]
  Benzodiazepines:      POSITIVE
    Alprazolam:         680 ng/mL   [Reference < 200 ng/mL]    ** CRITICAL **
  Cocaine Metabolite:   POSITIVE
    Benzoylecgonine:    380 ng/mL   [Reference: Not detected]  ** DETECTED **
    Cocaethylene:       95 ng/mL    [EtOH + cocaine adduct]    ** DETECTED **

THERAPEUTIC DRUGS
  Acetaminophen:        310 mcg/mL  [Reference < 20 mcg/mL]   ** CRITICAL — HEPATOTOXIC RANGE **
  Salicylate:           52 mg/dL    [Reference < 30 mg/dL]    ** ELEVATED **

CARBON MONOXIDE
  Carboxyhemoglobin:    24%         [Reference < 5%]           ** ELEVATED — SIGNIFICANT CO EXPOSURE **

============================================================
INTERPRETATION
============================================================

MULTIPLE CRITICAL TOXIC FINDINGS. Poly-substance toxidrome detected.
Concurrent fentanyl + alprazolam + ethanol represents compounded respiratory
depression risk. Acetaminophen at hepatotoxic range. COHb at 24% indicates
significant carbon monoxide exposure requiring scene correlation.

IMMEDIATE expert forensic toxicologist review required.
Causation of death cannot be determined from this report alone.

Analyst: DEMO SYSTEM | Lab: DEMO FORENSIC TOXICOLOGY LABORATORY
This is SYNTHETIC demo data for AI screening demonstration only.
""",
}


def create_tox_samples():
    """Create synthetic demo toxicology text samples if missing."""
    for path, content in TOX_SAMPLES.items():
        p = Path(path)
        if p.exists():
            print(f"  Already exists: {path}")
        else:
            p.write_text(content)
            print(f"  Created: {path}  (synthetic demo data)")


def main():
    print("NeuroForensic AI — Downloading REAL medical demo samples")
    print("=" * 60)
    print("Sources used:")
    print("  Chest X-ray  → ieee8023/covid-chestxray-dataset  (CC BY 4.0)")
    print("  Brain MRI    → nipy/nibabel fMRI test data       (MIT)")
    print("  Body CT      → ieee8023/covid-chestxray-dataset  (CC BY 4.0)")
    print("  Toxicology   → Synthetic demo text (generated locally)")
    print()

    failed = []

    for dest, url, label, source in DIRECT_IMAGES:
        ok = download_image(dest, url, label, source)
        if not ok:
            failed.append(dest)
        time.sleep(0.4)

    print()
    ok = download_brain_mri()
    if not ok:
        failed += ["samples/brain_normal.jpg", "samples/brain_suspicious.jpg"]

    print()
    print("Creating toxicology text samples…")
    create_tox_samples()

    print()
    if failed:
        print(f"  {len(failed)} download(s) failed: {failed}")
        print("  You can still upload your own images directly in the app.")
    else:
        print("  All samples ready.")
    print()
    print("Start the app:  streamlit run app.py")


if __name__ == "__main__":
    main()
