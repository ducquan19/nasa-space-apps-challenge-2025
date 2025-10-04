from typing import List
from datetime import datetime

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor


def forecast_lightgbm_multitarget(
    raw_df: pd.DataFrame, parameters: List[str], target_dt: datetime
) -> pd.DataFrame:
    df = raw_df.copy()
    df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24)

    X = df[["hour", "sin_hour", "cos_hour", "year"]]
    y = df[parameters]

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = MultiOutputRegressor(estimator=XGBRegressor())
    model.fit(X_train, y_train)

    hours = range(24)
    X_pred = pd.DataFrame(
        {
            "hour": hours,
            "sin_hour": np.sin(2 * np.pi * np.array(hours) / 24),
            "cos_hour": np.cos(2 * np.pi * np.array(hours) / 24),
            "year": target_dt.year,
        }
    )
    y_pred = model.predict(X_pred)

    pred_df = pd.DataFrame(y_pred, columns=parameters)
    pred_df["datetime"] = [
        target_dt.replace(hour=h, minute=0, second=0, microsecond=0) for h in hours
    ]

    return pred_df[["datetime"] + parameters]


def forecast_lightgbm_bootstrap(
    raw_df: pd.DataFrame,
    parameters: List[str],
    target_dt: datetime,
    ci_levels: List[float] = [0.3, 0.6, 0.9],
) -> pd.DataFrame:
    """
    raw_df: DataFrame with columns params + 'hour' + 'year'
    returns DataFrame with columns:
      datetime, <param>, <param>_low_30, <param>_high_30, ...
    """
    df = raw_df.copy().reset_index(drop=True)
    if df.empty:
        # return empty 24h with NaNs
        rows = [{"datetime": target_dt.replace(hour=h)} for h in range(24)]
        return pd.DataFrame(rows)

    df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24)

    X = df[["hour", "sin_hour", "cos_hour", "year"]]
    y = df[parameters]

    all_preds = {p: [] for p in parameters}

    model = MultiOutputRegressor(estimator=XGBRegressor())
    model.fit(X, y)

    hours = range(24)
    X_pred = pd.DataFrame(
        {
            "hour": hours,
            "sin_hour": np.sin(2 * np.pi * np.array(hours) / 24),
            "cos_hour": np.cos(2 * np.pi * np.array(hours) / 24),
            "year": target_dt.year,
        }
    )
    y_pred = model.predict(X_pred)  # shape (24, n_params)

    for j, p in enumerate(parameters):
        all_preds[p].append(y_pred[:, j])

    pred_df = pd.DataFrame({"datetime": [target_dt.replace(hour=h) for h in range(24)]})
    for p in parameters:
        stacked = np.vstack(all_preds[p])  # (n_models, 24)
        pred_df[p] = stacked.mean(axis=0)
        for ci in ci_levels:
            low = np.percentile(stacked, 50 - ci * 50, axis=0)
            high = np.percentile(stacked, 50 + ci * 50, axis=0)
            pred_df[f"{p}_low_{int(ci*100)}"] = low
            pred_df[f"{p}_high_{int(ci*100)}"] = high

    return pred_df
