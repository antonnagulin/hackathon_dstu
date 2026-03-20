package rating

import "testing"

func TestCalculator_Calculate_Success(t *testing.T) {
	calc := NewCalculator()

	input := Input{
		FactVolume:      8,
		PlanVolume:      10,
		FactDeals:       12,
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

	got, err := calc.Calculate(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if got.Score != 93.5 {
		t.Fatalf("expected score 93.5, got %v", got.Score)
	}

	if got.Level != "Black" {
		t.Fatalf("expected level Black, got %s", got.Level)
	}

	if got.Breakdown.VolumeIndex != 80 {
		t.Fatalf("expected volume index 80, got %v", got.Breakdown.VolumeIndex)
	}
	if got.Breakdown.DealsIndex != 120 {
		t.Fatalf("expected deals index 120, got %v", got.Breakdown.DealsIndex)
	}
	if got.Breakdown.BankShareIndex != 100 {
		t.Fatalf("expected bank share index 100, got %v", got.Breakdown.BankShareIndex)
	}
	if got.Breakdown.ConversionIndex != 70 {
		t.Fatalf("expected conversion index 70, got %v", got.Breakdown.ConversionIndex)
	}
}

func TestCalculator_Calculate_CapApplied(t *testing.T) {
	calc := NewCalculator()

	input := Input{
		FactVolume:      20,
		PlanVolume:      10,
		FactDeals:       30,
		PlanDeals:       10,
		FactBankShare:   90,
		TargetBankShare: 50,
		SubmittedApps:   10,
		ApprovedApps:    10,
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

	got, err := calc.Calculate(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if got.Breakdown.VolumeIndex != 120 {
		t.Fatalf("expected capped volume index 120, got %v", got.Breakdown.VolumeIndex)
	}
	if got.Breakdown.DealsIndex != 120 {
		t.Fatalf("expected capped deals index 120, got %v", got.Breakdown.DealsIndex)
	}
	if got.Breakdown.BankShareIndex != 120 {
		t.Fatalf("expected capped share index 120, got %v", got.Breakdown.BankShareIndex)
	}
	if got.Breakdown.ConversionIndex != 100 {
		t.Fatalf("expected conversion index 100, got %v", got.Breakdown.ConversionIndex)
	}
}

func TestCalculator_Calculate_InvalidWeights(t *testing.T) {
	calc := NewCalculator()

	input := Input{
		FactVolume:      8,
		PlanVolume:      10,
		FactDeals:       12,
		PlanDeals:       10,
		FactBankShare:   50,
		TargetBankShare: 50,
		SubmittedApps:   10,
		ApprovedApps:    7,
		MaxIndex:        120,
		Weights: Weights{
			Volume:     0.50,
			Deals:      0.25,
			BankShare:  0.25,
			Conversion: 0.15,
		},
		Thresholds: Thresholds{
			GoldFrom:  70,
			BlackFrom: 90,
		},
	}

	_, err := calc.Calculate(input)
	if err == nil {
		t.Fatal("expected error, got nil")
	}
}

func TestCalculator_Calculate_UsesProvidedConversion(t *testing.T) {
	calc := NewCalculator()
	conversion := 85.0

	input := Input{
		FactVolume:        8,
		PlanVolume:        10,
		FactDeals:         12,
		PlanDeals:         10,
		FactBankShare:     50,
		TargetBankShare:   50,
		ConversionPercent: &conversion,
		MaxIndex:          120,
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

	got, err := calc.Calculate(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if got.Breakdown.ConversionIndex != 85 {
		t.Fatalf("expected conversion index 85, got %v", got.Breakdown.ConversionIndex)
	}
}
