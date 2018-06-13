from flask import Flask, request, Response
from src.remote_signer import RemoteSigner

app = Flask(__name__)


@app.route('/', methods=['POST'])
def sign():
    data = request.get_json(force=True)
    rs = RemoteSigner(data)
    return Response(rs.sign(), status=200)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
