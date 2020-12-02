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
        customerEmail = customer['email']

        msg = '<h2>{},</h2><p>Merci pour votre(vos) commande(s) !</p>'.format(customer['name'])
        msg += '<p>Ce message vous confirme que le(la) ou les exposant(e)(s) ont été informé(e)(s) de votre ou de vos commande(s) et vous recontactera(ront) rapidement.</p>'

        msg += '<h2>Vos informations</h2><ul><li>Nom : {}</li><li>E-mail : {}</li><li>Téléphone : {}</li></ul>'.format(customer['name'], customerEmail, customer['phone'])

        cart = json.loads(params['cart'], encoding='utf-8')
        options = params['options']
        for exhibitorId in cart:
            exhibitor = cart[exhibitorId]
            msg += '<h2>{}</h2>'.format(exhibitor['name'])
            msg += '<table><tr><th>Produit</th><th>Prix unitaire</th><th>Quantité</th><th>Prix</th></tr>'
            total = 0
            for item in exhibitor['items']:
                unitprice = float(item['product']['price'])
                quantity = int(item['quantity'])
                msg += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{} €</td></tr>'.format(item['product']['name'], unitprice, quantity, unitprice * quantity)
                total += (unitprice * quantity)
            
            orderMean = options[exhibitorId]['payment']['mean']
            msg += '<tr><td></td><td></td><td></td><td>{} €</td></tr></table>'.format(total)
            msg += '<ul>'
            msg += '<li>Paiement : {}</li>'.format(orderMean)
            
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
            msg += '<li>Livraison : {}{}</li>'.format(deliveryMean, deliveryDetail)
            msg += '</ul>'

        msg = EmailMessage()
        msg['Subject'] = '[Christmas Market] Order #001'
        msg['From'] = 'Christmas Market <info@christmas-market.be>'
        msg['To'] = '{}, info@christmas-market.be'.format(customerEmail)
        msg['Cci'] = 'seb478@gmail.com, guillaumedemoff@gmail.com'
        msg.set_content(html2text.html2text(body))
        msg.add_alternative(msg, subtype='html')

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
