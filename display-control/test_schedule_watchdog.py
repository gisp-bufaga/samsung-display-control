"""
Test Script per Schedule e Watchdog
====================================

Esegui questo script per testare le funzionalità
SENZA avviare il server completo

Usage:
    python test_schedule_watchdog.py
"""

import sys
import os
import json
from datetime import datetime, timedelta
import time

# Setup path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)

print("="*70)
print("TEST SCHEDULE E WATCHDOG")
print("="*70)
print()

# Load config
config_file = os.path.join(project_root, 'config', 'config.json')
try:
    with open(config_file, 'r') as f:
        CONFIG = json.load(f)
    print(f"✅ Config caricata: {config_file}")
except Exception as e:
    print(f"❌ Errore caricamento config: {e}")
    sys.exit(1)

# Import MDC
try:
    from samsung_mdc import MDC
    print("✅ samsung-mdc disponibile")
    MDC_AVAILABLE = True
except ImportError:
    print("⚠️  samsung-mdc non installato")
    MDC_AVAILABLE = False

print()
print("-"*70)
print("CONFIGURAZIONE CORRENTE")
print("-"*70)

# Display info
display_ip = CONFIG['display']['ip']
print(f"Display IP: {display_ip}")
print(f"Display Name: {CONFIG['display']['name']}")
print()

# Schedule info
print("SCHEDULE:")
print(f"  Enabled: {CONFIG['schedule']['enabled']}")
print(f"  Power ON: {CONFIG['schedule']['power_on']}")
print(f"  Power OFF: {CONFIG['schedule']['power_off']}")
print(f"  Days: {', '.join(CONFIG['schedule']['days'])}")
print(f"  Source on startup: {CONFIG['schedule'].get('source_on_startup', 'hdmi1')}")
print()

# Watchdog info
print("WATCHDOG:")
print(f"  Enabled: {CONFIG['watchdog']['enabled']}")
print(f"  Check interval: {CONFIG['watchdog']['check_interval']}s")
print(f"  Max retry: {CONFIG['watchdog']['max_retry']}")
print()

print("-"*70)
print("TEST 1: Verifica Schedule Attivo")
print("-"*70)

def is_in_schedule():
    """Test function schedule"""
    if not CONFIG['schedule']['enabled']:
        return False
    
    now = datetime.now()
    day_name = now.strftime('%A').lower()
    schedule_days = [d.lower() for d in CONFIG['schedule']['days']]
    
    print(f"Oggi: {day_name}")
    print(f"Giorni schedule: {schedule_days}")
    
    if day_name not in schedule_days:
        print(f"❌ Oggi ({day_name}) NON è in schedule")
        return False
    
    print(f"✅ Oggi ({day_name}) è in schedule")
    
    current_time = now.time()
    on_time = datetime.strptime(CONFIG['schedule']['power_on'], '%H:%M').time()
    off_time = datetime.strptime(CONFIG['schedule']['power_off'], '%H:%M').time()
    
    print(f"Ora corrente: {current_time}")
    print(f"Range schedule: {on_time} - {off_time}")
    
    if on_time <= current_time <= off_time:
        print(f"✅ Ora corrente è IN RANGE schedule")
        print(f"   → Display DOVREBBE essere ACCESO")
        return True
    else:
        print(f"❌ Ora corrente è FUORI RANGE schedule")
        print(f"   → Display DOVREBBE essere SPENTO")
        return False

should_be_on = is_in_schedule()
print()

print("-"*70)
print("TEST 2: Connessione Display")
print("-"*70)

if not MDC_AVAILABLE:
    print("⚠️  Test saltato: samsung-mdc non installato")
    print()
else:
    print(f"Tentativo connessione a {display_ip}...")
    
    try:
        display = MDC(display_ip)
        print("✅ Connessione OK")
        
        try:
            power_status = display.get_power_status()
            print(f"✅ Power status: {power_status}")
            
            # Normalizza status
            if power_status in ['on', 'On', 'ON', '1', 1, True]:
                actual_power = 'on'
            elif power_status in ['off', 'Off', 'OFF', '0', 0, False]:
                actual_power = 'off'
            else:
                actual_power = str(power_status)
            
            print(f"   Status normalizzato: {actual_power}")
            print()
            
            # Confronto con schedule
            print("-"*70)
            print("TEST 3: Verifica Coerenza Schedule")
            print("-"*70)
            
            print(f"Display dovrebbe essere: {'ON' if should_be_on else 'OFF'}")
            print(f"Display effettivamente è: {actual_power.upper()}")
            print()
            
            if should_be_on and actual_power == 'on':
                print("✅ STATO CORRETTO: Display acceso come da schedule")
            elif not should_be_on and actual_power == 'off':
                print("✅ STATO CORRETTO: Display spento come da schedule")
            elif should_be_on and actual_power == 'off':
                print("❌ ERRORE: Display SPENTO ma dovrebbe essere ACCESO")
                print("   → Watchdog dovrebbe rilevare e accendere")
            elif not should_be_on and actual_power == 'on':
                print("⚠️  ATTENZIONE: Display ACCESO ma dovrebbe essere SPENTO")
                print("   → OK se accensione manuale, schedule spegnerà all'ora prevista")
            
        except Exception as e:
            print(f"❌ Errore lettura stato: {e}")
            
    except Exception as e:
        print(f"❌ Connessione FALLITA: {e}")
        print()
        print("Possibili cause:")
        print("  - IP errato in config.json")
        print("  - Display spento fisicamente")
        print("  - Cavo di rete non collegato")
        print("  - MDC non abilitato sul display")
        print("  - Firewall blocca porta 1515")

