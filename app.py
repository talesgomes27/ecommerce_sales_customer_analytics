"""Aplicação interativa Streamlit para simulação de cenários What-If de precificação e risco operacional."""

import pandas as pd
import streamlit as st

from src.core.schemas import (
    AcquisitionChannel,
    Category,
    RiskAlertLevel,
    SimulationScenarioInput,
)
from src.core.simulator import BusinessScenarioSimulator
from src.ui.charts import (
    plot_discount_sensitivity_curve,
    plot_waterfall_cost_breakdown,
)

# 1. Configuração da Página
st.set_page_config(
    page_title="Simulador de Cenários What-If | E-Commerce Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inicialização do Motor Core
simulator = BusinessScenarioSimulator()

# 3. Cabeçalho Corporativo
st.title("Simulador Estratégico de Precificação, Margem e Risco Operacional")
st.caption(
    "Motor analítico de simulação what-if calibrado sobre o histórico empírico de 138.116 transações comerciais."
)

st.info(
    "**Pergunta do Decisor:** *A que nível de desconto o aumento de volume deixa de compensar e "
    "a margem líquida passa a ser destruída por custos operacionais e risco de devolução?*"
)

# 4. Barra Lateral de Parâmetros Operacionais
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

# 5. Execução do Cenário
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

# 6. Painel Superior de KPIs Executivos
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
        delta=f"{diff_be:+.1f}% margem de folga",
        delta_color="normal" if diff_be >= 0 else "inverse",
    )

with kpi4:
    ret_pct = result.estimated_return_rate * 100.0
    canc_pct = result.estimated_cancellation_rate * 100.0
    st.metric(
        label="Risco Operacional Estimado",
        value=f"{ret_pct:.1f}% Devolução",
        delta=f"{canc_pct:.1f}% Cancelamento",
        delta_color="inverse",
    )

# 7. Faixa de Alerta Sanitário de Risco
st.markdown("---")
if result.risk_alert == RiskAlertLevel.SAFE_GREEN.value:
    st.success(
        f"🟢 **OPERAÇÃO FINANCEIRAMENTE SEGURA:** O desconto concedido ({discount_pct_input}%) "
        f"está confortavelmente abaixo do teto de break-even ({be_pct:.1f}%). "
        f"Margem de contribuição saudável em {result.contribution_margin_pct:.1f}%."
    )
elif result.risk_alert == RiskAlertLevel.WARNING_YELLOW.value:
    st.warning(
        f"🟡 **ATENÇÃO À COMPRESSÃO DE MARGEM:** O desconto de {discount_pct_input}% aproxima a operação "
        f"do limite de rentabilidade ({be_pct:.1f}%). Margem líquida reduzida a {result.contribution_margin_pct:.1f}%. "
        f"Monitore sensibilidade de devolução."
    )
else:
    st.error(
        f"🔴 **DESTRUIÇÃO DE CAIXA DETECTADA:** O desconto praticado ({discount_pct_input}%) supera o "
        f"ponto de equilíbrio de {be_pct:.1f}%. A cada unidade vendida, a operação consome "
        f"caixa líquido devido à sobreposição de CMV, frete, impostos e custos reversos."
    )

# 8. Análises Aprofundadas (Abas Interativas)
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
    st.markdown("##### Simulação Tabular Passo a Passo")
    df_matrix = pd.DataFrame(curve_data)
    df_matrix["discount_pct"] = (df_matrix["discount_pct"] * 100).round(1).astype(str) + "%"
    df_matrix["estimated_return_rate"] = (df_matrix["estimated_return_rate"] * 100).round(2).astype(
        str
    ) + "%"
    df_matrix["estimated_cancellation_rate"] = (
        df_matrix["estimated_cancellation_rate"] * 100
    ).round(2).astype(str) + "%"
    df_matrix["contribution_margin_pct"] = (
        df_matrix["contribution_margin_pct"].round(1).astype(str) + "%"
    )

    df_matrix = df_matrix.rename(
        columns={
            "discount_pct": "Desconto (%)",
            "unit_net_price": "Preço Líquido ($)",
            "net_revenue": "Receita Líquida ($)",
            "total_cost": "Custo Total ($)",
            "contribution_margin_value": "Margem Líquida ($)",
            "contribution_margin_pct": "Margem (%)",
            "estimated_return_rate": "Taxa Devolução",
            "estimated_cancellation_rate": "Taxa Cancelamento",
            "risk_alert": "Status Risco",
            "is_profitable": "Lucrativo?",
        }
    )

    st.dataframe(
        df_matrix,
        use_container_width=True,
        hide_index=True,
    )

# 9. Rodapé
st.markdown("---")
st.caption(
    "E-Commerce Sales & Customer Analytics · Motor Core Desacoplado (`src.core.simulator`) · "
    "Métricas de calibração baseadas no estudo empírico CRISP-ML(Q)."
)
