# Gate 1: Descoberta, Auditoria e Contratos de Dados (Prepare)

**Projeto:** `ecommerce_sales_customer_analytics`  
**Data da Auditoria:** 2026-10-16  
**Metodologia:** CRISP-ML(Q) + Data Storytelling  
**Status do Portão:** Concluído para validação humana  

---

## 1. Contexto Geral e Inventário de Fontes

O ecossistema de dados cobre o ciclo operacional de e-commerce entre 01/01/2021 e 31/12/2025. Os dados brutos residem em arquivos CSV na raiz do repositório.

| Arquivo | Granularidade | Registros | Colunas | Papel no Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| `ecommerce_sales_customer_analytics_150k.csv` | Pedido transacional consolidado | 138.116 | 46 | **Fonte primária canônica** de modelagem e KPIs executivos |
| `order_items.csv` | Item de pedido | 397.569 | 12 | Fonte auxiliar para abertura de mix e itens por carrinho |
| `product_catalog.csv` | Dimensão de produto | 1.175 | 9 | Catálogo com marcas, categorias e custos de fornecedores |
| `customer_master.csv` | Dimensão de cliente | 25.000 | 11 | Cadastro com dados demográficos e CAC |
| `dataset_statistics.csv` | Metadados de controle | 1 | 11 | Baseline oficial de checagem do conjunto consolidado |

### Diagnóstico de Consistência entre Fontes
A auditoria comparou o consolidado de pedidos (`ecommerce_sales_customer_analytics_150k.csv`) com as tabelas relacionais:
1. **Unicidade de Pedidos:** A base principal contém 138.116 pedidos sem nenhuma duplicata de linha ou de `order_id`. Todos os 138.116 identificadores existem em `order_items.csv`.
2. **Discrepância em Linhas de Itens:** Em 126.890 pedidos (91,9%), os itens em `order_items.csv` somam com precisão de centavos aos campos agregados de quantidade, receita bruta, impostos e frete da base consolidada. Nos 11.226 pedidos restantes (8,1%), detectou-se inserção não contígua de linhas excedentes no arquivo de itens. Portanto, a base `ecommerce_sales_customer_analytics_150k.csv` é o registro oficial de verdade contábil.
3. **Base de Clientes:** Dos 25.000 clientes cadastrados em `customer_master.csv`, 24.911 realizaram compras no período auditado; 89 clientes nunca registraram transações.

---

## 2. Dicionário Auditado das 46 Variáveis

As 46 variáveis do arquivo canônico foram agrupadas em 5 domínios de negócio funcionais.

### 2.1. Domínio Transacional e Temporal (4 variáveis)
| Coluna | Tipo | Nulos (%) | Únicos | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | String | 0 (0,0%) | 138.116 | Identificador unívoco do pedido (`ORD-XXXXXX`). Chave primária. |
| `order_date` | Date (YYYY-MM-DD) | 0 (0,0%) | 1.826 | Data da transação. Cobre exatamente 5 anos civis sem interrupções. |
| `order_time` | Time (HH:MM:SS) | 0 (0,0%) | 68.991 | Horário do registro do pedido. |
| `order_status` | Categorical | 0 (0,0%) | 4 | Status final: `Completed` (82,22%), `Returned` (6,85%), `Cancelled` (6,08%), `Pending` (4,85%). |

