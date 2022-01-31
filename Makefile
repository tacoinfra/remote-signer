


all: check zipfile

docker:
	docker build -t remote-signer .

zipfile:
	zip remote-signer.zip requirements.txt *.py src/*.py src/*.sh

check:
	python3 -m unittest test/test_remote_signer.py
