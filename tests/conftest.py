"""Fixtures compartilhadas para suíte de testes de dados e modelos."""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Retorna o diretório raiz do projeto."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def raw_data_path(project_root: Path) -> Path:
    """Retorna o caminho do arquivo consolidado de transações."""
    return project_root / "data" / "raw" / "ecommerce_sales_customer_analytics_150k.csv"
