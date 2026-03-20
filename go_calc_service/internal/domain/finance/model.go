package finance

type BonusRules struct {
	Silver float64
	Gold   float64
	Black  float64
}

type Input struct {
	Level string
	Score float64
	Rules BonusRules
}

type Result struct {
	Level string  `json:"level"`
	Score float64 `json:"score"`
	Bonus float64 `json:"bonus"`
}

type ScenarioResult struct {
	Current    Result  `json:"current"`
	Scenario   Result  `json:"scenario"`
	BonusDelta float64 `json:"bonus_delta"`
}
