# 🖥️ Samsung Display Control System

Sistema completo di controllo remoto per Samsung Signage Display con dashboard web, scheduling automatico, watchdog e notifiche.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Caratteristiche

- 🌐 **Controllo Remoto Sicuro** - Accesso via Tailscale VPN da qualsiasi luogo
- 📊 **Dashboard Web Responsive** - Interfaccia moderna con aggiornamenti real-time
- ⏰ **Scheduling Automatico** - Programmazione accensione/spegnimento per giorni e orari
- 🔄 **Watchdog Intelligente** - Recovery automatico in caso di problemi
- 🔔 **Notifiche** - Alert via Telegram o Email per eventi critici
- 📈 **Monitoring Sistema** - CPU, RAM, Uptime, Xibo Player status
- 📝 **Logging Completo** - Tracciamento di tutte le operazioni
- 🔌 **Gestione Sorgenti** - Cambio input (HDMI, DisplayPort, DVI)
- 🛡️ **Sicurezza** - Autenticazione, rate limiting, audit log

## 📸 Screenshot

![Dashboard](https://via.placeholder.com/800x450.png?text=Dashboard+Screenshot)
*Dashboard principale con status real-time*

## 🚀 Quick Start

### Prerequisiti

- Windows 10/11
- Python 3.8 o superiore
- Display Samsung con MDC abilitato
- Account Tailscale (gratuito)

### Installazione Rapida

1. **Clona la repository**
```cmd
   git clone https://github.com/gisp-bufaga/samsung-display-control.git
   cd samsung-display-control
```

2. **Esegui il wizard di setup**
```cmd
   scripts\windows\setup_wizard.bat
```

3. **Avvia il sistema**
```cmd
   scripts\windows\start.bat
```

4. **Accedi alla dashboard**
   - Locale: http://localhost:5000
   - Remoto: http://[TAILSCALE_IP]:5000
   - Login: `admin` / `admin123` (cambia subito!)

## 📖 Documentazione

- [📘 Guida Setup Completa](docs/SETUP.md)
- [🔧 Configurazione](docs/CONFIGURATION.md)
- [🐛 Troubleshooting](docs/TROUBLESHOOTING.md)
- [🔌 API Documentation](docs/API.md)

## 🎯 Funzionalità Principali

### Dashboard Web

- **Display Status**: Power, Source, Error count, Last check
- **System Info**: CPU, Memory, Uptime, Xibo status
- **Schedule Info**: Status orari programmati
- **Quick Controls**: ON/OFF, cambio sorgente
- **Configuration**: Modifica impostazioni da interfaccia
- **Logs Viewer**: Visualizzazione log in tempo reale

### Scheduling

Programma accensione/spegnimento automatici:
```json
{
  "schedule": {
    "enabled": true,
    "power_on": "08:00",
    "power_off": "20:00",
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
    "source_on_startup": "hdmi1"
  }
}
```

### Watchdog

Controllo automatico ogni 5 minuti:
- Verifica connettività display
- Rileva display spento quando dovrebbe essere acceso
- Tenta recovery automatico (power cycle)
- Invia alert dopo 3 tentativi falliti

### Notifiche

Alert su eventi importanti:
- ✅ Accensione/spegnimento schedulato
- ⚠️ Display non raggiungibile
- ❌ Errori critici

Supporto Telegram e Email.

## 🛠️ Installazione Dettagliata

### 1. Installazione Python

1. Scarica da [python.org](https://www.python.org/downloads/)
2. Durante installazione, spunta **"Add Python to PATH"**
3. Verifica:
```cmd
   python --version
```

### 2. Installazione Tailscale

1. Scarica da [tailscale.com](https://tailscale.com/download/windows)
2. Installa e fai login
3. Annota l'IP Tailscale:
```cmd
   tailscale ip -4
```

### 3. Configurazione Display

1. Assegna IP statico al display (es: 192.168.1.100)
2. Abilita MDC via Network nelle impostazioni display
3. Verifica connessione:
```cmd
   ping 192.168.1.100
```

### 4. Installazione Dipendenze
```cmd
cd samsung-display-control
pip install -r requirements.txt
```

### 5. Configurazione

1. Copia il file di esempio:
```cmd
   copy config\config.example.json config\config.json
```

2. Modifica `config\config.json` con l'IP del tuo display

3. Cambia la password default (vedi [CONFIGURATION.md](docs/CONFIGURATION.md))

### 6. Avvio

**Test manuale:**
```cmd
python src\display_system.py
```

**Avvio automatico:**
```cmd
scripts\windows\install_service.bat
```

## 📱 Accesso Mobile

1. Installa Tailscale su smartphone:
   - [Android](https://play.google.com/store/apps/details?id=com.tailscale.ipn)
   - [iOS](https://apps.apple.com/app/tailscale/id1470499037)

2. Login con stesso account

3. Apri browser e vai a: `http://[TAILSCALE_IP]:5000`

4. (Opzionale) Aggiungi shortcut alla home screen

## 🔧 Script Disponibili

| Script | Descrizione |
|--------|-------------|
| `start.bat` | Avvia il sistema |
| `stop.bat` | Ferma il sistema |
| `restart.bat` | Riavvia il sistema |
| `check_system.bat` | Verifica stato completo |
| `backup.bat` | Backup configurazione |
| `cleanup.bat` | Pulizia log |
| `test_display.bat` | Test connessione display |
| `view_logs.bat` | Log in tempo reale |
| `emergency_recovery.bat` | Recovery di emergenza |
| `quick_commands.bat` | Menu comandi rapidi |
| `setup_wizard.bat` | Setup guidato |
| `update_password.bat` | Cambio password |
| `install_service.bat` | Installa come servizio Windows |
| `uninstall_service.bat` | Rimuove servizio |

## 📊 Requisiti Sistema

### Hardware Minimo

- CPU: Intel Celeron o equivalente
- RAM: 2 GB
- Storage: 10 GB liberi
- Network: 100 Mbps

### Consumo Risorse

- CPU: ~3%
- RAM: ~100 MB
- Network: < 100 MB/mese

## 🔐 Sicurezza

- ✅ Autenticazione obbligatoria
- ✅ Password hash SHA-256
- ✅ Rate limiting API
- ✅ Connessione crittografata (Tailscale)
- ✅ Audit log di tutte le operazioni
- ✅ Session timeout configurabile

**Cambia immediatamente la password default!**

## 🐛 Troubleshooting

### Display non risponde
```cmd
# Test connessione
ping 192.168.1.100

# Test porta MDC
telnet 192.168.1.100 1515

# Recovery automatico
scripts\windows\emergency_recovery.bat
```

### Server non si avvia
```cmd
# Verifica porta occupata
netstat -ano | findstr :5000

# Visualizza log
scripts\windows\view_logs.bat
```

Vedi [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) per più dettagli.

## 🤝 Contributing

Contributi benvenuti! Per favore:

1. Fai fork della repository
2. Crea un branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## 📝 Changelog

Vedi [CHANGELOG.md](CHANGELOG.md) per la lista completa delle modifiche.

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT - vedi il file [LICENSE](LICENSE) per i dettagli.

## 🙏 Ringraziamenti

- [vgavro/samsung-mdc](https://github.com/vgavro/samsung-mdc) - Libreria Python per Samsung MDC
- [Tailscale](https://tailscale.com/) - VPN mesh network
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Socket.IO](https://socket.io/) - Real-time communication

## 📧 Supporto

- 📖 [Documentazione](docs/)
- 🐛 [Issue Tracker](https://github.com/gisp-bufaga/samsung-display-control/issues)
- 💬 [Discussions](https://github.com/gisp-bufaga/samsung-display-control/discussions)

## 🗺️ Roadmap

- [ ] Multi-display support
- [ ] Central management dashboard
- [ ] Mobile app nativa
- [ ] Docker support
- [ ] Linux support
- [ ] Cloud deployment option
- [ ] Advanced analytics
- [ ] Content management integration

## ⭐ Star History

Se questo progetto ti è utile, lascia una stella! ⭐

---

**Fatto con ❤️ per semplificare la gestione dei display Samsung**
