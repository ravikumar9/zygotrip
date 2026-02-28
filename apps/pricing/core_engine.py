from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PricingConfig:
    demand_thresholds: tuple = (20, 40, 60, 80)
    demand_multipliers: tuple = (
        Decimal('0.70'),
        Decimal('0.85'),
        Decimal('1.00'),
        Decimal('1.15'),
        Decimal('1.25'),
    )
    competitor_floor: Decimal = Decimal('0.90')
    competitor_cap: Decimal = Decimal('1.05')
    min_base_multiplier: Decimal = Decimal('0.70')
    max_base_multiplier: Decimal = Decimal('2.50')


class UnifiedPricingEngine:
    def __init__(self, config: PricingConfig | None = None):
        self.config = config or PricingConfig()

    def _demand_multiplier(self, demand_score: int | float | None) -> Decimal:
        score = int(demand_score or 0)
        thresholds = self.config.demand_thresholds
        multipliers = self.config.demand_multipliers
        if score <= thresholds[0]:
            return multipliers[0]
        if score <= thresholds[1]:
            return multipliers[1]
        if score <= thresholds[2]:
            return multipliers[2]
        if score <= thresholds[3]:
            return multipliers[3]
        return multipliers[4]

    def calculate_price(
        self,
        base_price: Decimal,
        demand_score: int | float | None = None,
        competitor_price: Decimal | None = None,
    ) -> dict:
        base = Decimal(str(base_price))
        demand_multiplier = self._demand_multiplier(demand_score)
        final_price = base * demand_multiplier

        if competitor_price is not None:
            competitor = Decimal(str(competitor_price))
            min_competitor = competitor * self.config.competitor_floor
            max_competitor = competitor * self.config.competitor_cap
            final_price = min(max(final_price, min_competitor), max_competitor)

        min_base = base * self.config.min_base_multiplier
        max_base = base * self.config.max_base_multiplier
        final_price = min(max(final_price, min_base), max_base)

        return {
            'base_price': base,
            'demand_score': demand_score,
            'competitor_price': competitor_price,
            'demand_multiplier': demand_multiplier,
            'final_price': final_price.quantize(Decimal('0.01')),
        }


def calculate_price(base_price: Decimal, demand_score: int | float | None = None, competitor_price: Decimal | None = None) -> dict:
    return UnifiedPricingEngine().calculate_price(
        base_price=base_price,
        demand_score=demand_score,
        competitor_price=competitor_price,
    )