### 2.2. Domínio Cliente e Inteligência (12 variáveis)
| Coluna | Tipo | Nulos (%) | Únicos | Descrição e Observações |
| :--- | :--- | :--- | :--- | :--- |
| `customer_id` | String | 0 (0,0%) | 24.911 | Identificador único do cliente (`CUST-XXXXXX`). |
| `customer_name` | String | 0 (0,0%) | 21.564 | Nome do comprador (PII descartável na modelagem). |
| `customer_age` | Integer | 0 (0,0%) | 57 | Idade do cliente (faixa entre 18 e 74 anos, média 45,9 anos). |
| `gender` | Categorical | 0 (0,0%) | 3 | Gênero: Female (48,10%), Male (47,99%), Non-Binary (3,90%). |
| `customer_segment` | Categorical | 0 (0,0%) | 4 | Segmentação comercial: Consumer (54,76%), Premium (25,16%), VIP (10,11%), Business (9,97%). |
| `customer_type` | Categorical | 0 (0,0%) | 3 | Classificação: Loyal (93,72%), Returning (6,03%), New (0,24%). |
| `customer_city` | String | 0 (0,0%) | 15.516 | Município de cobrança/entrega. |
| `customer_state` | String | 0 (0,0%) | 38 | Estado ou província. |
| `customer_country` | Categorical | 0 (0,0%) | 7 | País: USA (59,80%), UK (14,65%), Germany (8,39%), Canada (5,08%), Australia (4,92%), India (4,13%), UAE (3,02%). |
| `region` | Categorical | 0 (0,0%) | 5 | Macrorregião: South (31,85%), Central (21,45%), West (19,02%), East (15,64%), North (12,04%). |
| `customer_postal_code`| Integer | 0 (0,0%) | 22.117 | Código postal. |
| `sales_channel` | Categorical | 0 (0,0%) | 4 | Canal de venda: Mobile App (40,05%), Website (34,92%), Marketplace (14,99%), Social Media (10,04%). |

### 2.3. Domínio Marketing, Campanhas e Fidelidade (6 variáveis)
| Coluna | Tipo | Nulos (%) | Únicos | Descrição e Observações |
| :--- | :--- | :--- | :--- | :--- |
| `marketing_channel` | Categorical | 0 (0,0%) | 10 | Canal de atração: Organic Search (20,1%), Google Ads (14,9%), Direct (14,8%), Facebook Ads (12,1%), etc. |
| `campaign_name` | Categorical | 83.233 (60,3%) | 17 | Campanha vinculada. Nulo indica aquisição espontânea ou sem tag. |
| `coupon_code` | Categorical | 110.502 (80,0%) | 40 | Cupom promocional utilizado no fechamento do carrinho. |
| `loyalty_points_earned` | Integer | 0 (0,0%) | 846 | Pontos acumulados com o pedido (média 104, máx 1.621). |
| `loyalty_points_redeemed`| Integer | 0 (0,0%) | 642 | Pontos resgatados como crédito na compra (média 52, máx 1.063). |
| `is_repeat_customer` | Boolean | 0 (0,0%) | 2 | Flag estática de recompra no período (99,76% True). |

### 2.4. Domínio Logística e Pós-Venda (9 variáveis)
| Coluna | Tipo | Nulos (%) | Únicos | Descrição e Observações |
| :--- | :--- | :--- | :--- | :--- |
| `payment_method` | Categorical | 0 (0,0%) | 7 | Credit Card (30,0%), Debit Card (20,0%), PayPal (15,0%), Digital Wallet (11,9%), COD (10,0%), BNPL (8,0%), Bank Transfer (5,0%). |
| `payment_status` | Categorical | 0 (0,0%) | 4 | Paid (75,5%), Pending (10,1%), Failed (7,6%), Refunded (6,8%). |
| `currency` | Categorical | 0 (0,0%) | 7 | Moeda local da transação (USD, GBP, EUR, CAD, AUD, INR, AED). |
| `shipping_method` | Categorical | 0 (0,0%) | 4 | Standard (44,9%), Express (24,9%), Economy (20,1%), Same Day (10,1%). |
| `warehouse` | Categorical | 0 (0,0%) | 19 | Centro de distribuição expedidor (WH-001 a WH-019, balanceados em ~5,3% cada). |
| `delivery_days` | Float | 24.557 (17,8%) | 15 | Prazo real decorrido até entrega (0 a 14 dias, média 4,56). Nulo se o pedido não foi concluído. |
| `estimated_delivery_days`| Float | 24.557 (17,8%) | 11 | Prazo estimado de entrega prometido ao comprador (0 a 10 dias). |
| `delivery_status` | Categorical | 0 (0,0%) | 4 | On Time (62,9%), Cancelled (17,8%), Delayed (12,2%), Early (7,1%). |
| `return_status` | Categorical | 128.654 (93,1%)| 1 | Indicador de devolução confirmada (`Returned`). |
| `return_reason` | Categorical | 128.654 (93,1%)| 8 | Motivos: Wrong Product, Other, Changed Mind, Size Issue, Defective Product, Late Delivery, Not as Expected, Damaged. |
| `customer_rating` | Float | 24.557 (17,8%) | 35 | Nota de avaliação pós-entrega (1,6 a 5,0 estrelas, média 3,68). |
| `review_sentiment` | Categorical | 24.557 (17,8%) | 3 | Sentimento: Positive (56,5%), Neutral (25,1%), Negative (0,6%). |
| `customer_review` | String | 24.557 (17,8%) | 25 | Texto pré-formatado da avaliação do cliente. |

