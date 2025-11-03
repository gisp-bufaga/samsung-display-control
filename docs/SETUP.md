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
