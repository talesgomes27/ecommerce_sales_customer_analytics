"""Métricas de avaliação, diagnóstico preditivo, testes de hipótese e ROI de aquisição."""

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def evaluate_classifier_out_of_time(
    model: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    cost_fp: float = 1.0,
    cost_fn: float = 5.0,
) -> dict[str, Any]:
    """Avalia o modelo preditivo no conjunto de teste cego Out-of-Time.

    Computa PR-AUC, ROC-AUC, Brier Score, e calibra o limiar ótimo de corte
    fundamentado na matriz de custo operacional de negócio.

    Args:
        model: Estimador treinado (com método predict_proba).
        X_test: Matriz de features do teste.
        y_test: Rótulo real do teste.
        cost_fp: Custo relativo de um alarme falso (Falso Positivo).
        cost_fn: Custo relativo de um cancelamento/devolução não detectado (Falso Negativo).

    Returns:
        Dicionário com métricas pontuais, curvas e limiar de custo calibrado.
    """
    y_probs = model.predict_proba(X_test)[:, 1]

    pr_auc = float(average_precision_score(y_test, y_probs))
    roc_auc = float(roc_auc_score(y_test, y_probs))
    brier = float(brier_score_loss(y_test, y_probs))

    precisions, recalls, thresholds = precision_recall_curve(y_test, y_probs)
    fpr, tpr, _ = roc_curve(y_test, y_probs)

    # Calibração de corte ótimo por custo operacional
    best_threshold = 0.5
    min_cost = float("inf")

    # Amostragem de limiares para otimização de custo
    cand_thresholds = np.linspace(0.1, 0.9, 81)
    costs = []
    for th in cand_thresholds:
        preds = (y_probs >= th).astype(int)
        fp = int(((preds == 1) & (y_test == 0)).sum())
        fn = int(((preds == 0) & (y_test == 1)).sum())
        total_cost = fp * cost_fp + fn * cost_fn
        costs.append(total_cost)
        if total_cost < min_cost:
            min_cost = total_cost
            best_threshold = float(th)

    optimal_preds = (y_probs >= best_threshold).astype(int)
    optimal_f1 = float(f1_score(y_test, optimal_preds, zero_division=0))
    optimal_precision = float(precision_score(y_test, optimal_preds, zero_division=0))
    optimal_recall = float(recall_score(y_test, optimal_preds, zero_division=0))

    base_rate = float(y_test.mean())

    return {
        "pr_auc": pr_auc,
        "roc_auc": roc_auc,
        "brier_score": brier,
        "base_rate": base_rate,
        "pr_auc_lift_over_base": pr_auc / base_rate if base_rate > 0 else 1.0,
        "optimal_threshold": best_threshold,
        "optimal_f1": optimal_f1,
        "optimal_precision": optimal_precision,
        "optimal_recall": optimal_recall,
        "curve_data": {
            "precisions": precisions,
            "recalls": recalls,
            "thresholds": thresholds,
            "fpr": fpr,
            "tpr": tpr,
        },
    }


def compute_delivery_delay_hypothesis(df: pd.DataFrame) -> dict[str, Any]:
    """Testa formalmente a hipótese H5 (Penalidade na avaliação por atraso de entrega).

    Aplica o teste de Mann-Whitney U e o teste t de Welch sobre customer_rating
    comparando pedidos concluídos no prazo versus atrasados.

    Args:
        df: DataFrame contendo [order_status, delivery_days, estimated_delivery_days, customer_rating].

    Returns:
        Dicionário com estatísticas descritivas, p-valor e tamanho de efeito.
    """
    completed = df[
        (df["order_status"] == "Completed")
        & df["customer_rating"].notnull()
        & df["delivery_days"].notnull()
        & df["estimated_delivery_days"].notnull()
    ].copy()

    completed["is_delayed"] = completed["delivery_days"] > completed["estimated_delivery_days"]

    on_time = completed[~completed["is_delayed"]]["customer_rating"].values
    delayed = completed[completed["is_delayed"]]["customer_rating"].values

    u_stat, u_pval = stats.mannwhitneyu(on_time, delayed, alternative="two-sided")
    t_stat, t_pval = stats.ttest_ind(on_time, delayed, equal_var=False)

    mean_on_time = float(np.mean(on_time))
    mean_delayed = float(np.mean(delayed))
    diff_means = mean_on_time - mean_delayed

    # Cohen's d
    s_pooled = np.sqrt(
        (
            (len(on_time) - 1) * np.var(on_time, ddof=1)
            + (len(delayed) - 1) * np.var(delayed, ddof=1)
        )
        / (len(on_time) + len(delayed) - 2)
    )
    cohens_d = float(diff_means / s_pooled) if s_pooled > 0 else 0.0

    return {
        "n_on_time": len(on_time),
        "n_delayed": len(delayed),
        "mean_rating_on_time": mean_on_time,
        "mean_rating_delayed": mean_delayed,
        "rating_penalty": diff_means,
        "mann_whitney_u": float(u_stat),
        "mann_whitney_pvalue": float(u_pval),
        "ttest_stat": float(t_stat),
        "ttest_pvalue": float(t_pval),
        "cohens_d": cohens_d,
        "hypothesis_confirmed": bool(u_pval < 0.01 and diff_means > 0),
    }


def analyze_marketing_acquisition_efficiency(
    df_transactions: pd.DataFrame, df_customers: pd.DataFrame
) -> pd.DataFrame:
    """Calcula a relação LTV / CAC por canal de aquisição de marketing (Hipótese H2).

    Cruza a receita líquida acumulada por cliente com o CAC do cadastro.

    Args:
        df_transactions: Transações com [customer_id, marketing_channel, net_sales, profit].
        df_customers: Dimensão de clientes com [customer_id, customer_acquisition_cost].

    Returns:
        DataFrame agregado por canal com CAC médio, LTV médio e razão LTV/CAC.
    """
    cust_spend = (
        df_transactions.groupby(["customer_id", "marketing_channel"])
        .agg(
            total_net_sales=("net_sales", "sum"),
            total_profit=("profit", "sum"),
            order_count=("order_id", "count"),
        )
        .reset_index()
    )

    merged = pd.merge(
        cust_spend, df_customers[["customer_id", "customer_acquisition_cost"]], on="customer_id"
    )

    channel_stats = (
        merged.groupby("marketing_channel")
        .agg(
            total_customers=("customer_id", "count"),
            mean_cac=("customer_acquisition_cost", "mean"),
            mean_ltv=("total_net_sales", "mean"),
            mean_profit_ltv=("total_profit", "mean"),
        )
        .reset_index()
    )

    channel_stats["ltv_to_cac_ratio"] = channel_stats["mean_ltv"] / channel_stats["mean_cac"]
    channel_stats["profit_to_cac_ratio"] = (
        channel_stats["mean_profit_ltv"] / channel_stats["mean_cac"]
    )

    return channel_stats.sort_values(by="ltv_to_cac_ratio", ascending=False).reset_index(drop=True)
