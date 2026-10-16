"""Módulo de carregamento determinístico e tipagem das fontes de dados."""

from pathlib import Path

import pandas as pd


def load_canonical_data(file_path: str | Path) -> pd.DataFrame:
    """Carrega o arquivo consolidado de transações aplicando tipagem canônica.

    Args:
        file_path: Caminho para o arquivo CSV consolidado.

    Returns:
        pd.DataFrame: Conjunto de dados carregado com tipos consistentes.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    df = pd.read_csv(path)
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


def load_customer_master(file_path: str | Path) -> pd.DataFrame:
    """Carrega a dimensão de clientes com custos de aquisição (CAC).

    Args:
        file_path: Caminho para o arquivo customer_master.csv.

    Returns:
        pd.DataFrame: Base cadastral de clientes.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    return pd.read_csv(path)


def load_product_catalog(file_path: str | Path) -> pd.DataFrame:
    """Carrega o catálogo de produtos e fornecedores.

    Args:
        file_path: Caminho para o arquivo product_catalog.csv.

    Returns:
        pd.DataFrame: Catálogo completo de produtos.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    return pd.read_csv(path)


def load_order_items(file_path: str | Path) -> pd.DataFrame:
    """Carrega os itens individuais dos pedidos com quantidades e preços.

    Args:
        file_path: Caminho para o arquivo order_items.csv.

    Returns:
        pd.DataFrame: Detalhamento de itens por pedido.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    return pd.read_csv(path)
