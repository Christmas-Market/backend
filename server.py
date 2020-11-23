from flask import Flask, jsonify, request, status
from flask_cors import CORS

import json
import os
import requests

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def home():
    return jsonify({'ok': True})

@app.route('/placeorder', methods=['POST'])
def placeorder():
    print('>>> Placing a new order...')
    url = f"https://www.google.com/recaptcha/api/siteverify?secret={os.environ['RECAPTCHA_SECRET_KEY']}&response={request.json['token']}"
    resp = requests.post(url)
    if resp.status_code == 200:
        result = resp.json()
        if result['success'] and result['score'] > 0.5:
            print('>>> reCaptcha detects a safe interaction')
            print(result['score'])
            print('>>> Order placed')
            cart = json.loads(request.json['cart'].encode('utf-8'))
            print(cart)
            return jsonify({'ok': True})
    return jsonify({'ok': False}), status.HTTP_400_BAD_REQUEST

if __name__ == '__main__':
    app.run()
