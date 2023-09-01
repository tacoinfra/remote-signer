all: check zipfile

DC=docker-compose

rebuild:
	${DC} stop
	docker build -t remote-signer:latest .
	${DC} up --build --force-recreate --no-deps -d

.PHONY: test
test: up
	${DC} exec signer bash -c ' \
	python3 -m unittest test/test_remote_signer.py \
	'

lint: up
	${DC} exec signer bash -c ' \
	git config --global --add safe.directory "$${PWD}"; \
	pre-commit run --all-files \
	'

# see pyproject.toml for which
# files are actually checked:
# eg: pip install mypy django-stubs
mypy: up
	${DC} exec signer bash -c ' \
	mypy --check-untyped-defs src \
	'

coverage: up
	${DC} exec signer bash -c ' \
	pip3 install pytest-cov; \
	pytest --cov=src . \
	'

down:
	${DC} stop

up: 
	@${DC} up -d

ps:
	${DC} ps

bash: up
	${DC} exec signer bash

config: up
	${DC} exec signer bash -c ' \
	cp /keys.json /code/keys.json \
	'

int integration: config
	${DC} exec signer bash -c ' \
	pytest test/test_integration.py --cov=src\
	'

run: config
	@${DC} exec signer bash -c ' \
	echo ♉ dyanamo db: $$DYNAMO_DB_URL; \
	FLASK_APP="signer" /usr/local/bin/flask  run --reload --host=0.0.0.0 \
	'

# GE: older targets for reference

docker:
	docker build -t remote-signer .

zipfile:
	zip remote-signer.zip requirements.txt *.py src/*.py src/*.sh

check:
	python3 -m unittest test/test_remote_signer.py
