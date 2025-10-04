import json
from typing import List, Dict
from datetime import datetime

import numpy as np
import pandas as pd
import seaborn as sns
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import lightgbm as lgb


with open("core/thresholds.json", "r", encoding="utf-8") as f:
    PARAMETER = json.load(f)


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


def classify_threshold(val: float, thresholds: List[Dict]):
    for threshold in thresholds:
        if float(threshold["lower"]) <= val <= float(threshold["upper"]):
            return threshold

    return None


def plotly_fanmap_one_day(
    pred_df: pd.DataFrame, parameter: str, ci_levels: List[float] = [30, 60, 90]
):
    sns.set_style("whitegrid")
    colors = sns.color_palette("Set2", len(ci_levels))
    x = pred_df["datetime"].astype(str).tolist()
    x_dt = pred_df["datetime"]  # giữ dạng datetime
    traces = []

    # CI segments
    for idx, ci in enumerate(sorted(ci_levels, reverse=True)):
        low = pred_df[f"{parameter}_low_{ci}"].tolist()
        high = pred_df[f"{parameter}_high_{ci}"].tolist()
        traces.append(
            go.Scatter(
                x=x + x[::-1],
                y=low + high[::-1],
                fill="toself",
                fillcolor=f"rgba({int(colors[idx][0] * 255)}, {int(colors[idx][1] * 255)}, {int(colors[idx][2] * 255)}, 0.3)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                name=f"{ci}%",
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
            hovertemplate=f"%{{x}}<br>{PARAMETER[parameter]['name']}: %{{y:.2f}} {PARAMETER[parameter]['unit']} <extra></extra>",
        )
    )

    fig = go.Figure(data=traces)
    thresholds = PARAMETER[parameter]["thresholds"]

    # Gom các đoạn liên tiếp cùng loại gió
    segments = []
    current_class = None
    x0 = None

    for i, val in enumerate(mean_vals):
        cls = classify_threshold(val, thresholds)
        if cls != current_class:
            if current_class is not None:
                segments.append((x0, x_dt[i], current_class))
            current_class = cls
            x0 = x_dt[i]
    if current_class is not None:
        segments.append((x0, x_dt.iloc[-1], current_class))

    # Vẽ các vrect gom nhóm theo Beaufort
    for x0, x1, threshold in segments:
        if x0 == x1:
            x1 += 0.05
        fig.add_vrect(
            x0=x0,
            x1=x1,
            fillcolor=threshold["color"],
            opacity=0.3,  # tăng độ đậm
            layer="below",
            line_width=0,
            annotation_text=threshold["label"],
            annotation_position="top left",
            annotation=dict(font_size=12, font_color="black", font_weight="bold"),
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
            hovertemplate=f"%{{x}}<br>{PARAMETER[parameter]['name']}: %{{y:.2f}} {PARAMETER[parameter]['unit']} <extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=np.array(x)[minima],
            y=y[minima],
            mode="markers",
            marker=dict(color="blue", size=10, symbol="circle"),
            name="Min",
            hovertemplate=f"%{{x}}<br>{PARAMETER[parameter]['name']}: %{{y:.2f}} {PARAMETER[parameter]['unit']} <extra></extra>",
        )
    )

    # Layout
    fig.update_layout(
        title=f"{PARAMETER[parameter]['name']} on {x[0].split()[0]}",
        xaxis_title="Time",
        yaxis_title=f"{PARAMETER[parameter]['name']} ({PARAMETER[parameter]['unit']})",
        template="simple_white",
    )

    # Hiển thị lưới
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor="lightgray")

    return fig


def plot_fanmap_plotly(
    pred_df: pd.DataFrame, parameter: str, ci_levels: List[float] = [30, 60, 90]
):
    fig = plotly_fanmap_one_day(pred_df, parameter, ci_levels)
    return fig.to_dict()


def create_monthly_avg_df(raw_df: pd.DataFrame, parameters: List[str]):
    avg_df = raw_df.groupby(["month"])[parameters].mean().reset_index()
    return avg_df


