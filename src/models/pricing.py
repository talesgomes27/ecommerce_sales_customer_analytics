"""Modelagem econométrica e empírica da relação entre desconto, volume e margem de lucro."""

from typing import Any

import numpy as np
import pandas as pd


def analyze_discount_elasticity(df: pd.DataFrame) -> dict[str, Any]:
    """Analisa a sensibilidade e destruição de margem em função de descontos.

    Identifica a curva de rentabilidade, o limiar de desconto onde surgem
    operações no prejuízo (D*) e quantifica a destruição financeira de caixa.

    Args:
        df: DataFrame de transações com [gross_sales, discount_amount, profit, profit_margin_percentage].

    Returns:
        Dicionário com métricas-chave de precificação e dados agrupados em buckets.
    """
    df = df.copy()
    df["discount_pct"] = np.where(
        df["gross_sales"] > 0,
        (df["discount_amount"] / df["gross_sales"]) * 100,
        0.0,
    )

    unprofitable = df[df["profit"] < 0]
    profitable = df[df["profit"] >= 0]

    min_discount_unprofitable = (
        float(unprofitable["discount_pct"].min()) if len(unprofitable) > 0 else 0.0
    )
    total_loss_amount = float(unprofitable["profit"].sum()) if len(unprofitable) > 0 else 0.0
    mean_discount_unprof = (
        float(unprofitable["discount_pct"].mean()) if len(unprofitable) > 0 else 0.0
    )
    mean_discount_prof = float(profitable["discount_pct"].mean()) if len(profitable) > 0 else 0.0

    # Agrupamento em faixas de 5% de desconto
    bins = np.arange(0, 70, 5)
    df["disc_bucket"] = pd.cut(df["discount_pct"], bins=bins)

    bucket_stats = (
        df.groupby("disc_bucket", observed=False)
        .agg(
            total_orders=("order_id", "count"),
            mean_margin=("profit_margin_percentage", "mean"),
            median_profit=("profit", "median"),
            unprofitable_orders=("profit", lambda x: int((x < 0).sum())),
            pct_unprofitable=("profit", lambda x: float((x < 0).mean() * 100)),
        )
        .reset_index()
    )

    # Ponto de inflexão onde a margem média passa a ser negativa
    negative_margin_buckets = bucket_stats[bucket_stats["mean_margin"] < 0]
    critical_threshold = (
        float(negative_margin_buckets.iloc[0]["disc_bucket"].left)
        if len(negative_margin_buckets) > 0
        else 55.0
    )

    return {
        "unprofitable_orders_count": len(unprofitable),
        "unprofitable_orders_pct": float(len(unprofitable) / len(df) * 100),
        "total_loss_dollars": total_loss_amount,
        "mean_discount_unprofitable": mean_discount_unprof,
        "mean_discount_profitable": mean_discount_prof,
        "first_loss_discount_pct": min_discount_unprofitable,
        "critical_inflection_threshold_pct": critical_threshold,
        "bucket_stats": bucket_stats,
    }
