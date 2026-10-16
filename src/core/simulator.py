"""Motor de cálculo desacoplado para simulação de cenários de rentabilidade e risco operacional."""

import numpy as np

from src.core.schemas import (
    AcquisitionChannel,
    Category,
    RiskAlertLevel,
    SimulationResultOutput,
    SimulationScenarioInput,
)


class BusinessScenarioSimulator:
    """Motor analítico de simulação comercial, margem de contribuição e sensibilidade a descontos."""

    # Parâmetros base calibrados nos 138.116 registros históricos do projeto
    BASELINE_RETURN_RATE: float = 0.0685
    BASELINE_CANCELLATION_RATE: float = 0.0608

    # Ajustes por categoria em relação à média geral
    CATEGORY_RETURN_FACTORS: dict[Category, float] = {
        Category.FASHION: 0.025,
        Category.ELECTRONICS: 0.015,
        Category.HOME_APPLIANCES: 0.010,
        Category.JEWELRY: 0.005,
        Category.AUTOMOTIVE: 0.000,
        Category.SPORTS_OUTDOORS: -0.005,
        Category.BABY_KIDS: -0.005,
        Category.HOME_KITCHEN: -0.010,
        Category.BEAUTY_PERSONAL_CARE: -0.015,
        Category.HEALTH_WELLNESS: -0.020,
        Category.PET_SUPPLIES: -0.020,
        Category.OFFICE_SUPPLIES: -0.025,
        Category.TOYS_GAMES: -0.025,
        Category.BOOKS_MEDIA: -0.035,
        Category.GROCERY: -0.040,
    }

    # Ajustes por canal de aquisição
    CHANNEL_RETURN_FACTORS: dict[AcquisitionChannel, float] = {
        AcquisitionChannel.SOCIAL_MEDIA: 0.015,
        AcquisitionChannel.PAID_SEARCH: 0.010,
        AcquisitionChannel.AFFILIATE: 0.005,
        AcquisitionChannel.EMAIL: -0.005,
        AcquisitionChannel.DIRECT: -0.010,
        AcquisitionChannel.ORGANIC_SEARCH: -0.015,
    }

    def estimate_operational_risk_rates(
        self,
        delivery_days: int,
        discount_pct: float,
        category: Category,
        channel: AcquisitionChannel,
    ) -> tuple[float, float]:
        """Calcula probabilidades estimadas de devolução e cancelamento com base em heurísticas."""
        # 1. Taxa de Devolução (Return Rate)
        cat_adj = self.CATEGORY_RETURN_FACTORS.get(category, 0.0)
        chan_adj = self.CHANNEL_RETURN_FACTORS.get(channel, 0.0)

        p_return = self.BASELINE_RETURN_RATE + cat_adj + chan_adj

        # Penalidade de logística: atrasos e prazos longos aumentam devoluções (H5)
        if delivery_days > 5:
            extra_days = delivery_days - 5
            p_return += extra_days * 0.012

        # Descontos profundos aumentam compras por impulso e taxa de devolução
        if discount_pct > 0.40:
            excess_discount = discount_pct - 0.40
            p_return += excess_discount * 0.18

        # 2. Taxa de Cancelamento (Cancellation Rate)
        p_cancel = self.BASELINE_CANCELLATION_RATE + (chan_adj * 0.7)

        if delivery_days > 5:
            extra_days = delivery_days - 5
            p_cancel += extra_days * 0.009

        if discount_pct > 0.40:
            excess_discount = discount_pct - 0.40
            p_cancel += excess_discount * 0.12

        # Limites físicos de probabilidade [0.01, 0.75]
        p_return_clamped = float(np.clip(p_return, 0.01, 0.75))
        p_cancel_clamped = float(np.clip(p_cancel, 0.01, 0.60))

        return round(p_return_clamped, 4), round(p_cancel_clamped, 4)

    def calculate_unit_risk_provision(
        self,
        net_unit_price: float,
        unit_cost: float,
        tax_rate: float,
        p_return: float,
        p_cancel: float,
        reverse_logistics_cost: float,
    ) -> float:
        """Calcula o custo esperado de risco operacional provisionado por unidade."""
        # Margem unitária bruta que deixa de ser realizada em caso de cancelamento
        margin_lost_unit = max(0.0, net_unit_price * (1.0 - tax_rate) - unit_cost)

        # Provisão: custo logístico reverso ponderado + margem perdida pelo cancelamento
        risk_cost = (p_return * reverse_logistics_cost) + (p_cancel * margin_lost_unit)
        return float(risk_cost)

    def simulate_scenario(self, input_data: SimulationScenarioInput) -> SimulationResultOutput:
        """Executa simulação econômica completa para um cenário de precificação e volume."""
        q = input_data.quantity
        base_price = input_data.unit_price
        cogs_unit = input_data.unit_cost
        discount = input_data.discount_pct
        shipping_unit = input_data.shipping_cost
        tax_rate = input_data.tax_rate

        # 1. Preços e Faturamentos
        net_unit_price = base_price * (1.0 - discount)
        gross_revenue = round(float(q * base_price), 2)
        net_revenue = round(float(q * net_unit_price), 2)

        # 2. Taxas de Risco Operacional
        p_return, p_cancel = self.estimate_operational_risk_rates(
            delivery_days=input_data.delivery_days,
            discount_pct=discount,
            category=input_data.category,
            channel=input_data.channel,
        )

        # 3. Custos Diretos
        cogs_total = q * cogs_unit
        shipping_total = q * shipping_unit
        tax_total = net_revenue * tax_rate

        # 4. Provisão de Risco Operacional
        unit_risk = self.calculate_unit_risk_provision(
            net_unit_price=net_unit_price,
            unit_cost=cogs_unit,
            tax_rate=tax_rate,
            p_return=p_return,
            p_cancel=p_cancel,
            reverse_logistics_cost=input_data.reverse_logistics_cost,
        )
        total_risk_provision = q * unit_risk

        # 5. Custo Consolidado e Margem
        total_cost = round(float(cogs_total + shipping_total + tax_total + total_risk_provision), 2)
        contribution_margin_value = round(float(net_revenue - total_cost), 2)

        if net_revenue > 0:
            contribution_margin_pct = round(
                float((contribution_margin_value / net_revenue) * 100.0), 2
            )
        else:
            contribution_margin_pct = -100.0

        # 6. Ponto de Equilíbrio (Break-even Discount)
        break_even_discount = self.find_break_even_discount(input_data)

        # 7. Classificação do Alerta de Risco
        if contribution_margin_value < 0 or discount > break_even_discount or p_return >= 0.16:
            risk_alert = RiskAlertLevel.DANGER_RED.value
        elif contribution_margin_pct < 18.0 or p_return >= 0.09:
            risk_alert = RiskAlertLevel.WARNING_YELLOW.value
        else:
            risk_alert = RiskAlertLevel.SAFE_GREEN.value

        return SimulationResultOutput(
            gross_revenue=gross_revenue,
            net_revenue=net_revenue,
            total_cost=total_cost,
            contribution_margin_value=contribution_margin_value,
            contribution_margin_pct=contribution_margin_pct,
            break_even_discount=break_even_discount,
            estimated_return_rate=p_return,
            estimated_cancellation_rate=p_cancel,
            risk_alert=risk_alert,
        )

    def find_break_even_discount(self, input_data: SimulationScenarioInput) -> float:
        """Calcula o desconto comercial máximo no qual a margem líquida total se mantém não-negativa."""

        def evaluate_margin_at_discount(d: float) -> float:
            scenario = input_data.model_copy(update={"discount_pct": d})
            p_net = scenario.unit_price * (1.0 - d)
            p_ret, p_can = self.estimate_operational_risk_rates(
                delivery_days=scenario.delivery_days,
                discount_pct=d,
                category=scenario.category,
                channel=scenario.channel,
            )
            unit_risk = self.calculate_unit_risk_provision(
                net_unit_price=p_net,
                unit_cost=scenario.unit_cost,
                tax_rate=scenario.tax_rate,
                p_return=p_ret,
                p_cancel=p_can,
                reverse_logistics_cost=scenario.reverse_logistics_cost,
            )
            unit_margin = (
                p_net
                - scenario.unit_cost
                - scenario.shipping_cost
                - (p_net * scenario.tax_rate)
                - unit_risk
            )
            return unit_margin

        # Se já for deficitário sem desconto, break-even é zero
        if evaluate_margin_at_discount(0.0) < 0:
            return 0.0

        # Se ainda for superavitário com 90% de desconto, o limite é o próprio teto
        if evaluate_margin_at_discount(0.90) >= 0:
            return 0.90

        # Busca binária determinística entre 0.0 e 0.90
        low = 0.0
        high = 0.90
        for _ in range(40):
            mid = (low + high) / 2.0
            margin = evaluate_margin_at_discount(mid)
            if margin >= 0:
                low = mid
            else:
                high = mid

        return round(float(low), 4)

    def calculate_discount_sensitivity_curve(
        self,
        input_data: SimulationScenarioInput,
        steps: int = 20,
    ) -> list[dict[str, float | str | bool]]:
        """Gera curva paramétrica de sensibilidade variando o desconto de 0.0 a 0.90."""
        discounts = np.linspace(0.0, 0.90, max(5, steps))
        curve: list[dict[str, float | str | bool]] = []

        for d in discounts:
            scenario = input_data.model_copy(update={"discount_pct": float(d)})
            res = self.simulate_scenario(scenario)
            unit_net_price = round(float(scenario.unit_price * (1.0 - d)), 2)

            curve.append(
                {
                    "discount_pct": round(float(d), 4),
                    "unit_net_price": unit_net_price,
                    "net_revenue": res.net_revenue,
                    "total_cost": res.total_cost,
                    "contribution_margin_value": res.contribution_margin_value,
                    "contribution_margin_pct": res.contribution_margin_pct,
                    "estimated_return_rate": res.estimated_return_rate,
                    "estimated_cancellation_rate": res.estimated_cancellation_rate,
                    "risk_alert": res.risk_alert,
                    "is_profitable": bool(res.contribution_margin_value >= 0),
                }
            )

        return curve
