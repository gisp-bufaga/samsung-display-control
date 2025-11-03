"""
Sistema Completo di Controllo Display Samsung
con Dashboard, Scheduling, Notifiche e Monitoring

Requisiti:
pip install flask flask-socketio samsung-mdc schedule requests python-socketio

File necessari:
- display_system.py (questo file)
- config.json (configurazione)
"""

from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from functools import wraps
import hashlib
import secrets
import json
import logging
from datetime import datetime, timedelta
import threading
import time
import schedule
import os
import subprocess
import psutil

try:
    from samsung_mdc import MDC
except ImportError:
    print("ERRORE: Installa samsung-mdc con: pip install samsung-mdc")
    exit(1)

# =====================================================================
# CONFIGURAZIONE
# =====================================================================

CONFIG_FILE = 'config.json'
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'display.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DisplayControl')

# =====================================================================
# CONFIGURAZIONE DEFAULT
# =====================================================================

DEFAULT_CONFIG = {
    "display": {
        "ip": "192.168.1.100",
        "name": "Display Principale",
        "location": "Negozio Roma"
    },
    "schedule": {
        "enabled": True,
        "power_on": "08:00",
        "power_off": "20:00",
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
        "source_on_startup": "hdmi1"
    },
    "watchdog": {
        "enabled": True,
        "check_interval": 300,
        "max_retry": 3
    },
    "notifications": {
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_id": ""
        },
        "email": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "to_email": ""
        }
    },
    "security": {
        "username": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest()
    }
}

# Carica o crea configurazione
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        CONFIG = json.load(f)
        logger.info("Configurazione caricata da file")
else:
    CONFIG = DEFAULT_CONFIG
    with open(CONFIG_FILE, 'w') as f:
        json.dump(CONFIG, f, indent=2)
    logger.info("Creato file configurazione default")

# =====================================================================
# FLASK APP
# =====================================================================

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
socketio = SocketIO(app, cors_allowed_origins="*")

# =====================================================================
# DISPLAY CONTROLLER
# =====================================================================

