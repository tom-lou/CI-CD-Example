from flask import Flask, request, jsonify
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)

app.config['SECRET_KEY'] = 'ABC'

def generate_token():
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    payload = {'exp': expiration_time}
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token


@app.route('/get_token', methods=['GET'])
def get_token():
    token = generate_token()
    return jsonify({'token': token}), 200


@app.route('/multiply', methods=['POST'])
def multiply():
    token = request.headers.get('token')

    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

    if 'a' not in request.json or 'b' not in request.json:
        return jsonify({'error': 'Payload must contain keys "a" and "b"'}), 400

    a = request.json['a']
    b = request.json['b']

    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return jsonify({'error': 'Values of "a" and "b" must be numbers'}), 400

    result = a * b
    return jsonify({'result': result}), 200

if __name__ == '__main__':
    app.run(debug=True)
