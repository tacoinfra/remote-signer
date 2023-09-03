all: check zipfile

DC=docker-compose

rebuild:
	${DC} stop
	docker build --no-cache -t remote-signer:latest .
	docker build --no-cache -t remote-signer-dev:latest -f Dockerfile.dev . 
	${DC} up --build --force-recreate -d signer 
	${DC} up -d

# make test
# make test TEST=test_pybitcointools
.PHONY: test
test: up config
	@${DC} exec signer bash -c " \
		if [ -z "$(TEST)" ]; then \
			pytest; \
		else \
			pytest -k $(TEST); \
		fi \
	"

coverage: up
	${DC} exec signer bash -c ' \
	pytest --cov=src . \
	'

int integration: config
	${DC} exec signer bash -c ' \
	pytest test/test_integration.py \
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
