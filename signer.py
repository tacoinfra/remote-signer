from flask import Flask, request, Response
from src.remote_signer import RemoteSigner

app = Flask(__name__)


@app.route('/', methods=['POST'])
def sign():
    response = None
    try:
        data = request.get_json(force=True)
        rs = RemoteSigner(data)
        response = Response(rs.sign(), status=200)
    except Exception as e:
        response = Response(str(e), status=500)
    return response


@app.route('/', methods=['GET'])
def get_public_key():
    response = None
    try:
        rs = RemoteSigner()
        response = Response(rs.get_signer_pubkey(), status=200)
    except Exception as e:
        response = Response(str(e), status=500)
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
