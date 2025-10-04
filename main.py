import json
from datetime import datetime, timedelta
from typing import List

import numpy as np
import pandas as pd
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from core.geocode import geocode_osm, get_current_place
from core.data_fetcher import fetch_hourly_data, get_monthly_data_async
from core.analysis import (
    compute_ci_multitarget,
    plotly_one_day,
    plotly_many_days,
    compute_ci_from_pred_df,
    normalize_raw_df,
    forecast_lightgbm_multitarget,
    create_monthly_avg_df,
    plotly_monthly_overview,
)


app = FastAPI()
templates = Jinja2Templates(directory="frontend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PARAMETERS = ["T2M", "RH2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "WS2M"]


@app.get("/forecast_point_one_day")
def forecast_point_one_day(place: str = Query(...), date: str = Query(...)):
    latitude, longitude = geocode_osm(place)

    # 2. Parse date
    try:
        target_date = datetime.fromisoformat(date)
    except Exception:
        raise RuntimeError(f"Ngày không hợp lệ: {date}")

    # 3. Lấy dữ liệu NASA POWER
    raw_df = fetch_hourly_data(target_date, latitude, longitude, PARAMETERS)
    raw_df = normalize_raw_df(raw_df)
    if raw_df.empty:
        raise RuntimeError("Không có dữ liệu từ NASA POWER")

    pred_df, models = forecast_lightgbm_multitarget(
        raw_df,
        PARAMETERS,
        target_date,
        quantiles=[0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95],
        num_boost_round=10,
    )

    # 3) compute CI dataframe
    ci_df = compute_ci_from_pred_df(pred_df, PARAMETERS, ci_levels=[0.3, 0.6, 0.9])

    # 6. Vẽ biểu đồ cho tất cả param
    figures = {}
    for parameter in PARAMETERS:
        fig_dict = plotly_one_day(ci_df, parameter)
        figures[parameter] = json.dumps(fig_dict, default=str)  # ép thành JSON string

    return {
        "place": place,
        "coords": {"latitude": latitude, "longitude": longitude},
        "date": target_date.isoformat(),
        "figures": figures,  # lúc này mỗi cái là JSON string
    }


@app.get("/monthly_weather")
async def forecast_monthly(place: str = Query(...)):
    latitude, longitude = geocode_osm(place)

    target_date = datetime.now()
    raw_df = await get_monthly_data_async(
        target_date, latitude, longitude, ["PRECTOTCORR", "T2M"]
    )
    avg_df = create_monthly_avg_df(raw_df, ["PRECTOTCORR", "T2M"])
    if raw_df.empty:
        raise RuntimeError("Không có dữ liệu từ NASA POWER")

    # 3) compute CI dataframe

    figures = {}
    for parameter in ["PRECTOTCORR", "T2M"]:
        fig_dict = plotly_monthly_overview(avg_df, parameter).to_dict
        figures[parameter] = json.dumps(fig_dict, default=str)  # ép thành JSON string

    return {
        "place": place,
        "coords": {"latitude": latitude, "longitude": longitude},
        "date": target_date.isoformat(),
        "figures": figures,  # lúc này mỗi cái là JSON string
    }


@app.get("/forecast_point_many_days")
def forecast_point_many_days(
    place: str = Query(...), start_date: str = Query(...), end_date: str = Query(...)
):
    latitude, longitude = geocode_osm(place)
    start_date = datetime.fromisoformat(start_date)
    end_date = datetime.fromisoformat(end_date)
    ci_list = []
    target_date = start_date
    while target_date <= end_date:
        raw_df = fetch_hourly_data(target_date, latitude, longitude, PARAMETERS)
        raw_df = normalize_raw_df(raw_df)
        target_date += timedelta(1)
        # 2) dự đoán bằng LightGBM quantile
        pred_df, models = forecast_lightgbm_multitarget(
            raw_df,
            PARAMETERS,
            target_date,
            quantiles=[0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95],
            num_boost_round=10,
        )
        ci_df = compute_ci_from_pred_df(pred_df, PARAMETERS)
        ci_list.append(ci_df)

    ci = pd.concat(ci_list, axis=0).reset_index()
    ci = ci.drop_duplicates(subset=["datetime"], keep="last")
    ci = ci.drop(ci.columns[0], axis=1)

    # 6. Vẽ biểu đồ cho tất cả param
    figures = {}
    for parameter in PARAMETERS:
        fig_dict = plotly_many_days(ci, parameter)
        figures[parameter] = json.dumps(fig_dict, default=str)  # ép thành JSON string

    return {
        "place": place,
        "coords": {"latitude": latitude, "longitude": longitude},
        "date": target_date.isoformat(),
        "figures": figures,  # lúc này mỗi cái là JSON string
    }


