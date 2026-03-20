package http

import (
	"encoding/json"
	"errors"
	"io"
	stdhttp "net/http"

	"hackathon/go_service/internal/app/calculator"
	appfinance "hackathon/go_service/internal/app/finance"
	domainfinance "hackathon/go_service/internal/domain/finance"
	"hackathon/go_service/internal/domain/rating"
)

type Handler struct {
	calculatorService *calculator.Service
	financeService    *appfinance.Service
}

func NewHandler(calculatorService *calculator.Service, financeService *appfinance.Service) *Handler {
	return &Handler{
		calculatorService: calculatorService,
		financeService:    financeService,
	}
}

func (h *Handler) Health(w stdhttp.ResponseWriter, r *stdhttp.Request) {
	if r.Method != stdhttp.MethodGet {
		writeError(w, stdhttp.StatusMethodNotAllowed, "method not allowed")
		return
	}

	writeJSON(w, stdhttp.StatusOK, map[string]string{
		"status": "ok",
	})
}

func (h *Handler) Calculate(w stdhttp.ResponseWriter, r *stdhttp.Request) {
	if r.Method != stdhttp.MethodPost {
		writeError(w, stdhttp.StatusMethodNotAllowed, "method not allowed")
		return
	}

	defer r.Body.Close()

	var req CalculateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		if errors.Is(err, io.EOF) {
			writeError(w, stdhttp.StatusBadRequest, "empty request body")
			return
		}
		writeError(w, stdhttp.StatusBadRequest, "invalid json")
		return
	}

	result, err := h.calculatorService.Calculate(mapCalculateRequestToInput(req))
	if err != nil {
		writeError(w, stdhttp.StatusBadRequest, err.Error())
		return
	}

	writeJSON(w, stdhttp.StatusOK, mapResultToResponse(result))
}

func (h *Handler) Scenario(w stdhttp.ResponseWriter, r *stdhttp.Request) {
	if r.Method != stdhttp.MethodPost {
		writeError(w, stdhttp.StatusMethodNotAllowed, "method not allowed")
		return
	}

	defer r.Body.Close()

	var req ScenarioRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		if errors.Is(err, io.EOF) {
			writeError(w, stdhttp.StatusBadRequest, "empty request body")
			return
		}
		writeError(w, stdhttp.StatusBadRequest, "invalid json")
		return
	}

	input := mapCalculateRequestToInput(req.Input)

	delta := rating.ScenarioDelta{
		ExtraVolume:      req.Delta.ExtraVolume,
		ExtraDeals:       req.Delta.ExtraDeals,
		ExtraBankShare:   req.Delta.ExtraBankShare,
		ExtraSubmitted:   req.Delta.ExtraSubmitted,
		ExtraApproved:    req.Delta.ExtraApproved,
		ConversionTarget: req.Delta.ConversionTarget,
	}

	result, err := h.calculatorService.CalculateScenario(input, delta)
	if err != nil {
		writeError(w, stdhttp.StatusBadRequest, err.Error())
		return
	}

	resp := ScenarioResponse{
		Current:    mapResultToResponse(result.Current),
		Scenario:   mapResultToResponse(result.Scenario),
		ScoreDelta: result.ScoreDelta,
	}

	writeJSON(w, stdhttp.StatusOK, resp)
}

func (h *Handler) Finance(w stdhttp.ResponseWriter, r *stdhttp.Request) {
	if r.Method != stdhttp.MethodPost {
		writeError(w, stdhttp.StatusMethodNotAllowed, "method not allowed")
		return
	}

	defer r.Body.Close()

	var req FinanceRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		if errors.Is(err, io.EOF) {
			writeError(w, stdhttp.StatusBadRequest, "empty request body")
			return
		}
		writeError(w, stdhttp.StatusBadRequest, "invalid json")
		return
	}

	ratingResult, err := h.calculatorService.Calculate(mapCalculateRequestToInput(req.Input))
	if err != nil {
		writeError(w, stdhttp.StatusBadRequest, err.Error())
		return
	}

	financeResult, err := h.financeService.Calculate(domainfinance.Input{
		Level: ratingResult.Level,
		Score: ratingResult.Score,
		Rules: mapBonusRulesDTOToDomain(req.Rules),
	})
	if err != nil {
		writeError(w, stdhttp.StatusBadRequest, err.Error())
		return
	}

	writeJSON(w, stdhttp.StatusOK, mapFinanceResultToResponse(financeResult))
}

