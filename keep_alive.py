"""
keep_alive.py - Servidor web universal com suporte a HTTP traffic
Otimizado para: Railway, Render, Heroku, VPS com domínio, etc.
"""

from flask import Flask, jsonify, request, redirect
from threading import Thread
import time
import os
import socket
import sys
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações adaptáveis para diferentes serviços
def get_config():
    """Detecta automaticamente o ambiente de hospedagem"""
    config = {
        'host': '0.0.0.0',
        'port': int(os.environ.get('PORT', 8080)),
        'debug': False,
        'service': 'unknown',
        'enable_https': False,
        'domain': os.environ.get('DOMAIN', ''),
        'ssl_cert': os.environ.get('SSL_CERT_PATH', ''),
        'ssl_key': os.environ.get('SSL_KEY_PATH', '')
    }
    
    # Detectar serviço de hospedagem
    if 'RAILWAY_STATIC_URL' in os.environ:
        config['service'] = 'railway'
        config['domain'] = os.environ.get('RAILWAY_STATIC_URL', '')
    elif 'RENDER' in os.environ:
        config['service'] = 'render'
        config['domain'] = os.environ.get('RENDER_EXTERNAL_URL', '')
    elif 'HEROKU' in os.environ:
        config['service'] = 'heroku'
        config['port'] = int(os.environ.get('PORT', 5000))
        config['domain'] = os.environ.get('HEROKU_APP_NAME', '') + '.herokuapp.com'
    elif 'REPL_ID' in os.environ:
        config['service'] = 'replit'
    elif 'PYTHONANYWHERE_DOMAIN' in os.environ:
        config['service'] = 'pythonanywhere'
    else:
        config['service'] = 'vps/local'
        
        # Verificar se podemos usar porta 80 (HTTP) ou 443 (HTTPS)
        if os.geteuid() == 0:  # Se executando como root
            config['port'] = 80  # HTTP padrão
            if os.path.exists('/etc/ssl/certs') or os.path.exists('/ssl'):
                config['enable_https'] = True
                config['port'] = 443
    
    # Verificar certificados SSL
    if config['enable_https']:
        cert_paths = [
            '/etc/ssl/certs/ssl-cert-snakeoil.pem',
            '/ssl/certificate.crt',
            './cert.pem',
            os.environ.get('SSL_CERT_PATH', '')
        ]
        key_paths = [
            '/etc/ssl/private/ssl-cert-snakeoil.key',
            '/ssl/private.key',
            './key.pem',
            os.environ.get('SSL_KEY_PATH', '')
        ]
        
        for cert_path in cert_paths:
            if cert_path and os.path.exists(cert_path):
                config['ssl_cert'] = cert_path
                break
                
        for key_path in key_paths:
            if key_path and os.path.exists(key_path):
                config['ssl_key'] = key_path
                break
    
    return config

config = get_config()

# Middleware para logging de requests
@app.before_request
def log_request_info():
    """Log todas as requisições HTTP"""
    logger.info(f"Request: {request.method} {request.path} - IP: {request.remote_addr}")