def average_point(coords: list[list[float]]) -> tuple[float, float]:
    sum_lat = sum(pt[0] for pt in coords)
    sum_lng = sum(pt[1] for pt in coords)
    n = len(coords)
    return (sum_lat / n, sum_lng / n)


@app.post("/forecast_region")
def forecast_region_one_day(coords: List[List[float]], target_date: str = Query(...)):
    latitude, longitude = average_point(coords)

    try:
        target_date = datetime.fromisoformat(date)
    except Exception:
        raise RuntimeError(f"Ngày không hợp lệ: {date}")

    # 3. Lấy dữ liệu NASA POWER
    raw_df = fetch_hourly_data(target_date, latitude, longitude, PARAMETERS)
    raw_df = normalize_raw_df(raw_df)
    if raw_df.empty:
        raise RuntimeError("Không có dữ liệu từ NASA POWER")

    pred_df, models = forecast_lightgbm_multitarget(
        raw_df,
        PARAMETERS,
        target_date,
        quantiles=[0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95],
        num_boost_round=10,
    )

    # 3) compute CI dataframe
    ci_df = compute_ci_from_pred_df(pred_df, PARAMETERS, ci_levels=[0.3, 0.6, 0.9])

    # 6. Vẽ biểu đồ cho tất cả param
    figures = {}
    for parameter in PARAMETERS:
        fig_dict = plotly_one_day(ci_df, parameter)
        figures[parameter] = json.dumps(fig_dict, default=str)  # ép thành JSON string

    return {
        "place": place,
        "coords": {"latitude": latitude, "longitude": longitude},
        "date": target_date.isoformat(),
        "figures": figures,  # lúc này mỗi cái là JSON string
    }


@app.get("/", response_class=HTMLResponse)
def current_place(request: Request):
    data = get_current_place()
    # data = {"current_place": "Hanoi"}
    return templates.TemplateResponse(
        "homepage.html", {"request": request, "data": data}
    )


@app.get("/forecast_region_many_days")
def forecast_region_many_days(
    coords: List[List[float]], start_date: str = Query(...), end_date: str = Query(...)
):
    latitude, longitude = average_point(coords)
    start_date = datetime.fromisoformat(start_date)
    end_date = datetime.fromisoformat(end_date)
    target_date = start_date
    ci_list = []

    while target_date <= end_date:
        raw_df = fetch_hourly_data(target_date, latitude, longitude, PARAMETERS)
        raw_df = normalize_raw_df(raw_df)
        target_date += timedelta(1)
        # 2) dự đoán bằng LightGBM quantile
        pred_df, models = forecast_lightgbm_multitarget(
            raw_df,
            PARAMETERS,
            target_date,
            quantiles=[0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95],
            num_boost_round=10,
        )
        ci_df = compute_ci_from_pred_df(pred_df, PARAMETERS)
        ci_list.append(ci_df)

    ci = pd.concat(ci_list, axis=0).reset_index()
    ci = ci.drop_duplicates(subset=["datetime"], keep="last")

    # 6. Vẽ biểu đồ cho tất cả param
    figures = {}
    for parameter in PARAMETERS:
        fig_dict = plotly_many_days(ci_df, parameter)
        figures[parameter] = json.dumps(fig_dict, default=str)  # ép thành JSON string

    return {
        "place": place,
        "coords": {"latitude": latitude, "longitude": longitude},
        "date": target_date.isoformat(),
        "figures": figures,  # lúc này mỗi cái là JSON string
    }
