"""Suíte de testes de contratos de dados e integridade contábil."""

from pathlib import Path

from src.data.contracts import (
    EXPECTED_COLUMN_COUNT,
    EXPECTED_ROW_COUNT,
    validate_transactions_schema,
)
from src.data.loader import load_canonical_data


def test_raw_file_existence(raw_data_path: Path) -> None:
    """Valida se o arquivo bruto canônico existe e não está vazio."""
    assert raw_data_path.exists(), f"Arquivo não encontrado: {raw_data_path}"
    assert raw_data_path.stat().st_size > 0, "Arquivo bruto está vazio."


def test_load_canonical_dimensions(raw_data_path: Path) -> None:
    """Verifica volumetria exata de 138.116 linhas e 46 colunas."""
    df = load_canonical_data(raw_data_path)
    assert len(df) == EXPECTED_ROW_COUNT, f"Esperado {EXPECTED_ROW_COUNT} linhas, obtido {len(df)}"
    assert df.shape[1] == EXPECTED_COLUMN_COUNT, (
        f"Esperado {EXPECTED_COLUMN_COUNT} colunas, obtido {df.shape[1]}"
    )


def test_order_id_uniqueness(raw_data_path: Path) -> None:
    """Garante que order_id é chave primária unívoca sem nulos."""
    df = load_canonical_data(raw_data_path)
    assert df["order_id"].isnull().sum() == 0, "Existem valores nulos em order_id."
    assert df["order_id"].nunique() == EXPECTED_ROW_COUNT, "order_id possui duplicatas."


def test_accounting_algebra_net_sales(raw_data_path: Path) -> None:
    """Garante a identidade: net_sales = gross_sales - discount_amount + tax_amount + shipping_cost."""
    df = load_canonical_data(raw_data_path)
    expected_net = (
        df["gross_sales"] - df["discount_amount"] + df["tax_amount"] + df["shipping_cost"]
    )
    discrepancy = (df["net_sales"] - expected_net).abs()
    assert discrepancy.max() < 0.01, (
        f"Erro contábil em net_sales. Desvio máximo: {discrepancy.max()}"
    )


def test_accounting_algebra_profit(raw_data_path: Path) -> None:
    """Garante a identidade: profit = net_sales - shipping_cost - product_cost."""
    df = load_canonical_data(raw_data_path)
    expected_profit = df["net_sales"] - df["shipping_cost"] - df["product_cost"]
    discrepancy = (df["profit"] - expected_profit).abs()
    assert discrepancy.max() < 0.01, f"Erro contábil em profit. Desvio máximo: {discrepancy.max()}"


def test_temporal_boundary(raw_data_path: Path) -> None:
    """Valida o intervalo estrito de 2021-01-01 a 2025-12-31."""
    df = load_canonical_data(raw_data_path)
    min_date = df["order_date"].min()
    max_date = df["order_date"].max()
    assert str(min_date).startswith("2021-01-01"), f"Data mínima incorreta: {min_date}"
    assert str(max_date).startswith("2025-12-31"), f"Data máxima incorreta: {max_date}"


def test_schema_contracts_validation(raw_data_path: Path) -> None:
    """Executa a validação formal de schema via Pandera/Polars."""
    df = load_canonical_data(raw_data_path)
    validated_df = validate_transactions_schema(df)
    assert validated_df is not None


def test_catalog_and_items_loading(project_root: Path) -> None:
    """Valida o carregamento dos arquivos de catálogo e itens individuais."""
    from src.data.loader import load_order_items, load_product_catalog

    cat_path = project_root / "data" / "raw" / "product_catalog.csv"
    items_path = project_root / "data" / "raw" / "order_items.csv"

    if not cat_path.exists() or not items_path.exists():
        import pytest

        pytest.skip(
            "Arquivos de catálogo e itens ausentes no ambiente (excluídos do repositório remoto)."
        )

    df_cat = load_product_catalog(cat_path)
    df_items = load_order_items(items_path)

    assert len(df_cat) > 0, "Catálogo de produtos vazio."
    assert "product_category" in df_cat.columns, "Coluna product_category ausente no catálogo."
    assert len(df_items) > 0, "Tabela order_items vazia."
    assert "unit_price" in df_items.columns, "Coluna unit_price ausente em order_items."
