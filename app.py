from flask import Flask, request, jsonify
from flask_cors import CORS  # Нужно установить: pip install flask-cors
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)
CORS(app) # Это разрешит вашему index.html обращаться к API

PUBLIC_ID = 'pk_817b520f768b27ddd343920b55503'
API_SECRET = os.getenv('TTP_API_SECRET', 'ВАШ_ТЕСТОВЫЙ_СЕКРЕТ_ИЗ_ЛК')

@app.route('/charge', methods=['POST'])
def charge():
    data = request.json
    payload = {
        'Amount': data.get('amount'),
        'Currency': data.get('currency'),
        'Name': data.get('name'),
        'CardCryptogramPacket': data.get('cryptogram'),
        'IpAddress': request.remote_addr,
    }

    # Важно: используем правильный URL API TipTopPay
    response = requests.post(
        'https://api.tiptoppay.kz/payments/cards/auth',
        json=payload,
        auth=HTTPBasicAuth(PUBLIC_ID, API_SECRET)
    )
    
    return jsonify(response.json())

# Эндпоинт для 3DS (сюда вернется юзер)
@app.route('/postback-3ds', methods=['POST'])
def postback_3ds():
    transaction_id = request.form.get('MD')
    pa_res = request.form.get('PaRes')

    payload = {'TransactionId': transaction_id, 'PaRes': pa_res}

    response = requests.post(
        'https://api.tiptoppay.kz/payments/cards/post3ds',
        json=payload,
        auth=HTTPBasicAuth(PUBLIC_ID, API_SECRET)
    )
    
    result = response.json()
    if result.get('Success'):
        return "<h1>Успех! Оплата подтверждена.</h1>"
    else:
        return f"<h1>Ошибка: {result.get('Message')}</h1>"

if __name__ == '__main__':
    # Запуск на порту 5000
    app.run(host='127.0.0.1', port=5000, debug=True)