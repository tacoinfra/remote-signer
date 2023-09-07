all: check zipfile

DC=docker-compose

build: 
	${DC} up --build --force-recreate -d signer 
	${DC} up -d

rebuild: zipfile
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
		set -x; \
		source /home/ec2-user/env/bin/activate; \
		if [ -z "$(TEST)" ]; then \
			pytest; \
		else \
			pytest -k $(TEST); \
		fi \
	"

config: up
	${DC} exec signer bash -c ' \
		cp /home/ec2-user/keys.json /code/keys.json \
	'

coverage: up
	${DC} exec signer bash -c ' \
		source /home/ec2-user/env/bin/activate; \
		pytest --cov=src . \
	'

int integration: config
	${DC} exec signer bash -c ' \
		source /home/ec2-user/env/bin/activate; \
		pytest test/test_integration.py \
	'

lint: up
	${DC} exec signer bash -c ' \
		source /home/ec2-user/env/bin/activate; \
		git config --global --add safe.directory "$${PWD}"; \
		pre-commit run --all-files \
	'

# see pyproject.toml for which
# files are actually checked:
# eg: pip install mypy django-stubs
mypy: up
	${DC} exec signer bash -c ' \
		source /home/ec2-user/env/bin/activate; \
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

# runs off the unpacked zipfile, not a live reload
run: 
	@${DC} exec signer bash -c ' \
		/home/ec2-user/src/start-remote-signer.sh; \
	'

# live reload
debug: config
	@${DC} exec signer bash -c ' \
		source /home/ec2-user/env/bin/activate; \
		cd /code; \
		echo ♉ DYNAMO_DB_URL: $$DYNAMO_DB_URL; \
		echo ♉ DDB_TABLE: $$DDB_TABLE; \
		FLASK_APP="signer" /home/ec2-user/env/bin/flask  run --reload --host=0.0.0.0 \
	'

# GE: older targets for reference

docker:
	docker build -t remote-signer .

zipfile:
	zip remote-signer.zip requirements.txt *.py src/**/*.py src/*.sh

check:
	python3 -m unittest test/test_remote_signer.py
