FROM golang:1.22-alpine AS builder

WORKDIR /build

COPY go_calc_service/go.mod ./go_calc_service/
WORKDIR /build/go_calc_service

RUN go mod download

COPY go_calc_service/ .

RUN go build -o /calc-service ./cmd/calc_service

# --- runtime ---
FROM alpine:3.20

WORKDIR /app

COPY --from=builder /calc-service /app/calc-service

EXPOSE 8080

CMD ["/app/calc-service"]