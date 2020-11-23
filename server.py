from flask import Flask, jsonify, request, abort
from flask_cors import CORS

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
    url = 'https://www.google.com/recaptcha/api/siteverify?secret={}&response={}'.format(os.environ['RECAPTCHA_SECRET_KEY'], request.json['token'])
    resp = requests.post(url)
    if resp.status_code == 200:
        result = resp.json()
        if result['success'] and result['score'] > 0.5:
            print('>>> reCaptcha detects a safe interaction')
            print(result['score'])
            print('>>> Order placed')
            with open('order.json', 'w') as file:
                file.write(request.json['cart'])
            return jsonify({'ok': True})
    return abort(400)

if __name__ == '__main__':
    app.run()
