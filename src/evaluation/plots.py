"""Geração e exportação das figuras editoriais canônicas (300 DPI, aspect=1, sns.despine)."""

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.decomposition import PCA
from sklearn.metrics import brier_score_loss
from sklearn.preprocessing import StandardScaler

from src.data.loader import (
    load_canonical_data,
    load_customer_master,
    load_order_items,
    load_product_catalog,
)
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


def generate_data_leakage_boundary_figure(output_path: Path) -> Path:
    """Gera o diagrama infográfico de fronteira temporal e prevenção de data leakage."""
    fig, ax = plt.subplots(figsize=(14.5, 6.5), dpi=300)
    ax.set_facecolor("#ffffff")
    fig.patch.set_facecolor("#ffffff")

    ax.set_xlim(0, 14.5)
    ax.set_ylim(0, 7.2)
    ax.axis("off")

    # Box 1: At-Purchase (Verde)
    box1 = patches.FancyBboxPatch(
        (0.4, 0.5),
        4.3,
        6.2,
        boxstyle="round,pad=0.2",
        facecolor="#f4fbf7",
        edgecolor="#27ae60",
        linewidth=2.0,
    )
    ax.add_patch(box1)
    ax.text(
        2.55,
        6.25,
        "1. MOMENTO DA COMPRA (At-Purchase)\n[Atributos Permitidos para Treino e Inferência]",
        fontsize=11,
        fontweight="bold",
        color="#196f3d",
        ha="center",
        va="center",
    )

    items_green = [
        ("Dados Cadastrais do Cliente", "customer_age, gender, region, country, customer_segment"),
        ("Composição do Carrinho de Compras", "quantity, gross_sales, tax_amount, shipping_cost"),
        (
            "Histórico Retroativo (Point-in-Time)",
            "orders_count_prior, spend_prior, days_since_last_order",
        ),
        (
            "Canais de Venda e Logística Inicial",
            "sales_channel, marketing_channel, warehouse, shipping_method",
        ),
    ]

    y_pos = 5.0
    for title, desc in items_green:
        rect = patches.FancyBboxPatch(
            (0.6, y_pos - 0.45),
            3.9,
            0.9,
            boxstyle="round,pad=0.1",
            facecolor="#ffffff",
            edgecolor="#a9dfbf",
            linewidth=1.2,
        )
        ax.add_patch(rect)
        ax.text(
            0.8,
            y_pos + 0.12,
            f"[VÁLIDO] {title}",
            fontsize=9.2,
            fontweight="bold",
            color="#196f3d",
            va="center",
        )
        ax.text(0.8, y_pos - 0.18, desc, fontsize=7.8, color="#333333", va="center")
        y_pos -= 1.15

    # Seta para o Checkout
    ax.annotate(
        "",
        xy=(5.4, 3.6),
        xytext=(4.9, 3.6),
        arrowprops={"arrowstyle": "->", "lw": 2.5, "color": "#2980b9"},
    )

    # Box 2: Checkout / Inferência (Azul)
    box2 = patches.FancyBboxPatch(
        (5.5, 1.8),
        2.9,
        3.6,
        boxstyle="round,pad=0.2",
        facecolor="#ebf5fb",
        edgecolor="#2980b9",
        linewidth=2.0,
    )
    ax.add_patch(box2)
    ax.text(
        6.95,
        4.9,
        "CHECKOUT EM TEMPO REAL\nMOTOR DE INFERÊNCIA",
        fontsize=10.5,
        fontweight="bold",
        color="#1b4f72",
        ha="center",
        va="center",
    )
    ax.text(
        6.95,
        3.4,
        "Pipeline LightGBM\n\nPredição da Probabilidade:\nP(Y = 1 | At-Purchase)\n\nLimiar de Custo Mínimo:\nτ* = 0,55 (Economia: $92k/ano)\n\nDisparo Preventivo:\nAlerta no CD & Verificação 2D",
        fontsize=8.5,
        color="#1a252f",
        ha="center",
        va="center",
    )

    # Linha da Fronteira Temporal (Vermelha)
    ax.plot([8.8, 8.8], [0.3, 6.9], color="#c0392b", linestyle="--", linewidth=2.5)
    ax.text(
        8.8,
        7.05,
        "FRONTEIRA TEMPORAL INVIOLÁVEL",
        fontsize=9.5,
        fontweight="bold",
        color="#922b21",
        ha="center",
        va="bottom",
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": "#fadbd8",
            "edgecolor": "#c0392b",
            "lw": 1.2,
        },
    )

    # Box 3: Pós-Venda (Vermelho / Vazamento)
    box3 = patches.FancyBboxPatch(
        (9.2, 0.5),
        4.9,
        6.2,
        boxstyle="round,pad=0.2",
        facecolor="#fdf2f2",
        edgecolor="#c0392b",
        linewidth=2.0,
    )
    ax.add_patch(box3)
    ax.text(
        11.65,
        6.25,
        "2. PÓS-VENDA & EXPEDIÇÃO\n[Descarte Estrito: Prevenção contra Data Leakage]",
        fontsize=11,
        fontweight="bold",
        color="#922b21",
        ha="center",
        va="center",
    )

    items_red = [
        (
            "Vazamento de Alvo por Nulos Condicionais",
            "delivery_days, customer_rating, review_sentiment\n(24.557 nulos em 100% dos cancelados e devolvidos)",
        ),
        (
            "Desfecho Financeiro Determinístico",
            'payment_status == "Refunded" (100% Devolução)\npayment_status == "Failed" (100% Cancelamento)',
        ),
        (
            "Vazamento Look-Ahead (Visão de Futuro)",
            "customer_lifetime_value estático de 5 anos\n(Calculado após o encerramento de 2025)",
        ),
        (
            "Atalhos Sintéticos do Dataset Original",
            "discount_amount = 0 e loyalty_points = 0\n(Zerados artificialmente em pedidos abortados)",
        ),
    ]

    y_pos = 5.0
    for title, desc in items_red:
        rect = patches.FancyBboxPatch(
            (9.4, y_pos - 0.45),
            4.5,
            0.9,
            boxstyle="round,pad=0.1",
            facecolor="#ffffff",
            edgecolor="#f5b7b1",
            linewidth=1.2,
        )
        ax.add_patch(rect)
        ax.text(
            9.6,
            y_pos + 0.14,
            f"[DESCARTE] {title}",
            fontsize=9.0,
            fontweight="bold",
            color="#922b21",
            va="center",
        )
        ax.text(9.6, y_pos - 0.18, desc, fontsize=7.6, color="#444444", va="center")
        y_pos -= 1.15

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def generate_all_figures(project_root: Path, output_dir: Path) -> dict[str, Path]:
    """Executa o pipeline e exporta todas as figuras canônicas em alta resolução (300 DPI)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figures: dict[str, Path] = {}

    print("Gerando FIG-00: Data Leakage Boundary Diagram...")
    fig_path_0 = output_dir / "fig_timeline_leakage.png"
    generate_data_leakage_boundary_figure(fig_path_0)
    figures["fig_00"] = fig_path_0

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
        hue="Status da Entrega",
        legend=False,
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

    # -------------------------------------------------------------
    # FIG-06: Análise de Quadrante e Elasticidade de Categorias
    # -------------------------------------------------------------
    print("Gerando FIG-06: Category Quadrant & Pricing Volume...")
    cat_path = project_root / "product_catalog.csv"
    items_path = project_root / "order_items.csv"
    catalog = load_product_catalog(cat_path)
    items = load_order_items(items_path)

    merged_cat = items.merge(
        catalog[["product_id", "product_category"]],
        on="product_id",
        how="left",
    )
    cat_summary = (
        merged_cat.groupby("product_category")
        .agg(
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            quantity=("quantity", "sum"),
            avg_price=("unit_price", "mean"),
        )
        .reset_index()
    )
    cat_summary["margin_pct"] = (cat_summary["profit"] / cat_summary["net_sales"]) * 100
    cat_summary["sales_millions"] = cat_summary["net_sales"] / 1e6
    cat_summary["quantity_k"] = cat_summary["quantity"] / 1000

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    for ax in axes:
        ax.set_box_aspect(1)
        sns.despine(ax=ax)

    # Painel (a): Matriz de Quadrante Faturamento vs Margem Líquida
    mean_sales = cat_summary["sales_millions"].mean()
    mean_margin = (cat_summary["profit"].sum() / cat_summary["net_sales"].sum()) * 100

    axes[0].scatter(
        cat_summary["sales_millions"],
        cat_summary["margin_pct"],
        s=cat_summary["quantity_k"] * 12,
        color="#2980b9",
        alpha=0.6,
        edgecolor="#1b4f72",
        linewidth=1.2,
    )
    axes[0].axvline(mean_sales, color="#7f8c8d", linestyle="--", linewidth=1.2, alpha=0.7)
    axes[0].axhline(mean_margin, color="#7f8c8d", linestyle="--", linewidth=1.2, alpha=0.7)

    for _, row in cat_summary.iterrows():
        offset_y = 0.7 if row["margin_pct"] >= mean_margin else -1.2
        offset_x = 0.5 if row["sales_millions"] < 30 else -3.5
        axes[0].text(
            row["sales_millions"] + offset_x,
            row["margin_pct"] + offset_y,
            row["product_category"],
            fontsize=8,
            fontweight="semibold",
            color="#2c3e50",
            ha="center",
        )

    axes[0].set_title(
        "(a) Quadrante Receita ($M) vs. Margem Líquida (%)",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )
    axes[0].set_xlabel("Receita Líquida Total (Milhões US$)", fontsize=10)
    axes[0].set_ylabel("Margem de Lucro Real (%)", fontsize=10)
    axes[0].set_ylim(30, 58)
    axes[0].set_xlim(0, 46)
    axes[0].grid(True, alpha=0.25, linestyle="--")

    # Painel (b): Preço Médio Unitário vs Volume Total Vendido
    axes[1].scatter(
        cat_summary["avg_price"],
        cat_summary["quantity_k"],
        s=120,
        color="#27ae60",
        alpha=0.7,
        edgecolor="#1e8449",
        linewidth=1.2,
    )

    for _, row in cat_summary.iterrows():
        axes[1].text(
            row["avg_price"] + 15,
            row["quantity_k"],
            row["product_category"],
            fontsize=8,
            fontweight="semibold",
            color="#2c3e50",
            va="center",
        )

    axes[1].set_title(
        "(b) Preço Médio Unitário vs. Volume de Itens (k)",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )
    axes[1].set_xlabel("Preço Médio Unitário (US$)", fontsize=10)
    axes[1].set_ylabel("Volume Vendido (Milhares de Unidades)", fontsize=10)
    axes[1].set_xlim(0, 920)
    axes[1].set_ylim(44, 68)
    axes[1].grid(True, alpha=0.25, linestyle="--")

    fig_path_6 = output_dir / "fig_06_category_quadrant_analysis.png"
    fig.savefig(fig_path_6, dpi=300)
    plt.close(fig)
    figures["fig_06"] = fig_path_6

    # -------------------------------------------------------------
    # FIG-07: Diagnóstico Operacional: Motivos de Devolução e Meios de Pagamento
    # -------------------------------------------------------------
    print("Gerando FIG-07: Operational Diagnostics (Returns & Payment)...")
    returns_df = df[df["order_status"] == "Returned"]
    reason_counts = returns_df["return_reason"].value_counts().sort_values(ascending=True)
    reason_pct = (reason_counts / len(returns_df)) * 100

    pay_status = (
        df.groupby("payment_method")
        .agg(
            total=("order_id", "count"),
            returned=("order_status", lambda s: (s == "Returned").sum()),
            cancelled=("order_status", lambda s: (s == "Cancelled").sum()),
        )
        .reset_index()
    )
    pay_status["return_rate"] = (pay_status["returned"] / pay_status["total"]) * 100
    pay_status["cancel_rate"] = (pay_status["cancelled"] / pay_status["total"]) * 100
    pay_status = pay_status.sort_values(by="total", ascending=True)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    for ax in axes:
        ax.set_box_aspect(1)
        sns.despine(ax=ax)

    # Cores destacando falhas operacionais evitáveis
    colors_reason = [
        "#c0392b"
        if r in ["Wrong Product", "Size Issue", "Defective Product", "Product Not as Expected"]
        else "#2980b9"
        for r in reason_counts.index
    ]

    bars_reason = axes[0].barh(
        reason_counts.index,
        reason_counts.values,
        color=colors_reason,
        edgecolor="#333333",
        height=0.6,
        alpha=0.85,
    )
    axes[0].set_title(
        "(a) Motivos de Devolução (9.462 Ocorrências)", fontsize=11, fontweight="bold", pad=10
    )
    axes[0].set_xlabel("Frequência Absoluta de Devoluções", fontsize=10)
    axes[0].grid(True, axis="x", alpha=0.25, linestyle="--")

    for bar, pct in zip(bars_reason, reason_pct.values, strict=False):
        w = bar.get_width()
        axes[0].text(
            w + 18,
            bar.get_y() + bar.get_height() / 2,
            f"{int(w):,} ({pct:.1f}%)",
            va="center",
            ha="left",
            fontsize=8,
            fontweight="semibold",
        )
    axes[0].set_xlim(0, 1500)

    # Painel (b): Taxas de Devolução e Cancelamento por Meio de Pagamento
    y_pos = np.arange(len(pay_status))
    height = 0.35

    axes[1].barh(
        y_pos + height / 2,
        pay_status["return_rate"],
        height=height,
        label="Devoluções (%)",
        color="#e74c3c",
        alpha=0.85,
        edgecolor="#922b21",
    )
    axes[1].barh(
        y_pos - height / 2,
        pay_status["cancel_rate"],
        height=height,
        label="Cancelamentos (%)",
        color="#f39c12",
        alpha=0.85,
        edgecolor="#b9770e",
    )

    axes[1].set_yticks(y_pos)
    axes[1].set_yticklabels(pay_status["payment_method"], fontsize=9)
    axes[1].set_title(
        "(b) Taxas de Falha por Meio de Pagamento", fontsize=11, fontweight="bold", pad=10
    )
    axes[1].set_xlabel("Taxa do Evento sobre o Volume (%)", fontsize=10)
    axes[1].set_xlim(0, 9.5)
    axes[1].legend(loc="lower right", frameon=True, fontsize=8)
    axes[1].grid(True, axis="x", alpha=0.25, linestyle="--")

    fig_path_7 = output_dir / "fig_07_operational_diagnostics_returns_payments.png"
    fig.savefig(fig_path_7, dpi=300)
    plt.close(fig)
    figures["fig_07"] = fig_path_7

    # -------------------------------------------------------------
    # FIG-08: Calibração de Probabilidades e Curva de Custo Operacional
    # -------------------------------------------------------------
    print("Gerando FIG-08: Model Calibration & Cost Trade-off Curve...")
    y_prob_lgbm = lgbm_pipe.predict_proba(X_test)[:, 1]
    prob_true, prob_pred = calibration_curve(y_test, y_prob_lgbm, n_bins=10)
    brier = brier_score_loss(y_test, y_prob_lgbm)

    thresholds_sim = np.linspace(0.10, 0.90, 33)
    sim_costs = []
    for t in thresholds_sim:
        p_t = (y_prob_lgbm >= t).astype(int)
        fn_count = np.sum((y_test == 1) & (p_t == 0))
        fp_count = np.sum((y_test == 0) & (p_t == 1))
        sim_costs.append(fn_count * 45.0 + fp_count * 8.0)

    opt_idx = int(np.argmin(sim_costs))
    opt_t = thresholds_sim[opt_idx]
    opt_cost = sim_costs[opt_idx]
    base_cost = np.sum(y_test == 1) * 45.0

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    for ax in axes:
        ax.set_box_aspect(1)
        sns.despine(ax=ax)

    # Painel (a): Reliability Curve (Calibração)
    axes[0].plot(
        [0, 1], [0, 1], color="#7f8c8d", linestyle="--", linewidth=1.5, label="Calibração Ideal"
    )
    axes[0].plot(
        prob_pred,
        prob_true,
        marker="o",
        color="#2980b9",
        linewidth=2,
        markersize=6,
        label=f"LightGBM (Brier = {brier:.4f})",
    )
    axes[0].set_title(
        "(a) Curva de Calibração (Reliability Curve)", fontsize=11, fontweight="bold", pad=10
    )
    axes[0].set_xlabel("Probabilidade Predita P(Y = 1)", fontsize=10)
    axes[0].set_ylabel("Fração Real de Positivos", fontsize=10)
    axes[0].set_xlim(-0.02, 1.02)
    axes[0].set_ylim(-0.02, 1.02)
    axes[0].legend(loc="upper left", frameon=True, fontsize=8)
    axes[0].grid(True, alpha=0.25, linestyle="--")

    # Painel (b): Curva de Custo Operacional por Limiar
    axes[1].plot(
        thresholds_sim, sim_costs, color="#c0392b", linewidth=2.5, label="Custo Operacional C(τ)"
    )
    axes[1].axhline(
        base_cost,
        color="#7f8c8d",
        linestyle=":",
        linewidth=1.5,
        label=f"Sem Modelo (FN Total = ${base_cost:,.0f})",
    )
    axes[1].scatter(
        [opt_t], [opt_cost], color="#27ae60", s=130, zorder=5, label=f"Ótimo τ* = {opt_t:.2f}"
    )

    axes[1].annotate(
        f"Mínimo Global:\nτ* = {opt_t:.2f}\nCusto: ${opt_cost:,.0f}\nEconomia: ${base_cost - opt_cost:,.0f}",
        xy=(opt_t, opt_cost),
        xytext=(opt_t + 0.08, opt_cost + 25000),
        arrowprops={"arrowstyle": "->", "color": "#27ae60", "lw": 1.5},
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.4", "fc": "#eafaf1", "ec": "#27ae60", "lw": 1.2},
    )

    axes[1].set_title(
        "(b) Custo Operacional vs. Limiar de Decisão (τ)", fontsize=11, fontweight="bold", pad=10
    )
    axes[1].set_xlabel("Limiar de Decisão Operacional (τ)", fontsize=10)
    axes[1].set_ylabel("Custo Total Estimado em Dólares (US$)", fontsize=10)
    axes[1].legend(loc="upper left", frameon=True, fontsize=8)
    axes[1].grid(True, alpha=0.25, linestyle="--")

    fig_path_8 = output_dir / "fig_08_model_calibration_and_cost_curve.png"
    fig.savefig(fig_path_8, dpi=300)
    plt.close(fig)
    figures["fig_08"] = fig_path_8

    print("Todas as 8 figuras editoriais geradas com sucesso a 300 DPI!")
    return figures


if __name__ == "__main__":
    proj_root = Path(__file__).resolve().parent.parent.parent
    figs_dir = proj_root / "reports" / "figures"
    generate_all_figures(proj_root, figs_dir)
