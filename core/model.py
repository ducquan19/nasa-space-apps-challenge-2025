# core/model.py
import numpy as np
import pandas as pd
from sklearn.multioutput import MultiOutputRegressor
import lightgbm as lgb


def forecast_lightgbm_bootstrap(
    raw_df, params, target_dt, n_models=20, ci_levels=[0.3, 0.6, 0.9]
):
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
    y = df[params]

    all_preds = {p: [] for p in params}

    for i in range(n_models):
        sample_idx = np.random.choice(len(df), size=len(df), replace=True)
        X_train = X.iloc[sample_idx]
        y_train = y.iloc[sample_idx]

        model = MultiOutputRegressor(
            lgb.LGBMRegressor(
                objective="regression",
                n_estimators=200,
                learning_rate=0.05,
                random_state=i,
            )
        )
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
        y_pred = model.predict(X_pred)  # shape (24, n_params)

        for j, p in enumerate(params):
            all_preds[p].append(y_pred[:, j])

    pred_df = pd.DataFrame({"datetime": [target_dt.replace(hour=h) for h in range(24)]})
    for p in params:
        stacked = np.vstack(all_preds[p])  # (n_models, 24)
        pred_df[p] = stacked.mean(axis=0)
        for ci in ci_levels:
            low = np.percentile(stacked, 50 - ci * 50, axis=0)
            high = np.percentile(stacked, 50 + ci * 50, axis=0)
            pred_df[f"{p}_low_{int(ci*100)}"] = low
            pred_df[f"{p}_high_{int(ci*100)}"] = high

    return pred_df
