# Comandos del proyecto. `make help` lista todo.
SHELL := /bin/bash

ifeq (,$(wildcard .env))
$(error Falta .env: corré `cp .env.example .env`)
endif
include .env
export

API := apps/api

.PHONY: help install infra storage migrate migrate-test dev api web test lint reset docker-api

help: ## Lista los comandos
	@grep -hE '^[a-z-]+:.*## ' $(firstword $(MAKEFILE_LIST)) | awk -F':.*## ' '{printf "  make %-13s %s\n", $$1, $$2}'

install: ## Instala dependencias de Python y JS
	cd $(API) && uv sync
	npm install

infra: ## Levanta Postgres y el almacenamiento S3 y espera a que estén sanos
	docker compose up -d --wait

storage: infra ## Crea el bucket de imágenes si no existe
	cd $(API) && uv run python -m app.cli ensure-bucket

migrate: infra ## Aplica las migraciones a la base de desarrollo
	cd $(API) && uv run alembic upgrade head

migrate-test: infra ## Aplica las migraciones a la base de tests
	cd $(API) && uv run alembic -x database_url=$(TEST_DATABASE_URL) upgrade head

dev: install migrate storage ## Levanta todo: infraestructura, API y web (Ctrl+C corta)
	@echo "Web: http://localhost:3000  ·  en la red: http://$$(hostname -I | awk '{print $$1}'):3000"
	@trap 'kill 0' INT TERM EXIT; \
	$(MAKE) --no-print-directory api & \
	$(MAKE) --no-print-directory web & \
	wait

api: ## Solo la API, con recarga automática
	cd $(API) && uv run uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000

web: ## Solo la web, con recarga automática
	npm run dev -w @catalog/web

test: migrate-test ## Corre todos los tests
	cd $(API) && uv run pytest

lint: ## Revisa estilo y tipos de la API y la web
	cd $(API) && uv run ruff check . && uv run ruff format --check . && uv run mypy app tests alembic
	npm run lint -w @catalog/web
	npm run typecheck -w @catalog/web

docker-api: ## Construye la imagen de producción de la API
	docker build -f $(API)/Dockerfile --target prod -t catalog-api .

reset: ## Borra los datos de Postgres y del almacenamiento (arranca de cero)
	docker compose down -v
