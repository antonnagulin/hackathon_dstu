package main

import (
	"log"
	stdhttp "net/http"
	"time"

	"hackathon/go_service/internal/app/calculator"
	appfinance "hackathon/go_service/internal/app/finance"
	domainfinance "hackathon/go_service/internal/domain/finance"
	"hackathon/go_service/internal/domain/rating"
	transporthttp "hackathon/go_service/internal/transport/http"
)

func main() {
	ratingCalculator := rating.NewCalculator()
	calculatorService := calculator.NewService(ratingCalculator)

	financeCalculator := domainfinance.NewCalculator()
	financeService := appfinance.NewService(financeCalculator)

	handler := transporthttp.NewHandler(calculatorService, financeService)
	router := transporthttp.NewRouter(handler)

	server := &stdhttp.Server{
		Addr:              ":8080",
		Handler:           router,
		ReadHeaderTimeout: 5 * time.Second,
	}

	log.Println("calc-service started on :8080")

	if err := server.ListenAndServe(); err != nil && err != stdhttp.ErrServerClosed {
		log.Fatalf("server failed: %v", err)
	}
}
