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
