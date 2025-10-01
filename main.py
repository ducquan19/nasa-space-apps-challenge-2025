import json
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from core.geocode import geocode_osm
from core.data_fetcher import fetch_raw_data
from core.analysis import compute_ci_multitarget, plot_fanmap_plotly
from core.model import forecast_lightgbm_bootstrap

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Các tham số khí tượng cần
PARAMS = ["T2M", "RH2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "WS2M"]


def make_jsonable(obj):
    """Đệ quy chuyển object (numpy, Timestamp, dict, list) thành Python thuần để JSON encode được"""
    if isinstance(obj, (np.generic,)):
        return obj.item()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: make_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_jsonable(v) for v in obj]
    return obj


@app.get("/forecast")
def forecast(place: str = Query(...), date: str = Query(...)):
    # 1. Geocode -> lat, lon
    coords = geocode_osm(place)
    if not coords:
        return {"error": f"Không tìm thấy địa điểm '{place}'"}
    lat, lon = coords

    # 2. Parse date
    try:
        target_dt = datetime.fromisoformat(date)
    except Exception:
        return {"error": f"Ngày không hợp lệ: {date}"}

    # 3. Lấy dữ liệu NASA POWER
    raw_df = fetch_raw_data(target_dt, lat, lon, PARAMS)
    if raw_df.empty:
        return {"error": "Không có dữ liệu từ NASA POWER"}

    # 4. Tính CI theo giờ
    ci_df = compute_ci_multitarget(raw_df, PARAMS, target_dt)

    # 5. Tính daily summary
    n_models = 20
    hourly_df = forecast_lightgbm_bootstrap(
        raw_df, PARAMS, target_dt, n_models=n_models
    )

    # 5) tính daily summary từ hourly_df
    daily_summary = {}
    if not hourly_df.empty:
        base_vars = [p for p in PARAMS if p in hourly_df.columns]
        for v in base_vars:
            if v == "PRECTOTCORR":
                daily_summary["PRECTOTCORR_total"] = float(hourly_df[v].sum())
                daily_summary[v + "_mean"] = float(hourly_df[v].mean())
            else:
                daily_summary[v + "_mean"] = float(hourly_df[v].mean())

    # 6. Vẽ biểu đồ cho tất cả param
    html_charts = {}
    figures = {}
    for p in PARAMS:
        html_str, fig_dict = plot_fanmap_plotly(ci_df, p)
        html_charts[p] = html_str
        figures[p] = json.dumps(fig_dict, default=str)  # ép thành JSON string

    return {
        "place": place,
        "coords": {"lat": lat, "lon": lon},
        "date": target_dt.isoformat(),
        # "daily_summary": make_jsonable(daily_summary),
        # "hourly": make_jsonable(ci_df.to_dict(orient="records")),
        "html_charts": html_charts,
        "figures": figures,  # lúc này mỗi cái là JSON string
    }
