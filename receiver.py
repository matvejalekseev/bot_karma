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
    return resp


@app.route('/check_wsa', methods=['POST'])
def check_wsa():
    body = '''\
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
   <SOAP-ENV:Header>
      <Action wsu:Id="id-3e0bee45-ea5b-4f8d-959a-9bfa63dcea16" xmlns="http://www.w3.org/2005/08/addressing">sendResponse</Action>
      <MessageID wsu:Id="id-db0846a5-9e4d-4849-926e-5ce3d1a8057d" xmlns="http://www.w3.org/2005/08/addressing">476ad8ba-44e0-4a0b-a4bd-ee0d3d17413b</MessageID>
      <egisz:transportHeader xmlns:egisz="http://egisz.rosminzdrav.ru">
         <egisz:authInfo>
            <egisz:clientEntityId>92a2a443-6d8c-bfc7-3eff-65cdc2a6622d</egisz:clientEntityId>
         </egisz:authInfo>
      </egisz:transportHeader>
   </SOAP-ENV:Header>
   <SOAP-ENV:Body wsu:Id="body">
      <sendResponseResponse xmlns="http://emu.callback.mis.service.nr.eu.rt.ru/">
         <status xmlns="">0</status>
      </sendResponseResponse>
   </SOAP-ENV:Body>
</SOAP-ENV:Envelope>\
    '''
    resp = Response(body)
    return resp


if __name__ == '__main__':
    app.run(port=5000, host=HOST_RECEIVER)