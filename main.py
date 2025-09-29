# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pandas as pd

from core.geocode import geocode_osm
from core.data_fetcher import fetch_raw_data
from core.model import forecast_lightgbm_bootstrap
from core.analysis import summarize_and_fanmaps

app = FastAPI(title="Climate Forecast API (NASA + LightGBM)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# default variable list (match your raw data)
PARAMS = ["T2M", "RH2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "WS2M"]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/forecast")
def forecast(
    place: str, date: str, window: int = 5, years_back: int = 10, n_models: int = 20
):
    """
    Example: /forecast?place=Ho%20Chi%20Minh%20City&date=2025-10-02
    Returns JSON: hourly forecast list (24 items), daily_summary, fanmaps (base64)
    """
    # 1) geocode
    lat, lon = geocode_osm(place)
    if lat is None:
        raise HTTPException(status_code=404, detail="Place not found")

    # 2) parse date
    try:
        target_dt = datetime.strptime(date, "%Y-%m-%d")
    except Exception as e:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    # 3) fetch raw historical data from NASA POWER (async wrapper)
    try:
        raw_df = fetch_raw_data(
            target_dt, lat, lon, PARAMS, window=window, years_back=years_back
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error fetching NASA POWER: {e}")

    if raw_df.empty:
        raise HTTPException(
            status_code=502,
            detail="No historical data available for this location/date",
        )

    # 4) fit bootstrap ensemble (giữ nguyên để lấy hourly prediction)
    hourly_df = forecast_lightgbm_bootstrap(raw_df, PARAMS, target_dt, n_models=n_models)

    # 5) tính daily summary từ hourly_df
    daily_summary = {}
    if not hourly_df.empty:
        base_vars = [p for p in PARAMS if p in hourly_df.columns]
        for v in base_vars:
            if v == "PRECTOTCORR":
                daily_summary["PRECTOTCORR_total"] = float(hourly_df[v].sum())
                daily_summary[v+"_mean"] = float(hourly_df[v].mean())
            else:
                daily_summary[v+"_mean"] = float(hourly_df[v].mean())

    # 6) tính CI fanmaps từ raw_df (history)
    from core.analysis import summarize_and_fanmaps
    fanmap_result = summarize_and_fanmaps(raw_df, PARAMS, target_dt)

    return {
        "place": place,
        "lat": lat,
        "lon": lon,
        "target_date": target_dt.strftime("%Y-%m-%d"),
        "hourly": hourly_df.to_dict(orient="records"),
        "daily_summary": daily_summary,
        "fanmaps": fanmap_result["fanmaps"],
    }