class DisplayController:
    def __init__(self, ip):
        self.ip = ip
        self.status = {
            'power': 'unknown',
            'source': 'unknown',
            'last_check': None,
            'last_command': None,
            'error_count': 0
        }
        self.retry_count = 0
        self.max_retry = CONFIG['watchdog']['max_retry']
        
    def connect(self, retries=3):
        """Connessione al display con retry"""
        for i in range(retries):
            try:
                display = MDC(self.ip, verbose=False)
                return display
            except Exception as e:
                logger.warning(f"Tentativo connessione {i+1}/{retries} fallito: {e}")
                if i < retries - 1:
                    time.sleep(2)
        return None
    
    def power_on(self):
        """Accendi display"""
        try:
            display = self.connect()
            if not display:
                raise Exception("Impossibile connettersi al display")
            
            display.power(True)
            self.status['power'] = 'on'
            self.status['last_command'] = 'power_on'
            self.status['last_check'] = datetime.now().isoformat()
            self.retry_count = 0
            
            logger.info("Display acceso con successo")
            broadcast_status_update()
            return True
            
        except Exception as e:
            logger.error(f"Errore accensione display: {e}")
            self.status['error_count'] += 1
            return False
    
    def power_off(self):
        """Spegni display"""
        try:
            display = self.connect()
            if not display:
                raise Exception("Impossibile connettersi al display")
            
            display.power(False)
            self.status['power'] = 'off'
            self.status['last_command'] = 'power_off'
            self.status['last_check'] = datetime.now().isoformat()
            self.retry_count = 0
            
            logger.info("Display spento con successo")
            broadcast_status_update()
            return True
            
        except Exception as e:
            logger.error(f"Errore spegnimento display: {e}")
            self.status['error_count'] += 1
            return False
    
    def set_source(self, source):
        """Cambia sorgente input"""
        try:
            display = self.connect()
            if not display:
                raise Exception("Impossibile connettersi al display")
            
            display.source(source)
            self.status['source'] = source
            self.status['last_command'] = f'set_source_{source}'
            self.status['last_check'] = datetime.now().isoformat()
            
            logger.info(f"Sorgente cambiata a {source}")
            broadcast_status_update()
            return True
            
        except Exception as e:
            logger.error(f"Errore cambio sorgente: {e}")
            self.status['error_count'] += 1
            return False
    
    def check_status(self):
        """Verifica stato attuale del display"""
        try:
            display = self.connect()
            if not display:
                self.status['power'] = 'unreachable'
                self.status['last_check'] = datetime.now().isoformat()
                broadcast_status_update()
                return False
            
            power_status = display.get_power_status()
            self.status['power'] = power_status
            self.status['last_check'] = datetime.now().isoformat()
            self.retry_count = 0
            
            broadcast_status_update()
            return True
            
        except Exception as e:
            logger.error(f"Errore verifica stato: {e}")
            self.status['power'] = 'error'
            self.status['last_check'] = datetime.now().isoformat()
            self.status['error_count'] += 1
            broadcast_status_update()
            return False
    
    def watchdog(self):
        """Verifica e recovery automatico"""
        logger.info("Watchdog check...")
        
        if not self.check_status():
            logger.warning("Display non raggiungibile")
            self.retry_count += 1
            
            if self.retry_count >= self.max_retry:
                logger.critical(f"Max retry ({self.max_retry}) raggiunto!")
                send_notification(
                    "⚠️ ALERT: Display Non Raggiungibile",
                    f"Il display non risponde dopo {self.max_retry} tentativi. Intervento richiesto."
                )
                self.retry_count = 0
                return False
            
            # Tentativo power cycle
            logger.warning(f"Tentativo recovery {self.retry_count}/{self.max_retry}")
            time.sleep(5)
            self.power_off()
            time.sleep(10)
            self.power_on()
            time.sleep(5)
            self.set_source(CONFIG['schedule']['source_on_startup'])
            
        elif self.status['power'] == 'off':
            # Display spento quando dovrebbe essere acceso
            if is_in_schedule():
                logger.warning("Display spento durante orario schedulato - riaccensione")
                self.power_on()
                time.sleep(3)
                self.set_source(CONFIG['schedule']['source_on_startup'])
        
        return True

# Istanza globale controller
display_controller = DisplayController(CONFIG['display']['ip'])

# =====================================================================
# SCHEDULER
# =====================================================================

def is_in_schedule():
    """Verifica se l'ora corrente è dentro lo schedule"""
    if not CONFIG['schedule']['enabled']:
        return False
    
    now = datetime.now()
    day_name = now.strftime('%A').lower()
    
    if day_name not in CONFIG['schedule']['days']:
        return False
    
    current_time = now.time()
    on_time = datetime.strptime(CONFIG['schedule']['power_on'], '%H:%M').time()
    off_time = datetime.strptime(CONFIG['schedule']['power_off'], '%H:%M').time()
    
    return on_time <= current_time <= off_time

def scheduled_power_on():
    """Accensione schedulata"""
    logger.info("Esecuzione accensione schedulata")
    if display_controller.power_on():
        time.sleep(3)
        display_controller.set_source(CONFIG['schedule']['source_on_startup'])
        send_notification("✅ Display Acceso", "Accensione schedulata eseguita con successo")

def scheduled_power_off():
    """Spegnimento schedulato"""
    logger.info("Esecuzione spegnimento schedulato")
    if display_controller.power_off():
        send_notification("✅ Display Spento", "Spegnimento schedulato eseguito con successo")

