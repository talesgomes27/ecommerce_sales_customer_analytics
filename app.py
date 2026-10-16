"""Aplicação interativa Streamlit para simulação de cenários What-If de precificação e risco operacional."""

from datetime import datetime

import pandas as pd
import streamlit as st

from src.core.schemas import (
    AcquisitionChannel,
    Category,
    RiskAlertLevel,
    SimulationScenarioInput,
)
from src.core.simulator import BusinessScenarioSimulator
from src.models.inference import RiskModelInference
from src.models.schemas import RiskScenarioInput
from src.reports.executive_pdf import ExecutivePdfError, generate_executive_pdf_bytes
from src.ui.charts import (
    plot_discount_sensitivity_curve,
    plot_waterfall_cost_breakdown,
)

# Mapeamento AcquisitionChannel → marketing_channel (valores do dataset de treino)
CHANNEL_TO_MARKETING: dict[AcquisitionChannel, str] = {
    AcquisitionChannel.DIRECT: "Direct",
    AcquisitionChannel.ORGANIC_SEARCH: "Organic Search",
    AcquisitionChannel.PAID_SEARCH: "Google Ads",
    AcquisitionChannel.SOCIAL_MEDIA: "Facebook Ads",
    AcquisitionChannel.EMAIL: "Email Marketing",
    AcquisitionChannel.AFFILIATE: "Affiliate",
}


@st.cache_resource
def get_ml_inference_engine() -> RiskModelInference | None:
    """Carrega o modelo ML uma única vez por sessão."""
    try:
        return RiskModelInference()
    except Exception as e:  # noqa: BLE001
        st.warning(f"⚠️ Modo ML indisponível ({type(e).__name__}). Usando heurística.")
        return None


def build_ml_scenario(
    unit_price: float,
    unit_cost: float,
    quantity: int,
    discount_pct: float,
    shipping_cost: float,
    delivery_days: int,
    tax_rate: float,
    channel: AcquisitionChannel,
) -> RiskScenarioInput:
    """Constrói um RiskScenarioInput a partir dos inputs econômicos do simulador.

    As features transacionais ausentes no formulário (idade, histórico, demografia)
    são fixadas em medianas/modos do conjunto de treino (2021-2024, N=110.518).
    Em produção real viriam do perfil do cliente. Este é um compromisso para
    viabilizar o modo ML sem alterar a UX do decisor.
    """
    gross_sales = unit_price * quantity
    tax_amount = (unit_price * (1 - discount_pct) * quantity) * tax_rate
    product_cost = unit_cost * quantity

    return RiskScenarioInput(
        # Econômicos (derivados dos inputs do decisor)
        gross_sales=gross_sales,
        tax_amount=tax_amount,
        product_cost=product_cost,
        shipping_cost=shipping_cost * quantity,
        quantity=quantity,
        # Transacionais (medianas/modos do treino)
        customer_age=46.0,
        orders_count_prior=2,
        spend_prior=1953.89,
        days_since_last_order=113,
        # Categóricos
        gender="Male",
        customer_segment="Consumer",
        region="South",
        sales_channel="Mobile App",
        marketing_channel=CHANNEL_TO_MARKETING[channel],
        payment_method="Credit Card",
        shipping_method="Express" if delivery_days <= 3 else "Standard",
        warehouse="WH-014",
    )


