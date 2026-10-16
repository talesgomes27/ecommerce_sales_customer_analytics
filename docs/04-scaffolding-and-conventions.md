# Gate 4: Scaffolding, Estrutura de Diretórios e Convenções Operacionais

**Projeto:** `ecommerce_sales_customer_analytics`  
**Data:** 2026-10-16  
**Arquétipo:** A (Data Science, Analytics & ML — CRISP-ML(Q) + Data Storytelling)  
**Status do Portão:** Elaborado para validação humana  

---

## 1. Árvore Física Instanciada do Repositório

O projeto foi estruturado seguindo as convenções de pacotes modulares Python e a metodologia Quarto de publicação científica:

```text
ecommerce_sales_customer_analytics/
├── .git/                                    # Controle de versão Git inicializado (branch main)
├── .gitignore                               # Regras de exclusão (.venv, caches, _freeze, _site)
├── _quarto.yml                              # Configuração de publicação Quarto (pt-BR, freeze, cosmo)
├── pyproject.toml                           # Especificação PEP 621, dependências, Ruff e Pytest
├── AGENTS.md                                # Diretrizes operacionais e guardrails para agentes
├── task.md                                  # Rastreabilidade dos 5 Gates pré-código (planning-with-files)
├── about.txt                                # Documentação e metadados de domínio
├── dataset_statistics.csv                   # Resumo estatístico de baseline
├── ecommerce_sales_customer_analytics_150k.csv # Base canônica consolidada (138.116 pedidos, 46 variáveis)
├── order_items.csv                          # Base relacional de itens de pedidos (397.569 registros)
├── product_catalog.csv                      # Catálogo com 1.175 produtos e 15 categorias
├── customer_master.csv                      # Cadastro de 25.000 clientes com CAC
├── docs/                                    # Artefatos da pré-código (Memória Persistente)
│   ├── 00_archetype.md                      # Herança do Arquétipo A (stack python-uv-quarto)
│   ├── 01-data-discovery-and-contracts.md   # Auditoria das 46 variáveis, álgebra e data contracts
│   ├── 02-PRD-and-specs.md                  # Especificação formal, hipóteses H1-H5 e escopo negativo
│   ├── 03-architecture-and-schema.md        # Topologia de pipeline, etapas e storyboard Quarto
│   ├── 04-scaffolding-and-conventions.md    # Este documento
│   └── adr/                                 # Registros de Decisão Arquitetural
│       ├── 0001-pipeline-and-feature-store-architecture.md
│       ├── 0002-modelling-and-evaluation-strategy.md
│       └── 0003-quarto-storytelling-and-publication-standard.md
├── src/                                     # Código modular da aplicação analítica
│   ├── __init__.py                          # Pacote raiz do projeto
│   ├── data/                                # Camada de ingestão, sanitização e validação de schema
│   │   └── __init__.py
│   ├── features/                            # Engenharia de features point-in-time e RFM dinâmico
│   │   └── __init__.py
│   ├── models/                              # Treinamento de clustering, elasticidade e classificadores
│   │   └── __init__.py
│   └── evaluation/                          # Cálculo de métricas (PR-AUC, F1), custos e explicabilidade
│       └── __init__.py
├── tests/                                   # Suíte de testes unitários e de contratos
│   ├── __init__.py
│   └── conftest.py                          # Fixtures de sessão (caminhos e recursos de dados)
├── notebooks/                               # Espaço de experimentação exploratória e prototipagem
└── reports/                                 # Artefatos editoriais e gráficos para publicação
    ├── figures/                             # Imagens e gráficos estáticos de alta resolução (300 DPI)
    └── index.qmd                            # Relatório executivo canônico em 6 seções Quarto
```

---

## 2. Configurações de Tooling e Ambiente

### 2.1. Gerenciador de Dependências (`uv`) e `pyproject.toml`
- Gestor oficial do ambiente Python 3.12+ localizado no caminho canônico `/home/tales/.local/bin/uv`.
- Configuração conforme PEP 621 com dependências analíticas pinadas (`polars`, `pandas`, `scikit-learn`, `lightgbm`, `xgboost`, `pandera`, `statsmodels`, `seaborn`).
- Ferramental de qualidade: `ruff` (regras de estilo, import sorting e boas práticas) e `pytest` (testes automatizados estritos).

### 2.2. Motor Quarto (`_quarto.yml`)
- Binário canônico em `/usr/local/bin/quarto` (versão 1.10.18).
- Compilação configurada com:
  - `lang: pt-BR` (rótulos automáticos em português).
  - `execute: freeze: auto` (cache de execução dos modelos de machine learning).
  - `number-sections: true` com proibição de numeração manual nos títulos do `.qmd`.
  - Padrão editorial de figuras em 300 DPI (`fig-dpi: 300`).

### 2.3. Guardrails e Governança (`AGENTS.md`)
- Centraliza os caminhos canônicos de runtimes do sistema.
- Estabelece a proibição inegociável de uso de variáveis de pós-venda em modelagens preventivas *At-Purchase*.
- Impõe a partição temporal cega de 2025 para validação estatística.
- Determina a conformidade anti-IA na redação técnica e mensagens semânticas de commit no Git.
