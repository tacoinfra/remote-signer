# remote_signer

This is a Python Flask app that receives block headers
and passes them on to the baker CloudHSM to be signed.

## installation

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## execution
```
export HSM_PASSWORD=blah
FLASK_APP=signer flask run
```

## running the tests
```
export HSM_PASSWORD=blah
python -m unittest test/test_remote_signer.py
```