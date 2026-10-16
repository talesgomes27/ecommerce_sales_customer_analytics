"""Testes unitários para modelos estatísticos, clustering e classificadores."""

from pathlib import Path

import pandas as pd
import pytest

from src.data.loader import load_canonical_data
from src.evaluation.metrics import (
    compute_delivery_delay_hypothesis,
    evaluate_classifier_out_of_time,
)
from src.features.builder import (
    AT_PURCHASE_CATEGORICAL_COLS,
    AT_PURCHASE_NUMERIC_COLS,
    compute_point_in_time_features,
    get_feature_matrix,
    split_out_of_time,
)
from src.features.rfm import calculate_rfm_table
from src.models.clustering import fit_rfm_kmeans
from src.models.pricing import analyze_discount_elasticity
from src.models.train import train_baseline_model, train_lightgbm_model


@pytest.fixture(scope="module")
def sample_df(raw_data_path: Path) -> pd.DataFrame:
    """Carrega amostra determinística de 6.000 transações."""
    df = load_canonical_data(raw_data_path)
    return df.head(6000)


def test_rfm_kmeans_clustering(sample_df: pd.DataFrame) -> None:
    """Valida o ajuste do K-Means sobre RFM e métricas de agrupamento."""
    rfm = calculate_rfm_table(sample_df)
    result_df, metrics, centroids = fit_rfm_kmeans(rfm, n_clusters=4, random_state=42)

    assert "cluster" in result_df.columns
    assert "cluster_label" in result_df.columns
    assert metrics["silhouette_score"] > 0.0
    assert len(centroids) == 4


def test_discount_elasticity_analysis(sample_df: pd.DataFrame) -> None:
    """Valida a extração de métricas de elasticidade e limiares de margem."""
    res = analyze_discount_elasticity(sample_df)
    assert "unprofitable_orders_count" in res
    assert "critical_inflection_threshold_pct" in res
    assert res["unprofitable_orders_count"] >= 0


def test_model_training_and_evaluation(sample_df: pd.DataFrame) -> None:
    """Testa o pipeline completo de treino do baseline e LightGBM com avaliação."""
    pit_df = compute_point_in_time_features(sample_df)
    train_df, test_df = split_out_of_time(pit_df, cutoff_date="2024-01-01")

    # Garante que ambos os splits tenham dados na amostra
    if len(train_df) < 100 or len(test_df) < 100:
        pytest.skip("Amostra insuficiente para treino e teste.")

    X_train, y_train = get_feature_matrix(train_df)
    X_test, y_test = get_feature_matrix(test_df)

    # Treina Baseline
    baseline = train_baseline_model(
        X_train, y_train, AT_PURCHASE_NUMERIC_COLS, AT_PURCHASE_CATEGORICAL_COLS
    )
    baseline_eval = evaluate_classifier_out_of_time(baseline, X_test, y_test)
    assert 0.0 <= baseline_eval["pr_auc"] <= 1.0
    assert 0.0 <= baseline_eval["roc_auc"] <= 1.0

    # Treina LightGBM
    lgbm_pipe, importance_df = train_lightgbm_model(
        X_train, y_train, AT_PURCHASE_NUMERIC_COLS, AT_PURCHASE_CATEGORICAL_COLS, n_estimators=20
    )
    lgbm_eval = evaluate_classifier_out_of_time(lgbm_pipe, X_test, y_test)
    assert 0.0 <= lgbm_eval["pr_auc"] <= 1.0
    assert len(importance_df) > 0
    assert "gain_importance" in importance_df.columns


def test_delivery_delay_statistical_test(sample_df: pd.DataFrame) -> None:
    """Testa a função de teste estatístico da hipótese H5."""
    res = compute_delivery_delay_hypothesis(sample_df)
    assert "mann_whitney_pvalue" in res
    assert "ttest_pvalue" in res
    assert "cohens_d" in res