def setup_scheduler():
    """Configura scheduler"""
    if not CONFIG['schedule']['enabled']:
        logger.info("Scheduler disabilitato")
        return
    
    schedule.clear()
    
    days_map = {
        'monday': schedule.every().monday,
        'tuesday': schedule.every().tuesday,
        'wednesday': schedule.every().wednesday,
        'thursday': schedule.every().thursday,
        'friday': schedule.every().friday,
        'saturday': schedule.every().saturday,
        'sunday': schedule.every().sunday
    }
    
    for day in CONFIG['schedule']['days']:
        if day in days_map:
            days_map[day].at(CONFIG['schedule']['power_on']).do(scheduled_power_on)
            days_map[day].at(CONFIG['schedule']['power_off']).do(scheduled_power_off)
    
    logger.info(f"Scheduler configurato: ON={CONFIG['schedule']['power_on']}, OFF={CONFIG['schedule']['power_off']}")

def run_scheduler():
    """Thread scheduler"""
    while True:
        schedule.run_pending()
        time.sleep(60)

# =====================================================================
# WATCHDOG
# =====================================================================

def run_watchdog():
    """Thread watchdog"""
    while True:
        if CONFIG['watchdog']['enabled']:
            display_controller.watchdog()
        time.sleep(CONFIG['watchdog']['check_interval'])

# =====================================================================
# NOTIFICHE
# =====================================================================

def send_notification(title, message):
    """Invia notifiche configurate"""
    
    # Telegram
    if CONFIG['notifications']['telegram']['enabled']:
        try:
            import requests
            bot_token = CONFIG['notifications']['telegram']['bot_token']
            chat_id = CONFIG['notifications']['telegram']['chat_id']
            
            url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
            data = {
                'chat_id': chat_id,
                'text': f'<b>{title}</b>\n\n{message}',
                'parse_mode': 'HTML'
            }
            requests.post(url, data=data, timeout=10)
            logger.info(f"Notifica Telegram inviata: {title}")
        except Exception as e:
            logger.error(f"Errore invio Telegram: {e}")
    
    # Email
    if CONFIG['notifications']['email']['enabled']:
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText(message)
            msg['Subject'] = title
            msg['From'] = CONFIG['notifications']['email']['username']
            msg['To'] = CONFIG['notifications']['email']['to_email']
            
            server = smtplib.SMTP(
                CONFIG['notifications']['email']['smtp_server'],
                CONFIG['notifications']['email']['smtp_port']
            )
            server.starttls()
            server.login(
                CONFIG['notifications']['email']['username'],
                CONFIG['notifications']['email']['password']
            )
            server.send_message(msg)
            server.quit()
            logger.info(f"Email inviata: {title}")
        except Exception as e:
            logger.error(f"Errore invio email: {e}")

# =====================================================================
# SYSTEM MONITOR
# =====================================================================

