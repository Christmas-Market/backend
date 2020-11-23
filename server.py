from flask import Flask, jsonify, request, abort
from flask_cors import CORS

import os
import requests
import smtplib, ssl

app = Flask(__name__)
CORS(app)

context = ssl.create_default_context()

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
            with open('order.json', 'w', encoding='utf-8') as file:
                file.write(request.json['cart'])
            with smtplib.SMTP_SSL(os.environ['SMTP_SERVER'], 587, context=context) as server:
                server.login(os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])
                server.sendmail('info@christmas-market.be', 'guillaumedemoff@gmail.com', 'Subject: Christmas-Market Order #001\n\nCart: ' + request.json['cart'].encode('utf-8'))
            return jsonify({'ok': True})
    return abort(400)

if __name__ == '__main__':
    app.run()
