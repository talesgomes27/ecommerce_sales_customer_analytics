"""Schemas e contratos de dados tipados para simulação de cenários de negócio."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AcquisitionChannel(StrEnum):
    """Canais de aquisição de clientes auditados no e-commerce."""

    DIRECT = "Direct"
    ORGANIC_SEARCH = "Organic Search"
    PAID_SEARCH = "Paid Search"
    SOCIAL_MEDIA = "Social Media"
    EMAIL = "Email"
    AFFILIATE = "Affiliate"

    @classmethod
    def _missing_(cls, value: Any) -> Any:
        if isinstance(value, str):
            clean_val = value.strip().lower().replace("_", " ")
            for member in cls:
                if (
                    member.value.lower() == clean_val
                    or member.name.lower() == value.strip().lower()
                ):
                    return member
        return None


class Category(StrEnum):
    """Categorias comerciais de produtos catalogados."""

    AUTOMOTIVE = "Automotive"
    BABY_KIDS = "Baby & Kids"
    BEAUTY_PERSONAL_CARE = "Beauty & Personal Care"
    BOOKS_MEDIA = "Books & Media"
    ELECTRONICS = "Electronics"
    FASHION = "Fashion"
    GROCERY = "Grocery"
    HEALTH_WELLNESS = "Health & Wellness"
    HOME_KITCHEN = "Home & Kitchen"
    HOME_APPLIANCES = "Home Appliances"
    JEWELRY = "Jewelry"
    OFFICE_SUPPLIES = "Office Supplies"
    PET_SUPPLIES = "Pet Supplies"
    SPORTS_OUTDOORS = "Sports & Outdoors"
    TOYS_GAMES = "Toys & Games"

    @classmethod
    def _missing_(cls, value: Any) -> Any:
        if isinstance(value, str):
            clean_val = value.strip().lower().replace("_", " ")
            for member in cls:
                if (
                    member.value.lower() == clean_val
                    or member.name.lower() == value.strip().lower()
                ):
                    return member
        return None


class LoyaltyTier(StrEnum):
    """Níveis de fidelidade do cliente."""

    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"

    @classmethod
    def _missing_(cls, value: Any) -> Any:
        if isinstance(value, str):
            clean_val = value.strip().lower()
            for member in cls:
                if member.value.lower() == clean_val or member.name.lower() == clean_val:
                    return member
        return None


class Region(StrEnum):
    """Regiões operacionais de entrega."""

    CENTRAL = "Central"
    EAST = "East"
    NORTH = "North"
    SOUTH = "South"
    WEST = "West"

    @classmethod
    def _missing_(cls, value: Any) -> Any:
        if isinstance(value, str):
            clean_val = value.strip().lower()
            for member in cls:
                if member.value.lower() == clean_val or member.name.lower() == clean_val:
                    return member
        return None


class RiskAlertLevel(StrEnum):
    """Classificação de risco operacional e sanitário da margem."""

    SAFE_GREEN = "SAFE_GREEN"
    WARNING_YELLOW = "WARNING_YELLOW"
    DANGER_RED = "DANGER_RED"


class SimulationScenarioInput(BaseModel):
    """Parâmetros de entrada para simulação de um cenário comercial e logístico."""

    model_config = ConfigDict(use_enum_values=False, extra="forbid")

    unit_price: float = Field(
        ...,
        gt=0.0,
        description="Preço unitário base sem desconto de tabela em USD (> 0)",
    )
    unit_cost: float = Field(
        ...,
        gt=0.0,
        description="Custo unitário da mercadoria vendida (CMV) em USD (> 0)",
    )
    quantity: int = Field(
        ...,
        ge=1,
        description="Volume projetado de unidades vendidas (>= 1)",
    )
    discount_pct: float = Field(
        ...,
        ge=0.0,
        le=0.90,
        description="Percentual de desconto comercial aplicado [0.0, 0.90]",
    )
    shipping_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Custo logístico de frete/envio por unidade/pedido em USD (>= 0)",
    )
    tax_rate: float = Field(
        default=0.10,
        ge=0.0,
        le=0.50,
        description="Alíquota de imposto efetivo sobre faturamento líquido [0.0, 0.50]",
    )
    delivery_days: int = Field(
        default=3,
        ge=1,
        le=60,
        description="Prazo de entrega prometido em dias corridos (>= 1)",
    )
    category: Category = Field(
        default=Category.ELECTRONICS,
        description="Categoria comercial do produto",
    )
    channel: AcquisitionChannel = Field(
        default=AcquisitionChannel.DIRECT,
        description="Canal de aquisição de tráfego/venda",
    )
    reverse_logistics_cost: float = Field(
        default=45.0,
        ge=0.0,
        description="Custo operacional de transporte e reprocessamento por devolução em USD",
    )

    @field_validator("unit_cost")
    @classmethod
    def validate_cost_against_base_price(cls, v: float, info: Any) -> float:
        """Assegura sanidade física inicial de custo positivo."""
        return v


class SimulationResultOutput(BaseModel):
    """Resultados consolidados da simulação de rentabilidade e risco operacional."""

    model_config = ConfigDict(use_enum_values=False, extra="forbid")

    gross_revenue: float = Field(
        ...,
        description="Faturamento bruto total (Quantidade x Preço Base de tabela) em USD",
    )
    net_revenue: float = Field(
        ...,
        description="Faturamento líquido efetivo após descontos em USD",
    )
    total_cost: float = Field(
        ...,
        description="Custo total consolidado (CMV + Frete + Impostos + Provisão de Risco) em USD",
    )
    contribution_margin_value: float = Field(
        ...,
        description="Margem de contribuição líquida absoluta em USD",
    )
    contribution_margin_pct: float = Field(
        ...,
        description="Margem de contribuição percentual sobre o faturamento líquido",
    )
    break_even_discount: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Desconto comercial máximo antes da destruição total de margem [0.0, 1.0]",
    )
    estimated_return_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Taxa projetada de devolução do pedido",
    )
    estimated_cancellation_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Taxa projetada de cancelamento pré-envio",
    )
    risk_alert: str = Field(
        ...,
        description="Classificação do risco operacional: SAFE_GREEN, WARNING_YELLOW ou DANGER_RED",
    )