def get_system_info():
    """Informazioni sistema"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')
        
        # Uptime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))
        
        # Processi
        xibo_running = any('xibo' in p.name().lower() for p in psutil.process_iter(['name']))
        
        return {
            'cpu': cpu,
            'memory': mem.percent,
            'disk': disk.percent,
            'uptime': uptime_str,
            'xibo_running': xibo_running
        }
    except Exception as e:
        logger.error(f"Errore lettura info sistema: {e}")
        return None

# =====================================================================
# WEBSOCKET BROADCAST
# =====================================================================

def broadcast_status_update():
    """Invia aggiornamento stato a tutti i client connessi"""
    try:
        socketio.emit('status_update', {
            'display': display_controller.status,
            'system': get_system_info(),
            'schedule': {
                'enabled': CONFIG['schedule']['enabled'],
                'in_schedule': is_in_schedule()
            }
        })
    except:
        pass

# =====================================================================
# DECORATORI
# =====================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# =====================================================================
# ROUTES
# =====================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if (username == CONFIG['security']['username'] and 
            password_hash == CONFIG['security']['password_hash']):
            session['logged_in'] = True
            session['username'] = username
            session.permanent = True
            logger.info(f"Login effettuato: {username}")
            return redirect(url_for('dashboard'))
        else:
            logger.warning(f"Tentativo login fallito: {username}")
            return render_template_string(LOGIN_HTML, error="Credenziali non valide")
    
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_HTML, config=CONFIG)

# API Routes
@app.route('/api/display/power/<state>', methods=['POST'])
@login_required
def api_power(state):
    logger.info(f"Comando power_{state} da {request.remote_addr}")
    
    if state == 'on':
        success = display_controller.power_on()
    elif state == 'off':
        success = display_controller.power_off()
    else:
        return jsonify({'success': False, 'error': 'Stato non valido'}), 400
    
    return jsonify({
        'success': success,
        'message': f'Display {"acceso" if state == "on" else "spento"}',
        'status': display_controller.status
    })

@app.route('/api/display/source/<source>', methods=['POST'])
@login_required
def api_source(source):
    logger.info(f"Comando source_{source} da {request.remote_addr}")
    success = display_controller.set_source(source)
    
    return jsonify({
        'success': success,
        'message': f'Sorgente cambiata a {source}',
        'status': display_controller.status
    })

@app.route('/api/display/status')
@login_required
def api_status():
    display_controller.check_status()
    return jsonify({
        'display': display_controller.status,
        'system': get_system_info(),
        'schedule': {
            'enabled': CONFIG['schedule']['enabled'],
            'in_schedule': is_in_schedule()
        }
    })

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def api_config():
    if request.method == 'POST':
        try:
            new_config = request.json
            
            # Valida configurazione
            # (aggiungi validazione necessaria)
            
            # Salva
            with open(CONFIG_FILE, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            # Ricarica
            CONFIG.update(new_config)
            setup_scheduler()
            
            logger.info("Configurazione aggiornata")
            return jsonify({'success': True, 'message': 'Configurazione salvata'})
        except Exception as e:
            logger.error(f"Errore salvataggio config: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify(CONFIG)

@app.route('/api/logs')
@login_required
def api_logs():
    try:
        with open(os.path.join(LOG_DIR, 'display.log'), 'r') as f:
            logs = f.readlines()[-100:]  # Ultimi 100
        return jsonify({'logs': [l.strip() for l in reversed(logs)]})
    except Exception as e:
        return jsonify({'logs': [f'Errore lettura log: {e}']})

@app.route('/api/test/notification', methods=['POST'])
@login_required
def test_notification():
    send_notification("🧪 Test Notifica", "Questo è un test del sistema di notifiche")
    return jsonify({'success': True, 'message': 'Notifica di test inviata'})

# WebSocket handlers
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connesso: {request.sid}")
    emit('connected', {'message': 'Connesso al server'})
    broadcast_status_update()

@socketio.on('request_status')
def handle_status_request():
    display_controller.check_status()
    broadcast_status_update()

# =====================================================================
# HTML TEMPLATES
# =====================================================================

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Display Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 28px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: border 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:active {
            transform: translateY(0);
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-size: 14px;
        }
        .info {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🖥️ Display Control</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        <div class="info">
            Default: admin / admin123<br>
            Cambia password in config.json
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Display Control Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #0f1419;
            color: #fff;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        .header h1 {
            font-size: 28px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .header-info {
            text-align: right;
            font-size: 14px;
            opacity: 0.9;
        }
        .logout-btn {
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            color: white;
            font-size: 13px;
            display: inline-block;
            margin-top: 8px;
            transition: background 0.3s;
        }
        .logout-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .card h2 {
            font-size: 18px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            animation: pulse 2s infinite;
        }
        .status-on { background: #4CAF50; }
        .status-off { background: #999; }
        .status-error { background: #f44336; }
        .status-unknown { background: #FF9800; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 15px 0;
        }
        .stat-item {
            background: rgba(0,0,0,0.2);
            padding: 12px;
            border-radius: 8px;
        }
        .stat-label {
            font-size: 12px;
            opacity: 0.7;
            margin-bottom: 5px;
        }
        .stat-value {
            font-size: 20px;
            font-weight: bold;
        }
        .button-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        button {
            padding: 14px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 15px;
            font-weight: bold;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        button:active {
            transform: translateY(0);
        }
        .btn-on { background: linear-gradient(135deg, #4CAF50, #45a049); color: white; }
        .btn-off { background: linear-gradient(135deg, #999, #666); color: white; }
        .btn-source { background: linear-gradient(135deg, #2196F3, #0b7dda); color: white; }
        .btn-refresh { background: linear-gradient(135deg, #FF9800, #e68900); color: white; }
        .btn-danger { background: linear-gradient(135deg, #f44336, #da190b); color: white; }
        .logs-container {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        .log-entry {
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            word-wrap: break-word;
        }
        .log-time {
            color: #666;
            margin-right: 10px;
        }
        .log-level-INFO { color: #4CAF50; }
        .log-level-WARNING { color: #FF9800; }
        .log-level-ERROR { color: #f44336; }
        .schedule-info {
            background: rgba(102, 126, 234, 0.1);
            border-left: 4px solid #667eea;
            padding: 12px;
            border-radius: 8px;
            margin: 15px 0;
            font-size: 14px;
        }
        .schedule-active {
            color: #4CAF50;
            font-weight: bold;
        }
        .schedule-inactive {
            color: #999;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: #1a1f2e;
            padding: 30px;
            border-radius: 15px;
            max-width: 600px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
        }
        .modal h3 {
            margin-bottom: 20px;
            color: #667eea;
        }
        .modal-close {
            float: right;
            cursor: pointer;
            font-size: 24px;
            color: #999;
        }
        .modal-close:hover {
            color: #fff;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-size: 13px;
            opacity: 0.8;
        }
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(0,0,0,0.3);
            color: white;
            border-radius: 8px;
            font-size: 14px;
        }
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #45a049);
            transition: width 0.3s;
        }
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            display: none;
            z-index: 2000;
            min-width: 250px;
        }
        .toast.show {
            display: block;
            animation: slideIn 0.3s;
        }
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        .toast-success { border-left: 4px solid #4CAF50; }
        .toast-error { border-left: 4px solid #f44336; }
        .toast-info { border-left: 4px solid #2196F3; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>
                <span>🖥️</span>
                <span>Display Control</span>
            </h1>
            <div style="opacity: 0.8; font-size: 14px; margin-top: 5px;">
                {{ config.display.name }} - {{ config.display.location }}
            </div>
        </div>
        <div class="header-info">
            <div>👤 {{ session.username }}</div>
            <div id="currentTime">--:--:--</div>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    </div>

    <div class="grid">
        <!-- Display Status Card -->
        <div class="card">
            <h2>
                <span>📊</span>
                <span>Display Status</span>
                <span class="status-indicator status-unknown" id="displayStatusDot"></span>
            </h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-label">Power</div>
                    <div class="stat-value" id="displayPower">Unknown</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Source</div>
                    <div class="stat-value" id="displaySource">Unknown</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Error Count</div>
                    <div class="stat-value" id="displayErrors">0</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Last Check</div>
                    <div class="stat-value" id="lastCheck" style="font-size: 14px;">Never</div>
                </div>
            </div>
            <button class="btn-refresh" onclick="refreshStatus()" style="width: 100%; margin-top: 10px;">
                🔄 Refresh Status
            </button>
        </div>

        <!-- System Info Card -->
        <div class="card">
            <h2>
                <span>💻</span>
                <span>System Info</span>
            </h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-label">CPU Usage</div>
                    <div class="stat-value" id="cpuUsage">--%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="cpuProgress" style="width: 0%"></div>
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Memory</div>
                    <div class="stat-value" id="memUsage">--%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="memProgress" style="width: 0%"></div>
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Uptime</div>
                    <div class="stat-value" id="systemUptime" style="font-size: 16px;">--:--:--</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Xibo Player</div>
                    <div class="stat-value" id="xiboStatus">Unknown</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Schedule Info -->
    <div class="card" style="margin-bottom: 20px;">
        <h2>
            <span>⏰</span>
            <span>Schedule</span>
        </h2>
        <div class="schedule-info" id="scheduleInfo">
            Loading schedule...
        </div>
    </div>

    <div class="grid">
        <!-- Power Control Card -->
        <div class="card">
            <h2>
                <span>⚡</span>
                <span>Power Control</span>
            </h2>
            <div class="button-grid">
                <button class="btn-on" onclick="sendCommand('power', 'on')">
                    🟢 Power ON
                </button>
                <button class="btn-off" onclick="sendCommand('power', 'off')">
                    ⚫ Power OFF
                </button>
            </div>
        </div>

        <!-- Source Control Card -->
        <div class="card">
            <h2>
                <span>📺</span>
                <span>Input Source</span>
            </h2>
            <div class="button-grid">
                <button class="btn-source" onclick="sendCommand('source', 'hdmi1')">
                    HDMI 1
                </button>
                <button class="btn-source" onclick="sendCommand('source', 'hdmi2')">
                    HDMI 2
                </button>
                <button class="btn-source" onclick="sendCommand('source', 'displayport')">
                    DisplayPort
                </button>
                <button class="btn-source" onclick="sendCommand('source', 'dvi')">
                    DVI
                </button>
            </div>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="card" style="margin-top: 20px;">
        <h2>
            <span>🔧</span>
            <span>Quick Actions</span>
        </h2>
        <div class="button-grid">
            <button class="btn-refresh" onclick="openConfigModal()">
                ⚙️ Configuration
            </button>
            <button class="btn-refresh" onclick="openLogsModal()">
                📋 View Logs
            </button>
            <button class="btn-refresh" onclick="testNotification()">
                🔔 Test Notification
            </button>
            <button class="btn-danger" onclick="restartXibo()">
                🔄 Restart Xibo
            </button>
        </div>
    </div>

    <!-- Config Modal -->
    <div id="configModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('configModal')">&times;</span>
            <h3>⚙️ Configuration</h3>
            
            <div class="form-group">
                <label>Display IP Address</label>
                <input type="text" id="configDisplayIp" placeholder="192.168.1.100">
            </div>
            
            <div class="form-group">
                <label>Schedule Enabled</label>
                <select id="configScheduleEnabled">
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Power ON Time</label>
                <input type="time" id="configPowerOn">
            </div>
            
            <div class="form-group">
                <label>Power OFF Time</label>
                <input type="time" id="configPowerOff">
            </div>
            
            <div class="form-group">
                <label>Source on Startup</label>
                <select id="configSourceStartup">
                    <option value="hdmi1">HDMI 1</option>
                    <option value="hdmi2">HDMI 2</option>
                    <option value="displayport">DisplayPort</option>
                    <option value="dvi">DVI</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Watchdog Check Interval (seconds)</label>
                <input type="number" id="configWatchdogInterval" value="300" min="60">
            </div>
            
            <button class="btn-on" onclick="saveConfig()" style="width: 100%; margin-top: 20px;">
                💾 Save Configuration
            </button>
        </div>
    </div>

    <!-- Logs Modal -->
    <div id="logsModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('logsModal')">&times;</span>
            <h3>📋 System Logs</h3>
            <div class="logs-container" id="logsContent">
                Loading logs...
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div id="toast" class="toast"></div>

    <script>
        const socket = io();
        let statusData = null;

        // Socket connection
        socket.on('connect', () => {
            console.log('Connected to server');
            socket.emit('request_status');
        });

        socket.on('status_update', (data) => {
            statusData = data;
            updateUI(data);
        });

        // Update UI with status data
        function updateUI(data) {
            // Display status
            const display = data.display;
            const powerStatus = display.power;
            
            document.getElementById('displayPower').textContent = powerStatus.toUpperCase();
            document.getElementById('displaySource').textContent = display.source.toUpperCase();
            document.getElementById('displayErrors').textContent = display.error_count || 0;
            
            if (display.last_check) {
                const date = new Date(display.last_check);
                document.getElementById('lastCheck').textContent = date.toLocaleTimeString();
            }

            // Status indicator
            const statusDot = document.getElementById('displayStatusDot');
            statusDot.className = 'status-indicator';
            if (powerStatus === 'on') {
                statusDot.classList.add('status-on');
            } else if (powerStatus === 'off') {
                statusDot.classList.add('status-off');
            } else if (powerStatus === 'error' || powerStatus === 'unreachable') {
                statusDot.classList.add('status-error');
            } else {
                statusDot.classList.add('status-unknown');
            }

            // System info
            if (data.system) {
                const sys = data.system;
                document.getElementById('cpuUsage').textContent = sys.cpu.toFixed(1) + '%';
                document.getElementById('cpuProgress').style.width = sys.cpu + '%';
                
                document.getElementById('memUsage').textContent = sys.memory.toFixed(1) + '%';
                document.getElementById('memProgress').style.width = sys.memory + '%';
                
                document.getElementById('systemUptime').textContent = sys.uptime;
                
                document.getElementById('xiboStatus').textContent = sys.xibo_running ? '✅ Running' : '❌ Not Running';
            }

            // Schedule info
            if (data.schedule) {
                const scheduleDiv = document.getElementById('scheduleInfo');
                if (data.schedule.enabled) {
                    const status = data.schedule.in_schedule ? 
                        '<span class="schedule-active">✅ Active (display should be ON)</span>' :
                        '<span class="schedule-inactive">⏸️ Inactive (outside schedule hours)</span>';
                    scheduleDiv.innerHTML = status;
                } else {
                    scheduleDiv.innerHTML = '<span class="schedule-inactive">⏸️ Scheduling disabled</span>';
                }
            }
        }

        // Send command
        async function sendCommand(type, value) {
            try {
                const endpoint = type === 'power' ? 
                    `/api/display/power/${value}` : 
                    `/api/display/source/${value}`;
                
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast('✅ ' + data.message, 'success');
                    setTimeout(() => socket.emit('request_status'), 2000);
                } else {
                    showToast('❌ Command failed', 'error');
                }
            } catch (error) {
                showToast('❌ Connection error', 'error');
            }
        }

        // Refresh status
        function refreshStatus() {
            socket.emit('request_status');
            showToast('🔄 Refreshing...', 'info');
        }

        // Test notification
        async function testNotification() {
            try {
                const response = await fetch('/api/test/notification', {
                    method: 'POST'
                });
                const data = await response.json();
                showToast(data.message, 'success');
            } catch (error) {
                showToast('Failed to send test notification', 'error');
            }
        }

        // Restart Xibo
        async function restartXibo() {
            if (!confirm('Restart Xibo Player?')) return;
            
            showToast('🔄 Restarting Xibo...', 'info');
            // Implement restart logic via API
        }

        // Open modals
        function openConfigModal() {
            fetch('/api/config')
                .then(r => r.json())
                .then(config => {
                    document.getElementById('configDisplayIp').value = config.display.ip;
                    document.getElementById('configScheduleEnabled').value = config.schedule.enabled;
                    document.getElementById('configPowerOn').value = config.schedule.power_on;
                    document.getElementById('configPowerOff').value = config.schedule.power_off;
                    document.getElementById('configSourceStartup').value = config.schedule.source_on_startup;
                    document.getElementById('configWatchdogInterval').value = config.watchdog.check_interval;
                    
                    document.getElementById('configModal').style.display = 'flex';
                });
        }

        function openLogsModal() {
            fetch('/api/logs')
                .then(r => r.json())
                .then(data => {
                    const logsDiv = document.getElementById('logsContent');
                    logsDiv.innerHTML = '';
                    
                    data.logs.forEach(log => {
                        const entry = document.createElement('div');
                        entry.className = 'log-entry';
                        
                        // Parse log line
                        const parts = log.split(' - ');
                        if (parts.length >= 3) {
                            const level = parts[2];
                            entry.innerHTML = `
                                <span class="log-time">${parts[0]}</span>
                                <span class="log-level-${level}">${level}</span>
                                <span>${parts.slice(3).join(' - ')}</span>
                            `;
                        } else {
                            entry.textContent = log;
                        }
                        
                        logsDiv.appendChild(entry);
                    });
                    
                    document.getElementById('logsModal').style.display = 'flex';
                });
        }

        function closeModal(id) {
            document.getElementById(id).style.display = 'none';
        }

        // Save configuration
        async function saveConfig() {
            const config = {
                display: {
                    ip: document.getElementById('configDisplayIp').value,
                    name: "{{ config.display.name }}",
                    location: "{{ config.display.location }}"
                },
                schedule: {
                    enabled: document.getElementById('configScheduleEnabled').value === 'true',
                    power_on: document.getElementById('configPowerOn').value,
                    power_off: document.getElementById('configPowerOff').value,
                    days: {{ config.schedule.days | tojson }},
                    source_on_startup: document.getElementById('configSourceStartup').value
                },
                watchdog: {
                    enabled: true,
                    check_interval: parseInt(document.getElementById('configWatchdogInterval').value),
                    max_retry: {{ config.watchdog.max_retry }}
                },
                notifications: {{ config.notifications | tojson }},
                security: {{ config.security | tojson }}
            };

            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast('✅ Configuration saved! Restart may be required.', 'success');
                    closeModal('configModal');
                } else {
                    showToast('❌ Failed to save configuration', 'error');
                }
            } catch (error) {
                showToast('❌ Connection error', 'error');
            }
        }

        // Toast notification
        function showToast(message, type) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast toast-' + type + ' show';
            
            setTimeout(() => {
                toast.classList.remove('show');
            }, 4000);
        }

        // Update current time
        function updateTime() {
            const now = new Date();
            document.getElementById('currentTime').textContent = now.toLocaleTimeString();
        }
        setInterval(updateTime, 1000);
        updateTime();

        // Auto-refresh status every 30 seconds
        setInterval(() => {
            socket.emit('request_status');
        }, 30000);

        // Close modals on ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeModal('configModal');
                closeModal('logsModal');
            }
        });
    </script>
</body>
</html>
"""