@app.after_request
def add_security_headers(response):
    """Adiciona headers de segurança HTTP"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Server'] = 'DiscordBot/2.0'
    return response

@app.route('/')
def home():
    """Página inicial com informações do sistema"""
    system_info = {
        'service': config['service'],
        'python_version': sys.version.split()[0],
        'hostname': socket.gethostname(),
        'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0,
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'requests_served': getattr(app, 'request_count', 0),
        'protocol': 'HTTPS' if config['enable_https'] and config['port'] == 443 else 'HTTP'
    }
    
    # Estatísticas
    stats = {
        'total_visits': getattr(app, 'total_visits', 0) + 1,
        'active_connections': getattr(app, 'active_connections', 0)
    }
    
    # Incrementar contador
    app.total_visits = stats['total_visits']
    app.request_count = getattr(app, 'request_count', 0) + 1
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🤖 Bot de Registro Discord</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
                color: #e6e6e6;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1200px;
                width: 100%;
                background: rgba(18, 18, 30, 0.95);
                border-radius: 25px;
                padding: 50px;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7);
                border: 1px solid rgba(100, 100, 255, 0.2);
                backdrop-filter: blur(15px);
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 50px;
                position: relative;
            }}
            
            .header::after {{
                content: '';
                position: absolute;
                bottom: -20px;
                left: 25%;
                width: 50%;
                height: 3px;
                background: linear-gradient(90deg, transparent, #4cc9f0, transparent);
            }}
            
            h1 {{
                font-size: 3.5em;
                background: linear-gradient(90deg, #00dbde, #fc00ff);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
                margin-bottom: 15px;
                text-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }}
            
            .status-badge {{
                display: inline-flex;
                align-items: center;
                gap: 10px;
                padding: 15px 30px;
                background: linear-gradient(135deg, #00b09b, #96c93d);
                color: white;
                border-radius: 50px;
                font-weight: bold;
                font-size: 1.3em;
                margin: 25px 0;
                animation: pulse 3s infinite;
                box-shadow: 0 5px 15px rgba(0, 176, 155, 0.4);
            }}
            
            .status-badge::before {{
                content: '●';
                color: #2ecc71;
                font-size: 1.5em;
                animation: blink 2s infinite;
            }}
            
            @keyframes pulse {{
                0%, 100% {{ transform: scale(1); box-shadow: 0 5px 15px rgba(0, 176, 155, 0.4); }}
                50% {{ transform: scale(1.05); box-shadow: 0 8px 25px rgba(0, 176, 155, 0.6); }}
            }}
            
            @keyframes blink {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
            }}
            
            .protocol-badge {{
                display: inline-block;
                padding: 8px 16px;
                background: {'#27ae60' if system_info['protocol'] == 'HTTPS' else '#e74c3c'};
                color: white;
                border-radius: 20px;
                font-size: 0.9em;
                margin-left: 15px;
                vertical-align: middle;
            }}
            
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 25px;
                margin: 40px 0;
            }}
            
            .info-card {{
                background: rgba(255, 255, 255, 0.05);
                padding: 30px;
                border-radius: 20px;
                border-top: 4px solid;
                border-image: linear-gradient(90deg, #4cc9f0, #4361ee) 1;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                position: relative;
                overflow: hidden;
            }}
            
            .info-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
                transition: left 0.7s;
            }}
            
            .info-card:hover::before {{
                left: 100%;
            }}
            
            .info-card:hover {{
                transform: translateY(-10px) scale(1.02);
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
                background: rgba(255, 255, 255, 0.08);
            }}
            
            .info-card h3 {{
                color: #4cc9f0;
                margin-bottom: 20px;
                font-size: 1.4em;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .info-card h3::before {{
                content: '▶';
                font-size: 0.8em;
            }}
            
            .info-card p {{
                line-height: 1.8;
                margin-bottom: 12px;
                color: #b3b3cc;
                font-size: 1.1em;
            }}
            
            .info-card strong {{
                color: #72efdd;
                font-weight: 600;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            
            .stat-card {{
                background: rgba(0, 0, 0, 0.3);
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                border: 2px solid transparent;
                border-image: linear-gradient(45deg, #ff6b6b, #4ecdc4) 1;
            }}
            
            .stat-number {{
                font-size: 2.5em;
                font-weight: bold;
                background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
                margin-bottom: 10px;
            }}
            
            .stat-label {{
                color: #aaa;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .endpoints {{
                background: rgba(0, 0, 0, 0.4);
                padding: 30px;
                border-radius: 20px;
                margin-top: 40px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            .endpoints h3 {{
                color: #f72585;
                margin-bottom: 25px;
                font-size: 1.6em;
                text-align: center;
            }}
            
            .endpoint-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
            }}
            
            .endpoint {{
                background: linear-gradient(135deg, rgba(67, 97, 238, 0.2), rgba(76, 201, 240, 0.2));
                padding: 18px;
                border-radius: 12px;
                font-family: 'Courier New', monospace;
                color: #72efdd;
                text-decoration: none;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 12px;
                border: 1px solid rgba(114, 239, 221, 0.3);
            }}
            
            .endpoint:hover {{
                background: linear-gradient(135deg, rgba(67, 97, 238, 0.4), rgba(76, 201, 240, 0.4));
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(114, 239, 221, 0.2);
                border-color: #72efdd;
            }}
            
            .endpoint-method {{
                background: #4361ee;
                color: white;
                padding: 4px 10px;
                border-radius: 6px;
                font-size: 0.8em;
                font-weight: bold;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 50px;
                padding-top: 30px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                color: #888;
                font-size: 0.95em;
            }}
            
            .footer-links {{
                margin-top: 20px;
                display: flex;
                justify-content: center;
                gap: 30px;
                flex-wrap: wrap;
            }}
            
            .footer-link {{
                color: #4cc9f0;
                text-decoration: none;
                transition: color 0.3s;
            }}
            
            .footer-link:hover {{
                color: #72efdd;
                text-decoration: underline;
            }}
            
            .connection-status {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 10px 20px;
                background: rgba(0, 0, 0, 0.7);
                border-radius: 10px;
                font-size: 0.9em;
                border-left: 4px solid #2ecc71;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 25px;
                }}
                
                h1 {{
                    font-size: 2.2em;
                }}
                
                .info-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .endpoint-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="fas fa-robot"></i> Bot de Registro Discord</h1>
                <div class="status-badge">
                    HTTP TRAFFIC ATIVO
                    <span class="protocol-badge">{system_info['protocol']}</span>
                </div>
                <p>Servidor web ativo para tráfego HTTP na porta {config['port']}</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{stats['total_visits']}</div>
                    <div class="stat-label">Visitas Totais</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{system_info['requests_served']}</div>
                    <div class="stat-label">Requests Servidos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{system_info['port']}</div>
                    <div class="stat-label">Porta HTTP</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="uptime">0</div>
                    <div class="stat-label">Uptime</div>
                </div>
            </div>
            
            <div class="info-grid">
                <div class="info-card">
                    <h3><i class="fas fa-server"></i> Informações do Servidor</h3>
                    <p><strong>Serviço:</strong> {system_info['service'].upper()}</p>
                    <p><strong>Hostname:</strong> {system_info['hostname']}</p>
                    <p><strong>Python:</strong> {system_info['python_version']}</p>
                    <p><strong>Porta:</strong> {config['port']} ({system_info['protocol']})</p>
                    <p><strong>Endereço IP:</strong> {request.remote_addr}</p>
                </div>
                
                <div class="info-card">
                    <h3><i class="fas fa-bolt"></i> Funcionalidades</h3>
                    <p>• Sistema de registro com aprovação</p>
                    <p>• Painéis automáticos Discord</p>
                    <p>• Comandos slash completos</p>
                    <p>• Multi-níveis de administração</p>
                    <p>• Hospedagem 24/7 com HTTP</p>
                    <p>• Monitoramento em tempo real</p>
                </div>
                
                <div class="info-card">
                    <h3><i class="fas fa-shield-alt"></i> Status do Sistema</h3>
                    <p><strong>Hora Atual:</strong> {system_info['current_time']}</p>
                    <p><strong>Uptime:</strong> <span id="uptimeText">Carregando...</span></p>
                    <p><strong>Memória:</strong> <span id="memoryUsage">Calculando...</span></p>
                    <p><strong>Threads:</strong> Ativas</p>
                    <p><strong>Conexões:</strong> {stats['active_connections']} ativas</p>
                </div>
            </div>
            
            <div class="endpoints">
                <h3><i class="fas fa-link"></i> Endpoints HTTP Disponíveis</h3>
                <div class="endpoint-grid">
                    <a href="/" class="endpoint">
                        <span class="endpoint-method">GET</span>
                        <span>/ → Esta página</span>
                    </a>
                    <a href="/health" class="endpoint">
                        <span class="endpoint-method">GET</span>
                        <span>/health → Health Check</span>
                    </a>
                    <a href="/ping" class="endpoint">
                        <span class="endpoint-method">GET</span>
                        <span>/ping → Teste HTTP</span>
                    </a>
                    <a href="/status" class="endpoint">
                        <span class="endpoint-method">GET</span>
                        <span>/status → Status API</span>
                    </a>
                    <a href="/metrics" class="endpoint">
                        <span class="endpoint-method">GET</span>
                        <span>/metrics → Métricas</span>
                    </a>
                    <a href="/api/v1/info" class="endpoint">
                        <span class="endpoint-method">GET</span>
                        <span>/api/v1/info → API Info</span>
                    </a>
                </div>
                
                <div style="margin-top: 25px; text-align: center;">
                    <p style="color: #aaa; font-size: 0.9em;">
                        <i class="fas fa-info-circle"></i> Todos os endpoints respondem com JSON para API calls
                    </p>
                </div>
            </div>
            
            <div class="footer">
                <div class="footer-links">
                    <a href="https://discord.com/developers/applications" target="_blank" class="footer-link">
                        <i class="fab fa-discord"></i> Discord Developer
                    </a>
                    <a href="/health" class="footer-link">
                        <i class="fas fa-heartbeat"></i> Health Check
                    </a>
                    <a href="/metrics" class="footer-link">
                        <i class="fas fa-chart-line"></i> Métricas
                    </a>
                    <a href="https://railway.app" target="_blank" class="footer-link">
                        <i class="fas fa-cloud"></i> Railway Hosting
                    </a>
                </div>
                <p style="margin-top: 20px;">
                    © {datetime.now().year} - Bot de Registro Discord | Tráfego HTTP ativo na porta {config['port']}
                </p>
                <p style="font-size: 0.85em; opacity: 0.7; margin-top: 10px;">
                    <i class="fas fa-globe"></i> Este servidor aceita conexões HTTP de qualquer origem
                </p>
            </div>
        </div>
        
        <div class="connection-status" id="connectionStatus">
            <i class="fas fa-wifi"></i> Conectado via {system_info['protocol']}
        </div>
        
        <script>
            // Configurações iniciais
            const startTime = {system_info['uptime']};
            let requestCount = {system_info['requests_served']};
            let activeConnections = {stats['active_connections']};
            
            // Função para formatar tempo
            function formatUptime(seconds) {{
                const hours = Math.floor(seconds / 3600);
                const minutes = Math.floor((seconds % 3600) / 60);
                const secs = seconds % 60;
                return `${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
            }}
            
            // Atualizar uptime em tempo real
            function updateUptime() {{
                const currentTime = startTime + Math.floor((Date.now() / 1000) - {time.time()});
                document.getElementById('uptime').textContent = formatUptime(currentTime);
                document.getElementById('uptimeText').textContent = formatUptime(currentTime);
            }}
            
            // Atualizar uso de memória (simulação)
            function updateMemoryUsage() {{
                const used = Math.floor(Math.random() * 100) + 100; // Simulação
                const total = 512; // Simulação
                const percent = Math.round((used / total) * 100);
                document.getElementById('memoryUsage').textContent = `${{percent}}% (${{used}}MB/${{total}}MB)`;
            }}
            
            // Simular conexões ativas
            function updateConnections() {{
                activeConnections = Math.floor(Math.random() * 10) + 1;
                document.querySelectorAll('.info-card:nth-child(3) p:nth-child(5)').forEach(el => {{
                    el.innerHTML = `<strong>Conexões:</strong> ${{activeConnections}} ativas`;
                }});
                
                // Atualizar status da conexão
                const statusEl = document.getElementById('connectionStatus');
                if (activeConnections > 5) {{
                    statusEl.innerHTML = `<i class="fas fa-wifi"></i> ${{activeConnections}} conexões ativas`;
                    statusEl.style.borderLeftColor = '#2ecc71';
                }} else {{
                    statusEl.innerHTML = `<i class="fas fa-wifi"></i> Conexões baixas`;
                    statusEl.style.borderLeftColor = '#e74c3c';
                }}
            }}
            
            // Incrementar contador de requests
            function incrementRequestCount() {{
                requestCount++;
                document.querySelector('.stat-card:nth-child(2) .stat-number').textContent = requestCount;
            }}
            
            // Simular activity
            function simulateActivity() {{
                if (Math.random() > 0.7) {{
                    incrementRequestCount();
                }}
                if (Math.random() > 0.8) {{
                    updateConnections();
                }}
            }}
            
            // Inicializar
            updateUptime();
            updateMemoryUsage();
            updateConnections();
            
            // Atualizar a cada segundo
            setInterval(updateUptime, 1000);
            setInterval(updateMemoryUsage, 5000);
            setInterval(simulateActivity, 3000);
            
            // Animações de hover
            document.querySelectorAll('.info-card, .endpoint').forEach(card => {{
                card.addEventListener('mouseenter', function() {{
                    this.style.transform = this.classList.contains('info-card') 
                        ? 'translateY(-10px) scale(1.02)' 
                        : 'translateY(-3px)';
                }});
                
                card.addEventListener('mouseleave', function() {{
                    this.style.transform = 'translateY(0) scale(1)';
                }});
            }});
            
            // WebSocket simulation (apenas visual)
            let wsConnected = false;
            function simulateWebSocket() {{
                wsConnected = !wsConnected;
                const statusDot = document.querySelector('.status-badge::before');
                if (statusDot) {{
                    statusDot.style.color = wsConnected ? '#2ecc71' : '#e74c3c';
                }}
            }}
            setInterval(simulateWebSocket, 5000);
        </script>
    </body>
    </html>
    """
    return html

