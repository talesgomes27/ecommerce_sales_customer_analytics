"""Segmentação de clientes por clustering não supervisionado (K-Means) sobre RFM."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def fit_rfm_kmeans(
    rfm_df: pd.DataFrame, n_clusters: int = 4, random_state: int = 42
) -> tuple[pd.DataFrame, dict[str, float], pd.DataFrame]:
    """Ajusta modelo K-Means sobre variáveis RFM padronizadas.

    Args:
        rfm_df: DataFrame contendo colunas ['recency_days', 'frequency', 'monetary_value'].
        n_clusters: Número de agrupamentos desejados (padrão: 4).
        random_state: Semente fixa para determinismo.

    Returns:
        Tupla com:
            - rfm_df com coluna adicional 'cluster' e 'cluster_label'
            - Dicionário com métricas de qualidade (silhouette_score, inertia)
            - DataFrame com perfil médio dos centroides
    """
    features = ["recency_days", "frequency", "monetary_value"]
    X = rfm_df[features].copy()

    # Aplica log1p para amenizar assimetria de valor monetário e frequência
    X_log = np.log1p(X)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_log)

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)

    sil_score = float(
        silhouette_score(X_scaled, clusters, sample_size=5000, random_state=random_state)
    )
    metrics = {
        "silhouette_score": sil_score,
        "inertia": float(kmeans.inertia_),
    }

    result_df = rfm_df.copy()
    result_df["cluster"] = clusters

    # Perfil dos centroides em escala original
    centroids = result_df.groupby("cluster")[features].mean().reset_index()

    # Atribuição de rótulos gerenciais ordenados por valor monetário médio
    sorted_clusters = centroids.sort_values(by="monetary_value", ascending=False)[
        "cluster"
    ].tolist()
    label_map = {
        sorted_clusters[0]: "Champions",
        sorted_clusters[1]: "Loyal Customers",
        sorted_clusters[2]: "At-Risk High-Value",
        sorted_clusters[3]: "Occasional / Low-Value",
    }
    result_df["cluster_label"] = result_df["cluster"].map(label_map)

    return result_df, metrics, centroids
