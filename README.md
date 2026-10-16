# E-Commerce Sales & Customer Analytics

Repositório analítico e preditivo sobre 138.116 transações de e-commerce (2021–2025), desenvolvido sob a metodologia **CRISP-ML(Q) + Data Storytelling**.

## Estrutura do Projeto
- `docs/`: Documentos de concepção, contratos de dados, PRD, arquitetura e ADRs.
- `src/`: Módulos da aplicação analítica (`data`, `features`, `models`, `evaluation`).
- `tests/`: Suíte de testes automatizados e contratos contábeis.
- `reports/`: Relatório executivo editorial em Quarto (`index.qmd`) e figuras em 300 DPI.

## Ambiente e Execução
Gerenciamento de ambiente via `uv`:

```bash
# Executar suíte de testes
uv run pytest tests/ -v

# Linter e formatação
uv run ruff check . --fix && uv run ruff format .

# Renderizar relatório Quarto
quarto render reports/index.qmd
```
