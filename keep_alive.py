# keep_alive.py - Servidor web para manter o bot online
from flask import Flask
from threading import Thread
import time

app = Flask('')

@app.route('/')
def home():
    """Página inicial do servidor web"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Bot de Registro Discord</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 20px;
            }
            .status {
                font-size: 1.5em;
                color: #4CAF50;
                font-weight: bold;
            }
            .info {
                text-align: left;
                margin-top: 30px;
                padding: 20px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Bot de Registro Discord</h1>
            <div class="status">✅ Online e funcionando!</div>
            <p>Servidor web ativo para manter o bot 24/7</p>
            
            <div class="info">
                <h3>📊 Informações:</h3>
                <p>• Sistema de registro com aprovação</p>
                <p>• Painéis automáticos</p>
                <p>• Comandos slash completos</p>
                <p>• Hospedado no Railway</p>
                <p>• Uptime: 24/7</p>
            </div>
            
            <p style="margin-top: 30px; font-size: 0.9em; opacity: 0.8;">
                Esta página mantém o bot online mesmo sem interação
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Endpoint de saúde para monitoramento"""
    return {"status": "healthy", "timestamp": time.time()}

@app.route('/ping')
def ping():
    """Endpoint simples para testar"""
    return "pong"

def run():
    """Inicia o servidor Flask"""
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Inicia o servidor web em uma thread separada"""
    t = Thread(target=run)
    t.daemon = True  # Permite que o programa principal termine
    t.start()
    print("✅ Servidor web iniciado na porta 8080")