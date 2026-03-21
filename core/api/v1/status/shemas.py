from datetime import datetime

from ninja import Schema


class CalculateInSchema(Schema):
    FactVolume: float
    PlanVolume: float
    FactDeals: int
    PlanDeals: int
    FactBankShare: float
    TargetBankShare: float
    SubmittedApps: int
    ApprovedApps: int
    ConversionPercent: float
    MaxIndex: float
    Weights: dict
    Thresholds: dict

class GoServiceOutSchema(Schema):  # Исправлено: OutShema → OutSchema
    Score: float
    Level: str
    Breakdown: dict
    NextLevel: dict

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
