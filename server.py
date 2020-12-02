from flask import Flask, jsonify, request, abort
from flask_cors import CORS

import html2text
import json
import os
import requests
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText

payment = {
    "cash": "Cash",
    "online": "En ligne",
    "banktransfer": "Virement bancaire",
    "bancontact": "Bancontact"
}

delivery = {
    "delivery": "Livraison à domicile",
    "pickup": "Point de collecte",
    "postmail": "Livraison postale",
    "store": "Boutique"
}

app = Flask(__name__)
CORS(app)

def send_email(to, body):
    try:
        msg = EmailMessage()
        msg['Subject'] = '[Christmas Market] Order #001'
        msg['From'] = 'Christmas Market <info@christmas-market.be>'
        msg['To'] = to
        msg.set_content(html2text.html2text(body))
        msg.add_alternative(body, subtype='html')

        server = smtplib.SMTP(os.environ['SMTP_SERVER'], 587)
        server.ehlo()
        server.starttls()
        server.login(os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])
        server.send_message(msg)
    except Exception as e:
        raise e
    finally:
        server.quit()

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
        customerName = customer['name']
        customerEmail = customer['email']

        body = '<h2>{},</h2><p>Merci pour votre(vos) commande(s) !</p>'.format(customerName)
        body += '<p>Ce message vous confirme que le(la) ou les exposant(e)(s) ont été informé(e)(s) de votre ou de vos commande(s) et vous recontactera(ront) rapidement.</p>'

        body += '<h2>Vos informations</h2><ul><li>Nom : {}</li><li>E-mail : {}</li><li>Téléphone : {}</li></ul>'.format(customerName, customerEmail, customer['phone'])

        cart = json.loads(params['cart'], encoding='utf-8')
        options = params['options']
        for exhibitorId in cart:
            exhibitor = cart[exhibitorId]
            body += '<h2>{}</h2>'.format(exhibitor['name'])
            body += '<table><tr><th>Produit</th><th>Prix unitaire</th><th>Quantité</th><th>Prix</th></tr>'
            total = 0
            for item in exhibitor['items']:
                unitprice = float(item['product']['price'])
                quantity = int(item['quantity'])
                body += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{} €</td></tr>'.format(item['product']['name'], unitprice, quantity, unitprice * quantity)
                total += (unitprice * quantity)
            
            orderMean = options[exhibitorId]['payment']['mean']
            body += '<tr><td></td><td></td><td></td><td>{} €</td></tr></table>'.format(total)
            body += '<ul>'
            body += '<li>Paiement : {}</li>'.format(payment[orderMean])
            
            deliveryMean = options[exhibitorId]['delivery']['mean']
            deliveryDetail = ''
            if deliveryMean in ['delivery', 'pickup', 'postmail', 'store']:
                deliveryDetail = ' ('
                if deliveryMean == 'delivery' or deliveryMean == 'postmail':
                    deliveryDetail += options[exhibitorId]['delivery']['address']
                elif deliveryMean == 'store':
                    deliveryDetail += options[exhibitorId]['delivery']['selectedStore']
                elif deliveryMean == 'pickup':
                    deliveryDetail += options[exhibitorId]['delivery']['pickupLocation']
                deliveryDetail += ')'
            body += '<li>Livraison : {}{}</li>'.format(delivery[deliveryMean], deliveryDetail)
            body += '</ul>'

        send_email('{} <{}>'.format(customerName, customerEmail), body)
        send_email('seb478@gmail.com, guillaumedemoff@gmail.com', body)
    except Exception as e:
        print(e)
        return abort(400)
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run()
