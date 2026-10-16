"""Contratos formais de dados, esquemas Pandera e validações contábeis."""

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema

EXPECTED_ROW_COUNT: int = 138116
EXPECTED_COLUMN_COUNT: int = 46

VALID_ORDER_STATUSES = ["Completed", "Returned", "Cancelled", "Pending"]
VALID_GENDERS = ["Female", "Male", "Non-Binary"]
VALID_CUSTOMER_SEGMENTS = ["Consumer", "Premium", "VIP", "Business"]
VALID_REGIONS = ["South", "Central", "West", "East", "North"]
VALID_SALES_CHANNELS = ["Mobile App", "Website", "Marketplace", "Social Media"]
VALID_SHIPPING_METHODS = ["Standard", "Express", "Economy", "Same Day"]

transactions_schema = DataFrameSchema(
    columns={
        "order_id": Column(
            pa.String,
            checks=[
                Check.str_matches(r"^ORD-\d{6}$"),
            ],
            nullable=False,
            unique=True,
            description="Identificador unívoco do pedido.",
        ),
        "order_date": Column(
            pa.DateTime,
            nullable=False,
            description="Data da transação (2021 a 2025).",
        ),
        "customer_id": Column(
            pa.String,
            checks=[Check.str_matches(r"^CUST-\d{6}$")],
            nullable=False,
            description="Identificador do cliente.",
        ),
        "customer_age": Column(
            pa.Int64,
            checks=[Check.in_range(18, 100)],
            nullable=False,
            description="Idade do comprador.",
        ),
        "gender": Column(
            pa.String,
            checks=[Check.isin(VALID_GENDERS)],
            nullable=False,
        ),
        "customer_segment": Column(
            pa.String,
            checks=[Check.isin(VALID_CUSTOMER_SEGMENTS)],
            nullable=False,
        ),
        "region": Column(
            pa.String,
            checks=[Check.isin(VALID_REGIONS)],
            nullable=False,
        ),
        "sales_channel": Column(
            pa.String,
            checks=[Check.isin(VALID_SALES_CHANNELS)],
            nullable=False,
        ),
        "order_status": Column(
            pa.String,
            checks=[Check.isin(VALID_ORDER_STATUSES)],
            nullable=False,
        ),
        "shipping_method": Column(
            pa.String,
            checks=[Check.isin(VALID_SHIPPING_METHODS)],
            nullable=False,
        ),
        "quantity": Column(
            pa.Int64,
            checks=[Check.greater_than_or_equal_to(1)],
            nullable=False,
        ),
        "gross_sales": Column(
            pa.Float64,
            checks=[Check.greater_than(0)],
            nullable=False,
        ),
        "discount_amount": Column(
            pa.Float64,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=False,
        ),
        "tax_amount": Column(
            pa.Float64,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=False,
        ),
        "shipping_cost": Column(
            pa.Float64,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=False,
        ),
        "product_cost": Column(
            pa.Float64,
            checks=[Check.greater_than(0)],
            nullable=False,
        ),
        "net_sales": Column(
            pa.Float64,
            nullable=False,
        ),
        "profit": Column(
            pa.Float64,
            nullable=False,
        ),
        "profit_margin_percentage": Column(
            pa.Float64,
            nullable=False,
        ),
    },
    coerce=True,
    strict=False,
)


def validate_transactions_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Valida o DataFrame contra o esquema formal Pandera.

    Args:
        df: DataFrame contendo as transações brutas ou pré-processadas.

    Returns:
        DataFrame validado e tipado.

    Raises:
        pa.errors.SchemaError: Se alguma regra de contrato for violada.
    """
    return transactions_schema.validate(df)
