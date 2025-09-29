# core/data_fetcher.py
import asyncio
import aiohttp
import pandas as pd
from datetime import timedelta


async def fetch_power(session, lat, lon, start, end, params):
    url = (
        "https://power.larc.nasa.gov/api/temporal/hourly/point"
        f"?start={start}&end={end}&latitude={lat}&longitude={lon}"
        f"&parameters={','.join(params)}&format=JSON&community=RE"
    )
    async with session.get(url) as resp:
        resp.raise_for_status()
        js = await resp.json()
        # ensure expected structure
        if "properties" not in js or "parameter" not in js["properties"]:
            raise RuntimeError("POWER response missing 'parameter'")
        return js["properties"]["parameter"]


async def get_raw_data_async(target_dt, lat, lon, params, window=5, years_back=10):
    dfs = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for y in range(1, years_back + 1):
            past_year = target_dt.year - y
            start = (
                target_dt.replace(year=past_year) - timedelta(days=window)
            ).strftime("%Y%m%d")
            end = (target_dt.replace(year=past_year) + timedelta(days=window)).strftime(
                "%Y%m%d"
            )
            tasks.append(fetch_power(session, lat, lon, start, end, params))
        results = await asyncio.gather(*tasks)

    for i, r in enumerate(results, 1):
        past_year = target_dt.year - i
        # r is dict: param -> {timestamp: value}
        df = pd.DataFrame({p: pd.Series(r[p]) for p in params})
        # parse index like '2025092712' (YYYYmmddHH)
        df.index = pd.to_datetime(df.index, format="%Y%m%d%H", errors="coerce")
        df = df.dropna(how="all")
        df["year"] = past_year
        df["hour"] = df.index.hour
        dfs.append(df)

    if len(dfs) == 0:
        return pd.DataFrame(columns=params + ["year", "hour"])
    full_df = pd.concat(dfs, axis=0)
    return full_df.reset_index(drop=True)


def fetch_raw_data(target_dt, lat, lon, params, window=5, years_back=10):
    """Sync wrapper for get_raw_data_async. Returns pandas.DataFrame."""
    return asyncio.run(
        get_raw_data_async(
            target_dt, lat, lon, params, window=window, years_back=years_back
        )
    )
