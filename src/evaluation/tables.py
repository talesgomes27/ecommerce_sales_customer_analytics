"""Módulo de geração de tabelas analíticas formatadas via great_tables.

Este módulo encapsula os dataframes agregados e gera tabelas estilizadas
com tipografia executiva, formatação tipada de moedas, porcentagens e
destaques condicionais, sem depender da presença do arquivo bruto de 150k
em ambientes de CI ou repositórios remotos.
"""

import pandas as pd
from great_tables import GT, loc, style


def table_yearly_summary() -> GT:
    """Gera a tabela anual consolidada de indicadores executivos (2021-2025)."""
    data = [
        {
            "year": "2021",
            "orders": 27554,
            "net_sales": 35722650.67,
            "profit": 15325651.87,
            "ticket": 1296.46,
            "margin": 0.4495,
            "return_rate": 0.0662,
            "cancel_rate": 0.0585,
        },
        {
            "year": "2022",
            "orders": 27564,
            "net_sales": 35327882.62,
            "profit": 15167978.69,
            "ticket": 1281.67,
            "margin": 0.4501,
            "return_rate": 0.0662,
            "cancel_rate": 0.0614,
        },
        {
            "year": "2023",
            "orders": 27632,
            "net_sales": 35528143.74,
            "profit": 15247695.95,
            "ticket": 1285.76,
            "margin": 0.4501,
            "return_rate": 0.0683,
            "cancel_rate": 0.0617,
        },
        {
            "year": "2024",
            "orders": 27768,
            "net_sales": 35466452.28,
            "profit": 15292965.09,
            "ticket": 1277.24,
            "margin": 0.4520,
            "return_rate": 0.0703,
            "cancel_rate": 0.0635,
        },
        {
            "year": "2025",
            "orders": 27598,
            "net_sales": 35089134.43,
            "profit": 15112104.16,
            "ticket": 1271.44,
            "margin": 0.4516,
            "return_rate": 0.0715,
            "cancel_rate": 0.0589,
        },
        {
            "year": "Total",
            "orders": 138116,
            "net_sales": 177134263.74,
            "profit": 76146395.76,
            "ticket": 1282.50,
            "margin": 0.4507,
            "return_rate": 0.0685,
            "cancel_rate": 0.0608,
        },
    ]
    df = pd.DataFrame(data)

    gt = (
        GT(df)
        .cols_label(
            year="Ano",
            orders="Transações",
            net_sales="Faturamento Líquido",
            profit="Lucro Operacional",
            ticket="Ticket Médio",
            margin="Margem Média",
            return_rate="Taxa Devolução",
            cancel_rate="Taxa Cancelamento",
        )
        .fmt_currency(columns=["net_sales", "profit", "ticket"], currency="USD", decimals=2)
        .fmt_percent(columns=["margin", "return_rate", "cancel_rate"], decimals=2)
        .fmt_integer(columns=["orders"])
        .tab_style(
            style=style.text(weight="bold"),
            locations=loc.body(rows=[5]),
        )
        .tab_style(
            style=style.borders(sides="top", color="#2c3e50", weight="2px"),
            locations=loc.body(rows=[5]),
        )
        .tab_options(
            table_font_size="13px",
            table_width="100%",
            data_row_padding="5px",
        )
    )
    return gt