func (h *Handler) FinanceScenario(w stdhttp.ResponseWriter, r *stdhttp.Request) {
	if r.Method != stdhttp.MethodPost {
		writeError(w, stdhttp.StatusMethodNotAllowed, "method not allowed")
		return
	}

	defer r.Body.Close()

	var req FinanceScenarioRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		if errors.Is(err, io.EOF) {
			writeError(w, stdhttp.StatusBadRequest, "empty request body")
			return
		}
		writeError(w, stdhttp.StatusBadRequest, "invalid json")
		return
	}

	input := mapCalculateRequestToInput(req.Input)

	delta := rating.ScenarioDelta{
		ExtraVolume:      req.Delta.ExtraVolume,
		ExtraDeals:       req.Delta.ExtraDeals,
		ExtraBankShare:   req.Delta.ExtraBankShare,
		ExtraSubmitted:   req.Delta.ExtraSubmitted,
		ExtraApproved:    req.Delta.ExtraApproved,
		ConversionTarget: req.Delta.ConversionTarget,
	}

	scenarioResult, err := h.calculatorService.CalculateScenario(input, delta)
	if err != nil {
		writeError(w, stdhttp.StatusBadRequest, err.Error())
		return
	}

	rules := mapBonusRulesDTOToDomain(req.Rules)

	financeResult, err := h.financeService.CalculateScenario(
		domainfinance.Input{
			Level: scenarioResult.Current.Level,
			Score: scenarioResult.Current.Score,
			Rules: rules,
		},
		domainfinance.Input{
			Level: scenarioResult.Scenario.Level,
			Score: scenarioResult.Scenario.Score,
			Rules: rules,
		},
	)
	if err != nil {
		writeError(w, stdhttp.StatusBadRequest, err.Error())
		return
	}

	writeJSON(w, stdhttp.StatusOK, FinanceScenarioResponse{
		Current:    mapFinanceResultToResponse(financeResult.Current),
		Scenario:   mapFinanceResultToResponse(financeResult.Scenario),
		BonusDelta: financeResult.BonusDelta,
	})
}

func mapCalculateRequestToInput(req CalculateRequest) rating.Input {
	return rating.Input{
		FactVolume:        req.FactVolume,
		PlanVolume:        req.PlanVolume,
		FactDeals:         req.FactDeals,
		PlanDeals:         req.PlanDeals,
		FactBankShare:     req.FactBankShare,
		TargetBankShare:   req.TargetBankShare,
		SubmittedApps:     req.SubmittedApps,
		ApprovedApps:      req.ApprovedApps,
		ConversionPercent: req.ConversionPercent,
		MaxIndex:          req.MaxIndex,
		Weights: rating.Weights{
			Volume:     req.Weights.Volume,
			Deals:      req.Weights.Deals,
			BankShare:  req.Weights.BankShare,
			Conversion: req.Weights.Conversion,
		},
		Thresholds: rating.Thresholds{
			GoldFrom:  req.Thresholds.GoldFrom,
			BlackFrom: req.Thresholds.BlackFrom,
		},
	}
}

func mapResultToResponse(result rating.Result) CalculateResponse {
	return CalculateResponse{
		Score: result.Score,
		Level: result.Level,
		Breakdown: BreakdownResponse{
			VolumeIndex:        result.Breakdown.VolumeIndex,
			DealsIndex:         result.Breakdown.DealsIndex,
			BankShareIndex:     result.Breakdown.BankShareIndex,
			ConversionIndex:    result.Breakdown.ConversionIndex,
			VolumeContribution: result.Breakdown.VolumeContribution,
			DealsContribution:  result.Breakdown.DealsContribution,
			ShareContribution:  result.Breakdown.ShareContribution,
			ConvContribution:   result.Breakdown.ConvContribution,
		},
		NextLevel: NextLevelResponse{
			CurrentLevel: result.NextLevel.CurrentLevel,
			NextLevel:    result.NextLevel.NextLevel,
			MissingScore: result.NextLevel.MissingScore,
		},
	}
}

func mapBonusRulesDTOToDomain(r BonusRulesDTO) domainfinance.BonusRules {
	return domainfinance.BonusRules{
		Silver: r.Silver,
		Gold:   r.Gold,
		Black:  r.Black,
	}
}

func mapFinanceResultToResponse(result domainfinance.Result) FinanceResponse {
	return FinanceResponse{
		Level: result.Level,
		Score: result.Score,
		Bonus: result.Bonus,
	}
}
