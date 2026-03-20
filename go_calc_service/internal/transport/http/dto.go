package http

type CalculateRequest struct {
	FactVolume        float64  `json:"fact_volume"`
	PlanVolume        float64  `json:"plan_volume"`
	FactDeals         float64  `json:"fact_deals"`
	PlanDeals         float64  `json:"plan_deals"`
	FactBankShare     float64  `json:"fact_bank_share"`
	TargetBankShare   float64  `json:"target_bank_share"`
	SubmittedApps     float64  `json:"submitted_apps"`
	ApprovedApps      float64  `json:"approved_apps"`
	ConversionPercent *float64 `json:"conversion_percent,omitempty"`
	MaxIndex          float64  `json:"max_index"`

	Weights struct {
		Volume     float64 `json:"volume"`
		Deals      float64 `json:"deals"`
		BankShare  float64 `json:"bank_share"`
		Conversion float64 `json:"conversion"`
	} `json:"weights"`

	Thresholds struct {
		GoldFrom  float64 `json:"gold_from"`
		BlackFrom float64 `json:"black_from"`
	} `json:"thresholds"`
}

type ScenarioRequest struct {
	Input CalculateRequest `json:"input"`
	Delta struct {
		ExtraVolume      float64  `json:"extra_volume"`
		ExtraDeals       float64  `json:"extra_deals"`
		ExtraBankShare   float64  `json:"extra_bank_share"`
		ExtraSubmitted   float64  `json:"extra_submitted"`
		ExtraApproved    float64  `json:"extra_approved"`
		ConversionTarget *float64 `json:"conversion_target,omitempty"`
	} `json:"delta"`
}

type FinanceRequest struct {
	Input CalculateRequest `json:"input"`
	Rules BonusRulesDTO    `json:"rules"`
}

type FinanceScenarioRequest struct {
	Input CalculateRequest `json:"input"`
	Delta struct {
		ExtraVolume      float64  `json:"extra_volume"`
		ExtraDeals       float64  `json:"extra_deals"`
		ExtraBankShare   float64  `json:"extra_bank_share"`
		ExtraSubmitted   float64  `json:"extra_submitted"`
		ExtraApproved    float64  `json:"extra_approved"`
		ConversionTarget *float64 `json:"conversion_target,omitempty"`
	} `json:"delta"`
	Rules BonusRulesDTO `json:"rules"`
}

type CalculateResponse struct {
	Score     float64           `json:"score"`
	Level     string            `json:"level"`
	Breakdown BreakdownResponse `json:"breakdown"`
	NextLevel NextLevelResponse `json:"next_level"`
}

type ScenarioResponse struct {
	Current    CalculateResponse `json:"current"`
	Scenario   CalculateResponse `json:"scenario"`
	ScoreDelta float64           `json:"score_delta"`
}

type FinanceResponse struct {
	Level string  `json:"level"`
	Score float64 `json:"score"`
	Bonus float64 `json:"bonus"`
}

type FinanceScenarioResponse struct {
	Current    FinanceResponse `json:"current"`
	Scenario   FinanceResponse `json:"scenario"`
	BonusDelta float64         `json:"bonus_delta"`
}

type BreakdownResponse struct {
	VolumeIndex        float64 `json:"volume_index"`
	DealsIndex         float64 `json:"deals_index"`
	BankShareIndex     float64 `json:"bank_share_index"`
	ConversionIndex    float64 `json:"conversion_index"`
	VolumeContribution float64 `json:"volume_contribution"`
	DealsContribution  float64 `json:"deals_contribution"`
	ShareContribution  float64 `json:"share_contribution"`
	ConvContribution   float64 `json:"conv_contribution"`
}

type NextLevelResponse struct {
	CurrentLevel string   `json:"current_level"`
	NextLevel    *string  `json:"next_level,omitempty"`
	MissingScore *float64 `json:"missing_score,omitempty"`
}

type ErrorResponse struct {
	Error string `json:"error"`
}

type BonusRulesDTO struct {
	Silver float64 `json:"silver"`
	Gold   float64 `json:"Gold"`
	Black  float64 `json:"Black"`
}