### 2.5. Domínio Comercial, Precificação e Margens (8 variáveis)
| Coluna | Tipo | Nulos (%) | Únicos | Descrição e Observações |
| :--- | :--- | :--- | :--- | :--- |
| `quantity` | Integer | 0 (0,0%) | 24 | Unidades de produto no pedido (faixa de 1 a 24 itens, média 5,62). |
| `gross_sales` | Float | 0 (0,0%) | 100.130 | Valor bruto dos itens ($\text{preço de catálogo} \times \text{quantidade}$). |
| `discount_amount` | Float | 0 (0,0%) | 58.437 | Desconto monetário concedido na compra. |
| `tax_amount` | Float | 0 (0,0%) | 43.093 | Tributo incidente sobre a operação. |
| `shipping_cost` | Float | 0 (0,0%) | 11.973 | Custo/tarifa de frete repassado no pedido. |
| `net_sales` | Float | 0 (0,0%) | 112.204 | Receita líquida faturada. Total acumulado de \$177.134.263,74. |
| `product_cost` | Float | 0 (0,0%) | 88.450 | Custo dos produtos faturados aos fornecedores (COGS). |
| `profit` | Float | 0 (0,0%) | 91.021 | Lucro operacional da transação. Total acumulado de \$76.146.395,76. |
| `profit_margin_percentage`| Float | 0 (0,0%) | 7.947 | Margem de lucro relativa percentual da transação. |
| `customer_lifetime_value` | Float | 0 (0,0%) | 24.752 | LTV consolidado do cliente (estático em todo o histórico). |
| `customer_order_count` | Integer | 0 (0,0%) | 19 | Frequência total de compras do cliente na janela histórica (1 a 20). |

---

## 3. Auditoria Matemática e Consistência Contábil

A análise contábil inspecionou as 138.116 linhas para desvendar as relações algébricas exatas adotadas na composição financeira.

### 3.1. Equação da Receita Líquida (`net_sales`)
A auditoria comparou hipóteses de composição e encontrou correspondência com precisão de máquina ($3,64 \times 10^{-12}$ de resíduo flutuante máximo):
$$\text{net\_sales} = \text{gross\_sales} - \text{discount\_amount} + \text{tax\_amount} + \text{shipping\_cost}$$
*Interpretação:* O faturamento líquido nesta base engloba tanto o valor pago pelos itens (com desconto aplicado) quanto as quantias recolhidas para frete e impostos.

### 3.2. Equação do Lucro Operacional (`profit`)
A relação que fecha as somas com precisão absoluta ($2,73 \times 10^{-12}$ de desvio máximo) é:
$$\text{profit} = \text{net\_sales} - \text{shipping\_cost} - \text{product\_cost}$$
Expandindo a partir da receita líquida:
$$\text{profit} = (\text{gross\_sales} - \text{discount\_amount} + \text{tax\_amount}) - \text{product\_cost}$$
*Achado Crítico de Governança:* O frete faturado é neutralizado integralmente pelo custo logístico. Entretanto, o valor de `tax_amount` permanece na conta de lucro da transação neste dataset sintético, atuando como receita retida. Modelagens de margem gerencial devem isolar o efeito tributário para análises puras de contribuição comercial.

### 3.3. Margem Percentual de Lucro (`profit_margin_percentage`)
$$\text{profit\_margin\_percentage} = \left(\frac{\text{profit}}{\text{net\_sales}}\right) \times 100$$
O valor gerado na coluna é arredondado para duas casas decimais (erro máximo menor que 0,005).