def plotly_monthly_overview(pred_df: pd.DataFrame, parameter: str):
    sns.set_style("whitegrid")
    x = pred_df["month"].tolist()
    x_dt = pred_df["month"]  # giữ dạng datetime
    traces = []

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
    thresholds = PARAMETER[parameter]["thresholds"]

    # Gom các đoạn liên tiếp cùng loại gió
    segments = []
    current_class = None
    x0 = None

    for i, val in enumerate(mean_vals):
        cls = classify_threshold(val, thresholds)
        if cls != current_class:
            if current_class is not None:
                segments.append((x0, x_dt[i], current_class))
            current_class = cls
            x0 = x_dt[i]
    if current_class is not None:
        segments.append((x0, x_dt.iloc[-1], current_class))

    # Vẽ các vrect gom nhóm theo Beaufort
    for x0, x1, wc in segments:
        if x0 == x1:
            x1 += 0.05
        fig.add_vrect(
            x0=x0,
            x1=x1,
            fillcolor=wc["color"],
            opacity=0.3,  # tăng độ đậm
            layer="below",
            line_width=0,
            annotation_text=wc["label"],
            annotation_position="top left",
            annotation=dict(font_size=12, font_color="black", font_weight="bold"),
        )

    # Thêm legend (trace ẩn cho mỗi loại gió)
    for wc in thresholds:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(size=10, color=wc["color"]),
                name=wc["label"],
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
            hovertemplate=f"%{{x}}<br>{PARAMETER[parameter]['name']}: %{{y:.2f}} {PARAMETER[parameter]['unit']} <extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=np.array(x)[minima],
            y=y[minima],
            mode="markers",
            marker=dict(color="blue", size=10, symbol="circle"),
            name="Min",
            hovertemplate=f"%{{x}}<br>{PARAMETER[parameter]['name']}: %{{y:.2f}} {PARAMETER[parameter]['unit']} <extra></extra>",
        )
    )

    # Layout
    fig.update_layout(
        title=f"{PARAMETER[parameter]['name']} on {datetime.now().year}",
        xaxis_title="Time",
        yaxis_title=f"{PARAMETER[parameter]['name']} ({PARAMETER[parameter]['unit']})",
        template="simple_white",
    )

    # Hiển thị lưới
    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=[
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
    )
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor="lightgray")

    current_month = datetime.now().month

    fig.add_vline(
        x=current_month,
        line_width=2,
        line_dash="dash",  # kiểu nét đứt
        line_color="darkred",
        annotation_text=f"Current month",
        annotation_position="top",
        annotation=dict(font_size=12, font_color="black", font_weight="bold"),
    )

    return fig


