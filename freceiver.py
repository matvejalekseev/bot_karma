from flask import Flask, request, Response

app = Flask(__name__)

@app.before_request
def before_request():
    if True:
        print("HEADERS", request.headers)
        print("REQ_path", request.path)
        print("ARGS", request.args)
        print("DATA", request.data)
        print("FORM", request.form)


@app.route('/sign', methods=['POST'])
def json_example():
    resp = Response(request.data.decode('utf-8'))
    resp.headers = request.headers
    return resp

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="http://195.201.136.255")