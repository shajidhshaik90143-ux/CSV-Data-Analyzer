
import io
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.analyzer import (
    profile_dataframe,
    detect_outliers,
    numeric_summary,
    categorical_summary,
    correlation_matrix,
    clean_dataframe,
    suggest_columns,
)
from src.report import build_html_report

st.set_page_config(
    page_title="CSV Data Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main-title {font-size: 2.3rem; font-weight: 800; margin-bottom: 0.1rem;}
.sub-title {color: #64748b; margin-bottom: 1.5rem;}
.metric-card {padding: 1rem; border-radius: 12px; border: 1px solid #e2e8f0;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 CSV Data Analyzer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Upload a CSV and explore quality, statistics, relationships, outliers, and interactive visualizations.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Analyzer Settings")
    uploaded = st.file_uploader("Upload CSV file", type=["csv"])
    encoding = st.selectbox("Encoding", ["utf-8", "utf-8-sig", "latin-1", "cp1252"])
    separator = st.selectbox("Delimiter", ["Auto", ",", ";", "\t", "|"])
    st.divider()
    st.caption("CSV Data Analyzer • Streamlit + Pandas + Plotly")

if uploaded is None:
    st.info("👈 Upload a CSV file from the sidebar to begin.")
    st.markdown("""
### Included features
- Dataset overview and data-quality profiling
- Missing-value and duplicate analysis
- Automatic numeric/categorical/date column suggestions
- Interactive distributions, scatter plots, box plots and correlation heatmap
- IQR-based outlier detection
- Search and multi-column filtering
- Data cleaning with missing-value strategies
- CSV export and self-contained HTML report
- Responsive Streamlit dashboard
""")
    st.stop()

try:
    raw = uploaded.getvalue()
    sep = None if separator == "Auto" else separator
    df = pd.read_csv(io.BytesIO(raw), encoding=encoding, sep=sep, engine="python")
except Exception as exc:
    st.error(f"Could not read the CSV: {exc}")
    st.stop()

if df.empty:
    st.warning("The uploaded CSV contains no rows.")
    st.stop()

suggestions = suggest_columns(df)
profile = profile_dataframe(df)

with st.sidebar:
    st.success(f"Loaded {len(df):,} rows × {len(df.columns):,} columns")
    st.write("**Detected columns**")
    st.write(f"Numeric: `{len(suggestions['numeric'])}`")
    st.write(f"Categorical: `{len(suggestions['categorical'])}`")
    st.write(f"Date-like: `{len(suggestions['date'])}`")

tabs = st.tabs([
    "📌 Overview",
    "🔍 Data Explorer",
    "📈 Visualizations",
    "🔗 Correlations",
    "🚨 Outliers",
    "🧹 Data Cleaning",
    "📤 Export",
])

with tabs[0]:
    st.subheader("Dataset Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Columns", f"{len(df.columns):,}")
    c3.metric("Missing Cells", f"{int(df.isna().sum().sum()):,}")
    c4.metric("Duplicates", f"{int(df.duplicated().sum()):,}")
    c5.metric("Memory", f"{df.memory_usage(deep=True).sum()/1024**2:.2f} MB")

    st.subheader("Column Profile")
    st.dataframe(profile, use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        miss = df.isna().sum().sort_values(ascending=False)
        miss = miss[miss > 0]
        if len(miss):
            fig = px.bar(
                x=miss.index, y=miss.values,
                labels={"x": "Column", "y": "Missing Values"},
                title="Missing Values by Column",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No missing values detected.")
    with right:
        type_counts = df.dtypes.astype(str).value_counts().reset_index()
        type_counts.columns = ["dtype", "count"]
        fig = px.pie(type_counts, names="dtype", values="count", title="Column Data Types")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Preview")
    st.dataframe(df.head(100), use_container_width=True, height=350)

with tabs[1]:
    st.subheader("Interactive Data Explorer")
    query = st.text_input("Search across all columns", placeholder="Type a value to search...")
    filtered = df.copy()

    if query:
        mask = filtered.astype(str).apply(
            lambda col: col.str.contains(query, case=False, na=False, regex=False)
        ).any(axis=1)
        filtered = filtered[mask]

    filterable = [c for c in df.columns if df[c].nunique(dropna=True) <= 100]
    selected_filter_cols = st.multiselect(
        "Columns to filter", filterable, default=filterable[:3]
    )

    for col in selected_filter_cols:
        vals = df[col].dropna().unique().tolist()
        if len(vals) <= 100:
            selected = st.multiselect(f"{col}", vals)
            if selected:
                filtered = filtered[filtered[col].isin(selected)]

    st.caption(f"Showing {len(filtered):,} of {len(df):,} rows")
    st.dataframe(filtered, use_container_width=True, height=500)

with tabs[2]:
    st.subheader("Interactive Visualizations")
    cols = list(df.columns)

    chart_type = st.selectbox(
        "Chart type",
        ["Histogram", "Box Plot", "Scatter Plot", "Bar Chart", "Line Chart", "Area Chart"],
    )

    numeric = suggestions["numeric"]
    categorical = suggestions["categorical"] or cols

    if chart_type == "Histogram":
        if not numeric:
            st.warning("No numeric columns available.")
        else:
            x = st.selectbox("Numeric column", numeric)
            bins = st.slider("Bins", 5, 100, 30)
            fig = px.histogram(df, x=x, nbins=bins, marginal="box", title=f"Distribution of {x}")
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Box Plot":
        if not numeric:
            st.warning("No numeric columns available.")
        else:
            y = st.selectbox("Numeric column", numeric)
            group = st.selectbox("Optional group column", ["None"] + categorical)
            fig = px.box(
                df, y=y,
                x=None if group == "None" else group,
                points="outliers",
                title=f"Box Plot: {y}",
            )
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Scatter Plot":
        if len(numeric) < 2:
            st.warning("At least two numeric columns are required.")
        else:
            x = st.selectbox("X axis", numeric)
            y = st.selectbox("Y axis", [c for c in numeric if c != x])
            color = st.selectbox("Color by", ["None"] + categorical)
            size = st.selectbox("Size by", ["None"] + numeric)
            fig = px.scatter(
                df,
                x=x,
                y=y,
                color=None if color == "None" else color,
                size=None if size == "None" else size,
                hover_data=cols[:min(6, len(cols))],
                title=f"{y} vs {x}",
            )
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Bar Chart":
        cat = st.selectbox("Category", categorical)
        agg_options = ["Count"] + numeric
        metric = st.selectbox("Metric", agg_options)
        grouped = (
            df[cat].value_counts(dropna=False).head(30).reset_index()
            if metric == "Count"
            else df.groupby(cat, dropna=False)[metric].mean().sort_values(ascending=False).head(30).reset_index()
        )
        if metric == "Count":
            grouped.columns = [cat, "Count"]
            fig = px.bar(grouped, x=cat, y="Count", title=f"Count by {cat}")
        else:
            fig = px.bar(grouped, x=cat, y=metric, title=f"Average {metric} by {cat}")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type in ["Line Chart", "Area Chart"]:
        x = st.selectbox("X axis", cols)
        y = st.selectbox("Y axis", numeric if numeric else cols)
        plot_df = df[[x, y]].dropna().sort_values(x).head(5000)
        fig = px.line(plot_df, x=x, y=y, title=f"{y} over {x}")
        if chart_type == "Area Chart":
            fig.update_traces(fill="tozeroy")
        st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.subheader("Correlation Analysis")
    if len(suggestions["numeric"]) < 2:
        st.warning("At least two numeric columns are required for correlation analysis.")
    else:
        corr = correlation_matrix(df)
        fig = px.imshow(
            corr,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Pearson Correlation Matrix",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(corr.round(3), use_container_width=True)

with tabs[4]:
    st.subheader("Outlier Detection")
    if not suggestions["numeric"]:
        st.warning("No numeric columns available.")
    else:
        out_col = st.selectbox("Column", suggestions["numeric"])
        result = detect_outliers(df, out_col)
        a, b, c = st.columns(3)
        a.metric("Lower Bound", f"{result['lower']:.3f}")
        b.metric("Upper Bound", f"{result['upper']:.3f}")
        c.metric("Outliers", f"{result['count']:,}")
        st.dataframe(result["rows"], use_container_width=True)

        fig = px.box(df, y=out_col, points="outliers", title=f"Outliers: {out_col}")
        st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.subheader("Data Cleaning")
    st.caption("Cleaning creates a new in-memory dataset; your uploaded CSV is never modified.")
    work = df.copy()

    st.write("**Missing-value strategy**")
    strategy = st.selectbox(
        "Choose strategy",
        ["No changes", "Drop rows with missing values", "Fill numeric with median", "Fill numeric with mean", "Fill all with mode"],
    )
    if strategy != "No changes":
        if strategy == "Drop rows with missing values":
            work = work.dropna()
        elif strategy == "Fill numeric with median":
            for col in work.select_dtypes(include="number").columns:
                work[col] = work[col].fillna(work[col].median())
        elif strategy == "Fill numeric with mean":
            for col in work.select_dtypes(include="number").columns:
                work[col] = work[col].fillna(work[col].mean())
        elif strategy == "Fill all with mode":
            for col in work.columns:
                mode = work[col].mode(dropna=True)
                if len(mode):
                    work[col] = work[col].fillna(mode.iloc[0])

    remove_dupes = st.checkbox("Remove duplicate rows", value=False)
    if remove_dupes:
        work = work.drop_duplicates()

    convert_dates = st.checkbox("Attempt conversion of date-like columns", value=False)
    if convert_dates:
        for col in suggestions["date"]:
            work[col] = pd.to_datetime(work[col], errors="coerce")

    st.write(f"Original shape: **{df.shape[0]:,} × {df.shape[1]:,}**")
    st.write(f"Cleaned shape: **{work.shape[0]:,} × {work.shape[1]:,}**")
    st.dataframe(work.head(100), use_container_width=True)

with tabs[6]:
    st.subheader("Export & Report")
    st.write("Download the currently loaded dataset, a profile report, or a self-contained HTML analysis report.")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Original CSV",
        data=csv_bytes,
        file_name="analyzed_dataset.csv",
        mime="text/csv",
    )

    profile_csv = profile.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Column Profile",
        data=profile_csv,
        file_name="column_profile.csv",
        mime="text/csv",
    )

    html = build_html_report(df, profile)
    st.download_button(
        "📄 Download HTML Report",
        data=html.encode("utf-8"),
        file_name="csv_analysis_report.html",
        mime="text/html",
    )

    export_json = {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_columns": suggestions["numeric"],
        "categorical_columns": suggestions["categorical"],
        "date_columns": suggestions["date"],
    }
    st.download_button(
        "🧾 Download Analysis Summary JSON",
        data=json.dumps(export_json, indent=2).encode("utf-8"),
        file_name="analysis_summary.json",
        mime="application/json",
    )
