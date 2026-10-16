# Roadmap do Projeto: ecommerce_sales_customer_analytics

**Arquétipo:** A (Data Science, Analytics & ML — CRISP-ML(Q) + Data Storytelling)  
**Stack Primária:** Python 3.12+ (`uv`) + Quarto CLI (`.qmd`) + Ruff + Pytest  
**Status Atual:** Pré-Código e Execução Técnica 100% Concluídos. Relatório e Site Compilados com Sucesso.

---

## 1. Fase Pré-Código (`pre-code-pipeline`) — [CONCLUÍDA]

- [x] **Gate 1: Contexto Inicial, Descoberta e Contratos de Dados (*Prepare*)**
  - [x] Criação do contrato de herança (`docs/00_archetype.md`)
  - [x] Profiling estatístico *read-only* das 46 variáveis (`ecommerce_sales_customer_analytics_150k.csv`)
  - [x] Auditoria de tabelas relacionais (`customer_master.csv`, `order_items.csv`, `product_catalog.csv`)
  - [x] Verificação matemática contábil de fórmulas (`net_sales`, `profit`, `profit_margin_percentage`)
  - [x] Mapeamento rigoroso de fronteiras temporais e matriz contra *Data Leakage*
  - [x] Elaboração do documento formal de contratos (`docs/01-data-discovery-and-contracts.md`)
  - [x] Checkpoint: Validação formal do usuário sobre achados e contratos de dados
- [x] **Gate 2: Ideação, Escopo, Hipóteses e Especificação (*Ask & Plan*)**
  - [x] Definição das hipóteses centrais de negócio (precificação, churn/devolução, LTV)
  - [x] Especificação de métricas primárias e secundárias com justificativa estatística
  - [x] Mapeamento 1:1 de perguntas de negócio para visualizações/diagnósticos
  - [x] Delimitação de *Non-Goals* (escopo negativo)
  - [x] Elaboração do PRD analítico (`docs/02-PRD-and-specs.md`)
  - [x] Checkpoint: Aprovação do escopo e hipóteses de modelagem
- [x] **Gate 3: Arquitetura do Pipeline e Storyboard (*Process, Construct & Share*)**
  - [x] Topologia do pipeline (ingestão -> validação de contratos -> feature store -> treino -> inferência)
  - [x] Storyboard de visualizações conforme checklist Quarto (`sns.despine()`, `dpi=300`, `aspect=1`)
  - [x] Esquema de partição temporal estrita (*Out-of-Time* train/val/test)
  - [x] ADRs técnicas (`docs/adr/0001-*.md` a `0003-*.md`)
  - [x] Checkpoint: Validação da arquitetura técnica e do plano visual
- [x] **Gate 4: Scaffolding, Estrutura de Pastas e Convenções**
  - [x] Inicialização do repositório Git e criação do `.gitignore`
  - [x] Configuração do ambiente via `uv` (`pyproject.toml`, Ruff, Pytest)
  - [x] Estrutura física de diretórios (`data/`, `src/`, `notebooks/`, `reports/`, `tests/`)
  - [x] Configuração do Quarto (`_quarto.yml` com `lang: pt-BR`, `freeze: auto`, banner e tema)
  - [x] Guia de convenções operacionais em `AGENTS.md`
  - [x] Checkpoint: Aprovação do scaffolding do projeto
- [x] **Gate 5: Plano de Implementação e Critérios de Aceite (*Deployment / Act*)**
  - [x] Decomposição atômica de tarefas ordenadas por dependência
  - [x] Definição dos testes unitários e de contratos (Pytest + Pandera)
  - [x] Plano de verificação automatizada (`uv run pytest`, `quarto render`)
  - [x] Elaboração do plano em `docs/05-implementation-plan.md`
  - [x] Checkpoint: Aceite final do plano antes da liberação de escrita de código

---

## 2. Fase de Execução Técnica (`execution-pipeline`) — [CONCLUÍDA]

- [x] **Gate 1: Núcleo de Lógica e Contratos (src/ + tests/)**
  - [x] T1.1: Suíte de testes TDD de contratos contábeis e schema (`tests/test_contracts.py`) [Red]
  - [x] T1.2: Implementação de validação de schemas Pandera (`src/data/contracts.py`)
  - [x] T1.3: Implementação do loader canônico e tipagem determinística (`src/data/loader.py`)
  - [x] T1.4: Execução e passagem verde dos testes (`uv run pytest tests/test_contracts.py`) [Green]
  - [x] Checkpoint: Validação formal do Gate 1 da execução técnica
- [x] **Gate 2: Integração e Modelagem (CRISP-ML(Q) Stages 3, 4, 5)**
  - [x] Features cumulativas point-in-time e blindagem contra leakage (`src/features/builder.py`)
  - [x] RFM dinâmico (`src/features/rfm.py`) e clustering K-Means (`src/models/clustering.py`)
  - [x] Otimização de margem e limite ótimo de desconto $D^*$ (`src/models/pricing.py`)
  - [x] Classificador preventivo At-Purchase via LightGBM (`src/models/train.py`)
  - [x] Avaliação cega Out-of-Time em 2025 e PR-AUC (`src/evaluation/metrics.py`)
  - [x] Checkpoint: Aprovação dos pipelines de transformação e modelos
- [x] **Gate 3: Dataviz de Publicação (reports/figures/)**
  - [x] Exportação das 5 figuras canônicas a 300 DPI (`aspect=1`, `sns.despine()`)
  - [x] Checkpoint: Aprovação dos gráficos editoriais
- [x] **Gate 4: Relatório Executivo Quarto (reports/index.qmd)**
  - [x] Redação executiva anti-IA nas 6 seções canônicas com callouts e tabelas
  - [x] Checkpoint: Validação textual e narrativa
- [x] **Gate 5: Auditoria Quarto e Build de Entrega**
  - [x] Execução de `quarto check` e `quarto render` gerando `_site/` completo (11 páginas compiladas)
  - [x] 16 testes unitários e de contratos aprovados sem falhas (`uv run pytest tests/`)
  - [x] Análise de linter limpa (`uv run ruff check .` e `uv run ruff format --check .`)
  - [x] **Enriquecimento Editorial Pré-Release (Storytelling End-to-End):**
    - [x] `fig_06_category_quadrant_analysis.png`: Matriz de Quadrante Receita vs Margem e Preço Unitário vs Volume
    - [x] `fig_07_operational_diagnostics_returns_payments.png`: Decomposição dos 8 motivos de devolução e taxas por meio de pagamento
    - [x] `fig_08_model_calibration_and_cost_curve.png`: Curva de calibração (Brier = 0,0893) e curva de custo total por limiar $\tau$
    - [x] Tabela metodológica dos gates da esteira analítica (`@tbl-methodology`)
    - [x] Tabela de simulação de custos operacionais por limiar de decisão (`@tbl-threshold-costs`)
    - [x] Tabela diagnóstica e plano de contenção de devoluções no fulfillment (`@tbl-returns-action`)
  - [x] Checkpoint: Entrega e publicação validadas com sucesso

