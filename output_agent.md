# output_agent.md — Report Card Output Agent

## Identity
**Role:** Forensic Report Renderer
**Purpose:** Transform JSON from forensic_agent into clean Streamlit UI
**Validates:** Schema before rendering. Rejects malformed responses.

---

## Severity Color Map (Never Change)

| Value | Background | Text | Badge Label |
|---|---|---|---|
| Normal | #E1F5EE | #0F6E56 | No Anomalies Detected |
| Suspicious | #FAEEDA | #633806 | Review Recommended |
| Critical | #FCEBEB | #791F1F | Urgent Review Required |

---

## Report Card Structure

Render in this exact order:
1. Severity badge (colored)
2. Module name + dataset source
3. Metrics row: Anomalies / Confidence / Region
4. Findings list
5. Investigator Action (info box)
6. Disclaimer (warning box — ALWAYS LAST)

---

## Streamlit Render Function

```python
def render_report(result: dict):
    severity = result.get("severity", "Normal")
    colors = {
        "Normal":     {"bg": "#E1F5EE", "text": "#0F6E56", "label": "No Anomalies Detected"},
        "Suspicious": {"bg": "#FAEEDA", "text": "#633806", "label": "Review Recommended"},
        "Critical":   {"bg": "#FCEBEB", "text": "#791F1F", "label": "Urgent Review Required"},
    }
    c = colors.get(severity, colors["Normal"])

    st.markdown(f"""
    <div style='background:{c["bg"]};color:{c["text"]};padding:8px 18px;
    border-radius:8px;display:inline-block;font-weight:500;
    font-size:14px;margin-bottom:16px'>{c["label"]}</div>
    """, unsafe_allow_html=True)

    st.subheader(f"Forensic Screening Report — {result.get('module','')}")
    st.caption(f"Dataset grounding: {result.get('dataset_source','Unknown')}")
    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Anomalies", "Yes" if result.get("anomalies_detected") else "No")
    col2.metric("Confidence", result.get("confidence", "Unknown"))
    col3.metric("Region", result.get("region", "Unknown"))

    st.divider()
    st.markdown("**Findings**")
    findings = result.get("findings", [])
    if findings:
        for f in findings:
            st.markdown(f"- {f}")
    else:
        st.markdown("- No visual anomalies detected.")

    st.divider()
    st.markdown("**Investigator Action**")
    st.info(result.get("investigator_action", "No action specified."))
    st.warning(f"⚠ {result.get('disclaimer','AI screening only. Expert review required.')}")
```

---

## Validation Rules

```python
def validate_result(result: dict) -> bool:
    required = [
        "module", "anomalies_detected", "findings",
        "region", "severity", "investigator_action",
        "confidence", "dataset_source", "disclaimer"
    ]
    valid_severities  = ["Normal", "Suspicious", "Critical"]
    valid_confidences = ["Low", "Medium", "High"]

    for k in required:
        if k not in result:
            return False
    if result["severity"] not in valid_severities:
        return False
    if result["confidence"] not in valid_confidences:
        return False
    if not isinstance(result["findings"], list):
        return False
    return True
```

On validation failure:
- Show: st.error("Report generation failed. AI returned unexpected format. Please retry.")
- Never show raw JSON to user
- Never crash the app

---

## Page Header (Always Show)
```python
st.title("NeuroForensic AI")
st.caption("Multi-Modal Death Investigation Assistant | Healthcare Track | Hackathon Demo")
st.caption("Decision-support prototype. Not for clinical or legal use.")
```

## Page Footer (Always Show)
```python
st.markdown("---")
st.caption(
    "For demonstration purposes only. "
    "NeuroForensic AI does not replace qualified forensic pathologists. "
    "All outputs require expert validation. "
    "No real patient data is used or stored. "
    "Datasets: NIH ChestX-ray14, BraTS 2023, RSNA, MIMIC-IV, EEG-ImageNet, INTERPOL DVI."
)
```
