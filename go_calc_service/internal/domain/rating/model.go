package rating

type Input struct {
	FactVolume        float64
	PlanVolume        float64
	FactDeals         float64
	PlanDeals         float64
	FactBankShare     float64
	TargetBankShare   float64
	SubmittedApps     float64
	ApprovedApps      float64
	ConversionPercent *float64
	MaxIndex          float64
	Weights           Weights
	Thresholds        Thresholds
}

type Weights struct {
	Volume     float64
	Deals      float64
	BankShare  float64
	Conversion float64
}

type Thresholds struct {
	GoldFrom  float64
	BlackFrom float64
}

type Breakdown struct {
	VolumeIndex        float64
	DealsIndex         float64
	BankShareIndex     float64
	ConversionIndex    float64
	VolumeContribution float64
	DealsContribution  float64
	ShareContribution  float64
	ConvContribution   float64
}

type NextLevel struct {
	CurrentLevel string
	NextLevel    *string
	MissingScore *float64
}

type Result struct {
	Score     float64
	Level     string
	Breakdown Breakdown
	NextLevel NextLevel
}