def table_methodology() -> GT:
    """Gera a tabela da esteira metodológica do Arquétipo A."""
    data = [
        {
            "stage": "Pré-Código",
            "gate": "Gate 1: Data Discovery & Contracts",
            "focus": "Auditoria das 46 colunas, fechamento algébrico e contratos Pandera",
            "artifacts": "docs/00_archetype.md, docs/01-data-discovery-and-contracts.md",
        },
        {
            "stage": "Pré-Código",
            "gate": "Gate 2: PRD & Hypotheses",
            "focus": "Formulação das hipóteses H1 a H5, matriz de métricas e split temporal",
            "artifacts": "docs/02-PRD-and-specs.md",
        },
        {
            "stage": "Pré-Código",
            "gate": "Gate 3: Architecture & Schema",
            "focus": "Topologia em camadas, registro de ADRs (0001 a 0003) e storyboard",
            "artifacts": "docs/03-architecture-and-schema.md, docs/adr/",
        },
        {
            "stage": "Pré-Código",
            "gate": "Gate 4: Scaffolding & Tools",
            "focus": "Estruturação de diretórios, pyproject.toml, _quarto.yml e scripts",
            "artifacts": "docs/04-scaffolding-and-conventions.md, src/",
        },
        {
            "stage": "Pré-Código",
            "gate": "Gate 5: Implementation Plan",
            "focus": "Plano de cinco fases com TDD, matriz de rastreabilidade e aceite",
            "artifacts": "docs/05-implementation-plan.md",
        },
        {
            "stage": "Execução",
            "gate": "Fase 1: Dados & Contratos",
            "focus": "Implementação de loader.py e validação de contratos em lote",
            "artifacts": "src/data/contracts.py, src/data/loader.py, tests/test_contracts.py",
        },
        {
            "stage": "Execução",
            "gate": "Fase 2: Feature Engineering",
            "focus": "Features point-in-time, RFM dinâmico e split temporal",
            "artifacts": "src/features/builder.py, src/features/rfm.py, tests/test_features.py",
        },
        {
            "stage": "Execução",
            "gate": "Fase 3: Modelagem Estatística",
            "focus": "K-Means com K = 4, curva elástica (D*) e treino LightGBM",
            "artifacts": "src/models/clustering.py, src/models/pricing.py, src/models/train.py",
        },
        {
            "stage": "Execução",
            "gate": "Fase 4: Avaliação & Diagnóstico",
            "focus": "Teste cego 2025 (PR-AUC = 0,578), ganho factual, Mann-Whitney U",
            "artifacts": "src/evaluation/metrics.py, tests/test_models.py",
        },
        {
            "stage": "Execução",
            "gate": "Fase 5: Visualização & Relatório",
            "focus": "Exportação de figuras canônicas 300 DPI e compilação Quarto",
            "artifacts": "src/evaluation/plots.py, reports/index.qmd, _site/",
        },
    ]
    df = pd.DataFrame(data)
    gt = (
        GT(df)
        .cols_label(
            stage="Estágio",
            gate="Gate / Fase",
            focus="Foco Técnico e Decisões Adotadas",
            artifacts="Artefatos e Entregáveis",
        )
        .tab_style(
            style=style.text(weight="bold"),
            locations=loc.body(columns=["stage", "gate"]),
        )
        .tab_options(
            table_font_size="13px",
            table_width="100%",
            data_row_padding="5px",
        )
    )
    return gt


def table_discount_buckets() -> GT:
    """Gera a tabela de rentabilidade por faixas de desconto."""
    data = [
        {
            "bucket": "0% a 10%",
            "volume": 56764,
            "margin": 0.542,
            "median_profit": 512.30,
            "loss_orders": 0,
            "loss_share": 0.0000,
        },
        {
            "bucket": "10% a 20%",
            "volume": 41810,
            "margin": 0.468,
            "median_profit": 415.10,
            "loss_orders": 0,
            "loss_share": 0.0000,
        },
        {
            "bucket": "20% a 35%",
            "volume": 28089,
            "margin": 0.381,
            "median_profit": 310.45,
            "loss_orders": 0,
            "loss_share": 0.0000,
        },
        {
            "bucket": "35% a 40%",
            "volume": 4783,
            "margin": 0.286,
            "median_profit": 224.18,
            "loss_orders": 30,
            "loss_share": 0.0063,
        },
        {
            "bucket": "40% a 45%",
            "volume": 3616,
            "margin": 0.224,
            "median_profit": 168.90,
            "loss_orders": 183,
            "loss_share": 0.0506,
        },
        {
            "bucket": "45% a 50%",
            "volume": 2067,
            "margin": 0.161,
            "median_profit": 115.20,
            "loss_orders": 307,
            "loss_share": 0.1485,
        },
        {
            "bucket": "50% a 55%",
            "volume": 963,
            "margin": 0.069,
            "median_profit": 42.10,
            "loss_orders": 316,
            "loss_share": 0.3281,
        },
        {
            "bucket": "55% a 60%",
            "volume": 687,
            "margin": -0.059,
            "median_profit": -38.50,
            "loss_orders": 416,
            "loss_share": 0.6055,
        },
        {
            "bucket": "> 60%",
            "volume": 79,
            "margin": -0.061,
            "median_profit": -45.12,
            "loss_orders": 44,
            "loss_share": 0.5570,
        },
    ]
    df = pd.DataFrame(data)

    gt = (
        GT(df)
        .cols_label(
            bucket="Faixa de Desconto",
            volume="Volume de Pedidos",
            margin="Margem Média",
            median_profit="Lucro Mediano",
            loss_orders="Pedidos Deficitários",
            loss_share="Proporção no Prejuízo",
        )
        .fmt_integer(columns=["volume", "loss_orders"])
        .fmt_percent(columns=["margin", "loss_share"], decimals=2)
        .fmt_currency(columns=["median_profit"], currency="USD", decimals=2)
        .tab_style(
            style=[style.fill(color="#ffebee"), style.text(color="#c62828", weight="bold")],
            locations=loc.body(rows=[7, 8]),
        )
        .tab_options(
            table_font_size="13px",
            table_width="100%",
            data_row_padding="5px",
        )
    )
    return gt


