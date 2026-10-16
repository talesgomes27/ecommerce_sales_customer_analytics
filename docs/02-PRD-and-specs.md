# Gate 2: Especificação do Produto Analítico e Hipóteses de Negócio (PRD & Specs)

**Projeto:** `ecommerce_sales_customer_analytics`  
**Data:** 2026-10-16  
**Arquétipo:** A (Data Science, Analytics & ML — CRISP-ML(Q) + Data Storytelling)  
**Status do Portão:** Elaborado para validação humana  

---

## 1. Problema de Negócio e Contexto Estratégico

### 1.1. Contexto do E-commerce
A operação transacionou \$177.134.263,74 em receita líquida e \$76.146.395,76 em lucro operacional ao longo de 5 anos (138.116 pedidos e 24.911 clientes ativos). A despeito da aparente saúde financeira e do ticket médio elevado (\$1.282,50), a liderança executiva enfrenta três pontos cegos:
1. **Canibalização de Margem:** Políticas promocionais agressivas concederam \$32.819.346,82 em descontos. Em 1.296 transações (0,94% da base), o desconto corroeu integralmente a margem bruta, gerando prejuízos diretos de até 59,55% por venda.
2. **Perdas Operacionais Evitáveis:** As taxas acumuladas de devolução (6,85%) e cancelamento (6,08%) totalizam 12,93% dos pedidos. O cancelamento gera frustração imediata e custo de processamento, enquanto a devolução acarreta custo logístico reverso e depreciação de inventário.
3. **Miopia no Relacionamento com Clientes:** A base depende de métricas estáticas agregadas no fim do período histórico. Não há segmentação comportamental dinâmica que diferencie clientes de alto valor recorrente daqueles em risco de evasão, nem governança sobre o Retorno do Investimento em Aquisição (LTV / CAC).

### 1.2. Stakeholders e Objetivos Executivos
- **Diretoria Comercial e Pricing:** Estabelecer a curva ótima de desconto que maximize o lucro operacional sem produzir pedidos deficitários.
- **Gerência de Operações e Logística:** Identificar e mitigar fatores de risco de cancelamento e devolução no ato da compra (*At-Purchase*).
- **Liderança de Marketing e CRM:** Desenvolver segmentação RFM dinâmica e direcionar orçamentos de mídia para canais com maior retorno sobre o custo de aquisição (CAC).

---

## 2. Perguntas Norteadoras e Hipóteses de Negócio

| ID | Pergunta de Negócio | Hipótese Formal Testável | Critério de Aceite / Refutação |
| :--- | :--- | :--- | :--- |
| **Q1** | Qual o ponto de inflexão em que o desconto passa a destruir valor operacional em vez de aumentar a contribuição? | **$H_1$ (Inflexão de Margem):** Existe um limiar crítico $D^* \in [35\%, 45\%]$ no qual a derivada do lucro em relação ao desconto torna-se estritamente negativa ($\frac{\partial \text{Profit}}{\partial \text{Discount}} < 0$). Vendas acima desse patamar concentram mais de 90% das transações com margem negativa. | Identificação de $D^*$ por categoria e demonstração empírica de perda líquida de margem. |
| **Q2** | Quais canais de aquisição geram clientes de maior qualidade econômica frente ao custo unitário de aquisição (CAC)? | **$H_2$ (Eficiência de CAC vs. LTV):** Canais orgânicos e de recomendação (Organic Search, Direct, Referral) geram relação $\frac{\text{LTV}}{\text{CAC}}$ pelo menos 25% superior a canais pagos (Google Ads, Facebook Ads), apesar do menor volume absoluto inicial. | Cálculo pontual de LTV acumulado vs. CAC de `customer_master.csv` por canal de marketing. |
| **Q3** | É possível antecipar preventivamente cancelamentos e devoluções usando exclusivamente dados do carrinho no checkout? | **$H_3$ (Risco Preventivo At-Purchase):** Um classificador supervisionado treinado estritamente com atributos do momento da compra supera um baseline de taxa base, atingindo $\text{PR-AUC} \ge 0,25$ (mais de 3,5x o baseline de 6,8%) sem utilizar dados de pós-venda. | Avaliação cega *Out-of-Time* (2025) com matriz de confusão e ganho de precisão sobre a taxa base. |
| **Q4** | Como a base de clientes se divide sob a ótica comportamental de Recência, Frequência e Valor (RFM)? | **$H_4$ (Concentração de Valor RFM):** A segmentação comportamental revelará que o decil superior de clientes fiéis (Champions/Loyalists) é responsável por mais de 35% do faturamento global e apresenta menor elasticidade negativa a preços. | Agrupamento estatístico com Silhouette $> 0,40$ e validação da curva de Pareto na receita. |
| **Q5** | O descompasso entre prazo estimado e prazo real de entrega penaliza sistematicamente a avaliação do cliente? | **$H_5$ (Penalidade por Atraso):** Pedidos concluídos com `delivery_days > estimated_delivery_days` sofrem penalidade média estatisticamente significativa ($\ge 0,5$ estrela) em `customer_rating` ($p < 0,001$). | Teste t de Student ou teste Mann-Whitney U comparando pedidos no prazo vs. atrasados. |

