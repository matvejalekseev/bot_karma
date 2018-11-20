from flask import Flask, request, Response

app = Flask(__name__)

@app.route('/sign', methods=['POST'])
def json_example():
    resp = Response(request.data.decode('utf-8'))
    resp.headers = request.headers
    return resp

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="195.201.136.255")