# 1. Configuração da Página
st.set_page_config(
    page_title="Simulador de Cenários What-If | E-Commerce Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Injeção de Estilo CSS Executivo de Alta Visibilidade
st.markdown(
    """
    <style>
    /* Estilização Geral do Canvas */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }

    /* Barra Lateral de Controles */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    /* Cartões de Métrica / KPIs */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-color: #cbd5e1;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        color: #475569 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
    }

    /* Abas de Navegação */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        padding-bottom: 6px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        color: #334155;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.4rem 1.1rem;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-color: #2563eb !important;
    }

    /* Container com Borda e Sombra para Plots e Tabelas */
    .visual-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Inicialização do Motor Core
simulator = BusinessScenarioSimulator()

# 4. Cabeçalho Corporativo
st.title("Simulador Estratégico de Precificação, Margem e Risco Operacional")
st.caption(
    "Motor analítico de simulação what-if calibrado sobre o histórico empírico de 138.116 transações comerciais."
)

st.info(
    "**Pergunta do Decisor:** *A que nível de desconto o aumento de volume deixa de compensar e "
    "a margem líquida passa a ser destruída por custos operacionais e risco de devolução?*"
)

# 5. Barra Lateral de Parâmetros Operacionais
st.sidebar.header("⚙️ Parâmetros do Cenário")

with st.sidebar.expander("1. Estrutura de Preço & Volume", expanded=True):
    unit_price = st.number_input(
        "Preço Base de Tabela (USD)",
        min_value=1.0,
        max_value=10000.0,
        value=1200.0,
        step=50.0,
        help="Preço unitário cheio de catálogo antes de concessão de desconto comercial.",
    )

    unit_cost = st.number_input(
        "Custo do Produto - CMV (USD)",
        min_value=0.5,
        max_value=8000.0,
        value=580.0,
        step=20.0,
        help="Custo da mercadoria vendida (fornecedor/manufatura).",
    )

    quantity = st.number_input(
        "Volume Projetado (Unidades)",
        min_value=1,
        max_value=10000,
        value=50,
        step=5,
        help="Quantidade de unidades estimadas para a campanha ou lote.",
    )

    discount_pct_input = st.slider(
        "Desconto Comercial Concedido (%)",
        min_value=0,
        max_value=90,
        value=20,
        step=1,
        help="Percentual de abatimento de preço a ser testado.",
    )
    discount_pct = discount_pct_input / 100.0

with st.sidebar.expander("2. Logística, Tributos & Risco", expanded=True):
    shipping_cost = st.number_input(
        "Frete Unitário de Envio (USD)",
        min_value=0.0,
        max_value=500.0,
        value=25.0,
        step=5.0,
        help="Custo logístico de entrega cobrado pela transportadora por unidade.",
    )

    delivery_days = st.slider(
        "Prazo de Entrega Prometido (Dias)",
        min_value=1,
        max_value=30,
        value=4,
        step=1,
        help="Prazos superiores a 5 dias elevam exponencialmente o risco de devolução e cancelamento.",
    )

    tax_rate_input = st.slider(
        "Alíquota Tributária Efetiva (%)",
        min_value=0,
        max_value=40,
        value=10,
        step=1,
        help="Impostos incidentes sobre a receita líquida faturada.",
    )
    tax_rate = tax_rate_input / 100.0

    reverse_logistics_cost = st.number_input(
        "Custo de Logística Reversa (USD)",
        min_value=0.0,
        max_value=300.0,
        value=45.0,
        step=5.0,
        help="Custo operacional de frete de retorno, triagem e recondicionamento por pedido devolvido.",
    )

with st.sidebar.expander("3. Segmentação & Canal", expanded=False):
    category = st.selectbox(
        "Categoria Comercial",
        options=list(Category),
        index=list(Category).index(Category.ELECTRONICS),
        format_func=lambda x: x.value,
    )

    channel = st.selectbox(
        "Canal de Aquisição",
        options=list(AcquisitionChannel),
        index=list(AcquisitionChannel).index(AcquisitionChannel.DIRECT),
        format_func=lambda x: x.value,
    )

# 6. Execução do Cenário
scenario_input = SimulationScenarioInput(
    unit_price=float(unit_price),
    unit_cost=float(unit_cost),
    quantity=int(quantity),
    discount_pct=float(discount_pct),
    shipping_cost=float(shipping_cost),
    tax_rate=float(tax_rate),
    delivery_days=int(delivery_days),
    category=category,
    channel=channel,
    reverse_logistics_cost=float(reverse_logistics_cost),
)

result = simulator.simulate_scenario(scenario_input)

# 6.5. Toggle de modo de inferência
inference_engine = get_ml_inference_engine()

modo = st.radio(
    "**Modo de estimativa de risco:**",
    options=["🔵 Principal (ML LightGBM)", "⚪ Comparação (Heurística Calibrada)"],
    index=0 if inference_engine else 1,
    horizontal=True,
    help=(
        "O modo ML aplica o LightGBM treinado em 2021-2024 com calibração de Elkan "
        "(τ* = 0.1549). Usa features transacionais do perfil do cliente (idade, "
        "histórico, demografia) fixadas em medianas do treino. "
        "O modo Heurístico usa médias históricas e deltas de categoria/canal, "
        "respondendo apenas aos inputs econômicos do formulário. "
        "Cenários no limiar podem retornar decisões diferentes entre modos."
    ),
)

# 6.6. Override do risco quando o modo ML está ativo
risk_source = "Heurística"
if modo.startswith("🔵") and inference_engine is not None:
    try:
        ml_input = build_ml_scenario(
            unit_price=unit_price,
            unit_cost=unit_cost,
            quantity=quantity,
            discount_pct=discount_pct_input / 100.0,
            shipping_cost=shipping_cost,
            delivery_days=delivery_days,
            tax_rate=tax_rate_input / 100.0,
            channel=channel,
        )
        ml_result = inference_engine.predict_risk(ml_input)

        # Substituição cirúrgica — apenas campos de risco
        result.estimated_return_rate = ml_result["prob_devolucao_calibrada"]
        result.estimated_cancellation_rate = 0.0  # modelo prevê dev+canç agregado
        risk_source = "ML"
    except Exception as e:  # noqa: BLE001
        st.warning(f"Fallback para heurística: {type(e).__name__}: {e}")
        risk_source = "Heurística"

# 7. Painel Superior de KPIs Executivos
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        label="Receita Líquida Total",
        value=f"${result.net_revenue:,.2f}",
        delta=f"Bruta: ${result.gross_revenue:,.2f}",
        delta_color="off",
    )

with kpi2:
    is_positive = result.contribution_margin_value >= 0
    st.metric(
        label="Margem de Contribuição",
        value=f"${result.contribution_margin_value:,.2f}",
        delta=f"{result.contribution_margin_pct:.1f}% da receita",
        delta_color="normal" if is_positive else "inverse",
    )

with kpi3:
    be_pct = result.break_even_discount * 100.0
    diff_be = be_pct - discount_pct_input
    st.metric(
        label="Break-even de Desconto (D*)",
        value=f"{be_pct:.1f}%",
        delta=f"{diff_be:+.1f}% folga",
        delta_color="normal" if diff_be >= 0 else "inverse",
    )

with kpi4:
    ret_pct = result.estimated_return_rate * 100.0
    st.metric(
        label="Risco Operacional Estimado",
        value=f"{ret_pct:.1f}% Devolução",
        delta=(
            f"{result.estimated_cancellation_rate * 100:.1f}% Cancelamento"
            if risk_source == "Heurística"
            else "n/d (risco agregado no ML)"
        ),
        delta_color="inverse",
    )
    fonte_label = "ML (τ*=0.1549)" if risk_source == "ML" else "Heurística"
    st.caption(f"Fonte: **{fonte_label}**")

# 8. Faixa de Alerta Sanitário de Risco
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
if result.risk_alert == RiskAlertLevel.SAFE_GREEN.value:
    st.success(
        f"🟢 **OPERAÇÃO FINANCEIRAMENTE SEGURA:** O desconto praticado ({discount_pct_input}%) "
        f"está confortavelmente abaixo do teto de break-even ({be_pct:.1f}%). "
        f"Margem de contribuição saudável em {result.contribution_margin_pct:.1f}%."
    )
elif result.risk_alert == RiskAlertLevel.WARNING_YELLOW.value:
    st.warning(
        f"🟡 **ATENÇÃO À COMPRESSÃO DE MARGEM:** O desconto de {discount_pct_input}% aproxima a operação "
        f"do limite de rentabilidade ({be_pct:.1f}%). Margem líquida reduzida a {result.contribution_margin_pct:.1f}%. "
        f"Monitore o volume e a taxa de devolução."
    )
else:
    st.error(
        f"🔴 **DESTRUIÇÃO DE CAIXA DETECTADA:** O desconto praticado ({discount_pct_input}%) supera o "
        f"ponto de equilíbrio de {be_pct:.1f}%. A cada unidade vendida, a operação consome "
        f"caixa líquido devido à sobreposição de CMV, frete, impostos e custos reversos."
    )

# 9. Governança e Exportação Executiva (One-Pager Typst)
st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
scenario_dict = {
    "unit_price": float(unit_price),
    "unit_cost": float(unit_cost),
    "quantity": int(quantity),
    "discount_pct": float(discount_pct),
    "shipping_cost": float(shipping_cost),
    "tax_rate": float(tax_rate),
    "delivery_days": int(delivery_days),
    "reverse_logistics_cost": float(reverse_logistics_cost),
    "category": category.value if hasattr(category, "value") else str(category),
    "channel": channel.value if hasattr(channel, "value") else str(channel),
    "gross_revenue": result.gross_revenue,
    "net_revenue": result.net_revenue,
    "total_cost": result.total_cost,
    "contribution_margin_value": result.contribution_margin_value,
    "contribution_margin_pct": result.contribution_margin_pct,
    "break_even_discount": result.break_even_discount,
    "estimated_return_rate": result.estimated_return_rate,
    "estimated_cancellation_rate": result.estimated_cancellation_rate,
    "risk_alert": result.risk_alert,
    "risk_source": risk_source,
}

pdf_bytes: bytes | None = None
pdf_error: str | None = None
try:
    pdf_bytes = generate_executive_pdf_bytes(scenario_dict, risk_source=risk_source)
except ExecutivePdfError as e:
    pdf_error = str(e)
except Exception as e:
    pdf_error = f"Erro inesperado na geração documental: {e}"

col_doc_info, col_doc_btn = st.columns([3, 2])
with col_doc_info:
    st.markdown(
        "<div style='padding-top: 6px; color: #475569; font-size: 0.88rem;'>"
        "📋 <b>Governança de Pricing:</b> Exporte o memorando formal de uma página (One-Pager A4) "
        "com parâmetros de lote, KPIs e parecer sanitário compilado via Typst."
        "</div>",
        unsafe_allow_html=True,
    )

with col_doc_btn:
    if pdf_bytes is not None:
        st.download_button(
            label="📄 Baixar Parecer Executivo em PDF",
            data=pdf_bytes,
            file_name=f"parecer_pricing_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            help="Compila instantaneamente o parecer em documento executivo via Typst.",
        )
    else:
        st.error(f"⚠️ Indisponibilidade momentânea na emissão do PDF: {pdf_error}")

# 10. Abas de Análise Visual e Tabular
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
tab_curve, tab_dre, tab_matrix = st.tabs(
    [
        "📈 Curva de Sensibilidade & Break-even",
        "💧 Decomposição DRE (Waterfall)",
        "📋 Matriz Paramétrica de Simulação",
    ]
)

with tab_curve:
    curve_data = simulator.calculate_discount_sensitivity_curve(scenario_input, steps=25)
    fig_curve = plot_discount_sensitivity_curve(
        curve_data=curve_data,
        current_discount=discount_pct,
        break_even_discount=result.break_even_discount,
    )
    st.plotly_chart(fig_curve, use_container_width=True)

with tab_dre:
    fig_waterfall = plot_waterfall_cost_breakdown(scenario_input, result)
    st.plotly_chart(fig_waterfall, use_container_width=True)

with tab_matrix:
    st.markdown("#### Matriz de Simulação de Sensibilidade por Faixa de Desconto")
    df_raw = pd.DataFrame(curve_data)

    # Cria cópia formatada para visualização
    df_display = pd.DataFrame(
        {
            "Desconto": df_raw["discount_pct"].apply(lambda x: f"{x * 100:.1f}%"),
            "Preço Líquido": df_raw["unit_net_price"].apply(lambda x: f"${x:,.2f}"),
            "Receita Líquida": df_raw["net_revenue"].apply(lambda x: f"${x:,.2f}"),
            "Custo Total": df_raw["total_cost"].apply(lambda x: f"${x:,.2f}"),
            "Margem Líquida": df_raw["contribution_margin_value"].apply(lambda x: f"${x:,.2f}"),
            "Margem %": df_raw["contribution_margin_pct"].apply(lambda x: f"{x:.1f}%"),
            "Taxa Devolução": df_raw["estimated_return_rate"].apply(lambda x: f"{x * 100:.2f}%"),
            "Taxa Cancelamento": df_raw["estimated_cancellation_rate"].apply(
                lambda x: f"{x * 100:.2f}%"
            ),
            "Status Risco": df_raw["risk_alert"].apply(
                lambda x: (
                    "🟢 Seguro"
                    if x == "SAFE_GREEN"
                    else ("🟡 Alerta" if x == "WARNING_YELLOW" else "🔴 Perigo")
                )
            ),
            "Lucrativo?": df_raw["is_profitable"].apply(lambda x: "Sim" if x else "Não"),
        }
    )

    # Estilização condicional da tabela com destaque por linha
    def style_rows(row: pd.Series) -> list[str]:
        is_lucrativo = row["Lucrativo?"] == "Sim"
        if not is_lucrativo:
            return ["background-color: #fee2e2; color: #991b1b; font-weight: 500"] * len(row)
        return ["background-color: #ffffff; color: #0f172a"] * len(row)

    styled_df = df_display.style.apply(style_rows, axis=1)

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
    )

# 10. Rodapé
st.markdown("---")
st.caption(
    "E-Commerce Sales & Customer Analytics · Motor Core Desacoplado (`src.core.simulator`) · "
    "Métricas de calibração baseadas no estudo empírico CRISP-ML(Q)."
)
