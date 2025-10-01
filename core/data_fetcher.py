import asyncio
from typing import Any, Dict, List
from datetime import timedelta, datetime

import aiohttp
import pandas as pd


async def fetch_power(
    session: aiohttp.ClientSession,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    parameters: List[str],
) -> Dict[str, Any]:
    """
    Fetch hourly power data from NASA POWER API.

    Args:
        session (aiohttp.ClientSession): Active aiohttp session for making requests.
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        start_date (str): Start date in YYYYMMDD format.
        end_date (str): End date in YYYYMMDD format.
        parameters (List[str]): List of parameters to fetch.

    Returns:
        Dict[str, Any]: Dictionary containing the requested parameters.

    Raises:
        RuntimeError: If response JSON does not contain the expected structure.
    """
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


async def get_raw_data_async(
    target_dt: datetime,
    latitude: float,
    longitude: float,
    parameters: List[str],
    window: int = 5,
    years_back: int = 10,
) -> pd.DataFrame:
    dfs: List[pd.DataFrame] = []

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
            tasks.append(
                fetch_power(session, latitude, longitude, start, end, parameters)
            )

        results = await asyncio.gather(*tasks)

    for i, result in enumerate(results, 1):
        past_year = target_dt.year - i
        df = pd.DataFrame({p: pd.Series(result[p]) for p in parameters})
        df.index = pd.to_datetime(df.index, format="%Y%m%d%H")
        df["year"] = past_year
        df["hour"] = df.index.hour
        dfs.append(df)

    if not dfs:
        return pd.DataFrame(columns=parameters + ["year", "hour"])

    full_df = pd.concat(dfs, axis=0)
    return full_df.reset_index(drop=True)


def fetch_raw_data(
    target_dt: datetime,
    latitude: float,
    longitude: float,
    parameters: List[str],
    window: int = 5,
    years_back: int = 10,
) -> pd.DataFrame:
    """
    Sync wrapper for get_raw_data_async. Returns pandas.DataFrame.
    """
    return asyncio.run(
        get_raw_data_async(
            target_dt,
            latitude,
            longitude,
            parameters,
            window=window,
            years_back=years_back,
        )
    )
