# 🐛 Troubleshooting

Guida alla risoluzione dei problemi comuni.

## 📋 Indice

1. [Problemi Display](#problemi-display)
2. [Problemi Server](#problemi-server)
3. [Problemi Tailscale](#problemi-tailscale)
4. [Problemi Schedule](#problemi-schedule)
5. [Problemi Notifiche](#problemi-notifiche)
6. [Recovery](#recovery)

---

## 🖥️ Problemi Display

### Display Non Risponde

**Sintomi:**
- Status: "unreachable" o "error"
- Comandi non hanno effetto

**Diagnostica:**
```cmd
# 1. Test ping
ping 192.168.1.100

# 2. Test porta MDC
telnet 192.168.1.100 1515

# 3. Test Python
python
>>> from samsung_mdc import MDC
>>> d = MDC('192.168.1.100')
>>> d.get_power_status()
```

**Soluzioni:**

1. **Verifica IP corretto** in `config.json`
2. **Verifica cavo rete** collegato
3. **Verifica MDC abilitato** sul display:
   - Menu → Network → MDC: Enabled
4. **Riavvia display** (fisicamente)
5. **Verifica firewall** Windows non blocca porta 1515

### Display Si Spegne Inaspettatamente

**Cause Possibili:**
- Schedule attivo
- Watchdog sta tentando recovery
- Comando manuale da altro sistema

**Verifica:**
```cmd
# Controlla log
scripts\windows\view_logs.bat

# Cerca eventi power_off
findstr "power_off" logs\display.log
```

### Errore "Cannot connect to display"

**Soluzione:**
```cmd
# 1. Verifica servizio running
scripts\windows\check_system.bat

# 2. Test manuale connessione
python -c "from samsung_mdc import MDC; MDC('192.168.1.100').get_power_status()"

# 3. Recovery
scripts\windows\emergency_recovery.bat
```

---

## 🖧 Problemi Server

### Server Non Si Avvia

**Errore: "Address already in use"**
```cmd
# Trova processo su porta 5000
netstat -ano | findstr :5000

# Kill processo
taskkill /F /PID [PID_NUMBER]

# Riavvia
scripts\windows\start.bat
```

**Errore: "ModuleNotFoundError"**
```cmd
# Reinstalla dipendenze
pip install -r requirements.txt
```

**Errore: "Permission denied"**
```cmd
# Esegui come amministratore
# Tasto destro su cmd → "Esegui come amministratore"
```

### Dashboard Non Carica

**Soluzione:**

1. **Verifica server running:**
```cmd
   tasklist | findstr python
```

2. **Controlla log:**
```cmd
   type logs\display.log
```

3. **Verifica firewall:**
```cmd
   netsh advfirewall firewall show rule name=all | findstr 5000
```

4. **Test connessione locale:**
```cmd
   curl http://localhost:5000
```

### WebSocket Non Funziona

**Sintomi:**
- Status non si aggiorna automaticamente
- Comandi funzionano ma dashboard statica

**Soluzione:**
1. Refresh pagina (Ctrl+F5)
2. Controlla console browser (F12)
3. Verifica log server per errori WebSocket

---

## 🌐 Problemi Tailscale

### Non Riesco a Connettermi Via Tailscale

**Verifica Stato:**
```cmd
tailscale status
```

**Soluzione:**

1. **Riavvia Tailscale:**
```cmd
   net stop Tailscale
   net start Tailscale
```

2. **Verifica IP:**
```cmd
   tailscale ip -4
```

3. **Login di nuovo:**
```cmd
   tailscale login
```

4. **Controlla firewall** non blocca Tailscale

### IP Tailscale Cambiato

**Soluzione:**
- IP Tailscale è stabile e non dovrebbe cambiare
- Se cambia, verifica con `tailscale ip -4`
- Aggiorna bookmark con nuovo IP

### Connessione Lenta

**Cause:**
- Relay server DERP utilizzato
- Connessione diretta fallita

**Verifica:**
```cmd
tailscale netcheck
```

**Soluzione:**
- Verifica firewall permette UDP
- Controlla NAT del router

---

## ⏰ Problemi Schedule

### Schedule Non Funziona

**Verifica Configurazione:**

1. **Schedule abilitato:**
```json
   "schedule": { "enabled": true }
```

2. **Giorni corretti:**
```json
   "days": ["monday", "tuesday", ...]
```

3. **Orari validi:**
```json
   "power_on": "08:00",  // HH:MM formato 24h
   "power_off": "20:00"
```

**Verifica Log:**
```cmd
findstr "scheduled" logs\display.log
```

**Test Manuale:**

Aspetta l'ora schedulata e verifica nel log:
