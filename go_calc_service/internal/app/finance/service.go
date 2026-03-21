package finance

import (
	domainfinance "hackathon/go_service/internal/domain/finance"
)

type Service struct {
	calculator *domainfinance.Calculator
}

func NewService(calculator *domainfinance.Calculator) *Service {
	return &Service{
		calculator: calculator,
	}
}

func (s *Service) Calculate(input domainfinance.Input) (domainfinance.Result, error) {
	return s.calculator.Calculate(input)
}

func (s *Service) CalculateScenario(current domainfinance.Input, scenario domainfinance.Input) (domainfinance.ScenarioResult, error) {
	return s.calculator.CalculateScenario(current, scenario)
}