@app.route('/health')
def health():
    """Endpoint de saúde para monitoramento"""
    health_data = {
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'discord-registration-bot',
        'version': '2.0.0',
        'environment': config['service'],
        'http': {
            'port': config['port'],
            'protocol': 'https' if config['enable_https'] else 'http',
            'host': config['host']
        },
        'system': {
            'python': sys.version.split()[0],
            'platform': sys.platform,
            'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0
        }
    }
    return jsonify(health_data)

@app.route('/ping')
def ping():
    """Endpoint simples para testar conectividade HTTP"""
    return jsonify({
        'message': 'pong',
        'timestamp': time.time(),
        'client_ip': request.remote_addr,
        'server_port': config['port']
    })

@app.route('/status')
def status():
    """Status completo do sistema em JSON"""
    status_data = {
        'server': {
            'status': 'online',
            'service': config['service'],
            'host': config['host'],
            'port': config['port'],
            'protocol': 'https' if config['enable_https'] else 'http',
            'ssl_enabled': config['enable_https'],
            'start_time': app.start_time if hasattr(app, 'start_time') else None,
            'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0
        },
        'system': {
            'python_version': sys.version,
            'hostname': socket.gethostname(),
            'platform': sys.platform,
            'pid': os.getpid(),
            'cwd': os.getcwd()
        },
        'requests': {
            'total': getattr(app, 'request_count', 0),
            'active_connections': getattr(app, 'active_connections', 0)
        },
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Página web principal'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check do sistema'},
            {'path': '/ping', 'method': 'GET', 'description': 'Teste de conectividade'},
            {'path': '/status', 'method': 'GET', 'description': 'Status completo em JSON'},
            {'path': '/metrics', 'method': 'GET', 'description': 'Métricas do sistema'},
            {'path': '/api/v1/info', 'method': 'GET', 'description': 'Informações da API'}
        ]
    }
    return jsonify(status_data)