print()
print("-"*70)
print("TEST 4: Simulazione Prossimo Schedule Event")
print("-"*70)

now = datetime.now()
on_time_str = CONFIG['schedule']['power_on']
off_time_str = CONFIG['schedule']['power_off']

on_time_today = datetime.strptime(
    f"{now.strftime('%Y-%m-%d')} {on_time_str}", 
    '%Y-%m-%d %H:%M'
)
off_time_today = datetime.strptime(
    f"{now.strftime('%Y-%m-%d')} {off_time_str}", 
    '%Y-%m-%d %H:%M'
)

# Trova prossimo event
next_events = []

# Power ON oggi
if on_time_today > now:
    next_events.append(('Power ON', on_time_today))
else:
    # Power ON domani
    on_time_tomorrow = on_time_today + timedelta(days=1)
    next_events.append(('Power ON', on_time_tomorrow))

# Power OFF oggi
if off_time_today > now:
    next_events.append(('Power OFF', off_time_today))
else:
    # Power OFF domani
    off_time_tomorrow = off_time_today + timedelta(days=1)
    next_events.append(('Power OFF', off_time_tomorrow))

# Ordina per tempo
next_events.sort(key=lambda x: x[1])

print("Prossimi eventi schedule:")
for event_name, event_time in next_events[:3]:
    time_until = event_time - now
    hours = int(time_until.total_seconds() // 3600)
    minutes = int((time_until.total_seconds() % 3600) // 60)
    
    print(f"  {event_name}: {event_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"    → tra {hours}h {minutes}m")

print()
print("-"*70)
print("TEST 5: Calcolo Prossimo Watchdog Check")
print("-"*70)

if CONFIG['watchdog']['enabled']:
    check_interval = CONFIG['watchdog']['check_interval']
    print(f"Watchdog check interval: {check_interval}s ({check_interval//60} minuti)")
    print()
    
    if should_be_on and MDC_AVAILABLE:
        print("Al prossimo check (tra max {check_interval}s), watchdog:")
        if actual_power == 'off':
            print("  → Rileverà display spento")
            print("  → Tenterà accensione con force_wake")
            print("  → Imposterà source a", CONFIG['schedule'].get('source_on_startup'))
        elif actual_power == 'on':
            print("  → Verificherà che display sia ancora acceso")
            print("  → Tutto OK, nessuna azione")
        else:
            print(f"  → Stato attuale: {actual_power}")
    else:
        print("Watchdog verificherà connettività display")
else:
    print("⏸️  Watchdog disabilitato in config")

print()
print("="*70)
print("SUGGERIMENTI PER TEST")
print("="*70)
print()

if should_be_on:
    print("💡 Per testare schedule POWER ON:")
    print("   1. Spegni display manualmente")
    print("   2. Aspetta prossimo watchdog check")
    print("   3. Watchdog dovrebbe riaccenderlo")
    print()
    print("   OPPURE")
    print()
    print("   1. Modifica config: power_on = ora corrente + 2 minuti")
    print("   2. Riavvia display_system.py")
    print("   3. Aspetta 2 minuti")
    print("   4. Display dovrebbe accendersi automaticamente")
else:
    print("💡 Per testare schedule POWER OFF:")
    print("   1. Accendi display manualmente")
    print("   2. Modifica config: power_off = ora corrente + 2 minuti")
    print("   3. Riavvia display_system.py")
    print("   4. Aspetta 2 minuti")
    print("   5. Display dovrebbe spegnersi automaticamente")

print()
print("💡 Per testare watchdog recovery:")
print("   1. Assicurati che display dovrebbe essere acceso (schedule)")
print("   2. Spegni display manualmente")
print("   3. Watchdog lo rileverà al prossimo check")
print("   4. Dovrebbe tentare riaccensione")

print()
print("💡 Per test rapidi:")
print("   Modifica temporaneamente in config.json:")
print('   "check_interval": 60  // 1 minuto invece di 5')
print("   (ricorda di ripristinare a 300 dopo i test!)")

print()
print("="*70)
print("TEST COMPLETATO")
print("="*70)