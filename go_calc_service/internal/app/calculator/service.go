package calculator

import "hackathon/go_service/internal/domain/rating"

type Service struct {
	calculator *rating.Calculator
}

func NewService(calculator *rating.Calculator) *Service {
	return &Service{
		calculator: calculator,
	}
}

func (s *Service) Calculate(input rating.Input) (rating.Result, error) {
	return s.calculator.Calculate(input)
}

func (s *Service) CalculateScenario(input rating.Input, delta rating.ScenarioDelta) (rating.ScenarioResult, error) {
	return s.calculator.CalculateScenario(input, delta)
}