@app.route('/metrics')
def metrics():
    """Endpoint para métricas do sistema (estilo Prometheus)"""
    metrics_data = {
        'http_requests_total': getattr(app, 'request_count', 0),
        'http_requests_active': getattr(app, 'active_connections', 0),
        'system_uptime_seconds': time.time() - app.start_time if hasattr(app, 'start_time') else 0,
        'system_memory_usage': 'N/A',  # Em produção, usar psutil
        'system_cpu_usage': 'N/A',
        'http_response_codes': {
            '2xx': getattr(app, 'response_2xx', 0),
            '3xx': getattr(app, 'response_3xx', 0),
            '4xx': getattr(app, 'response_4xx', 0),
            '5xx': getattr(app, 'response_5xx', 0)
        }
    }
    return jsonify(metrics_data)

@app.route('/api/v1/info')
def api_info():
    """Informações da API"""
    return jsonify({
        'api': {
            'name': 'Discord Registration Bot API',
            'version': '1.0.0',
            'description': 'API para monitoramento do bot de registro Discord',
            'documentation': '/',
            'health': '/health',
            'status': '/status'
        },
        'author': {
            'name': 'Discord Bot System',
            'contact': 'Via endpoints HTTP'
        },
        'license': 'MIT',
        'timestamp': time.time()
    })

