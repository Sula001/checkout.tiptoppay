import os
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from requests.auth import HTTPBasicAuth

# 1. Ищем и загружаем файл
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)
    print(f"--- Файл .env найден: {env_file} ---")
    
    # ОТЛАДКА: Проверим, что реально внутри файла (первые 10 символов каждой строки)
    with open(env_file, 'r', encoding='utf-8') as f:
        print("--- Содержимое файла (для проверки имен): ---")
        for line in f:
            print(f"Строка: {line.strip().split('=')[0]}...") 
else:
    print("--- КРИТИЧЕСКАЯ ОШИБКА: Файл .env не найден! ---")

app = Flask(__name__)
CORS(app)

# 2. Получаем ключи
PUBLIC_ID = os.getenv('TTP_PUBLIC_ID')
API_SECRET = os.getenv('TTP_API_SECRET')

app = Flask(__name__)
CORS(app)

PUBLIC_ID = os.getenv('TTP_PUBLIC_ID')
API_SECRET = os.getenv('TTP_API_SECRET')

@app.route('/charge', methods=['POST'])
def charge():
    data = request.json
    payload = {
        'Amount': data.get('amount'),
        'Currency': data.get('currency', 'KZT'),
        'Name': data.get('name'),
        'Email': data.get('email'),
        'CardCryptogramPacket': data.get('cryptogram'),
        'IpAddress': request.remote_addr,
    }

    print(f"--- Запрос на оплату ({data.get('amount')} KZT) ---")

    try:
        response = requests.post(
            'https://api.tiptoppay.kz/payments/cards/auth',
            json=payload,
            auth=HTTPBasicAuth(PUBLIC_ID, API_SECRET),
            timeout=30
        )

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            print(f"Ошибка API: {response.status_code} - {response.text}")
            return jsonify({
                "Success": False,
                "Message": "Ошибка авторизации платежа",
                "Details": response.text
            }), response.status_code

    except Exception as e:
        print(f"Ошибка соединения: {e}")
        return jsonify({"Success": False, "Message": "Сервер недоступен"}), 500

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
    
    try:
        result = response.json()
        is_success = result.get('Success', False)
        message = result.get('Message', 'Операция завершена')
    except:
        is_success = False
        message = "Ошибка ответа банка"

    title = "Оплата успешна" if is_success else "Ошибка оплаты"
    color = "#10b981" if is_success else "#ef4444"
    icon = "✅" if is_success else "❌"

    # URL для кнопки возврата (поправь порт, если он отличается)
    return_url = "http://127.0.0.1:5500/frontend/index.html"

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background: #0f172a; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: #1e293b; padding: 40px; border-radius: 16px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3); width: 320px; }}
            .icon {{ font-size: 50px; color: {color}; margin-bottom: 20px; }}
            h2 {{ margin: 0 0 10px 0; }}
            p {{ color: #94a3b8; margin-bottom: 25px; font-size: 14px; }}
            .btn {{ 
                background: #3b82f6; color: white; text-decoration: none; 
                padding: 12px 20px; border-radius: 8px; font-weight: bold;
                display: block; transition: 0.3s;
            }}
            .btn:hover {{ background: #2563eb; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">{icon}</div>
            <h2>{title}</h2>
            <p>{message}</p>
            <a href="{return_url}" class="btn">Повторить оплату</a>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Проверка загрузки ключей в консоли при запуске
    if not API_SECRET or not PUBLIC_ID:
        print("ОШИБКА: Ключи не найдены в .env! Проверьте файл.")
    else:
        print(f"Сервер запущен. PUBLIC_ID: {PUBLIC_ID[:6]}***")
        
    app.run(port=5000, debug=True)