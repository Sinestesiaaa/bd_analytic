# Breakdown Analytics Project

Python + Streamlit project for heavy equipment breakdown analysis.

## Structure

```text
project_breakdown/
  data/
    raw/        <- put input Excel files here
    clean/
    master/
  scripts/
    cleaning.py
    classify.py
    analytics.py
    visualization.py
    utils.py
  app.py
  requirements.txt
```

## Quick Start

1. Create environment and install dependencies:
   - `pip install -r requirements.txt`
2. Put your Excel files into `data/raw/`.
3. Run dashboard:
   - `streamlit run app.py`

## Current Features

- Multi-file Excel load
- Time cleaning and cross-midnight duration handling
- Duration validation (`Duration_Real` and `Duration_Check`)
- Automatic category classification
- KPI summary
- Plotly charts and timeline
- Streamlit filter sidebar