---

## 3. Requisitos Funcionais e Não-Funcionais

### 3.1. Requisitos Funcionais (RF)
- **RF-01 (Auditoria e Validação de Contratos):** Implementar suíte de testes com `pytest` e contratos com `pandera`/`patito` baseada em `docs/01-data-discovery-and-contracts.md`.
- **RF-02 (Engenharia de Atributos Pontuais):** Reconstruir métricas históricas de clientes de forma estritamente cumulativa (*point-in-time features*), sem utilizar campos com *look-ahead leakage* (`customer_lifetime_value`, `customer_order_count`, `customer_type`).
- **RF-03 (Motor de Segmentação RFM):** Calcular recência (dias desde a última compra), frequência acumulada e valor total gasto por cliente até cada data de corte, gerando clusters comportamentais interpretáveis.
- **RF-04 (Análise de Elasticidade e Margens):** Modelar matematicamente a relação entre percentual de desconto concedido, volume vendido e lucro líquido resultante, desagregado por categoria de catálogo.
- **RF-05 (Pipeline Preditivo Supervisionado):** Treinar e calibrar modelos de classificação supervisionada (ex: Logistic Regression balanceada, LightGBM, XGBoost) para estimativa de risco de desfecho desfavorável no momento da compra (*At-Purchase*).
- **RF-06 (Relatório Quarto Automatizado):** Consolidar narrativa, gráficos de 300 DPI e recomendações no padrão canônico de 6 seções Quarto (`.qmd`) com compilação HTML.

### 3.2. Requisitos Não-Funcionais (RNF)
- **RNF-01 (Blindagem de Vazamento de Dados):** Nenhuma variável com nulos derivados de desfecho (`delivery_days`, `customer_rating`, `review_sentiment`) ou determinismo (`payment_status == 'Refunded'/'Failed'`) poderá ser utilizada como preditora em modelos *At-Purchase*.
- **RNF-02 (Reprodutibilidade Estrita):** Fixação de sementes aleatórias globais (`seed = 42`) para todas as rotinas estocásticas, amostragens e splits.
- **RNF-03 (Isolamento de Ambiente):** Gestão de dependências e execução exclusivas via `uv run`, sem poluição do Python global.
- **RNF-04 (Padrão Gráfico Editorial):** Conformidade estrita com `quarto-quality-checklist.md` (`sns.despine()`, paletas com contraste adequado, proporções quadradas `set_box_aspect(1)` em subplots emparelhados e exportação com `dpi=300`).

---

## 4. Estratégia de Validação e Justificativa Matemática das Métricas

### 4.1. Esquema de Partição Temporal (*Out-of-Time*)
Dado o caráter temporal da série (2021 a 2025 com 1.826 dias contínuos), a partição aleatória (k-fold tradicional cruzando o tempo) acarretaria vazamento de dinâmica macroeconômica e sazonal. Adota-se o particionamento temporal canônico:

```
[ 2021-01-01  ──────────  2024-12-31 ]  ──→  [ 2025-01-01  ───────  2025-12-31 ]
          TREINO & VALIDAÇÃO                          TESTE CEGO (OUT-OF-TIME)
       110.518 pedidos (80,0%)                        27.598 pedidos (20,0%)
```

- **Janela de Treino e Ajuste (2021 a 2024):** 110.518 transações para engenharia de atributos, busca de hiperparâmetros e validação cruzada temporal em blocos (*TimeSeriesSplit*).
- **Janela de Teste Cego (2025):** 27.598 transações reservadas estritamente para avaliação final de generalização, sem qualquer intervenção no ajuste de modelos.

### 4.2. Justificativa Matemática da Métrica Primária

#### A. Tarefa Preditiva Supervisionada (Devolução / Cancelamento At-Purchase)
- **Desbalanceamento:** Taxa de retorno de 6,85% e taxa de cancelamento de 6,08%. Se o modelo predissesse sempre a classe negativa, alcançaria acurácia de 93,15% sendo inútil.
- **Métrica Primária:** **PR-AUC (Precision-Recall AUC / Average Precision)**. Ao contrário da ROC-AUC (que é inflada pelo grande volume de verdadeiros negativos), a PR-AUC foca estritamente na capacidade de identificar a classe minoritária sem inundar a operação de alarmes falsos:
$$\text{PR-AUC} = \int_0^1 P(R) \, dR \approx \sum_k (R_k - R_{k-1}) P_k$$
- **Métrica Secundária:** **F1-Score calibrado por Custo/Benefício**. O corte de probabilidade ótimo ($\tau^*$) será calibrado considerando o custo de reter preventivamente um pedido ou auditar um carrinho versus a margem bruta preservada.

