# core/analysis.py
import pandas as pd
import matplotlib.pyplot as plt
import io, base64


def compute_daily_summary(hourly_df):
    """
    hourly_df: DataFrame with 'datetime' and variables.
    Returns dict daily averages; for PRECTOTCORR returns total.
    """
    if hourly_df.empty:
        return {}
    df = hourly_df.copy()
    # ensure datetime
    df["datetime"] = pd.to_datetime(df["datetime"])
    # numeric cols excluding CI cols
    base_vars = [
        c
        for c in df.columns
        if not c.endswith(
            ("_low_30", "_high_30", "_low_60", "_high_60", "_low_90", "_high_90")
        )
        and c != "datetime"
    ]
    # For PRECTOTCORR we compute total (sum) because precip more meaningful as sum
    summary = {}
    for v in base_vars:
        if v == "PRECTOTCORR":
            summary["PRECTOTCORR_total"] = float(df[v].sum())
            summary[v + "_mean"] = float(df[v].mean())
        else:
            summary[v + "_mean"] = float(df[v].mean())
    return summary


def plot_fanmap_base64(hourly_df, param, ci_levels=[30, 60, 90]):
    """
    hourly_df: DataFrame containing columns param and param_low_X, param_high_X.
    Returns base64 PNG string.
    """
    if hourly_df.empty or param not in hourly_df.columns:
        return None

    df = hourly_df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])

    fig, ax = plt.subplots(figsize=(10, 4))
    x = df["datetime"]

    for ci in sorted(ci_levels, reverse=True):
        low_col = f"{param}_low_{ci}"
        high_col = f"{param}_high_{ci}"
        if low_col in df.columns and high_col in df.columns:
            ax.fill_between(
                x, df[low_col], df[high_col], alpha=0.25 * (ci / 90), label=f"{ci}% CI"
            )

    ax.plot(x, df[param], color="black", linewidth=2, label="Mean")
    ax.set_title(f"Fanmap – {param}")
    ax.set_xlabel("Hour")
    ax.set_ylabel(param)
    ax.legend()
    ax.grid(True)
    plt.xticks(rotation=45)

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return b64


def summarize_and_fanmaps(hourly_df, params):
    summary = compute_daily_summary(hourly_df)
    fanmaps = {}
    for p in params:
        b64 = plot_fanmap_base64(hourly_df, p)
        fanmaps[p] = b64
    return {"daily_summary": summary, "fanmaps": fanmaps}
