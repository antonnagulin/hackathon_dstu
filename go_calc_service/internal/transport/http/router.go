package http

import stdhttp "net/http"

func NewRouter(handler *Handler) *stdhttp.ServeMux {
	mux := stdhttp.NewServeMux()

	mux.HandleFunc("/health", handler.Health)
	mux.HandleFunc("/api/v1/calculate", handler.Calculate)
	mux.HandleFunc("/api/v1/scenario", handler.Scenario)
	mux.HandleFunc("/api/v1/finance", handler.Finance)
	mux.HandleFunc("/api/v1/finance/scenario", handler.FinanceScenario)

	return mux
}
