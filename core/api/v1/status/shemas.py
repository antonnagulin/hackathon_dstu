from datetime import datetime
from typing import Optional

from ninja import Schema


class CalculateInSchema(Schema):
    fact_volume: float
    plan_volume: float
    fact_deals: int
    plan_deals: int
    fact_bank_share: float
    target_bank_share: float
    submitted_apps: int
    approved_apps: int
    conversion_percent: float
    max_index: float
    weights: dict
    thresholds: dict


class GoServiceOutSchema(Schema):
    score: float
    level: str
    # breakdown: dict
    next_level: dict

class ScenarioDeltaInSchema(Schema):
    ExtraVolume: float = 0.0
    ExtraDeals: int = 0
    ExtraBankShare: float = 0.0
    ExtraSubmitted: int = 0
    ExtraApproved: int = 0
    ConversionTarget: float = 0.0

class ScenarioInSchema(Schema):
    Input: CalculateInSchema
    Delta: ScenarioDeltaInSchema

class BreakdownOutSchema(Schema):
    VolumeIndex: float
    DealsIndex: float
    BankShareIndex: float
    ConversionIndex: float
    VolumeContribution: float
    DealsContribution: float
    ShareContribution: float
    ConvContribution: float

class NextLevelOutSchema(Schema):
    CurrentLevel: str
    NextLevel: str | None = None
    MissingScore: float

class CalculateOutSchema(Schema):
    Score: float
    Level: str
    Breakdown: BreakdownOutSchema
    NextLevel: NextLevelOutSchema

class ScenarioOutSchema(Schema):
    Current: CalculateOutSchema
    Scenario: CalculateOutSchema
    ScoreDelta: float

class EmployeeRatingSchema(Schema):
    EmployeeId: int
    Name: str
    Position: str | None = None
    CurrentScore: float
    CurrentLevel: str
    CalculatedAt: datetime
    ScenarioApplied: bool = False
    ScenarioScoreDelta: float | None = None

class HealthCheckSchema(Schema):
    Service: str
    Status: str
    Timestamp: datetime
    Version: str | None = None
      


class FinancialForecastSchema(Schema):
    next_level: str | None = None
    income_growth_year: float
    mortgage_saving_year: float
    other_benefit_year: float
    total_benefit_year: float
    title: str
    description: str


class StatusScreenSchema(Schema):
    employee_id: int
    name: str
    level: str
    score: float
    next_level: str | None = None
    points_to_next_level: float | None = None
    progress_percent: float
    financial_forecast: FinancialForecastSchema
    next_level_points: float
    
    
    
    
    
class FinancialForecastSchema(Schema):
    next_level: str | None = None
    income_growth_year: float
    mortgage_saving_year: float
    other_benefit_year: float
    total_benefit_year: float
    title: str
    description: str


class ScenarioStateSchema(Schema):
    level: str
    score: float
    bonus: float


class ScenarioDeltaSchema(Schema):
    score_delta: float
    bonus_delta: float
    income_growth_year: float
    mortgage_saving_year: float
    other_benefit_year: float
    total_benefit_year: float


class AppliedChangesSchema(Schema):
    extra_volume: float
    extra_deals: int
    extra_bank_share: float
    extra_submitted: int
    extra_approved: int
    extra_products: int

    
    
class ScenarioScreenInSchema(Schema):
    extra_deals: int = 0
    extra_volume: float = 0.0
    extra_bank_share: float = 0.0
    extra_submitted: int = 0
    extra_approved: int = 0
    extra_products: int = 0


class ScenarioCurrentStatusSchema(Schema):
    level: str
    points_to_next_level: float


class ScenarioResultSchema(Schema):
    new_score: float
    new_level: str
    new_income: float
    new_saving: float


class ScenarioScreenOutSchema(Schema):
    current_status: ScenarioCurrentStatusSchema
    result: ScenarioResultSchema
    
    
class RatingDetailItemSchema(Schema):
    code: str
    title: str
    points: float
    formula: str
    how_to_improve: str


class RatingDetailsScreenSchema(Schema):
    level: str
    score: float
    next_level: str | None = None
    points_to_next_level: float | None = None
    items: list[RatingDetailItemSchema]
    
    

class LevelPrivilegeItemSchema(Schema):
    title: str
    description: str
    financial_effect_rub: float
    status: str
    unlock_level: str


class LevelPrivilegesScreenSchema(Schema):
    current_level: str
    active: list[LevelPrivilegeItemSchema]
    locked: list[LevelPrivilegeItemSchema]