### 3.4. Transações Deficitárias (Margem Negativa)
- **Volumetria:** 1.296 pedidos (0,94% do volume global) operam no prejuízo ($\text{profit} < 0$).
- **Impacto Financeiro:** Prejuízos unitários variam de -\$0,01 até -\$1.281,59 (margens de até -59,55%).
- **Causa Raiz:** Nestes pedidos, o desconto médio atinge \$1.284,98 sobre uma venda bruta média de \$2.533,67 (desconto de 50,7%). Descontos acima de 40% a 50% superam a margem bruta de catálogo, gerando destruição direta de caixa.

---

## 4. Matriz de Prevenção contra Vazamento de Dados (*Data Leakage*)

Esta matriz estabelece regras estritas para impedir que variáveis sintomáticas ou calculadas a posteriori contaminem o treinamento de modelos estatísticos ou de machine learning.

```
+---------------------------------------------------------------------------------------------------+
|                                 FRONTEIRA DE INGESTÃO E TEMPO                                      |
+------------------------------------+--------------------------------------------------------------+
| MOMENTO DA COMPRA (At-Purchase)    | PÓS-VENDA & PROCESSAMENTO OPERACIONAL (Post-Purchase)        |
| - Gênero, Idade, Região            | - delivery_days, estimated_delivery_days (100% NaN em perdas)|
| - sales_channel, marketing_channel | - delivery_status (Classifica Cancelled em perdas)           |
| - quantity, gross_sales, desconto  | - payment_status ('Refunded' = 100% Ret; 'Failed' = 100% Can)|
| - warehouse, shipping_method       | - return_status, return_reason                               |
| - customer_acquisition_cost        | - customer_rating, review_sentiment, customer_review         |
+------------------------------------+--------------------------------------------------------------+
```

### 4.1. Vazamento Direto de Alvo (*Target Leakage*)
1. **Nulos Estruturais em Pós-Venda:**
   As colunas `delivery_days`, `estimated_delivery_days`, `customer_rating`, `review_sentiment` e `customer_review` possuem exatamente 24.557 registros nulos. A auditoria comprovou que esses nulos correspondem à soma exata de:
   - `order_status == 'Returned'` (9.462 pedidos)
   - `order_status == 'Cancelled'` (8.398 pedidos)
   - `order_status == 'Pending'` (6.697 pedidos)
   Nenhum pedido cancelado ou devolvido possui avaliação ou prazo de entrega registrado. Se qualquer uma dessas variáveis entrar no treino de um classificador de churn, devolução ou cancelamento, o modelo aprenderá o atalho espúrio `delivery_days is NaN -> Não Concluído`, atingindo 100% de acurácia artificial e valor preditivo nulo em produção.
2. **Determinismo em `payment_status`:**
   - 100% dos pedidos devolvidos (`Returned`) apresentam `payment_status == 'Refunded'`.
   - 100% dos pedidos cancelados (`Cancelled`) apresentam `payment_status == 'Failed'`.
   Esses estados de pagamento refletem o desfecho da transação, e não o momento de submissão do carrinho. São estritamente proibidos em modelos preventivos *At-Purchase*.
3. **Mapeamento em `delivery_status`:**
   A classe `Cancelled` em `delivery_status` reúne todos os pedidos cancelados, devolvidos e pendentes. É um vazamento idêntico ao rótulo alvo.

### 4.2. Vazamento Temporal e Visão do Futuro (*Look-Ahead Leakage*)
1. **Atributos de Cliente Estáticos:**
   As variáveis `customer_lifetime_value`, `customer_order_count`, `customer_type` e `is_repeat_customer` foram geradas agregando os 5 anos completos (2021 a 2025).
   Um pedido efetuado em 2021 por um cliente que comprou 19 vezes até 2025 já possui `customer_order_count = 19` e `is_repeat_customer = True` gravados na linha de 2021.
2. **Regra de Isolamento:**
   Em qualquer análise preditiva ou regressão temporal, essas quatro variáveis estáticas **NÃO** podem ser consumidas como features brutas. Elas devem ser substituídas por métricas cumulativas pontuais (*point-in-time features* calculadas estritamente com histórico anterior a cada `order_date`).

### 4.3. Vazamento por Dependência Algébrica
As variáveis financeiras `gross_sales`, `discount_amount`, `tax_amount`, `shipping_cost`, `product_cost`, `net_sales` e `profit` formam uma identidade linear fechada. Em tarefas de regressão (ex: prever `profit`), utilizar os componentes diretos da soma gera colinearidade perfeita e trivialização do modelo.

