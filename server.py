from flask import Flask, jsonify, request, abort
from flask_cors import CORS

import os
import requests
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText

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
            
            cart = ''
            if 'cart' in request.json:
                cart = request.json['cart']
            paymentMeans = ''
            if 'payment' in request.json:
                paymentMeans = request.json['payment']
            deliveryMeans = ''
            if 'delivery' in request.json:
                deliveryMeans = request.json['delivery']

            try:
                msg = EmailMessage()
                msg['Subject'] = '[Christmas Market] Order #001'
                msg['From'] = 'Christmas Market <info@christmas-market.be>'
                msg['To'] = 'seb478@gmail.com, guillaumedemoff@gmail.com'
                msg.set_content(
                    'Cart: ' + cart +
                    'Payment means: ' + str(paymentMeans) +
                    'Delivery means: ' + str(deliveryMeans)
                )
                msg.add_alternative(
                    '<b>Cart:</b> ' + cart +
                    '<br><b>Payment means</b>: ' + str(paymentMeans) +
                    '<br><b>Delivery means</b>: ' + str(deliveryMeans)
                , subtype='html')

                server = smtplib.SMTP(os.environ['SMTP_SERVER'], 587)
                server.ehlo()
                server.starttls()
                server.login(os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])
                server.send_message(msg)
            except Exception as e:
                print(e)
                return abort(400)
            finally:
                server.quit()

            return jsonify({'ok': True})
    return abort(400)

if __name__ == '__main__':
    app.run()
