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
ACTIVATE_VENV := . .venv/bin/activate
DOCKER_COMPOSE=/usr/bin/docker-compose


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
	rm -rf .venv


env:  ## Enter python virtualenv
	$(ACTIVATE_VENV); $$SHELL


setup: ## Setup virtualenv development environment. Needs to run before attempting to use a virtualenv.
	sudo apt-get install -y python3-virtualenv docker.io docker-compose libpq-dev  # needed to build psycopg2
	virtualenv .venv -p /usr/bin/python3
	$(ACTIVATE_VENV); pip3 install -r requirements.txt


migration:  ## create migration scripts if models are changed.
	$(ACTIVATE_VENV); python manage.py makemigrations


database: ## Start postgres db with docker and run migrations
	$(DOCKER_COMPOSE) up -d postgres
	sleep 5
	$(ACTIVATE_VENV); python manage.py migrate


test:  ## Run test suite
	$(ACTIVATE_VENV);  pytest -svv --disable-warnings


run-server: ## Run backend & frontend server
	$(ACTIVATE_VENV);  python manage.py runserver 0.0.0.0:8000


createsuperuser:
	$(ACTIVATE_VENV);  bash -c "DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_PASSWORD=123 DJANGO_SUPERUSER_EMAIL=a@1.com python manage.py createsuperuser --no-input"


static-files:
	$(ACTIVATE_VENV); python manage.py collectstatic 
