# core/analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io, base64


def compute_ci_multitarget(raw_df, params, target_dt, ci_levels=[0.3, 0.6, 0.9]):
    """
    Tạo dataframe dự đoán + các khoảng tin cậy từ dữ liệu quá khứ.
    raw_df: historical data (many years back)
    params: variables list
    target_dt: target datetime
    ci_levels: list like [0.3,0.6,0.9]
    """
    hours = range(24)
    pred_dt_index = [
        target_dt.replace(hour=h, minute=0, second=0, microsecond=0) for h in hours
    ]
    ci_dict = {"datetime": pred_dt_index}

    for p in params:
        for h in hours:
            values = raw_df[raw_df["hour"] == h][p].dropna()
            if len(values) == 0:
                values = pd.Series([0])
            for ci in ci_levels:
                lower = np.percentile(values, 50 - ci * 50)
                upper = np.percentile(values, 50 + ci * 50)
                ci_dict.setdefault(f"{p}_low_{int(ci*100)}", []).append(lower)
                ci_dict.setdefault(f"{p}_high_{int(ci*100)}", []).append(upper)
        mean_vals = [raw_df[raw_df["hour"] == h][p].mean() for h in hours]
        ci_dict[p] = mean_vals

    return pd.DataFrame(ci_dict)


def plot_fanmap_base64(ci_df, param, ci_levels=[30, 60, 90]):
    """
    Vẽ fanmap từ ci_df (compute_ci_multitarget).
    """
    if ci_df.empty or param not in ci_df.columns:
        return None

    df = ci_df.copy()
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


def summarize_and_fanmaps(raw_df, params, target_dt):
    ci_df = compute_ci_multitarget(raw_df, params, target_dt)
    fanmaps = {}
    for p in params:
        b64 = plot_fanmap_base64(ci_df, p)
        fanmaps[p] = b64
    return {"ci_df": ci_df, "fanmaps": fanmaps}