---

## 5. Contratos de Dados (*Data Contracts*)

Regras formais que qualquer lote de dados deve cumprir antes do estágio de preparação e modelagem.

### 5.1. Contrato de Integridade Estrutural e Chaves
- `order_id`: Chave primária. Tipo `string`, formato regex `^ORD-[0-9]{6}$`, sem valores nulos, unicidade de 100%.
- `customer_id`: Chave estrangeira para clientes. Formato regex `^CUST-[0-9]{6}$`, sem valores nulos.
- `order_date`: Data ISO `YYYY-MM-DD`, restrita ao intervalo contínuo `[2021-01-01, 2025-12-31]`.

### 5.2. Contrato de Domínio e Limites Numéricos
- `customer_age`: Inteiro no intervalo $[18, 100]$.
- `quantity`: Inteiro estritamente positivo ($quantity \ge 1$).
- `gross_sales`: Ponto flutuante estritamente positivo ($gross\_sales > 0$).
- `discount_amount`: Ponto flutuante não-negativo ($discount\_amount \ge 0$). Deve cumprir $discount\_amount \le gross\_sales$.
- `tax_amount`: Ponto flutuante não-negativo ($tax\_amount \ge 0$).
- `shipping_cost`: Ponto flutuante não-negativo ($shipping\_cost \ge 0$).
- `product_cost`: Ponto flutuante estritamente positivo ($product\_cost > 0$).
- `net_sales`: Ponto flutuante com tolerância contábil: $|net\_sales - (gross\_sales - discount\_amount + tax\_amount + shipping\_cost)| < 0,01$.
- `profit`: Ponto flutuante com tolerância: $|profit - (net\_sales - shipping\_cost - product\_cost)| < 0,01$.
- `profit_margin_percentage`: Ponto flutuante com tolerância: $|profit\_margin\_percentage - (\frac{profit}{net\_sales} \times 100)| < 0,05$.

### 5.3. Contrato de Categorias e Validação de Conjunto
- `order_status` $\in \{\text{'Completed'}, \text{'Returned'}, \text{'Cancelled'}, \text{'Pending'}\}$.
- `gender` $\in \{\text{'Female'}, \text{'Male'}, \text{'Non-Binary'}\}$.
- `customer_segment` $\in \{\text{'Consumer'}, \text{'Premium'}, \text{'VIP'}, \text{'Business'}\}$.
- `region` $\in \{\text{'South'}, \text{'Central'}, \text{'West'}, \text{'East'}, \text{'North'}\}$.
- `sales_channel` $\in \{\text{'Mobile App'}, \text{'Website'}, \text{'Marketplace'}, \text{'Social Media'}\}$.
- `shipping_method` $\in \{\text{'Standard'}, \text{'Express'}, \text{'Economy'}, \text{'Same Day'}\}$.

---

## 6. Oportunidades Analíticas e Frentes de Modelagem

Com base no profiling auditado, emergem 3 avenidas de exploração analítica para o Gate 2:

1. **Segmentação Comportamental & RFM (Customer Intelligence):**
   - Recalcular Recência, Frequência e Valor Monetário dinâmicos por cliente.
   - Cruzar clusters comportamentais com a segmentação corporativa (`customer_segment`), canal de aquisição e CAC registrado em `customer_master.csv`.
2. **Elasticidade e Sensibilidade a Descontos (Pricing & Margins):**
   - Mapear a fronteira ótima de descontos por categoria de produto e canal de vendas.
   - Identificar a curva exata em que o desconto adicional deixa de gerar lucro incremental e passa a integrar a coorte de vendas deficitárias (0,94% da base).
3. **Modelagem Preditiva Preventiva (*At-Purchase Risk Modeling*):**
   - Classificador supervisionado para prever probabilidade de devolução (`Returned`) ou cancelamento (`Cancelled`) utilizando estritamente variáveis disponíveis no momento da compra (*At-Purchase*).
   - Validação temporal rigorosa (*Out-of-Time*): treino com pedidos de 2021 a 2024 e teste cego com pedidos de 2025.
