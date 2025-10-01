from typing import List
from datetime import datetime

import numpy as np
import pandas as pd
import seaborn as sns
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from core.thresholds import PARAM_THRESHOLDS


def compute_ci_multitarget(
    raw_df: pd.DataFrame,
    parameters: List[str],
    target_dt: datetime,
    ci_levels: List[float] = [0.3, 0.6, 0.9],
) -> pd.DataFrame:
    hours = range(24)
    pred_dt_index = [
        target_dt.replace(hour=h, minute=0, second=0, microsecond=0) for h in hours
    ]
    ci_dict = {"datetime": pred_dt_index}

    for parameter in parameters:
        for h in hours:
            values = raw_df[raw_df["hour"] == h][parameter].dropna()
            if len(values) == 0:
                values = pd.Series([0])
            for ci in ci_levels:
                lower = np.percentile(values, 50 - ci * 50)
                upper = np.percentile(values, 50 + ci * 50)
                ci_dict.setdefault(f"{parameter}_low_{int(ci * 100)}", []).append(lower)
                ci_dict.setdefault(f"{parameter}_high_{int(ci * 100)}", []).append(
                    upper
                )
        mean_vals = [raw_df[raw_df["hour"] == h][parameter].mean() for h in hours]
        ci_dict[parameter] = mean_vals

    return pd.DataFrame(ci_dict)


def plot_fanmap(
    pred_df: pd.DataFrame, parameter: str, ci_levels: List[float] = [30, 60, 90]
):
    plt.figure(figsize=(12, 5))
    x = pred_df["datetime"]

    for ci in sorted(ci_levels, reverse=True):
        plt.fill_between(
            x,
            pred_df[f"{parameter}_low_{ci}"],
            pred_df[f"{parameter}_high_{ci}"],
            alpha=0.3 * (ci / 90),
            label=f"{ci}% CI",
        )

    plt.plot(x, pred_df[parameter], color="black", linewidth=2, label="Mean")

    plt.xlabel("Hour")
    plt.ylabel(parameter)
    plt.title(f"Fan Map for {parameter} on {x[0].date()}")
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.show()


def prepare_plotly_fanmap_with_vbands_v2(
    pred_df: pd.DataFrame, parameter, ci_levels=[30, 60, 90]
):
    sns.set_style("whitegrid")
    colors = sns.color_palette("Set2", len(ci_levels))
    x = pred_df["datetime"].astype(str).tolist()
    x_dt = pred_df["datetime"]  # giữ dạng datetime
    traces = []

    # CI bands
    for idx, ci in enumerate(sorted(ci_levels, reverse=True)):
        low = pred_df[f"{parameter}_low_{ci}"].tolist()
        high = pred_df[f"{parameter}_high_{ci}"].tolist()
        traces.append(
            go.Scatter(
                x=x + x[::-1],
                y=low + high[::-1],
                fill="toself",
                fillcolor=f"rgba({int(colors[idx][0]*255)}, {int(colors[idx][1]*255)}, {int(colors[idx][2]*255)}, 0.3)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                name=f"{ci}% CI",
            )
        )

    # Mean line
    mean_vals = pred_df[parameter].tolist()
    traces.append(
        go.Scatter(
            x=x,
            y=mean_vals,
            mode="lines+markers",
            line=dict(color="black", width=2),
            name="Mean",
            hovertemplate=f"Time: %{{x}}<br>{parameter}: %{{y:.2f}}<extra></extra>",
        )
    )

    fig = go.Figure(data=traces)

    # --- Beaufort classes ---
    thresholds = PARAM_THRESHOLDS[parameter]

    def classify(val):
        for threshold in thresholds:
            if threshold["y0"] <= val <= threshold["y1"]:
                return threshold
        return None

    # Gom các đoạn liên tiếp cùng loại gió
    bands = []
    current_class = None
    x0 = None

    for i, val in enumerate(mean_vals):
        cls = classify(val)
        if cls != current_class:
            if current_class is not None:
                bands.append((x0, x_dt[i], current_class))
            current_class = cls
            x0 = x_dt[i]
    if current_class is not None:
        bands.append((x0, x_dt.iloc[-1], current_class))

    # Vẽ các vrect gom nhóm theo Beaufort
    for x0, x1, threshold in bands:
        fig.add_vrect(
            x0=x0,
            x1=x1,
            fillcolor=threshold["color"],
            opacity=0.45,  # tăng độ đậm
            layer="below",
            line_width=0,
            annotation_text=threshold["label"],
            annotation_position="top left",
            annotation=dict(font_size=9, font_color="black"),
        )

    # Thêm legend (trace ẩn cho mỗi loại gió)
    for threshold in thresholds:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(size=10, color=threshold["color"]),
                name=threshold["label"],
            )
        )

    # --- Local maxima / minima ---
    y = np.array(mean_vals)
    maxima = np.r_[False, (y[1:-1] > y[:-2]) & (y[1:-1] > y[2:]), False]
    minima = np.r_[False, (y[1:-1] < y[:-2]) & (y[1:-1] < y[2:]), False]

    fig.add_trace(
        go.Scatter(
            x=np.array(x)[maxima],
            y=y[maxima],
            mode="markers",
            marker=dict(color="red", size=10, symbol="circle"),
            name="Max",
            hovertemplate=f"Time: %{{x}}<br>{parameter}: %{{y:.2f}}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=np.array(x)[minima],
            y=y[minima],
            mode="markers",
            marker=dict(color="blue", size=10, symbol="circle"),
            name="Min",
            hovertemplate=f"Time: %{{x}}<br>{parameter}: %{{y:.2f}}<extra></extra>",
        )
    )

    # Layout
    fig.update_layout(
        title=f"Fan Map for {parameter} on {x[0].split()[0]}",
        xaxis_title="Time",
        yaxis_title=parameter,
        template="simple_white",
    )

    # Hiển thị lưới
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")

    # fig.show()
    return fig


def plot_fanmap_plotly(pred_df, param, ci_levels=[30, 60, 90]):
    fig = prepare_plotly_fanmap_with_vbands_v2(pred_df, param, ci_levels)

    html_str = fig.to_html(full_html=False, include_plotlyjs="cdn")
    fig_dict = fig.to_dict()

    return html_str, fig_dict
