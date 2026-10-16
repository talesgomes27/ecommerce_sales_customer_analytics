"""Construção de features pontuais (point-in-time) e blindagem contra vazamento de dados."""

import numpy as np
import pandas as pd

AT_PURCHASE_NUMERIC_COLS = [
    "customer_age",
    "quantity",
    "gross_sales",
    "discount_amount",
    "tax_amount",
    "shipping_cost",
    "product_cost",
    "loyalty_points_earned",
    "loyalty_points_redeemed",
    "discount_pct",
    "orders_count_prior",
    "spend_prior",
    "days_since_last_order",
]

AT_PURCHASE_CATEGORICAL_COLS = [
    "gender",
    "customer_segment",
    "region",
    "sales_channel",
    "marketing_channel",
    "payment_method",
    "shipping_method",
    "warehouse",
]

PROHIBITED_LEAKAGE_COLS = [
    "delivery_days",
    "estimated_delivery_days",
    "customer_rating",
    "review_sentiment",
    "customer_review",
    "return_status",
    "return_reason",
    "delivery_status",
    "payment_status",
    "customer_lifetime_value",
    "customer_order_count",
    "customer_type",
    "is_repeat_customer",
]


def compute_point_in_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula variáveis históricas estritamente retroativas por cliente.

    Ordena as transações cronologicamente e computa contagens cumulativas,
    gastos acumulados e recência em dias, considerando apenas pedidos prévios
    ao momento t de cada transação.

    Args:
        df: DataFrame canônico contendo todas as transações.

    Returns:
        DataFrame enriquecido com as features temporais pontuais.
    """
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df = df.sort_values(by=["customer_id", "order_date", "order_time"]).reset_index(drop=True)

    # Desconto percentual
    df["discount_pct"] = np.where(
        df["gross_sales"] > 0,
        (df["discount_amount"] / df["gross_sales"]) * 100,
        0.0,
    )

    # Variáveis retroativas por cliente
    grouped = df.groupby("customer_id")

    # Contagem de pedidos prévios (cumcount é 0-indexed)
    df["orders_count_prior"] = grouped.cumcount()

    # Gasto prévio acumulado (shift para excluir o pedido atual)
    df["spend_prior"] = (grouped["net_sales"].cumsum() - df["net_sales"]).clip(lower=0.0)

    # Dias desde o pedido anterior
    prev_date = grouped["order_date"].shift(1)
    df["days_since_last_order"] = (df["order_date"] - prev_date).dt.days.fillna(-1.0)

    # Rótulo alvo supervisionado (Cancelado ou Devolvido)
    df["is_unfavorable"] = df["order_status"].isin(["Returned", "Cancelled"]).astype(int)

    return df


def split_out_of_time(
    df: pd.DataFrame, cutoff_date: str = "2025-01-01"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Divide os dados em partição temporal estrita (Treino/Validação vs. Teste Cego).

    Args:
        df: DataFrame enriquecido com features point-in-time.
        cutoff_date: Data de corte no formato 'YYYY-MM-DD'.

    Returns:
        Tupla contendo (df_train, df_test).
    """
    cutoff = pd.to_datetime(cutoff_date)
    train_mask = df["order_date"] < cutoff
    test_mask = df["order_date"] >= cutoff

    df_train = df[train_mask].copy()
    df_test = df[test_mask].copy()
    return df_train, df_test


def get_feature_matrix(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Extrai a matriz de features At-Purchase e a série alvo, sem vazamento.

    Args:
        df: DataFrame enriquecido.

    Returns:
        Tupla (X, y) pronta para transformações e modelagem.
    """
    feature_cols = AT_PURCHASE_NUMERIC_COLS + AT_PURCHASE_CATEGORICAL_COLS
    X = df[feature_cols].copy()
    y = df["is_unfavorable"].copy()
    return X, y