# ---------- Utility: ensure raw_df có các cột cần thiết ----------
def normalize_raw_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Đảm bảo index là datetime, thêm year/month/day/hour cols."""
    if raw_df.index.name != "index" and not isinstance(raw_df.index, pd.DatetimeIndex):
        raw_df.index = pd.to_datetime(raw_df.index)
    raw_df = raw_df.copy()
    raw_df["year"] = raw_df.index.year
    raw_df["month"] = raw_df.index.month
    raw_df["day"] = raw_df.index.day
    raw_df["hour"] = raw_df.index.hour
    return raw_df


# ---------- Build group-aggregates features ----------
def build_aggregates(raw_df: pd.DataFrame, parameters: List):
    """
    Tạo bảng aggregates theo (month, day, hour) từ lịch sử:
    trả về DataFrame keyed by (month, day, hour) với các feature stats cho mỗi param.
    """
    groups = raw_df.groupby(["month", "day", "hour"])
    agg_frames = []
    for p in parameters:
        agg = (
            groups[p]
            .agg(
                [
                    ("hist_mean", "mean"),
                    ("hist_std", "std"),
                    ("hist_median", "median"),
                    (
                        "hist_q05",
                        lambda x: (
                            np.nanpercentile(x.dropna(), 5)
                            if len(x.dropna()) > 0
                            else np.nan
                        ),
                    ),
                    (
                        "hist_q95",
                        lambda x: (
                            np.nanpercentile(x.dropna(), 95)
                            if len(x.dropna()) > 0
                            else np.nan
                        ),
                    ),
                    ("hist_count", "count"),
                ]
            )
            .reset_index()
        )
        # rename columns to include parameter prefix
        agg = agg.rename(
            columns={
                "hist_mean": f"{p}_hist_mean",
                "hist_std": f"{p}_hist_std",
                "hist_median": f"{p}_hist_median",
                "hist_q05": f"{p}_hist_q05",
                "hist_q95": f"{p}_hist_q95",
                "hist_count": f"{p}_hist_count",
            }
        )
        agg_frames.append(agg)
    # merge all param aggregates on month,day,hour
    from functools import reduce

    agg_all = reduce(
        lambda left, right: left.merge(right, on=["month", "day", "hour"], how="outer"),
        agg_frames,
    )
    return agg_all


# ---------- Build features for training (merge aggregates back) ----------
def build_training_table(
    raw_df: pd.DataFrame, parameters: List[str], agg_all: pd.DataFrame
):
    """
    Trả về X (features) và y_dict (targets per param)
    X: mỗi row là 1 timestamp trong raw_df, features bao gồm hour cyclical, doy cyclical, và agg fields.
    """
    df = raw_df.reset_index().rename(columns={"index": "datetime"}).copy()
    # merge agg features
    df = df.merge(agg_all, on=["month", "day", "hour"], how="left")
    # time cyclical
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["doy"] = df["datetime"].dt.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * df["doy"] / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * df["doy"] / 365.25)

    # choose feature columns (all agg cols + cyclical)
    agg_cols = [
        c
        for c in df.columns
        if any(
            suffix in c
            for suffix in [
                "_hist_mean",
                "_hist_std",
                "_hist_median",
                "_hist_q05",
                "_hist_q95",
                "_hist_count",
            ]
        )
    ]
    feature_cols = [
        "hour",
        "hour_sin",
        "hour_cos",
        "doy",
        "doy_sin",
        "doy_cos",
    ] + agg_cols
    X = df[feature_cols].fillna(0.0)
    # build y dict per param
    y_dict = {p: df[p].values for p in parameters}
    index = df["datetime"]
    X.index = index
    return X, y_dict, feature_cols


# ---------- Forecast: train quantile models per param and predict 24h for target_dt ----------
def forecast_lightgbm_multitarget(
    raw_df: pd.DataFrame,
    parameters: List[str],
    target_dt: datetime,
    quantiles: List[float] = [0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95],
    transform_precip: bool = True,
    num_boost_round: int = 200,
):
    """
    Input:
        - raw_df: historical DataFrame (datetime index) covering +/-window days across many past years
        - parameters: list of parameter names to model
        - target_dt: date (datetime) for which we predict 24 hours (hour 0..23)
    Output:
        - pred_df: DataFrame with datetime(24h) and predicted quantiles for each param.
        - models: dict of trained models {param: {quantile: model}}
    """
    raw_df = normalize_raw_df(raw_df)
    agg_all = build_aggregates(raw_df, parameters)
    X, y_dict, feature_cols = build_training_table(raw_df, parameters, agg_all)

    models = {p: {} for p in parameters}
    preds_per_param = {}

    for p in parameters:
        # prepare target vector
        y = y_dict[p]
        # optional transform for precipitation since it's skewed
        is_precip = (p.upper() == "PRECTOTCORR") and transform_precip
        if is_precip:
            y_train = np.log1p(np.maximum(y, 0.0))  # log1p on non-negative
        else:
            y_train = y

        # train one model per quantile
        for q in quantiles:
            parameters_lgb = {
                "objective": "quantile",
                "alpha": q,
                "learning_rate": 0.05,
                "num_leaves": 31,
                "min_data_in_leaf": 10,
                "verbose": -1,
            }
            dtrain = lgb.Dataset(X.values, y_train, free_raw_data=False)
            model = lgb.train(parameters_lgb, dtrain, num_boost_round=num_boost_round)
            models[p][q] = model

        # build prediction features for 24 hours of target_dt
        hours = list(range(24))
        rows = []
        for h in hours:
            dt = target_dt.replace(hour=h, minute=0, second=0, microsecond=0)
            m = dt.month
            d = dt.day
            hh = dt.hour
            # lookup aggregated stats row (month, day, hour)
            row_agg = agg_all[
                (agg_all["month"] == m)
                & (agg_all["day"] == d)
                & (agg_all["hour"] == hh)
            ]
            if row_agg.shape[0] == 0:
                # fallback: use same month-hour aggregated (ignore day)
                row_agg = agg_all[(agg_all["month"] == m) & (agg_all["hour"] == hh)]
            if row_agg.shape[0] == 0:
                # fallback: zeros
                base = {c: 0.0 for c in feature_cols}
            else:
                # take first match
                row = row_agg.iloc[0].to_dict()
                base = {}
                for c in feature_cols:
                    base[c] = row.get(c, 0.0)
            # add cyclical time features
            base["hour"] = hh
            base["hour_sin"] = np.sin(2 * np.pi * hh / 24)
            base["hour_cos"] = np.cos(2 * np.pi * hh / 24)
            base["doy"] = dt.timetuple().tm_yday
            base["doy_sin"] = np.sin(2 * np.pi * base["doy"] / 365.25)
            base["doy_cos"] = np.cos(2 * np.pi * base["doy"] / 365.25)
            rows.append(base)
        X_pred = pd.DataFrame(rows, index=[target_dt.replace(hour=h) for h in hours])[
            feature_cols
        ].fillna(0.0)

        # predict quantiles and inverse transform if needed
        preds_q = {}
        for q in quantiles:
            model = models[p][q]
            yhat = model.predict(X_pred.values)
            if is_precip:
                yhat = np.expm1(yhat)  # inverse of log1p
                yhat = np.maximum(yhat, 0.0)
            preds_q[q] = yhat
        preds_per_param[p] = preds_q

    # assemble pred_df: datetime + for each param: q05..q95 and median and mean (median from q50)
    hours = list(range(24))
    dt_index = [
        target_dt.replace(hour=h, minute=0, second=0, microsecond=0) for h in hours
    ]
    pred_dict = {"datetime": dt_index}
    for p in parameters:
        qmap = preds_per_param[p]
        for q, arr in qmap.items():
            col = f"{p}_q{int(q*100):02d}"
            pred_dict[col] = arr
        # conveniently add median as q50 if present
        if 0.5 in qmap:
            pred_dict[p] = qmap[0.5]
        else:
            # approximate median with mean of q35 and q65 if 0.5 absent
            pred_dict[p] = 0.5 * (qmap[0.35] + qmap[0.65])

    pred_df = pd.DataFrame(pred_dict)
    return pred_df, models


def compute_ci_from_pred_df(
    pred_df: pd.DataFrame,
    parameters: List[str],
    ci_levels: List[float] = [0.3, 0.6, 0.9],
) -> pd.DataFrame:
    """
    pred_df: output của forecast_lightgbm_multitarget
    trả về dataframe có columns:
        datetime, {param}_low_{ci%}, {param}_high_{ci%}, and param (median)
    """
    out = {"datetime": pred_df["datetime"]}
    # mapping ci -> quantiles pair
    mapping = {
        0.9: (5, 95),
        0.6: (20, 80),
        0.3: (35, 65),
    }
    # allow custom ci_levels
    for p in parameters:
        # median column exists as p in pred_df
        out[p] = pred_df[p].values
        for ci in ci_levels:
            pct_lower, pct_upper = mapping.get(
                round(ci, 2), (int(50 - ci * 50), int(50 + ci * 50))
            )
            col_low = f"{p}_low_{int(ci*100)}"
            col_high = f"{p}_high_{int(ci*100)}"
            out[col_low] = pred_df[f"{p}_q{pct_lower:02d}"].values
            out[col_high] = pred_df[f"{p}_q{pct_upper:02d}"].values
    df_out = pd.DataFrame(out)

    # 👉 Thêm dòng 24h = 0h hôm sau
    last_row = df_out.iloc[-1].copy()
    last_row["datetime"] = last_row["datetime"] + pd.Timedelta(hours=1)
    df_out = pd.concat([df_out, pd.DataFrame([last_row])], ignore_index=True)

    return df_out
