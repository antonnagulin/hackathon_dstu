package rating

import "errors"

var (
	ErrInvalidPlanVolume      = errors.New("plan_volume must be greater than 0")
	ErrInvalidPlanDeals       = errors.New("plan_deals must be greater than 0")
	ErrInvalidTargetBankShare = errors.New("target_bank_share must be greater than 0")
	ErrInvalidWeights         = errors.New("weights sum must be equal to 1")
	ErrInvalidSubmittedApps   = errors.New("submitted_apps cannot be negative")
	ErrInvalidApprovedApps    = errors.New("approved_apps cannot be negative")
	ErrApprovedExceedsSent    = errors.New("approved_apps cannot exceed submitted_apps")
)