def table_marketing_performance() -> GT:
    """Gera a tabela de retorno de mídia e LTV/CAC."""
    data = [
        {
            "channel": "Organic Search",
            "customers": 5004,
            "cac": 42.12,
            "ltv": 2125.30,
            "ratio": "50,5x",
            "profit_cac": "21,7x",
        },
        {
            "channel": "Google Ads",
            "customers": 3721,
            "cac": 42.26,
            "ltv": 1897.38,
            "ratio": "44,9x",
            "profit_cac": "19,3x",
        },
        {
            "channel": "Direct",
            "customers": 3699,
            "cac": 42.23,
            "ltv": 1870.51,
            "ratio": "44,3x",
            "profit_cac": "19,1x",
        },
        {
            "channel": "Facebook Ads",
            "customers": 3003,
            "cac": 42.04,
            "ltv": 1755.73,
            "ratio": "41,8x",
            "profit_cac": "18,0x",
        },
        {
            "channel": "Instagram",
            "customers": 2489,
            "cac": 41.83,
            "ltv": 1673.43,
            "ratio": "40,0x",
            "profit_cac": "17,2x",
        },
        {
            "channel": "Email Marketing",
            "customers": 2022,
            "cac": 42.18,
            "ltv": 1598.36,
            "ratio": "37,9x",
            "profit_cac": "16,3x",
        },
        {
            "channel": "Referral",
            "customers": 2018,
            "cac": 42.18,
            "ltv": 1583.37,
            "ratio": "37,5x",
            "profit_cac": "16,2x",
        },
        {
            "channel": "Affiliate",
            "customers": 1235,
            "cac": 41.91,
            "ltv": 1475.99,
            "ratio": "35,2x",
            "profit_cac": "15,1x",
        },
        {
            "channel": "TikTok",
            "customers": 981,
            "cac": 42.33,
            "ltv": 1428.03,
            "ratio": "33,7x",
            "profit_cac": "14,5x",
        },
        {
            "channel": "YouTube",
            "customers": 739,
            "cac": 42.64,
            "ltv": 1380.61,
            "ratio": "32,4x",
            "profit_cac": "13,9x",
        },
    ]
    df = pd.DataFrame(data)

    gt = (
        GT(df)
        .cols_label(
            channel="Canal de Marketing",
            customers="Clientes Adquiridos",
            cac="CAC Médio",
            ltv="LTV Médio",
            ratio="Razão LTV / CAC",
            profit_cac="Lucro Médio / CAC",
        )
        .fmt_integer(columns=["customers"])
        .fmt_currency(columns=["cac", "ltv"], currency="USD", decimals=2)
        .tab_style(
            style=[style.fill(color="#e8f5e9"), style.text(color="#2e7d32", weight="bold")],
            locations=loc.body(rows=[0]),
        )
        .tab_options(
            table_font_size="13px",
            table_width="100%",
            data_row_padding="5px",
        )
    )
    return gt


