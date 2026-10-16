"""Contratos de dados e validação de esquemas para inferência de risco."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.features.builder import PROHIBITED_LEAKAGE_COLS

GenderType = Literal["Female", "Male", "Non-Binary"]
CustomerSegmentType = Literal["Business", "Consumer", "Premium", "VIP"]
RegionType = Literal["Central", "East", "North", "South", "West"]
SalesChannelType = Literal["Marketplace", "Mobile App", "Social Media", "Website"]
MarketingChannelType = Literal[
    "Affiliate",
    "Direct",
    "Email Marketing",
    "Facebook Ads",
    "Google Ads",
    "Instagram",
    "Organic Search",
    "Referral",
    "TikTok",
    "YouTube",
]
PaymentMethodType = Literal[
    "Bank Transfer",
    "Buy Now Pay Later",
    "Cash on Delivery",
    "Credit Card",
    "Debit Card",
    "Digital Wallet",
    "PayPal",
]
ShippingMethodType = Literal["Economy", "Express", "Same Day", "Standard"]
WarehouseType = Literal[
    "WH-001",
    "WH-002",
    "WH-003",
    "WH-004",
    "WH-005",
    "WH-006",
    "WH-007",
    "WH-008",
    "WH-009",
    "WH-010",
    "WH-011",
    "WH-012",
    "WH-013",
    "WH-014",
    "WH-015",
    "WH-016",
    "WH-017",
    "WH-018",
    "WH-019",
]


class RiskScenarioInput(BaseModel):
    """Contrato de entrada para o modelo LightGBM at-purchase.

    Espelha fielmente as variáveis numéricas e categóricas do metadata.json,
    blindando a inferência contra campos desconhecidos e vazamento de dados.
    """

    model_config = ConfigDict(extra="forbid")

    # Numéricos (9)
    customer_age: float = Field(ge=18, le=100, description="Idade do cliente em anos")
    quantity: int = Field(ge=1, le=100, description="Quantidade de itens no pedido")
    gross_sales: float = Field(ge=0, description="Valor bruto de venda")
    tax_amount: float = Field(ge=0, description="Montante de impostos")
    shipping_cost: float = Field(ge=0, description="Custo de frete")
    product_cost: float = Field(ge=0, description="Custo unitário do produto (CPV)")
    orders_count_prior: int = Field(ge=0, description="Contagem acumulada de pedidos prévios")
    spend_prior: float = Field(ge=0, description="Gasto financeiro total prévio do cliente")
    days_since_last_order: int = Field(ge=0, description="Recência em dias desde o último pedido")

    # Categóricos (8)
    gender: GenderType = Field(description="Gênero do cliente")
    customer_segment: CustomerSegmentType = Field(description="Segmento do cliente")
    region: RegionType = Field(description="Região geográfica")
    sales_channel: SalesChannelType = Field(description="Canal de venda da transação")
    marketing_channel: MarketingChannelType = Field(description="Canal de marketing de aquisição")
    payment_method: PaymentMethodType = Field(description="Método de pagamento empregado")
    shipping_method: ShippingMethodType = Field(description="Modalidade de frete selecionada")
    warehouse: WarehouseType = Field(description="Centro de distribuição expedidor")

    @model_validator(mode="before")
    @classmethod
    def _validate_raw_leakage(cls, data: dict) -> dict:
        """Intercepta payload bruto para barrar imediatamente variáveis de leakage."""
        if isinstance(data, dict):
            forbidden = set(data.keys()) & set(PROHIBITED_LEAKAGE_COLS)
            if forbidden:
                raise ValueError(f"Campos proibidos (leakage) detectados: {sorted(forbidden)}")
        return data

    def check_no_leakage(self) -> None:
        """Levanta se qualquer campo extra (proibido) estiver presente."""
        forbidden = set(self.model_dump().keys()) & set(PROHIBITED_LEAKAGE_COLS)
        if forbidden:
            raise ValueError(f"Campos proibidos (leakage) detectados: {sorted(forbidden)}")
