SHELL := /usr/bin/env bash

backend-prod:
	docker compose -f docker-compose.prod.yml up -d --build

backend-prod-down:
	docker compose -f docker-compose.prod.yml down

backend-dev:
	docker compose up -d --build

backend-dev-down:
	docker compose down

run-project-prod:
	$(MAKE) backend-prod

upgrade:
	$(MAKE) run-project-prod

down-project-prod:
	$(MAKE) backend-prod-down

run-project-dev:
	$(MAKE) backend-dev

down-project-dev:
	$(MAKE) backend-dev-down

.PHONY: clean
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete