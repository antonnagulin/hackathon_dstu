package rating

type ScenarioDelta struct {
	ExtraVolume      float64
	ExtraDeals       float64
	ExtraBankShare   float64
	ExtraSubmitted   float64
	ExtraApproved    float64
	ConversionTarget *float64
}

type ScenarioResult struct {
	Current    Result  `json:"current"`
	Scenario   Result  `json:"scenario"`
	ScoreDelta float64 `json:"score_delta"`
}

func (c *Calculator) CalculateScenario(in Input, delta ScenarioDelta) (ScenarioResult, error) {
	current, err := c.Calculate(in)
	if err != nil {
		return ScenarioResult{}, err
	}

	scenarioInput := in
	scenarioInput.FactVolume += delta.ExtraVolume
	scenarioInput.FactDeals += delta.ExtraDeals
	scenarioInput.FactBankShare += delta.ExtraBankShare
	scenarioInput.SubmittedApps += delta.ExtraSubmitted
	scenarioInput.ApprovedApps += delta.ExtraApproved

	if delta.ConversionTarget != nil {
		scenarioInput.ConversionPercent = delta.ConversionTarget
	}

	scenario, err := c.Calculate(scenarioInput)
	if err != nil {
		return ScenarioResult{}, err
	}

	return ScenarioResult{
		Current:    current,
		Scenario:   scenario,
		ScoreDelta: round2(scenario.Score - current.Score),
	}, nil
}
