package finance

import "errors"

var ErrUnknownLevel = errors.New("unknown level")

type Calculator struct{}

func NewCalculator() *Calculator {
	return &Calculator{}
}

func (c *Calculator) Calculate(in Input) (Result, error) {
	bonus, err := bonusByLevel(in.Level, in.Rules)
	if err != nil {
		return Result{}, err
	}

	return Result{
		Level: in.Level,
		Score: in.Score,
		Bonus: bonus,
	}, nil
}

func (c *Calculator) CalculateScenario(current Input, scenario Input) (ScenarioResult, error) {
	currentResult, err := c.Calculate(current)
	if err != nil {
		return ScenarioResult{}, err
	}

	scenarioResult, err := c.Calculate(scenario)
	if err != nil {
		return ScenarioResult{}, err
	}

	return ScenarioResult{
		Current:    currentResult,
		Scenario:   scenarioResult,
		BonusDelta: scenarioResult.Bonus - currentResult.Bonus,
	}, nil
}

func bonusByLevel(level string, rules BonusRules) (float64, error) {
	switch level {
	case "Silver":
		return rules.Silver, nil
	case "Gold":
		return rules.Gold, nil
	case "Black":
		return rules.Black, nil
	default:
		return 0, ErrUnknownLevel
	}
}
