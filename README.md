# 📊 CSV Data Analyzer

A strong, portfolio-ready CSV analysis dashboard built with **Python, Pandas, Streamlit and Plotly**.

## Features

- CSV upload with encoding and delimiter controls
- Automatic dataset profiling
- Row/column counts
- Missing-value analysis
- Duplicate detection
- Data-type analysis
- Numeric statistics
- Categorical summaries
- Search across the dataset
- Multi-column categorical filtering
- Histogram
- Box plot
- Scatter plot with color and size controls
- Bar chart
- Line chart
- Area chart
- Pearson correlation heatmap
- IQR-based outlier detection
- Missing-value cleaning strategies
- Duplicate removal
- Date conversion
- CSV export
- Column-profile export
- JSON analysis summary
- Self-contained HTML report

## Project Structure

```text
CSV Data Analyzer/
├── app.py
├── requirements.txt
├── README.md
└── src/
    ├── __init__.py
    ├── analyzer.py
    └── report.py
```

## Windows Setup

Open PowerShell in the project folder.

### 1. Create virtual environment

```powershell
py -3.10 -m venv .venv
```

If `py -3.10` is unavailable:

```powershell
python -m venv .venv
```

### 2. Activate

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run

```powershell
streamlit run app.py
```

The browser should open the Streamlit application.

## If port 8501 is busy

```powershell
streamlit run app.py --server.port 8502
```

## Important

Do not name your own Python files:

- `pandas.py`
- `streamlit.py`
- `plotly.py`
- `numpy.py`

because these names can conflict with installed packages.

## Recommended Python

Python 3.10 or 3.11 is recommended for a stable local setup.

## Portfolio Description

**CSV Data Analyzer** is an interactive data analytics platform that allows users to upload CSV datasets, automatically profile data quality, explore statistics, visualize distributions and relationships, detect outliers, clean missing data, and export analysis reports. The application demonstrates practical data-analysis skills using Pandas and interactive visualization with Plotly inside a Streamlit dashboard.
