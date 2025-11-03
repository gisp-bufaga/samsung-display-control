# 🔌 API Documentation

Documentazione completa API REST del sistema.

## 🌐 Base URL

- Locale: `http://localhost:5000`
- Remoto: `http://[TAILSCALE_IP]:5000`

## 🔐 Autenticazione

Tutte le API richiedono autenticazione tramite session cookie.

### Login
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=admin&password=your_password
```

**Response:**
- Redirect a `/` se successo
- Errore se credenziali invalide

## 📡 Endpoints

### Display Control

#### Power ON
```http
POST /api/display/power/on
```

**Response:**
```json
{
  "success": true,
  "message": "Display acceso",
  "status": {
    "power": "on",
    "source": "hdmi1",
    "last_check": "2024-01-15T10:30:00",
    "error_count": 0
  }
}
```

#### Power OFF
```http
POST /api/display/power/off
```

**Response:**
```json
{
  "success": true,
  "message": "Display spento",
  "status": { ... }
}
```

#### Change Source
```http
POST /api/display/source/{source}
```

**Parameters:**
- `source`: `hdmi1`, `hdmi2`, `displayport`, `dvi`

**Example:**
```http
POST /api/display/source/hdmi1
```

**Response:**
```json
{
  "success": true,
  "message": "Sorgente cambiata a hdmi1",
  "status": { ... }
}
```

#### Get Status
```http
GET /api/display/status
```

**Response:**
```json
{
  "display": {
    "power": "on",
    "source": "hdmi1",
    "last_check": "2024-01-15T10:30:00",
    "last_command": "power_on",
    "error_count": 0
  },
  "system": {
    "cpu": 15.2,
    "memory": 45.8,
    "disk": 60.5,
    "uptime": "2 days, 5:30:15",
    "xibo_running": true
  },
  "schedule": {
    "enabled": true,
    "in_schedule": true
  }
}
```

### Configuration

#### Get Configuration
```http
GET /api/config
```

**Response:**
```json
{
  "display": { ... },
  "schedule": { ... },
  "watchdog": { ... },
  "notifications": { ... },
  "security": { ... }
}
```

#### Update Configuration
```http
POST /api/config
Content-Type: application/json

{
  "display": {
    "ip": "192.168.1.100",
    "name": "Nuovo Nome"
  },
  ...
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configurazione salvata"
}
```

### Logs

#### Get Recent Logs
```http
GET /api/logs
```

**Response:**
```json
{
  "logs": [
    "2024-01-15 10:30:01 - DisplayControl - INFO - Display acceso",
    "2024-01-15 10:29:55 - DisplayControl - INFO - Login effettuato: admin",
    ...
  ]
}
```

### Notifications

#### Test Notification
```http
POST /api/test/notification
```

**Response:**
```json
{
  "success": true,
  "message": "Notifica di test inviata"
}
```

## 🔌 WebSocket Events

### Connect
```javascript
const socket = io();

socket.on('connect', () => {
  console.log('Connected to server');
});
```

### Request Status Update
```javascript
socket.emit('request_status');
```

### Receive Status Update
```javascript
socket.on('status_update', (data) => {
  console.log('Display:', data.display);
  console.log('System:', data.system);
  console.log('Schedule:', data.schedule);
});
```

### Connection Events
```javascript
socket.on('connected', (data) => {
  console.log(data.message);
});

socket.on('disconnect', () => {
  console.log('Disconnected from server');
});
```

## 💻 Esempi Utilizzo

### cURL
```bash
# Login
curl -X POST http://localhost:5000/login \
  -d "username=admin&password=admin123" \
  -c cookies.txt

# Power ON (usando cookie)
curl -X POST http://localhost:5000/api/display/power/on \
  -b cookies.txt

# Get Status
curl http://localhost:5000/api/display/status \
  -b cookies.txt
```

### Python
```python
import requests

# Session per mantenere login
session = requests.Session()

# Login
session.post('http://localhost:5000/login', data={
    'username': 'admin',
    'password': 'admin123'
})

# Power ON
response = session.post('http://localhost:5000/api/display/power/on')
print(response.json())

# Get Status
status = session.get('http://localhost:5000/api/display/status')
print(status.json())
```

### PowerShell
```powershell
# Login
$body = @{
    username = 'admin'
    password = 'admin123'
}
$session = Invoke-WebRequest -Uri 'http://localhost:5000/login' `
  -Method POST -Body $body -SessionVariable websession

# Power ON
Invoke-RestMethod -Uri 'http://localhost:5000/api/display/power/on' `
  -Method POST -WebSession $websession
```

### JavaScript (Node.js)
```javascript
const axios = require('axios');

// Client con cookie jar
const client = axios.create({
  baseURL: 'http://localhost:5000',
  withCredentials: true
});

// Login
await client.post('/login', new URLSearchParams({
  username: 'admin',
  password: 'admin123'
}));

// Power ON
const response = await client.post('/api/display/power/on');
console.log(response.data);
```

## 🔒 Rate Limiting

Le API sono protette da rate limiting:

- **Power Control**: 10 comandi/minuto
- **General APIs**: 50 richieste/ora
- **Global Limit**: 200 richieste/giorno

**Response quando limite superato:**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

## 🐛 Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "Stato non valido"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Impossibile connettersi al display"
}
```

## 📊 Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (parametri invalidi) |
| 401 | Unauthorized (login richiesto) |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |

## 🔄 Webhook Integration (Future)

Feature pianificata per notificare eventi esterni:
```http
POST /api/webhooks
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["power_on", "power_off", "error"]
}
```

---

**Per integrazioni personalizzate, contatta il maintainer del progetto.**
