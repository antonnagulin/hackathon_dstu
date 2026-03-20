package rating

import "testing"

func TestCalculator_CalculateScenario_ExtraDeals(t *testing.T) {
	calc := NewCalculator()

	input := Input{
		FactVolume:      8,
		PlanVolume:      10,
		FactDeals:       10,
		PlanDeals:       10,
		FactBankShare:   50,
		TargetBankShare: 50,
		SubmittedApps:   10,
		ApprovedApps:    7,
		MaxIndex:        120,
		Weights: Weights{
			Volume:     0.35,
			Deals:      0.25,
			BankShare:  0.25,
			Conversion: 0.15,
		},
		Thresholds: Thresholds{
			GoldFrom:  70,
			BlackFrom: 90,
		},
	}

	result, err := calc.CalculateScenario(input, ScenarioDelta{
		ExtraDeals: 2,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if result.Scenario.Score <= result.Current.Score {
		t.Fatalf("expected scenario score > current score, got current=%v scenario=%v",
			result.Current.Score, result.Scenario.Score)
	}
}

func TestCalculator_CalculateScenario_ConversionTarget(t *testing.T) {
	calc := NewCalculator()
	target := 85.0

	input := Input{
		FactVolume:      8,
		PlanVolume:      10,
		FactDeals:       10,
		PlanDeals:       10,
		FactBankShare:   50,
		TargetBankShare: 50,
		SubmittedApps:   10,
		ApprovedApps:    7,
		MaxIndex:        120,
		Weights: Weights{
			Volume:     0.35,
			Deals:      0.25,
			BankShare:  0.25,
			Conversion: 0.15,
		},
		Thresholds: Thresholds{
			GoldFrom:  70,
			BlackFrom: 90,
		},
	}

	result, err := calc.CalculateScenario(input, ScenarioDelta{
		ConversionTarget: &target,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if result.Scenario.Breakdown.ConversionIndex != 85 {
		t.Fatalf("expected conversion 85, got %v", result.Scenario.Breakdown.ConversionIndex)
	}
}