@app.route('/favicon.ico')
def favicon():
    """Favicon para navegadores"""
    return '', 204  # No Content

@app.errorhandler(404)
def not_found(error):
    """Handler para páginas não encontradas"""
    return jsonify({
        'error': 'Endpoint não encontrado',
        'status': 404,
        'path': request.path,
        'suggestions': ['/', '/health', '/ping', '/status']
    }), 404

@app.errorhandler(500)
def server_error(error):
    """Handler para erros internos"""
    return jsonify({
        'error': 'Erro interno do servidor',
        'status': 500,
        'timestamp': time.time()
    }), 500

def run_server():
    """Inicia o servidor Flask com suporte a HTTP/HTTPS"""
    try:
        logger.info(f"🚀 Iniciando servidor web em {config['host']}:{config['port']}")
        logger.info(f"📡 Serviço detectado: {config['service'].upper()}")
        logger.info(f"🌐 Protocolo: {'HTTPS' if config['enable_https'] else 'HTTP'}")
        logger.info(f"🔗 Acesse: http{'s' if config['enable_https'] else ''}://{config['host']}:{config['port']}")
        
        if config['domain']:
            logger.info(f"🌍 Domínio configurado: {config['domain']}")
        
        # Registrar tempo de início
        app.start_time = time.time()
        app.request_count = 0
        app.active_connections = 0
        
        # Configurar servidor HTTP/HTTPS
        if config['enable_https'] and config['ssl_cert'] and config['ssl_key']:
            logger.info(f"🔐 HTTPS habilitado com certificado: {config['ssl_cert']}")
            
            # Para produção, usar waitress ou gunicorn
            try:
                import ssl
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(config['ssl_cert'], config['ssl_key'])
                
                # Iniciar servidor HTTPS
                app.run(
                    host=config['host'],
                    port=config['port'],
                    debug=config['debug'],
                    threaded=True,
                    use_reloader=False,
                    ssl_context=context
                )
            except Exception as ssl_error:
                logger.error(f"❌ Erro SSL: {ssl_error}")
                logger.info("🔄 Voltando para HTTP...")
                app.run(
                    host=config['host'],
                    port=config['port'],
                    debug=config['debug'],
                    threaded=True,
                    use_reloader=False
                )
        else:
            # Iniciar servidor HTTP normal
            app.run(
                host=config['host'],
                port=config['port'],
                debug=config['debug'],
                threaded=True,
                use_reloader=False
            )
            
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor: {e}")
        
        # Tentar portas alternativas
        alt_ports = [5000, 3000, 8000, 8080]
        for port in alt_ports:
            if port != config['port']:
                logger.info(f"🔄 Tentando porta alternativa {port}...")
                try:
                    app.run(
                        host=config['host'],
                        port=port,
                        debug=False,
                        threaded=True,
                        use_reloader=False
                    )
                    break
                except:
                    continue
        
        logger.error("💡 Dica: Verifique permissões de porta ou use outra PORT no ambiente")

def keep_alive():
    """
    Inicia o servidor web em uma thread separada
    Suporta HTTP traffic em qualquer porta
    """
    try:
        server_thread = Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Pequena pausa para garantir inicialização
        time.sleep(3)
        
        logger.info(f"✅ Servidor HTTP iniciado na porta {config['port']}")
        logger.info(f"🏠 Hospedagem: {config['service'].upper()}")
        logger.info(f"🔗 Endpoints disponíveis:")
        logger.info(f"   • http://localhost:{config['port']}/")
        logger.info(f"   • http://localhost:{config['port']}/health")
        logger.info(f"   • http://localhost:{config['port']}/ping")
        logger.info(f"   • http://localhost:{config['port']}/status")
        logger.info(f"   • http://localhost:{config['port']}/metrics")
        
        return True
    except Exception as e:
        logger.error(f"⚠️ Aviso: Não foi possível iniciar servidor HTTP: {e}")
        logger.info("💡 O bot continuará funcionando sem servidor web")
        return False

# Teste rápido se executado diretamente
if __name__ == '__main__':
    print("🧪 Testando servidor HTTP...")
    keep_alive()
    # Manter o script rodando
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Servidor HTTP finalizado")
