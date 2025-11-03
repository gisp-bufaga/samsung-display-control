# 📘 Guida Setup Completa

Questa guida ti accompagna passo-passo nell'installazione e configurazione del sistema Samsung Display Control.

## 📋 Indice

1. [Prerequisiti](#prerequisiti)
2. [Installazione Python](#installazione-python)
3. [Installazione Tailscale](#installazione-tailscale)
4. [Configurazione Display](#configurazione-display)
5. [Installazione Sistema](#installazione-sistema)
6. [Primo Avvio](#primo-avvio)
7. [Configurazione Avanzata](#configurazione-avanzata)
8. [Accesso Mobile](#accesso-mobile)

---

## 📋 Prerequisiti

### Hardware
- Mini-PC con Windows 10/11
- Display Samsung con supporto MDC
- Switch di rete o router
- Cavi Ethernet

### Software
- Windows 10/11 (versione 64-bit)
- Connessione Internet
- Account email per Tailscale

### Display Samsung
- MDC Protocol supportato
- Connessione di rete configurata
- Accesso al menu impostazioni

---

## 🐍 Installazione Python

### 1. Download

Vai su [python.org/downloads](https://www.python.org/downloads/) e scarica Python 3.8 o superiore.

### 2. Installazione

⚠️ **IMPORTANTE**: Durante l'installazione:
- ✅ Spunta "**Add Python to PATH**"
- ✅ Seleziona "Install for all users" (opzionale ma consigliato)

### 3. Verifica

Apri Command Prompt e verifica:
```cmd
python --version
```

Output atteso: `Python 3.x.x`
```cmd
pip --version
```

Output atteso: `pip 23.x.x from ...`

---

## 🌐 Installazione Tailscale

### 1. Download

Vai su [tailscale.com/download/windows](https://tailscale.com/download/windows)

### 2. Installazione

- Esegui l'installer
- Segui il wizard di installazione
- Al termine, Tailscale si avvia automaticamente

### 3. Login

- Si apre il browser per l'autenticazione
- Login con Google, Microsoft o GitHub
- Approva il dispositivo nella dashboard

### 4. Verifica IP
```cmd
tailscale ip -4
```

Output esempio: `100.64.1.5`

**📝 Annota questo IP** - ti servirà per accesso remoto!

---

## 🖥️ Configurazione Display

### 1. Assegna IP Statico

Sul router, assegna un IP statico al display:
- Esempio: `192.168.1.100`
- Annota l'IP per la configurazione

### 2. Abilita MDC

Sul display Samsung:
1. Premi `MENU` sul telecomando
2. Vai a `Network` → `Network Settings`
3. Trova `MDC` o `Network Control`
4. Imposta su `Enabled` o `On`
5. Salva e riavvia display

### 3. Test Connessione
```cmd
ping 192.168.1.100
```

Dovresti vedere risposte positive.

---

## 📦 Installazione Sistema

### 1. Clona Repository
```cmd
cd C:\
git clone https://github.com/gisp-bufaga/samsung-display-control.git
cd samsung-display-control
```

### 2. Installazione Guidata

**Opzione A: Setup Wizard (Consigliata)**
```cmd
scripts\windows\setup_wizard.bat
```

Segui le istruzioni a schermo.

**Opzione B: Manuale**
```cmd
# Installa dipendenze
pip install -r requirements.txt

# Crea configurazione
copy config\config.example.json config\config.json

# Modifica config con tuo editor
notepad config\config.json
```

### 3. Modifica Configurazione

Apri `config\config.json` e modifica:
```json
{
  "display": {
    "ip": "192.168.1.100",  ← IL TUO IP DISPLAY
    "name": "Il Mio Display",
    "location": "Ufficio"
  }
}
```

---

## 🚀 Primo Avvio

### 1. Test Manuale
```cmd
python src\display_system.py
```

Dovresti vedere:

======================================================================
🖥️  DISPLAY CONTROL SYSTEM
Display: Il Mio Display (192.168.1.100)
...
Server starting on: http://0.0.0.0:5000

======================================================================

### 2. Accedi alla Dashboard

Apri browser e vai a: `http://localhost:5000`

- Username: `admin`
- Password: `admin123`

### 3. Test Comandi

Nella dashboard:
1. Click su "🔄 Refresh Status" - verifica connessione
2. Click su "🟢 Power ON" - testa accensione
3. Verifica che il display risponda

### 4. Ferma il Server

Premi `Ctrl+C` nella finestra Command Prompt.

---

## ⚙️ Configurazione Avanzata

### Avvio Automatico

**Opzione A: Task Scheduler**
```cmd
scripts\windows\install_service.bat
```

Richiede privilegi amministratore.

**Opzione B: Script di Startup**

1. Crea shortcut di `scripts\windows\start.bat`
2. Premi `Win+R`, digita `shell:startup`
3. Incolla lo shortcut nella cartella

### Cambio Password
```cmd
scripts\windows\update_password.bat
```

Oppure manualmente:
```python
python
>>> import hashlib
>>> hashlib.sha256("tua_nuova_password".encode()).hexdigest()
```

Copia l'hash in `config\config.json` → `security.password_hash`

### Configurazione Schedule

Modifica in `config\config.json`:
```json
"schedule": {
  "enabled": true,
  "power_on": "08:00",
  "power_off": "20:00",
  "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
  "source_on_startup": "hdmi1"
}
```

### Notifiche Telegram

1. Crea bot con [@BotFather](https://t.me/BotFather)
2. Ottieni token e chat_id
3. Configura in `config.json`:
```json
"telegram": {
  "enabled": true,
  "bot_token": "123456:ABC-DEF...",
  "chat_id": "123456789"
}
```

---

## 📱 Accesso Mobile

### Android

1. Installa [Tailscale](https://play.google.com/store/apps/details?id=com.tailscale.ipn)
2. Login con stesso account
3. Apri Chrome: `http://100.64.1.5:5000`
4. Login: `admin` / `tua_password`
5. Menu → "Aggiungi a schermata Home"

### iOS

1. Installa [Tailscale](https://apps.apple.com/app/tailscale/id1470499037)
2. Login con stesso account
3. Safari: `http://100.64.1.5:5000`
4. Login: `admin` / `tua_password`
5. Condividi → "Aggiungi a Home"

---

## ✅ Verifica Installazione

### Checklist

- [ ] Python installato e funzionante
- [ ] Tailscale connesso (IP ottenuto)
- [ ] Display risponde a ping
- [ ] Server si avvia senza errori
- [ ] Dashboard accessibile localmente
- [ ] Comando Power ON/OFF funziona
- [ ] Dashboard accessibile via Tailscale
- [ ] Accesso da mobile OK
- [ ] Password cambiata

### Test Finale
```cmd
scripts\windows\check_system.bat
```

Tutti i check dovrebbero essere OK.

---

## 🆘 Problemi Comuni

### Python non trovato

Reinstalla Python spuntando "Add to PATH".

### Display non risponde
```cmd
# Verifica IP corretto
ping 192.168.1.100

# Verifica MDC abilitato sul display
```

### Port 5000 occupata
```cmd
netstat -ano | findstr :5000
taskkill /F /PID [numero_pid]
```

### Tailscale non connette
```cmd
net stop Tailscale
net start Tailscale
```

---

## 📚 Prossimi Passi

- Leggi [CONFIGURATION.md](CONFIGURATION.md) per configurazione dettagliata
- Consulta [API.md](API.md) per integrazioni
- Vedi [TROUBLESHOOTING.md](TROUBLESHOOTING.md) per problemi

---

**Setup completato! 🎉**

