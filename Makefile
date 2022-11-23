.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
    match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
    if match:
        target, help = match.groups()
        print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

SHELL := /bin/bash
PYTHON3 := $(shell which python3)
PROJECT_ROOT=$(strip $(shell dirname $(realpath .)))
IMAGE := images_api:dev
DOCKER_COMPOSE=/usr/bin/docker-compose
DOCKER=docker
ACTIVATE_VENV := $(DOCKER) run --network host --rm -v `pwd`:/app -it $(IMAGE)
POSTGRES_READY := $(DOCKER_COMPOSE) exec postgres pg_isready -U postgres


help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)


clean-test: ## Remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache


clean-pyc: ## Remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +


clean-database: ## drop database.
	$(DOCKER_COMPOSE) down -v


clean: clean-pyc clean-test clean-database ## Remove all generated artifacts and drop DB
	$(DOCKER) rmi $(IMAGE)


setup: ## Setup development environment in docker. Needs to run before anything else.
	$(DOCKER) build -f Dockerfile-dev -t $(IMAGE) .


env:  ## Enter python virtualenv
	$(ACTIVATE_VENV) /bin/bash


migration:  ## create migration scripts if models are changed.
	$(ACTIVATE_VENV) python manage.py makemigrations


database: ## Start postgres db with docker and run migrations
	$(DOCKER_COMPOSE) up -d postgres
	until $(POSTGRES_READY); do sleep 3; done
	$(ACTIVATE_VENV) python manage.py migrate


test:  ## Run test suite
	$(ACTIVATE_VENV) pytest -svv --disable-warnings


run-server: ## Run backend & frontend server
	$(ACTIVATE_VENV) python manage.py runserver 0.0.0.0:8000


createsuperuser:
	$(ACTIVATE_VENV) bash -c "DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_PASSWORD=123 DJANGO_SUPERUSER_EMAIL=a@1.com python manage.py createsuperuser --no-input"


static-files:
	$(ACTIVATE_VENV) python manage.py collectstatic