def table_rfm_segments() -> GT:
    """Gera a tabela de segmentação comportamental RFM."""
    data = [
        {
            "segment": "Champions",
            "customers": 7854,
            "share": 0.315,
            "recency": 29.8,
            "frequency": 6.4,
            "spend": 8146.00,
            "ticket": 1272.81,
        },
        {
            "segment": "Loyal Customers",
            "customers": 5459,
            "share": 0.219,
            "recency": 261.3,
            "frequency": 7.5,
            "spend": 10526.81,
            "ticket": 1403.57,
        },
        {
            "segment": "At-Risk High-Value",
            "customers": 8670,
            "share": 0.348,
            "recency": 415.2,
            "frequency": 4.3,
            "spend": 5144.89,
            "ticket": 1196.48,
        },
        {
            "segment": "Occasional / Low-Value",
            "customers": 2928,
            "share": 0.118,
            "recency": 606.2,
            "frequency": 2.2,
            "spend": 1837.95,
            "ticket": 835.43,
        },
    ]
    df = pd.DataFrame(data)

    gt = (
        GT(df)
        .cols_label(
            segment="Segmento",
            customers="Clientes",
            share="Proporção",
            recency="Recência Média (dias)",
            frequency="Frequência Média",
            spend="Valor Gasto Médio",
            ticket="Ticket Médio",
        )
        .fmt_integer(columns=["customers"])
        .fmt_percent(columns=["share"], decimals=1)
        .fmt_number(columns=["recency", "frequency"], decimals=1)
        .fmt_currency(columns=["spend", "ticket"], currency="USD", decimals=2)
        .tab_style(
            style=style.text(weight="bold"),
            locations=loc.body(columns=["segment"]),
        )
        .tab_options(
            table_font_size="13px",
            table_width="100%",
            data_row_padding="5px",
        )
    )
    return gt


def table_category_performance() -> GT:
    """Gera a tabela de desempenho econômico por categoria de produto."""
    data = [
        {
            "category": "Electronics",
            "sales": 41148162.90,
            "profit": 14103982.74,
            "margin": 0.3428,
            "price": 797.79,
            "items": 55784,
        },
        {
            "category": "Jewelry",
            "sales": 25561333.78,
            "profit": 10391635.32,
            "margin": 0.4065,
            "price": 567.23,
            "items": 48859,
        },
        {
            "category": "Home Appliances",
            "sales": 24842478.64,
            "profit": 10288878.45,
            "margin": 0.4142,
            "price": 479.34,
            "items": 56281,
        },
        {
            "category": "Automotive",
            "sales": 16449898.28,
            "profit": 6477194.28,
            "margin": 0.3938,
            "price": 303.68,
            "items": 58046,
        },
        {
            "category": "Sports & Outdoors",
            "sales": 15726848.17,
            "profit": 7230037.31,
            "margin": 0.4597,
            "price": 260.96,
            "items": 64752,
        },
        {
            "category": "Home & Kitchen",
            "sales": 10971629.82,
            "profit": 5203824.25,
            "margin": 0.4743,
            "price": 236.72,
            "items": 49682,
        },
        {
            "category": "Baby & Kids",
            "sales": 9690605.60,
            "profit": 4818148.07,
            "margin": 0.4972,
            "price": 192.40,
            "items": 53945,
        },
        {
            "category": "Health & Wellness",
            "sales": 9228068.04,
            "profit": 4263304.41,
            "margin": 0.4620,
            "price": 158.19,
            "items": 62054,
        },
        {
            "category": "Office Supplies",
            "sales": 8884212.85,
            "profit": 4585377.04,
            "margin": 0.5161,
            "price": 164.30,
            "items": 57631,
        },
        {
            "category": "Fashion",
            "sales": 7434589.51,
            "profit": 3669631.60,
            "margin": 0.4936,
            "price": 162.35,
            "items": 48774,
        },
        {
            "category": "Pet Supplies",
            "sales": 6421229.71,
            "profit": 3263681.62,
            "margin": 0.5083,
            "price": 128.27,
            "items": 53093,
        },
        {
            "category": "Toys & Games",
            "sales": 5472675.99,
            "profit": 2800442.39,
            "margin": 0.5117,
            "price": 102.68,
            "items": 55788,
        },
        {
            "category": "Beauty & Personal Care",
            "sales": 4735647.66,
            "profit": 2477469.89,
            "margin": 0.5232,
            "price": 82.38,
            "items": 59765,
        },
        {
            "category": "Grocery",
            "sales": 2990696.44,
            "profit": 1648934.90,
            "margin": 0.5514,
            "price": 54.14,
            "items": 55607,
        },
        {
            "category": "Books & Media",
            "sales": 2840799.90,
            "profit": 1475496.28,
            "margin": 0.5194,
            "price": 45.38,
            "items": 62305,
        },
    ]
    df = pd.DataFrame(data)

    gt = (
        GT(df)
        .cols_label(
            category="Categoria",
            sales="Faturamento",
            profit="Lucro Operacional",
            margin="Margem Líquida",
            price="Preço Médio",
            items="Volume de Itens",
        )
        .fmt_currency(columns=["sales", "profit", "price"], currency="USD", decimals=2)
        .fmt_percent(columns=["margin"], decimals=2)
        .fmt_integer(columns=["items"])
        .tab_style(
            style=style.text(weight="bold"),
            locations=loc.body(columns=["category"]),
        )
        .tab_options(
            table_font_size="13px",
            table_width="100%",
            data_row_padding="4px",
        )
    )
    return gt


