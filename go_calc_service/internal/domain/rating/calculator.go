package rating

import "math"

type Calculator struct{}

func NewCalculator() *Calculator {
	return &Calculator{}
}

func (c *Calculator) Calculate(in Input) (Result, error) {
	if err := validateInput(in); err != nil {
		return Result{}, err
	}

	maxIndex := in.MaxIndex
	if maxIndex <= 0 {
		maxIndex = 120
	}

	volumeIndex := capped(percent(in.FactVolume, in.PlanVolume), maxIndex)
	dealsIndex := capped(percent(in.FactDeals, in.PlanDeals), maxIndex)
	bankShareIndex := capped(percent(in.FactBankShare, in.TargetBankShare), maxIndex)

	conversionIndex := 0.0
	if in.ConversionPercent != nil {
		conversionIndex = capped(*in.ConversionPercent, maxIndex)
	} else if in.SubmittedApps > 0 {
		conversionIndex = capped(percent(in.ApprovedApps, in.SubmittedApps), maxIndex)
	}

	volumeContribution := in.Weights.Volume * volumeIndex
	dealsContribution := in.Weights.Deals * dealsIndex
	shareContribution := in.Weights.BankShare * bankShareIndex
	convContribution := in.Weights.Conversion * conversionIndex

	score := round2(
		volumeContribution +
			dealsContribution +
			shareContribution +
			convContribution,
	)

	level := DetectLevel(score, in.Thresholds)
	nextLevel := BuildNextLevel(score, level, in.Thresholds)

	return Result{
		Score: score,
		Level: level,
		Breakdown: Breakdown{
			VolumeIndex:        round2(volumeIndex),
			DealsIndex:         round2(dealsIndex),
			BankShareIndex:     round2(bankShareIndex),
			ConversionIndex:    round2(conversionIndex),
			VolumeContribution: round2(volumeContribution),
			DealsContribution:  round2(dealsContribution),
			ShareContribution:  round2(shareContribution),
			ConvContribution:   round2(convContribution),
		},
		NextLevel: nextLevel,
	}, nil
}

func validateInput(in Input) error {
	if in.PlanVolume <= 0 {
		return ErrInvalidPlanVolume
	}
	if in.PlanDeals <= 0 {
		return ErrInvalidPlanDeals
	}
	if in.TargetBankShare <= 0 {
		return ErrInvalidTargetBankShare
	}
	if in.SubmittedApps < 0 {
		return ErrInvalidSubmittedApps
	}
	if in.ApprovedApps < 0 {
		return ErrInvalidApprovedApps
	}
	if in.SubmittedApps > 0 && in.ApprovedApps > in.SubmittedApps {
		return ErrApprovedExceedsSent
	}

	weightsSum := in.Weights.Volume + in.Weights.Deals + in.Weights.BankShare + in.Weights.Conversion
	if !almostEqual(weightsSum, 1.0) {
		return ErrInvalidWeights
	}

	return nil
}

func percent(fact, plan float64) float64 {
	if plan == 0 {
		return 0
	}
	return (fact / plan) * 100
}

func capped(v, maxV float64) float64 {
	if v < 0 {
		return 0
	}
	if v > maxV {
		return maxV
	}
	return v
}

func round2(v float64) float64 {
	return math.Round(v*100) / 100
}

func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

func almostEqual(a, b float64) bool {
	const eps = 1e-9
	return math.Abs(a-b) < eps
}
