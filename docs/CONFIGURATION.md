# ⚙️ Configurazione

Guida dettagliata alla configurazione del sistema.

## 📁 File di Configurazione

Il file principale è `config/config.json`.

### Struttura Completa
```json
{
  "display": { ... },
  "schedule": { ... },
  "watchdog": { ... },
  "notifications": { ... },
  "security": { ... }
}
```

---

## 🖥️ Display
```json
"display": {
  "ip": "192.168.1.100",
  "name": "Display Principale",
  "location": "Negozio Roma"
}
```

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `ip` | string | IP del display Samsung |
| `name` | string | Nome identificativo |
| `location` | string | Posizione fisica |

---

## ⏰ Schedule
```json
"schedule": {
  "enabled": true,
  "power_on": "08:00",
  "power_off": "20:00",
  "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
  "source_on_startup": "hdmi1"
}
```

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `enabled` | boolean | Abilita/disabilita schedule |
| `power_on` | string | Ora accensione (HH:MM) |
| `power_off` | string | Ora spegnimento (HH:MM) |
| `days` | array | Giorni attivi |
| `source_on_startup` | string | Sorgente all'avvio |

### Giorni Disponibili

- `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`

### Sorgenti Disponibili

- `hdmi1`, `hdmi2`, `displayport`, `dvi`

---

## 🔄 Watchdog
```json
"watchdog": {
  "enabled": true,
  "check_interval": 300,
  "max_retry": 3
}
```

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `enabled` | boolean | Abilita watchdog |
| `check_interval` | integer | Intervallo controlli (secondi) |
| `max_retry` | integer | Tentativi prima di alert |

### Comportamento

1. Controlla stato ogni `check_interval` secondi
2. Se display non risponde, incrementa contatore retry
3. Se retry > `max_retry`, invia notifica
4. Se display spento in orario schedule, tenta riaccensione

---

## 🔔 Notifiche

### Telegram
```json
"telegram": {
  "enabled": true,
  "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
  "chat_id": "123456789"
}
```

#### Setup Telegram

1. Cerca `@BotFather` su Telegram
2. `/newbot` → segui istruzioni
3. Copia TOKEN ricevuto
4. Cerca il tuo bot e `/start`
5. Ottieni CHAT_ID da: `https://api.telegram.org/bot[TOKEN]/getUpdates`

### Email
```json
"email": {
  "enabled": true,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "your_email@gmail.com",
  "password": "abcd efgh ijkl mnop",
  "to_email": "recipient@email.com"
}
```

#### Setup Gmail

1. Vai a [Google Account Security](https://myaccount.google.com/security)
2. Abilita "Verifica in due passaggi"
3. Cerca "Password per le app"
4. Genera password per "Mail"
5. Usa password generata (16 caratteri)

---

## 🔐 Sicurezza
```json
"security": {
  "username": "admin",
  "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
}
```

### Generare Password Hash

**Metodo 1: Script**
```cmd
scripts\windows\update_password.bat
```

**Metodo 2: Python**
```python
import hashlib
password = "tua_password_sicura"
hash_pw = hashlib.sha256(password.encode()).hexdigest()
print(hash_pw)
```

### Password Requirements

- Minimo 8 caratteri
- Mix di lettere maiuscole/minuscole
- Almeno un numero
- Caratteri speciali consigliati

---

## 🔧 Configurazione Avanzata

### Modifica dalla Dashboard

1. Accedi alla dashboard
2. Click "⚙️ Configuration"
3. Modifica parametri
4. Click "💾 Save Configuration"

### Modifica Manuale

1. Ferma il sistema: `scripts\windows\stop.bat`
2. Modifica `config\config.json`
3. Verifica sintassi JSON (online validator)
4. Riavvia: `scripts\windows\start.bat`

### Backup Configurazione
```cmd
scripts\windows\backup.bat
```

Salva in: `backups\[data]\`

---

## ✅ Validazione

### Test Configurazione

Dopo modifiche, verifica:
```cmd
python
>>> import json
>>> with open('config/config.json') as f:
...     config = json.load(f)
>>> print("OK!")
```

### Verifica Display
```cmd
scripts\windows\test_display.bat
```

---

## 📊 Esempi Configurazione

### Solo Giorni Feriali
```json
"days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
```

### Weekend Incluso
```json
"days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
```

### Orario Prolungato Venerdì
Richiede schedule personalizzato (feature futura).

### Disabilita Schedule
```json
"schedule": {
  "enabled": false
}
```

### Watchdog Più Frequente
```json
"watchdog": {
  "check_interval": 180  // 3 minuti
}
```

---

**Per domande sulla configurazione, consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
