# Diretrizes Operacionais do Repositório: ecommerce_sales_customer_analytics

Este repositório adota os padrões do **Arquétipo A (Data Science, Analytics & ML)** sob a metodologia híbrida **CRISP-ML(Q) + Data Storytelling**. Todos os agentes e desenvolvedores devem cumprir as regras abaixo.

---

## 1. Runtimes e Comandos Canônicos

| Ferramenta | Caminho Canônico | Comando Padrão |
| :--- | :--- | :--- |
| **uv** | `/home/tales/.local/bin/uv` | `uv run <comando>` |
| **Git** | `/usr/bin/git` | `git commit -m "feat: ..."` |
| **Quarto CLI** | `/usr/local/bin/quarto` | `quarto render` |
| **Testes** | Integrado via `uv` | `uv run pytest` |
| **Linter & Formatter** | Integrado via `uv` | `uv run ruff check . --fix && uv run ruff format .` |

> **Aviso de Execução:** Nunca ative manualmente ambientes virtuais com `source .venv/bin/activate`. Toda execução deve ser prefixada com `uv run`.

---

## 2. Guardrails Críticos contra Vazamento de Dados (*Data Leakage*)

1. **Blindagem de Pós-Venda (*At-Purchase*):**
   - É terminantemente proibido incluir as seguintes colunas em modelos supervisionados de predição de risco de compra:
     `delivery_days`, `estimated_delivery_days`, `customer_rating`, `review_sentiment`, `customer_review`, `return_status`, `return_reason`, `delivery_status`.
   - `payment_status` não deve ser consumido diretamente se contiver os estados finais `Refunded` (100% devoluções) e `Failed` (100% cancelamentos).
2. **Blindagem Temporal (*Look-Ahead Leakage*):**
   - Atributos consolidados no fim da série (`customer_lifetime_value`, `customer_order_count`, `customer_type`, `is_repeat_customer`) não podem ser consumidos como variáveis brutas.
   - Toda feature histórica deve ser gerada estritamente com dados retroativos anteriores à data do pedido ($t < \text{order\_date}$).
3. **Partição Temporal Canônica:**
   - Modelos preditivos devem ser treinados e ajustados exclusivamente no período **2021 a 2024** (80% dos dados).
   - O ano de **2025** (20% dos dados) é reservado estritamente como conjunto de teste cego (*Out-of-Time*).

---

## 3. Padrão Editorial Quarto e Visualizações (`reports/index.qmd`)

1. **Metadados Obrigatórios (`_quarto.yml`):**
   - `lang: pt-BR` para textos automáticos em português.
   - `execute: freeze: auto` para blindar modelos pesados contra reexecução desnecessária.
   - `number-sections: true` ativo.
2. **Numeração de Cabeçalhos:**
   - **NUNCA** escreva números manuais nos títulos de seções do `.qmd` (escreva `## Contexto de Negócio e Hipóteses`, e não `## 1. Contexto de Negócio e Hipóteses`).
3. **Padrão Gráfico (Matplotlib / Seaborn):**
   - Subplots lado a lado gerados via painel único `fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)`.
   - Proporção estrita `ax.set_box_aspect(1)` em ambos os eixos pareados.
   - Aplicação obrigatória de `sns.despine(ax=ax)`.
   - Resolução editorial de exportação em `dpi=300`.
   - Importância de atributos em modelos de árvore calculada estritamente por **`gain`** (`importance_type='gain'`).

---

## 4. Política Anti-IA de Redação e Commits

- **Voz Sênior e Pragmática:** Escreva como um desenvolvedor ou cientista de dados real. Evite tom professoral, adjetivação inflada de marketing (*"robusto"*, *"pioneiro"*, *"vital"*) e fórmulas clichês (*"não apenas X, mas também Y"*, conclusões em uma linha).
- **Variação de Ritmo:** Alterne períodos curtos e objetivos com parágrafos mais explicativos.
- **Commits Convencionais:** Mensagens imperativas e limpas: `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`. Sem menções a inteligência artificial.
