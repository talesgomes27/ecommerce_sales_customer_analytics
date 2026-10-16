"""Testes unitários para engenharia de features pontuais e RFM."""

from pathlib import Path

import pandas as pd
import pytest

from src.data.loader import load_canonical_data
from src.features.builder import (
    compute_point_in_time_features,
    get_feature_matrix,
    split_out_of_time,
)
from src.features.rfm import calculate_rfm_table


@pytest.fixture(scope="module")
def sample_df(raw_data_path: Path) -> pd.DataFrame:
    """Carrega uma amostra determinística de 5.000 registros para testes rápidos."""
    df = load_canonical_data(raw_data_path)
    return df.head(5000)


def test_point_in_time_no_lookahead(sample_df: pd.DataFrame) -> None:
    """Garante que a primeira compra de qualquer cliente tenha histórico zero."""
    pit_df = compute_point_in_time_features(sample_df)

    # Para cada cliente, o primeiro pedido deve ter contagem prévia 0 e gasto prévio 0.0
    first_orders = pit_df.groupby("customer_id").first()
    assert (first_orders["orders_count_prior"] == 0).all(), "Primeiro pedido não tem contagem zero."
    assert (first_orders["spend_prior"] == 0.0).all(), "Primeiro pedido não tem gasto prévio zero."
    assert (first_orders["days_since_last_order"] == -1.0).all(), "Recência inicial não é -1.0."


def test_split_out_of_time_separation(sample_df: pd.DataFrame) -> None:
    """Garante que não há contaminação temporal entre treino e teste cego."""
    pit_df = compute_point_in_time_features(sample_df)
    train_df, test_df = split_out_of_time(pit_df, cutoff_date="2025-01-01")

    if len(train_df) > 0 and len(test_df) > 0:
        assert train_df["order_date"].max() < pd.to_datetime("2025-01-01")
        assert test_df["order_date"].min() >= pd.to_datetime("2025-01-01")


def test_feature_matrix_no_leakage_columns(sample_df: pd.DataFrame) -> None:
    """Garante que colunas proibidas de pós-venda não constam na matriz de features."""
    pit_df = compute_point_in_time_features(sample_df)
    X, y = get_feature_matrix(pit_df)

    prohibited = [
        "delivery_days",
        "estimated_delivery_days",
        "customer_rating",
        "review_sentiment",
        "customer_review",
        "return_status",
        "return_reason",
        "delivery_status",
        "payment_status",
    ]
    for col in prohibited:
        assert col not in X.columns, f"Coluna de vazamento encontrada em X: {col}"

    assert len(X) == len(y)
    assert set(y.unique()).issubset({0, 1})


def test_rfm_calculation_validity(sample_df: pd.DataFrame) -> None:
    """Valida o cálculo de Recência, Frequência e Valor Monetário."""
    rfm = calculate_rfm_table(sample_df)
    assert len(rfm) == sample_df["customer_id"].nunique()
    assert (rfm["frequency"] >= 1).all()
    assert (rfm["monetary_value"] > 0).all()
    assert (rfm["recency_days"] >= 0).all()
