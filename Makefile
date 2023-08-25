all: check zipfile

DC=docker-compose

# see pyproject.toml for which
# files are actually checked:
# pip install mypy django-stubs; \

mypy:
	${DC} up -d
	${DC} exec signer bash -c ' \
	mypy --check-untyped-defs src \
	'

lint:
	${DC} exec signer bash -c ' \
	git config --global --add safe.directory "$${PWD}"; \
	pre-commit run --all-files \
	'
bash:
	${DC} exec signer bash

down:
	${DC} stop

up:
	${DC} up -d

ps:
	${DC} ps

rebuild:
	${DC} stop
	docker build -t remote-signer:latest .
	${DC} up --build --force-recreate --no-deps -d

docker:
	docker build -t remote-signer .

zipfile:
	zip remote-signer.zip requirements.txt *.py src/*.py src/*.sh

check:
	python3 -m unittest test/test_remote_signer.py