def table_model_evaluation() -> GT:
    """Gera a tabela de avaliação comparativa de modelos no teste cego 2025."""
    data = [
        {
            "model": "Taxa Base Ingênua",
            "pr_auc": 0.129,
            "roc_auc": 0.500,
            "brier": 0.113,
            "threshold": "-",
            "f1": "-",
            "precision": 0.129,
            "recall": 1.000,
        },
        {
            "model": "Baseline Logit",
            "pr_auc": 0.188,
            "roc_auc": 0.616,
            "brier": 0.229,
            "threshold": "0,52",
            "f1": 0.274,
            "precision": 0.221,
            "recall": 0.361,
        },
        {
            "model": "LightGBM At-Purchase",
            "pr_auc": 0.578,
            "roc_auc": 0.885,
            "brier": 0.089,
            "threshold": "0,35",
            "f1": 0.541,
            "precision": 0.488,
            "recall": 0.607,
        },
    ]
    df = pd.DataFrame(data)

    gt = (
        GT(df)
        .cols_label(
            model="Modelo",
            pr_auc="PR-AUC",
            roc_auc="ROC-AUC",
            brier="Brier Score",
            threshold="Limiar Ótimo (tau*)",
            f1="F1 Ótimo",
            precision="Precisão no Corte",
            recall="Recall no Corte",
        )
        .fmt_number(columns=["pr_auc", "roc_auc", "brier", "precision", "recall"], decimals=3)
        .tab_style(
            style=[style.fill(color="#e3f2fd"), style.text(weight="bold")],
            locations=loc.body(rows=[2]),
        )
        .tab_options(
            table_font_size="13px",
            table_width="100%",
            data_row_padding="5px",
        )
    )
    return gt