# =====================================================================
# MAIN
# =====================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🖥️  DISPLAY CONTROL SYSTEM")
    print("=" * 70)
    print(f"Display: {CONFIG['display']['name']} ({CONFIG['display']['ip']})")
    print(f"Location: {CONFIG['display']['location']}")
    print(f"Schedule: {'Enabled' if CONFIG['schedule']['enabled'] else 'Disabled'}")
    print(f"Watchdog: {'Enabled' if CONFIG['watchdog']['enabled'] else 'Disabled'}")
    print(f"Telegram: {'Enabled' if CONFIG['notifications']['telegram']['enabled'] else 'Disabled'}")
    print(f"Email: {'Enabled' if CONFIG['notifications']['email']['enabled'] else 'Disabled'}")
    print("=" * 70)
    print(f"\nDefault Login: admin / admin123")
    print(f"Server starting on: http://0.0.0.0:5000")
    print(f"Access via Tailscale: http://[TAILSCALE_IP]:5000")
    print("\nPress Ctrl+C to stop")
    print("=" * 70)
    
    # Setup scheduler
    setup_scheduler()
    
    # Start background threads
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler thread started")
    
    watchdog_thread = threading.Thread(target=run_watchdog, daemon=True)
    watchdog_thread.start()
    logger.info("Watchdog thread started")
    
    # Check initial display status
    display_controller.check_status()
    
    # Start Flask-SocketIO server
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        logger.info("Server stopped by user")
    except Exception as e:
        logger.critical(f"Server error: {e}")
        raise
