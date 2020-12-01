from flask import Flask, jsonify, request, abort
from flask_cors import CORS

import html2text
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

    # Check the parameters
    params = request.json
    if 'token' not in params or 'cart' not in params or 'options' not in params or 'customer' not in params:
        return abort(400)

    # Check the captcha
    url = 'https://www.google.com/recaptcha/api/siteverify?secret={}&response={}'.format(os.environ['RECAPTCHA_SECRET_KEY'], params['token'])
    resp = requests.post(url)
    if resp.status_code != 200:
        return abort(400)

    result = resp.json()
    if 'success' not in result or 'score' not in result or not result['success'] or result['score'] <= 0.5:
        return abort(400)

    # ReCaptcha detected a safe interaction
    print('>>> reCaptcha detects a safe interaction', result['score'])
    try:
        customer = params['customer']
        header = '<h2>Nouvelle commande</h2><ul><li>Nom : {}</li><li>E-mail : {}</li><li>Téléphone : {}</li></ul>'.format(customer['name'], customer['email'], customer['phone'])
        body = header

        msg = EmailMessage()
        msg['Subject'] = '[Christmas Market] Order #001'
        msg['From'] = 'Christmas Market <info@christmas-market.be>'
        msg['To'] = 'seb478@gmail.com, guillaumedemoff@gmail.com'
        msg.set_content(html2text.html2text(body))
        msg.add_alternative(body, subtype='html')

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

if __name__ == '__main__':
    app.run()
