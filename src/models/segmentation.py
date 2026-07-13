# src/models/segmentation.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def load_rfm(run_query_fn, load_sql_fn) -> pd.DataFrame:
    df = run_query_fn(load_sql_fn('rfm_scoring.sql'))
    df.columns = df.columns.str.lower()
    return df


def scale_features(df: pd.DataFrame) -> tuple:
    features = df[['recency_days', 'frequency', 'monetary_value']]
    scaler   = RobustScaler()
    scaled   = scaler.fit_transform(features)
    return scaled, scaler


def find_optimal_k(scaled: np.ndarray,k_range: range = range(2, 8)) -> dict:
    results = {}
    for k in k_range:
        km  = KMeans(n_clusters=k, random_state=42, n_init=10).fit(scaled)
        sil = silhouette_score(
            scaled, km.labels_,
            sample_size=5000, random_state=42
        )
        results[k] = {
            'inertia':  round(km.inertia_, 2),
            'silhouette_score': round(sil, 4)
        }
    return results


def fit_segments(scaled: np.ndarray, k: int) -> tuple:
    km     = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(scaled)
    return labels, km


def profile_segments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute mean RFM metrics per segment and assign business labels.
    """
    profiles = df.groupby('segment').agg(
        recency  =('recency_days',   'mean'),
        frequency=('frequency',      'mean'),
        monetary =('monetary_value', 'mean'),
        count    =('user_id',        'count')
    ).round(1).reset_index()

    med_recency  = profiles['recency'].median()
    med_monetary = profiles['monetary'].median()

    def assign_label(row):
        recent    = row['recency']  < med_recency
        high_spend= row['monetary'] >= med_monetary
        if recent and high_spend:
            return 'Champions'
        elif recent and not high_spend:
            return 'Promising'
        elif not recent and high_spend:
            return 'At Risk'
        else:
            return 'Lost'

    profiles['label'] = profiles.apply(assign_label, axis=1)
    return profiles