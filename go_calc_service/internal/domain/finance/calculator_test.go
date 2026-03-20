package finance

import "testing"

func TestCalculator_Calculate(t *testing.T) {
	calc := NewCalculator()

	result, err := calc.Calculate(Input{
		Level: "Gold",
		Score: 88.5,
		Rules: BonusRules{
			Silver: 0,
			Gold:   20000,
			Black:  40000,
		},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if result.Bonus != 20000 {
		t.Fatalf("expected bonus 20000, got %v", result.Bonus)
	}
}

func TestCalculator_CalculateScenario(t *testing.T) {
	calc := NewCalculator()

	result, err := calc.CalculateScenario(
		Input{
			Level: "Gold",
			Score: 88.5,
			Rules: BonusRules{
				Silver: 0,
				Gold:   20000,
				Black:  40000,
			},
		},
		Input{
			Level: "Black",
			Score: 93.5,
			Rules: BonusRules{
				Silver: 0,
				Gold:   20000,
				Black:  40000,
			},
		},
	)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if result.BonusDelta != 20000 {
		t.Fatalf("expected bonus delta 20000, got %v", result.BonusDelta)
	}
}
