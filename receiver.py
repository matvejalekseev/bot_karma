from flask import Flask, request, Response
from conf import HOST_RECEIVER

app = Flask(__name__)

@app.route('/sign', methods=['POST'])
def sign():
    resp = Response(request.data.decode('utf-8'))
    resp.headers = request.headers
    return resp


@app.route('/check_length', methods=['POST'])
def check_length():
    resp = Response(request.data.decode('utf-8'))
    resp.headers.clear()
    for header in request.headers:
        if header[0] == 'Content-Length':
            resp.headers.add(header[0], int(header[1])-200)
        else:
            resp.headers.add(header[0], header[1])
    print(resp.data.decode('utf-8'))
    return resp


if __name__ == '__main__':
    app.run(port=5000, host=HOST_RECEIVER)