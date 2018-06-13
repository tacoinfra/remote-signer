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
FLASK_APP=signer flask run
```
