
import pandas as pd
import numpy as np


def suggest_columns(df):
    numeric = df.select_dtypes(include=np.number).columns.tolist()

    categorical = [
        c for c in df.columns
        if c not in numeric and (
            pd.api.types.is_object_dtype(df[c]) or
            pd.api.types.is_categorical_dtype(df[c]) or
            pd.api.types.is_bool_dtype(df[c])
        )
    ]

    date_cols = []
    for c in df.columns:
        if c in numeric:
            continue
        sample = df[c].dropna().astype(str).head(100)
        if len(sample) >= 3:
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() >= 0.75:
                date_cols.append(c)

    return {"numeric": numeric, "categorical": categorical, "date": date_cols}


def profile_dataframe(df):
    rows = []
    total = len(df)

    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        unique = int(s.nunique(dropna=True))

        if pd.api.types.is_numeric_dtype(s):
            min_v = s.min()
            max_v = s.max()
            mean_v = s.mean()
            median_v = s.median()
        else:
            min_v = max_v = mean_v = median_v = None

        rows.append({
            "Column": col,
            "Data Type": str(s.dtype),
            "Non-Null": int(s.notna().sum()),
            "Missing": missing,
            "Missing %": round((missing / total) * 100, 2) if total else 0,
            "Unique": unique,
            "Unique %": round((unique / total) * 100, 2) if total else 0,
            "Min": min_v,
            "Max": max_v,
            "Mean": mean_v,
            "Median": median_v,
        })

    return pd.DataFrame(rows)


def numeric_summary(df):
    return df.select_dtypes(include=np.number).describe().T.reset_index().rename(columns={"index": "Column"})


def categorical_summary(df):
    rows = []
    for col in df.select_dtypes(exclude=np.number).columns:
        vc = df[col].value_counts(dropna=False).head(10)
        rows.append({
            "Column": col,
            "Unique": int(df[col].nunique(dropna=True)),
            "Top Value": str(vc.index[0]) if len(vc) else "",
            "Top Frequency": int(vc.iloc[0]) if len(vc) else 0,
        })
    return pd.DataFrame(rows)


def correlation_matrix(df):
    return df.select_dtypes(include=np.number).corr()


def detect_outliers(df, column):
    s = pd.to_numeric(df[column], errors="coerce").dropna()
    if s.empty:
        return {"lower": 0, "upper": 0, "count": 0, "rows": df.iloc[0:0]}

    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    mask = pd.to_numeric(df[column], errors="coerce").lt(lower) | pd.to_numeric(df[column], errors="coerce").gt(upper)
    rows = df.loc[mask].copy()

    return {
        "lower": float(lower),
        "upper": float(upper),
        "count": int(mask.sum()),
        "rows": rows,
    }


def clean_dataframe(df, strategy="none", remove_duplicates=False):
    out = df.copy()

    if strategy == "drop":
        out = out.dropna()
    elif strategy == "median":
        for c in out.select_dtypes(include=np.number).columns:
            out[c] = out[c].fillna(out[c].median())
    elif strategy == "mean":
        for c in out.select_dtypes(include=np.number).columns:
            out[c] = out[c].fillna(out[c].mean())
    elif strategy == "mode":
        for c in out.columns:
            mode = out[c].mode(dropna=True)
            if len(mode):
                out[c] = out[c].fillna(mode.iloc[0])

    if remove_duplicates:
        out = out.drop_duplicates()

    return out