def table_threshold_costs() -> GT:
    """Gera a tabela de trade-offs de custo operacional por limiar de decisão."""
    data = [
        {
            "threshold": 0.10,
            "fn": 0,
            "fp": 23159,
            "cost_fn": 0.0,
            "cost_fp": 185272.0,
            "cost_total": 185272.0,
            "savings": -23362.0,
            "profile": "Conservadorismo extremo (intervenção em massa)",
        },
        {
            "threshold": 0.25,
            "fn": 33,
            "fp": 19536,
            "cost_fn": 1485.0,
            "cost_fp": 156288.0,
            "cost_total": 157773.0,
            "savings": 4137.0,
            "profile": "Alta cobertura com sobrecarga operacional",
        },
        {
            "threshold": 0.35,
            "fn": 77,
            "fp": 15646,
            "cost_fn": 3465.0,
            "cost_fp": 125168.0,
            "cost_total": 128633.0,
            "savings": 33277.0,
            "profile": "Maximização do F1-Score (Recall 60,7%)",
        },
        {
            "threshold": 0.45,
            "fn": 197,
            "fp": 10702,
            "cost_fn": 8865.0,
            "cost_fp": 85616.0,
            "cost_total": 94481.0,
            "savings": 67429.0,
            "profile": "Zona de transição equilibrada",
        },
        {
            "threshold": 0.50,
            "fn": 383,
            "fp": 7620,
            "cost_fn": 17235.0,
            "cost_fp": 60960.0,
            "cost_total": 78195.0,
            "savings": 83715.0,
            "profile": "Ponto de corte balanceado padrão",
        },
        {
            "threshold": 0.55,
            "fn": 891,
            "fp": 3665,
            "cost_fn": 40095.0,
            "cost_fp": 29320.0,
            "cost_total": 69415.0,
            "savings": 92495.0,
            "profile": "Mínimo Global de Custo Financeiro (tau*)",
        },
        {
            "threshold": 0.60,
            "fn": 1631,
            "fp": 1279,
            "cost_fn": 73395.0,
            "cost_fp": 10232.0,
            "cost_total": 83627.0,
            "savings": 78283.0,
            "profile": "Alta precisão com perda de cobertura",
        },
        {
            "threshold": 0.70,
            "fn": 3299,
            "fp": 82,
            "cost_fn": 148455.0,
            "cost_fp": 656.0,
            "cost_total": 149111.0,
            "savings": 12799.0,
            "profile": "Intervenção mínima",
        },
        {
            "threshold": 0.90,
            "fn": 3598,
            "fp": 0,
            "cost_fn": 161910.0,
            "cost_fp": 0.0,
            "cost_total": 161910.0,
            "savings": 0.0,
            "profile": "Política passiva / Inação (Sem modelo)",
        },
    ]
    df = pd.DataFrame(data)

    gt = (
        GT(df)
        .cols_label(
            threshold="Limiar (tau)",
            fn="Falsos Negativos (FN)",
            fp="Falsos Positivos (FP)",
            cost_fn="Custo FN",
            cost_fp="Custo FP",
            cost_total="Custo Total",
            savings="Economia Líquida",
            profile="Perfil da Decisão",
        )
        .fmt_number(columns=["threshold"], decimals=2)
        .fmt_integer(columns=["fn", "fp"])
        .fmt_currency(
            columns=["cost_fn", "cost_fp", "cost_total", "savings"], currency="USD", decimals=2
        )
        .tab_style(
            style=[style.fill(color="#e8f5e9"), style.text(color="#1b5e20", weight="bold")],
            locations=loc.body(rows=[5]),
        )
        .tab_options(
            table_font_size="13px",
            table_width="100%",
            data_row_padding="5px",
        )
    )
    return gt


