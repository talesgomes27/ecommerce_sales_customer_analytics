"""Geração e exportação das figuras editoriais canônicas (300 DPI, aspect=1, sns.despine)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.data.loader import load_canonical_data, load_customer_master
from src.evaluation.metrics import (
    analyze_marketing_acquisition_efficiency,
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

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#333333"
plt.rcParams["axes.linewidth"] = 0.8


def generate_all_figures(project_root: Path, output_dir: Path) -> dict[str, Path]:
    """Executa o pipeline e exporta as 5 figuras canônicas em alta resolução (300 DPI)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures: dict[str, Path] = {}

    raw_path = project_root / "ecommerce_sales_customer_analytics_150k.csv"
    cust_path = project_root / "customer_master.csv"

    print("Carregando bases canônicas...")
    df = load_canonical_data(raw_path)
    df_cust = load_customer_master(cust_path)

    # -------------------------------------------------------------
    # FIG-01: Pricing e Destruição de Margem (Painel Duplo Aspect 1:1)
    # -------------------------------------------------------------
    print("Gerando FIG-01: Pricing Elasticity...")
    df["discount_pct"] = np.where(
        df["gross_sales"] > 0,
        (df["discount_amount"] / df["gross_sales"]) * 100,
        0.0,
    )
    analyze_discount_elasticity(df)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    for ax in axes:
        ax.set_box_aspect(1)
        sns.despine(ax=ax)

    # Amostra de 5.000 pontos para o scatter não sobrecarregar
    sample_scatter = df.sample(n=5000, random_state=42)
    sns.scatterplot(
        data=sample_scatter,
        x="discount_pct",
        y="profit_margin_percentage",
        alpha=0.25,
        s=15,
        color="#2b5c8f",
        ax=axes[0],
    )
    axes[0].axhline(0, color="#d9534f", linestyle="--", linewidth=1.5, label="Margem Zero")
    axes[0].axvline(
        35.9, color="#e67e22", linestyle=":", linewidth=1.5, label="D* Limiar Crítico (35,9%)"
    )
    axes[0].set_title("(a) Desconto vs. Margem de Lucro", fontsize=11, fontweight="bold", pad=10)
    axes[0].set_xlabel("Desconto Concedido (%)", fontsize=10)
    axes[0].set_ylabel("Margem de Lucro Real (%)", fontsize=10)
    axes[0].set_ylim(-65, 85)
    axes[0].legend(loc="lower left", frameon=True, fontsize=8)
    axes[0].grid(True, alpha=0.25, linestyle="--")

    # Painel (b): Distribuição de Prejuízo
    unprof = df[df["profit"] < 0]
    sns.histplot(
        data=unprof,
        x="profit_margin_percentage",
        bins=25,
        kde=True,
        color="#c0392b",
        ax=axes[1],
    )
    axes[1].set_title(
        "(b) Distribuição das 1.296 Vendas no Prejuízo", fontsize=11, fontweight="bold", pad=10
    )
    axes[1].set_xlabel("Margem Negativa (%)", fontsize=10)
    axes[1].set_ylabel("Frequência de Transações", fontsize=10)
    axes[1].annotate(
        "Perda Total: $201.225,34\nDesconto Médio: 51,7%",
        xy=(-40, 90),
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.4", "fc": "#fdf2e9", "ec": "#e67e22", "lw": 1},
    )
    axes[1].grid(True, alpha=0.25, linestyle="--")

    fig_path_1 = output_dir / "fig_01_pricing_elasticity.png"
    fig.savefig(fig_path_1, dpi=300)
    plt.close(fig)
    figures["fig_01"] = fig_path_1

    # -------------------------------------------------------------
    # FIG-02: Eficiência de Canais de Marketing LTV / CAC
    # -------------------------------------------------------------
    print("Gerando FIG-02: Marketing Acquisition ROI...")
    mkt_stats = analyze_marketing_acquisition_efficiency(df, df_cust)

    fig, ax = plt.subplots(figsize=(8, 5.2), constrained_layout=True)
    sns.despine(ax=ax)

    bars = ax.barh(
        mkt_stats["marketing_channel"],
        mkt_stats["ltv_to_cac_ratio"],
        color="#2471a3",
        edgecolor="#1b4f72",
        height=0.6,
    )
    ax.invert_yaxis()
    ax.set_title(
        "Retorno sobre Custo de Aquisição (Razão LTV / CAC) por Canal",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )
    ax.set_xlabel("Razão LTV / CAC (Receita Gerada por Dólar Investido)", fontsize=10)
    ax.set_ylabel("Canal de Marketing", fontsize=10)
    ax.grid(True, axis="x", alpha=0.25, linestyle="--")

    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + 3,
            bar.get_y() + bar.get_height() / 2,
            f"{w:.1f}x",
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
        )

    fig_path_2 = output_dir / "fig_02_acquisition_efficiency.png"
    fig.savefig(fig_path_2, dpi=300)
    plt.close(fig)
    figures["fig_02"] = fig_path_2

    # -------------------------------------------------------------
    # FIG-03: Segmentação RFM e Concentração de Valor (Pareto)
    # -------------------------------------------------------------
    print("Gerando FIG-03: RFM Segmentation & Pareto...")
    rfm_table = calculate_rfm_table(df)
    rfm_clustered, _, centroids = fit_rfm_kmeans(rfm_table, n_clusters=4, random_state=42)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    for ax in axes:
        ax.set_box_aspect(1)
        sns.despine(ax=ax)

    # Painel (a): Projeção PCA 2D dos Clusters
    X_rfm = rfm_clustered[["recency_days", "frequency", "monetary_value"]]
    X_log = np.log1p(X_rfm)
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(StandardScaler().fit_transform(X_log))
    rfm_clustered["pca1"] = X_pca[:, 0]
    rfm_clustered["pca2"] = X_pca[:, 1]

    colors = {
        "Champions": "#27ae60",
        "Loyal Customers": "#2980b9",
        "At-Risk High-Value": "#e67e22",
        "Occasional / Low-Value": "#7f8c8d",
    }
    for label, col in colors.items():
        subset = rfm_clustered[rfm_clustered["cluster_label"] == label]
        axes[0].scatter(subset["pca1"], subset["pca2"], c=col, label=label, alpha=0.4, s=12)

    axes[0].set_title(
        "(a) Clusters Comportamentais RFM (PCA)", fontsize=11, fontweight="bold", pad=10
    )
    axes[0].set_xlabel("Componente Principal 1", fontsize=10)
    axes[0].set_ylabel("Componente Principal 2", fontsize=10)
    axes[0].legend(loc="lower right", frameon=True, fontsize=8)
    axes[0].grid(True, alpha=0.25, linestyle="--")

    # Painel (b): Curva de Pareto de Receita
    sorted_cust = rfm_clustered.sort_values(by="monetary_value", ascending=False).reset_index(
        drop=True
    )
    cum_rev = sorted_cust["monetary_value"].cumsum() / sorted_cust["monetary_value"].sum() * 100
    cum_cust = (np.arange(1, len(sorted_cust) + 1) / len(sorted_cust)) * 100

    axes[1].plot(cum_cust, cum_rev, color="#1b4f72", linewidth=2.5, label="Curva Empírica")
    axes[1].plot([0, 100], [0, 100], color="#95a5a6", linestyle=":", label="Linha de Igualdade")
    axes[1].axvline(20, color="#d9534f", linestyle="--", alpha=0.7)
    axes[1].axhline(
        cum_rev.iloc[int(len(cum_rev) * 0.2)], color="#d9534f", linestyle="--", alpha=0.7
    )
    rev_20 = cum_rev.iloc[int(len(cum_rev) * 0.2)]
    axes[1].annotate(
        f"Top 20% clientes =\n{rev_20:.1f}% da receita",
        xy=(20, rev_20),
        xytext=(35, rev_20 - 15),
        arrowprops={"arrowstyle": "->", "color": "#d9534f", "lw": 1.2},
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.3", "fc": "#fdf2e9", "ec": "#d9534f"},
    )
    axes[1].set_title(
        "(b) Concentração de Receita (Curva de Pareto)", fontsize=11, fontweight="bold", pad=10
    )
    axes[1].set_xlabel("% Acumulado de Clientes", fontsize=10)
    axes[1].set_ylabel("% Acumulado de Receita", fontsize=10)
    axes[1].legend(loc="lower right", frameon=True, fontsize=8)
    axes[1].grid(True, alpha=0.25, linestyle="--")

    fig_path_3 = output_dir / "fig_03_rfm_segmentation.png"
    fig.savefig(fig_path_3, dpi=300)
    plt.close(fig)
    figures["fig_03"] = fig_path_3

    # -------------------------------------------------------------
    # FIG-04: Classificação Preventiva At-Purchase (PR-Curve + Gain)
    # -------------------------------------------------------------
    print("Gerando FIG-04: At-Purchase Model Evaluation & Gain...")
    pit_df = compute_point_in_time_features(df)
    train_df, test_df = split_out_of_time(pit_df, cutoff_date="2025-01-01")

    X_train, y_train = get_feature_matrix(train_df)
    X_test, y_test = get_feature_matrix(test_df)

    baseline_pipe = train_baseline_model(
        X_train, y_train, AT_PURCHASE_NUMERIC_COLS, AT_PURCHASE_CATEGORICAL_COLS
    )
    lgbm_pipe, importance_df = train_lightgbm_model(
        X_train, y_train, AT_PURCHASE_NUMERIC_COLS, AT_PURCHASE_CATEGORICAL_COLS, n_estimators=100
    )

    base_eval = evaluate_classifier_out_of_time(baseline_pipe, X_test, y_test)
    lgbm_eval = evaluate_classifier_out_of_time(lgbm_pipe, X_test, y_test)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    for ax in axes:
        ax.set_box_aspect(1)
        sns.despine(ax=ax)

    # Painel (a): Curvas Precision-Recall
    base_rate = float(y_test.mean())
    axes[0].plot(
        base_eval["curve_data"]["recalls"],
        base_eval["curve_data"]["precisions"],
        color="#7f8c8d",
        linestyle="--",
        label=f"Baseline Logit (PR-AUC = {base_eval['pr_auc']:.3f})",
    )
    axes[0].plot(
        lgbm_eval["curve_data"]["recalls"],
        lgbm_eval["curve_data"]["precisions"],
        color="#2980b9",
        linewidth=2,
        label=f"LightGBM (PR-AUC = {lgbm_eval['pr_auc']:.3f})",
    )
    axes[0].axhline(
        base_rate, color="#c0392b", linestyle=":", label=f"Taxa Base ({base_rate * 100:.1f}%)"
    )
    axes[0].set_title(
        "(a) Curvas Precision-Recall (Teste Cego 2025)", fontsize=11, fontweight="bold", pad=10
    )
    axes[0].set_xlabel("Recall (Revocação)", fontsize=10)
    axes[0].set_ylabel("Precision (Precisão)", fontsize=10)
    axes[0].set_ylim(0, 1.05)
    axes[0].legend(loc="upper right", frameon=True, fontsize=8)
    axes[0].grid(True, alpha=0.25, linestyle="--")

    # Painel (b): Importância por Ganho Real (Gain)
    top10_gain = importance_df.head(10).sort_values(by="gain_importance", ascending=True)
    axes[1].barh(
        top10_gain["feature"],
        top10_gain["gain_importance"],
        color="#27ae60",
        edgecolor="#1e8449",
        height=0.6,
    )
    axes[1].set_title(
        "(b) Top 10 Preditores por Ganho Real (Gain)", fontsize=11, fontweight="bold", pad=10
    )
    axes[1].set_xlabel("Importância Factual (Ganho na Redução de Erro)", fontsize=10)
    axes[1].grid(True, axis="x", alpha=0.25, linestyle="--")

    fig_path_4 = output_dir / "fig_04_at_purchase_evaluation.png"
    fig.savefig(fig_path_4, dpi=300)
    plt.close(fig)
    figures["fig_04"] = fig_path_4

    # -------------------------------------------------------------
    # FIG-05: Penalidade por Atraso Logístico na Avaliação (H5)
    # -------------------------------------------------------------
    print("Gerando FIG-05: Delivery Delay Impact...")
    delay_res = compute_delivery_delay_hypothesis(df)

    completed = df[
        (df["order_status"] == "Completed")
        & df["customer_rating"].notnull()
        & df["delivery_days"].notnull()
        & df["estimated_delivery_days"].notnull()
    ].copy()
    completed["Status da Entrega"] = np.where(
        completed["delivery_days"] > completed["estimated_delivery_days"],
        "Atrasado",
        "No Prazo",
    )

    fig, ax = plt.subplots(figsize=(7, 5.2), constrained_layout=True)
    sns.despine(ax=ax)

    sns.boxplot(
        data=completed,
        x="Status da Entrega",
        y="customer_rating",
        palette=["#2ecc71", "#e74c3c"],
        width=0.45,
        ax=ax,
    )
    ax.set_title(
        "Impacto do Atraso Logístico na Avaliação do Cliente",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )
    ax.set_xlabel("Cumprimento do Prazo de Entrega", fontsize=10)
    ax.set_ylabel("Avaliação do Cliente (1 a 5 estrelas)", fontsize=10)
    ax.grid(True, axis="y", alpha=0.25, linestyle="--")

    p_val_str = (
        "< 0,001"
        if delay_res["mann_whitney_pvalue"] < 0.001
        else f"= {delay_res['mann_whitney_pvalue']:.4f}"
    )
    ax.annotate(
        f"Média No Prazo: {delay_res['mean_rating_on_time']:.2f}\n"
        f"Média Atrasado: {delay_res['mean_rating_delayed']:.2f}\n"
        f"Penalidade: -{delay_res['rating_penalty']:.2f} estrelas\n"
        f"Mann-Whitney U: p {p_val_str}\n"
        f"Cohen's d: {delay_res['cohens_d']:.2f}",
        xy=(0.5, 2.0),
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.4", "fc": "#f4f6f7", "ec": "#bdc3c7"},
    )

    fig_path_5 = output_dir / "fig_05_delivery_delay_impact.png"
    fig.savefig(fig_path_5, dpi=300)
    plt.close(fig)
    figures["fig_05"] = fig_path_5

    print("Todas as 5 figuras geradas com sucesso!")
    return figures


if __name__ == "__main__":
    proj_root = Path(__file__).resolve().parent.parent.parent
    figs_dir = proj_root / "reports" / "figures"
    generate_all_figures(proj_root, figs_dir)
