"""Cálculo dinâmico de Recência, Frequência e Valor Monetário (RFM)."""

import pandas as pd


def calculate_rfm_table(df: pd.DataFrame, reference_date: str | None = None) -> pd.DataFrame:
    """Calcula métricas RFM por cliente até a data de referência.

    Args:
        df: DataFrame com transações (deve conter customer_id, order_date, order_id, net_sales).
        reference_date: Data limite (string 'YYYY-MM-DD'). Se None, usa max(order_date) + 1 dia.

    Returns:
        pd.DataFrame com colunas [recency_days, frequency, monetary_value, avg_ticket].
    """
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])

    if reference_date is not None:
        ref_dt = pd.to_datetime(reference_date)
        df = df[df["order_date"] <= ref_dt]
    else:
        ref_dt = df["order_date"].max() + pd.Timedelta(days=1)

    rfm = (
        df.groupby("customer_id")
        .agg(
            last_order_date=("order_date", "max"),
            frequency=("order_id", "nunique"),
            monetary_value=("net_sales", "sum"),
        )
        .reset_index()
    )

    rfm["recency_days"] = (ref_dt - rfm["last_order_date"]).dt.days
    rfm["avg_ticket"] = rfm["monetary_value"] / rfm["frequency"]

    return rfm[["customer_id", "recency_days", "frequency", "monetary_value", "avg_ticket"]]
