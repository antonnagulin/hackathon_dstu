.PHONY: up down build logs web-logs go-logs shell migrate makemigrations createsuperuser restart restart-go restart-all

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

web-logs:
	docker compose logs -f web

go-logs:
	docker compose logs -f go-calc-service

shell:
	docker compose exec web python manage.py shell

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

createsuperuser:
	docker compose exec web python manage.py createsuperuser

restart:
	docker compose restart web

restart-go:
	docker compose restart go-calc-service

restart-all:
	docker compose down
	docker compose up -d --build