#### B. Tarefa de Otimização de Pricing e Descontos
- **Métricas:** Elasticidade-preço da demanda e **Lucro Marginal Líquido**:
$$\Delta \text{Profit} = \text{Profit}(D) - \text{Profit}(0)$$
O ponto de corte $D^*$ corresponde à raiz de $\frac{\partial \text{Profit}}{\partial D} = 0$.

#### C. Tarefa de Segmentação de Clientes
- **Métricas:** **Silhouette Score** ($s \in [-1, 1]$) e **Calinski-Harabasz Index** (razão de variância entre clusters sobre intra-cluster), complementados por testes de estabilidade e interpretabilidade gerencial.

---

## 5. Matriz 1:1: Perguntas de Negócio vs. Visualizações e Diagnósticos

Conforme o checklist de qualidade Quarto, toda pergunta formulada na Seção 1 possui correspondência direta em visualização e diagnóstico.

| Pergunta / Hipótese | Seção do Relatório Quarto | Visualização Planejada (300 DPI) | Diagnóstico Quantitativo e Teste Estatístico |
| :--- | :--- | :--- | :--- |
| **Q1 / $H_1$ (Desconto vs. Margem)** | Seção 3 (Process / EDA) & Seção 6 (Act) | Painel duplo: (a) Scatterplot com linha de tendência polinomial de `Discount_Pct` vs. `Profit_Margin`, (b) Histograma com densidade KDE das 1.296 vendas com prejuízo. Proporção 1:1 (`set_box_aspect(1)`). | Estimativa do ponto de inflexão $D^*$, percentual de vendas deficitárias acima do limiar e cálculo da perda monetária acumulada. |
| **Q2 / $H_2$ (Canais de Marketing vs. LTV/CAC)** | Seção 3 (Process / EDA) & Seção 5 (Share) | Gráfico de barras horizontais ordenadas comparando $\frac{\text{LTV}}{\text{CAC}}$ por `marketing_channel`, com anotação direta dos valores médios de CAC e margem média gerada. | Intervalos de confiança de 95% via bootstrap para o ROI de aquisição por canal. |
| **Q3 / $H_3$ (Risco Preventivo At-Purchase)** | Seção 4 (Construct) & Seção 5 (Share) | Curvas PR (Precision-Recall) comparativas entre Baseline aleatório, Regressão Logística e LightGBM/XGBoost, acompanhadas do gráfico de importância de atributos por ganho real (`importance_type='gain'`). | Tabela multi-métrica com PR-AUC, ROC-AUC, Brier Score e matriz de confusão no limiar de custo ótimo no conjunto de teste de 2025. |
| **Q4 / $H_4$ (Segmentação RFM)** | Seção 3 (Process / EDA) & Seção 6 (Act) | Gráfico de dispersão 2D das componentes principais (PCA ou t-SNE) coloridas pelos clusters RFM, com diagrama em radar/barras do perfil médio de cada grupo. | Curva de Pareto demonstrando o percentual acumulado de receita gerado por cada segmento e índice de Silhouette dos clusters. |
| **Q5 / $H_5$ (Impacto de Atrasos Logísticos)** | Seção 3 (Process / EDA) | Boxplot pareado comparando a distribuição de `customer_rating` para entregas no prazo (`delivery_days <= estimated`) versus entregas atrasadas, com exibição das médias pontuais. | Teste t de Welch ou Mann-Whitney U reportando estatística do teste, p-valor e tamanho de efeito (Cohen's d). |

---

## 6. Escopo Negativo (*Non-Goals*)

A delimitação do que **NÃO** será executado impede desvios de escopo e consumo inútil de recursos.

1. **Predição de Séries Temporais Macro:** Não desenvolveremos modelos autoregressivos complexos (ARIMA/Prophet) para previsão de demanda diária agregada. O foco está na decisão por pedido e por cliente.
2. **Processamento de Linguagem Natural (NLP) em Avaliações:** A coluna `customer_review` contém apenas 25 variações sintéticas de texto correspondentes à nota numérica. Não faremos ajuste de LLMs ou embeddings textuais profundos, pois a informação já está capturada em `customer_rating` e `review_sentiment`.
3. **Engenharia de Microserviço ou Deploy em Produção:** O escopo do projeto se encerra na entrega analítica, validação estatística, visualizações canônicas e relatório executivo automatizado em Quarto (`.qmd` / HTML). Não serão criadas APIs FastAPI, containers Docker de inferência em tempo real ou bancos relacionais em produção.
4. **Utilização de Variáveis de Pós-Venda em Modelos At-Purchase:** É terminantemente vedado o uso de `delivery_days`, `customer_rating`, `return_reason` e `payment_status` nos modelos de risco prévio de checkout.
