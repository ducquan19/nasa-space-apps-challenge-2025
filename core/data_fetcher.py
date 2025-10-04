import asyncio
from typing import Any, Dict, List
from datetime import timedelta, datetime

import aiohttp
import pandas as pd


async def fetch_hourly_data_from_power_dav(
    session: aiohttp.ClientSession,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    parameters: List[str],
) -> Dict[str, Any]:
    url = (
        "https://power.larc.nasa.gov/api/temporal/hourly/point"
        f"?start={start_date}&end={end_date}"
        f"&latitude={latitude}&longitude={longitude}"
        f"&parameters={','.join(parameters)}"
        f"&format=JSON&community=RE"
    )

    async with session.get(url) as response:
        response.raise_for_status()
        data: Dict[str, Any] = await response.json()

        if "properties" not in data or "parameter" not in data["properties"]:
            raise RuntimeError("POWER response missing 'parameter'")

        return data["properties"]["parameter"]


async def get_hourly_data_async(
    target_date: datetime,
    latitude: float,
    longitude: float,
    parameters: List[str],
    window: int = 5,
    years_back: int = 10,
) -> pd.DataFrame:
    dfs: List[pd.DataFrame] = []

    async with aiohttp.ClientSession() as session:
        sessions = []
        for i in range(1, years_back + 1):
            past_year = target_date.year - i
            start_date = (
                target_date.replace(year=past_year) - timedelta(days=window)
            ).strftime("%Y%m%d")
            end_date = (
                target_date.replace(year=past_year) + timedelta(days=window)
            ).strftime("%Y%m%d")
            sessions.append(
                fetch_hourly_data_from_power_dav(
                    session, latitude, longitude, start_date, end_date, parameters
                )
            )

        results = await asyncio.gather(*sessions)

    for i, result in enumerate(results, 1):
        past_year = target_date.year - i
        df = pd.DataFrame(
            {parameter: pd.Series(result[parameter]) for parameter in parameters}
        )
        df.index = pd.to_datetime(df.index, format="%Y%m%d%H")
        dfs.append(df)

    full_df = pd.concat(dfs, axis=0)
    return full_df


def fetch_hourly_data(
    target_date: datetime,
    latitude: float,
    longitude: float,
    parameters: List[str],
    window: int = 5,
    years_back: int = 10,
) -> pd.DataFrame:

    return asyncio.run(
        get_hourly_data_async(
            target_date,
            latitude,
            longitude,
            parameters,
            window=window,
            years_back=years_back,
        )
    )


async def fetch_monthly_data_from_power_dav(
    session: aiohttp.ClientSession,
    latitude: float,
    longitude: float,
    start_year: str,
    end_year: str,
    parameters: List[str],
) -> Dict[str, Any]:
    url = (
        "https://power.larc.nasa.gov/api/temporal/monthly/point"
        f"?start={start_year}&end={end_year}"
        f"&latitude={latitude}&longitude={longitude}"
        f"&parameters={','.join(parameters)}"
        f"&format=JSON&community=RE"
    )
    async with session.get(url) as response:
        response.raise_for_status()
        js = await response.json()
        return js["properties"]["parameter"]


async def get_monthly_data_async(
    target_date: datetime,
    latitude: float,
    longitude: float,
    parameters: List[str],
    window: int = 0,
    years_back: int = 10,
):
    dfs = []
    async with aiohttp.ClientSession() as session:
        sessions = []
        for i in range(1, years_back + 1):
            past_year = target_date.year - i
            start_year = (
                target_date.replace(year=past_year) - timedelta(days=window)
            ).strftime("%Y")
            end_year = (
                target_date.replace(year=past_year) + timedelta(days=window)
            ).strftime("%Y")
            sessions.append(
                fetch_monthly_data_from_power_dav(
                    session, latitude, longitude, start_year, end_year, parameters
                )
            )
        results = await asyncio.gather(*sessions)

    # convert to dataframe list
    for i, result in enumerate(results, 1):
        past_year = target_date.year - i
        for p in parameters:
            del result[p][f"{past_year}13"]
        df = pd.DataFrame({parameter: pd.Series(result[p]) for parameter in parameters})
        df.index = pd.to_datetime(df.index, format="%Y%m")
        df["year"] = past_year
        df["month"] = df.index.month
        dfs.append(df)

    full_df = pd.concat(dfs, axis=0)
    return full_df.reset_index(drop=True)


def fetch_monthly_data(
    target_date: datetime,
    latitude: float,
    longitude: float,
    parameters: List[str],
    window: int = 5,
    years_back: int = 10,
) -> pd.DataFrame:

    return asyncio.run(
        get_monthly_data_async(
            target_date,
            latitude,
            longitude,
            parameters,
            window=window,
            years_back=years_back,
        )
    )