def table_returns_root_cause() -> GT:
    """Gera a tabela de causas-raiz de devolução e ações mitigadoras."""
    data = [
        {
            "cause": "Wrong Product",
            "volume": 1237,
            "share": 0.1307,
            "cost": 55665.0,
            "category": "Electronics, Fashion",
            "action": "Leitura de código de barras 2D obrigatória antes do empacotamento",
        },
        {
            "cause": "Other",
            "volume": 1208,
            "share": 0.1277,
            "cost": 54360.0,
            "category": "Variadas",
            "action": "Refinamento dos formulários de SAC para redução de respostas genéricas",
        },
        {
            "cause": "Changed Mind",
            "volume": 1204,
            "share": 0.1272,
            "cost": 54180.0,
            "category": "Jewelry, Toys",
            "action": "Oferta de crédito em loja com bônus de 5% em vez de estorno imediato",
        },
        {
            "cause": "Size Issue",
            "volume": 1182,
            "share": 0.1249,
            "cost": 53190.0,
            "category": "Fashion, Sports",
            "action": "Tabela interativa de medidas e provador virtual com inteligência 3D",
        },
        {
            "cause": "Defective Product",
            "volume": 1174,
            "share": 0.1241,
            "cost": 52830.0,
            "category": "Electronics, Appliances",
            "action": "Bloqueio temporário de SKUs e auditoria de lotes de fornecedores críticos",
        },
        {
            "cause": "Late Delivery",
            "volume": 1172,
            "share": 0.1239,
            "cost": 52740.0,
            "category": "Automotive, Kids",
            "action": "Ajuste dinâmico de SLA por região e redistribuição para armazéns locais",
        },
        {
            "cause": "Product Not as Expected",
            "volume": 1147,
            "share": 0.1212,
            "cost": 51615.0,
            "category": "Home, Beauty",
            "action": "Atualização de fotos reais, vídeos de uso e fichas técnicas completas",
        },
        {
            "cause": "Damaged Product",
            "volume": 1138,
            "share": 0.1203,
            "cost": 51210.0,
            "category": "Grocery, Books",
            "action": "Revisão dos padrões de embalagem protetora e plástico-bolha no armazém",
        },
        {
            "cause": "Total",
            "volume": 9462,
            "share": 1.0000,
            "cost": 425790.0,
            "category": "-",
            "action": "-",
        },
    ]
    df = pd.DataFrame(data)

    gt = (
        GT(df)
        .cols_label(
            cause="Causa Raiz de Devolução",
            volume="Volume",
            share="Proporção",
            cost="Custo Reverso Acumulado",
            category="Categoria Predominante",
            action="Ação Mitigadora no Fulfillment e Catálogo",
        )
        .fmt_integer(columns=["volume"])
        .fmt_percent(columns=["share"], decimals=2)
        .fmt_currency(columns=["cost"], currency="USD", decimals=2)
        .tab_style(
            style=style.text(weight="bold"),
            locations=loc.body(rows=[8]),
        )
        .tab_style(
            style=style.borders(sides="top", color="#2c3e50", weight="2px"),
            locations=loc.body(rows=[8]),
        )
        .tab_options(
            table_font_size="13px",
            table_width="100%",
            data_row_padding="5px",
        )
    )
    return gt


def table_roadmap() -> GT:
    """Gera a tabela do cronograma tático de implementação das recomendações."""
    data = [
        {
            "phase": "Q1",
            "timing": "Mês 1–3",
            "initiative": "Implementação da trava sistêmica de desconto em 35% no e-commerce",
            "owner": "Pricing & TI",
            "okr": "Zerar operações com margem negativa (Lucro < 0)",
        },
        {
            "phase": "Q2",
            "timing": "Mês 4–6",
            "initiative": "Integração do modelo LightGBM At-Purchase (tau* = 0,55) ao checkout",
            "owner": "Data Science & Engenharia",
            "okr": "Reduzir a taxa de devolução de 7,15% para abaixo de 6,00%",
        },
        {
            "phase": "Q3",
            "timing": "Mês 7–9",
            "initiative": "Bipagem 2D no armazém e atualização de guias de medidas no catálogo",
            "owner": "Operações & Logística",
            "okr": "Reduzir em 40% devoluções por produto errado e tamanho",
        },
        {
            "phase": "Q4",
            "timing": "Mês 10–12",
            "initiative": "Realocação de mídia para canais > 44x e régua de CRM para clientes em risco",
            "owner": "Growth & CRM",
            "okr": "Aumentar LTV/CAC ponderado em 15% e reativar 350 clientes",
        },
    ]
    df = pd.DataFrame(data)

    gt = (
        GT(df)
        .cols_label(
            phase="Fase",
            timing="Prazo",
            initiative="Iniciativa Principal",
            owner="Responsável",
            okr="Métrica de Sucesso (OKR)",
        )
        .tab_style(
            style=style.text(weight="bold"),
            locations=loc.body(columns=["phase"]),
        )
        .tab_options(
            table_font_size="13px",
            table_width="100%",
            data_row_padding="5px",
        )
    )
    return gt
