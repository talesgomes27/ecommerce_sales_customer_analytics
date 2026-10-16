# ADR 0001: Arquitetura Modular de Pipeline Analítico e Engenharia de Features Pontuais

**Status:** Aprovado  
**Data:** 2026-10-16  
**Contexto Técnico:** Arquétipo A (Data Science, Analytics & ML)  

---

## Contexto e Problema
A base histórica do e-commerce reúne 138.116 pedidos e 46 variáveis de 2021 a 2025. A auditoria do Gate 1 revelou que atributos como `customer_lifetime_value`, `customer_order_count` e `customer_type` foram sumarizados no final da série de 5 anos (*look-ahead leakage*). Além disso, o arquivo consolidado de pedidos é a verdade contábil canônica, exigindo validação sistemática de contratos antes de qualquer modelagem.

Precisamos de uma topologia de pipeline que garanta:
1. Validação estrutural e contábil automatizada das fontes brutas.
2. Reconstrução dinâmica e estritamente cumulativa (*point-in-time*) de histórico de clientes e produtos, impedindo vazamento temporal.
3. Modularidade desacoplada para suportar tanto análises transversais (EDA, RFM) quanto modelagens temporais supervisionadas (*Out-of-Time*).

## Decisão Técnica
Adotamos uma arquitetura modular em camadas, orquestrada via módulos Python em `src/` e executada sob o gerenciador `uv`:

1. **Camada de Ingestão e Contratos (`src/data/`):**
   - Carregamento canônico de `ecommerce_sales_customer_analytics_150k.csv` e tabelas dimensionais (`customer_master.csv`, `product_catalog.csv`).
   - Aplicação de contratos estritos de schema e integridade matemática via `pandera`/`patito` baseados em `docs/01-data-discovery-and-contracts.md`.

2. **Camada de Engenharia de Features Pontuais (`src/features/`):**
   - Criação de agregados estritamente retroativos por cliente na data de cada pedido $t$: contagem cumulativa de pedidos prévios, receita prévia e recência em dias.
   - Cálculo de recência, frequência e valor monetário (RFM) dinâmico.
   - Descarte formal de atributos estáticos futuros (`customer_lifetime_value` bruto, `is_repeat_customer`).

3. **Camada de Partição e Modelagem (`src/models/`):**
   - Split temporal estrito: Treino/Validação (2021-01-01 a 2024-12-31) e Teste Cego (2025-01-01 a 2025-12-31).
   - Isolamento total de atributos de pós-venda (`delivery_days`, `customer_rating`, `review_sentiment`, `payment_status == 'Refunded'/'Failed'`).

## Consequências
- **Positivas:**
  - Garantia formal contra vazamento temporal e vazamento de alvo.
  - Reprodutibilidade assegurada por pipelines funcionais determinísticos (`seed = 42`).
  - Código limpo, testável via `pytest` e reutilizável pelo relatório Quarto.
- **Negativas / Trade-offs:**
  - O cálculo dinâmico cumulativo exige computação em janela temporal sobre 138 mil linhas, mitigada pelo uso de operações vetorizadas eficientes em Polars/Pandas.
