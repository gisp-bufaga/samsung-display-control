"""
Dashboard Agent per samsung-display-control
Comunica con dashboard centralizzata per controllo remoto

Requisiti:
- aiohttp
- psutil  
- python-dotenv
"""

import asyncio
import aiohttp
import json
import os
import socket
import time
import psutil
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carica variabili d'ambiente
from dotenv import load_dotenv
load_dotenv()


class DashboardAgent:
    """Agent che comunica con la dashboard centralizzata"""
    
    def __init__(self):
        self.dashboard_url = os.getenv('DASHBOARD_URL', 'http://localhost:3000')
        self.device_id = os.getenv('DEVICE_ID', socket.gethostname())
        self.api_key = os.getenv('DASHBOARD_API_KEY')
        self.poll_interval = int(os.getenv('AGENT_POLL_INTERVAL', '30'))
        self.retry_attempts = int(os.getenv('AGENT_RETRY_ATTEMPTS', '3'))
        
        self.registered = False
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Verifica configurazione
        if not self.api_key:
            raise ValueError("DASHBOARD_API_KEY non configurata in .env")
        
        logger.info(f"Agent inizializzato per device: {self.device_id}")
        logger.info(f"Dashboard URL: {self.dashboard_url}")
    
    async def start(self):
        """Avvia l'agent"""
        logger.info("🚀 Avvio Dashboard Agent...")
        
        # Crea sessione HTTP
        self.session = aiohttp.ClientSession(
            headers={'X-API-Key': self.api_key},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        try:
            # Registrazione iniziale
            await self.register()
            
            # Loop principale
            await self.run_loop()
            
        except KeyboardInterrupt:
            logger.info("⚠️  Interrupt ricevuto, chiusura...")
        except Exception as e:
            logger.error(f"❌ Errore fatale: {e}")
        finally:
            await self.cleanup()
    
    async def register(self) -> bool:
        """Registra questo device con la dashboard"""
        logger.info("📝 Tentativo registrazione con dashboard...")
        
        for attempt in range(self.retry_attempts):
            try:
                data = {
                    "device_id": self.device_id,
                    "hostname": socket.gethostname(),
                    "tailscale_ip": self._get_tailscale_ip(),
                    "capabilities": [
                        "samsung_magicinfo",
                        "screenshot",
                        "logs",
                        "system_info",
                        "reboot"
                    ]
                }
                
                async with self.session.post(
                    f"{self.dashboard_url}/api/devices/register",
                    json=data
                ) as resp:
                    if resp.status == 200:
                        config = await resp.json()
                        self.poll_interval = config.get("poll_interval", self.poll_interval)
                        self.registered = True
                        logger.info(f"✅ Registrato con successo!")
                        logger.info(f"   Poll interval: {self.poll_interval}s")
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"❌ Registrazione fallita ({resp.status}): {error}")
                        
            except Exception as e:
                logger.error(f"❌ Errore registrazione (tentativo {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(5)
        
        return False
    
    async def run_loop(self):
        """Loop principale - heartbeat e controllo comandi"""
        logger.info("🔄 Loop principale attivo")
        
        while True:
            try:
                # Invia heartbeat
                await self.send_heartbeat()
                
                # Attendi prossimo ciclo
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"❌ Errore nel loop: {e}")
                await asyncio.sleep(10)  # Attendi prima di riprovare
    
    async def send_heartbeat(self):
        """Invia heartbeat con status del sistema"""
        try:
            # Raccogli status
            status = await self._collect_status()
            
            # Invia a dashboard
            async with self.session.post(
                f"{self.dashboard_url}/api/devices/heartbeat",
                json={
                    "device_id": self.device_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": status
                }
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    
                    # Check comandi in attesa
                    if result.get("commands_pending", 0) > 0:
                        logger.info(f"📨 {result['commands_pending']} comandi in coda")
                        await self._fetch_and_execute_commands()
                        
                elif resp.status == 401 or resp.status == 403:
                    logger.error("❌ API key non valida - riavvia agent con key corretta")
                    raise ValueError("Invalid API key")
                else:
                    logger.warning(f"⚠️  Heartbeat fallito: {resp.status}")
                    
        except Exception as e:
            logger.error(f"❌ Errore heartbeat: {e}")
    
    async def _collect_status(self) -> Dict[str, Any]:
        """Raccoglie informazioni di sistema e Samsung display"""
        
        # System metrics
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime = int(time.time() - psutil.boot_time())
        
        # Samsung display status
        samsung_status = await self._get_samsung_status()
        
        # Services status
        services = {
            "fastapi": await self._check_service_status("app"),
            "content_player": "unknown"  # Implementa se hai content player
        }
        
        return {
            "online": True,
            "cpu_usage": cpu,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "uptime": uptime,
            "samsung_display": samsung_status,
            "services": services,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_samsung_status(self) -> Dict[str, Any]:
        """Ottiene status del display Samsung tramite API locale"""
        try:
            # Chiama l'API FastAPI locale (porta 8000 di default)
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/api/status") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "connected": data.get("connected", False),
                            "power": data.get("power_status", "unknown"),
                            "input": data.get("input_source", "unknown"),
                            "volume": data.get("volume", 0)
                        }
        except Exception as e:
            logger.warning(f"⚠️  Impossibile ottenere status Samsung: {e}")
        
        return {
            "connected": False,
            "power": "unknown",
            "input": "unknown",
            "volume": 0
        }
    
    async def _check_service_status(self, service_name: str) -> str:
        """Verifica status di un servizio Docker"""
        try:
            # Check se container è in running
            import subprocess
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={service_name}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and "Up" in result.stdout:
                return "running"
            else:
                return "stopped"
                
        except Exception as e:
            logger.debug(f"Check service {service_name} failed: {e}")
            return "unknown"
    
    async def _fetch_and_execute_commands(self):
        """Recupera ed esegue comandi dalla dashboard"""
        try:
            async with self.session.get(
                f"{self.dashboard_url}/api/commands",
                params={"device_id": self.device_id}
            ) as resp:
                if resp.status == 200:
                    commands = await resp.json()
                    
                    for cmd in commands:
                        logger.info(f"🎯 Esecuzione comando: {cmd['type']}")
                        result = await self._execute_command(cmd)
                        await self._send_command_result(cmd["command_id"], result)
                        
        except Exception as e:
            logger.error(f"❌ Errore fetch commands: {e}")
    
    async def _execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue un comando localmente"""
        cmd_type = command["type"]
        params = command.get("params", {})
        start_time = time.time()
        
        try:
            # Power control
            if cmd_type == "samsung_power":
                return await self._samsung_power(params)
            
            # Input source
            elif cmd_type == "samsung_input":
                return await self._samsung_input(params)
            
            # Volume
            elif cmd_type == "samsung_volume":
                return await self._samsung_volume(params)
            
            # Screenshot
            elif cmd_type == "screenshot":
                return await self._take_screenshot()
            
            # System reboot
            elif cmd_type == "system_reboot":
                return await self._system_reboot(params)
            
            # Get logs
            elif cmd_type == "get_logs":
                return await self._get_logs(params)
            
            else:
                return {
                    "status": "error",
                    "message": f"Comando sconosciuto: {cmd_type}"
                }
                
        except Exception as e:
            logger.error(f"❌ Errore esecuzione comando: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        finally:
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"⏱️  Comando eseguito in {execution_time}ms")
    
    async def _samsung_power(self, params: Dict) -> Dict:
        """Controlla power del display Samsung"""
        action = params.get("action")  # "on" o "off"
        
        async with aiohttp.ClientSession() as session:
            endpoint = f"http://localhost:8000/api/power/{action}"
            async with session.post(endpoint) as resp:
                if resp.status == 200:
                    return {
                        "status": "success",
                        "action": action,
                        "message": f"Display {action}"
                    }
                else:
                    error = await resp.text()
                    return {
                        "status": "error",
                        "message": error
                    }
    
    async def _samsung_input(self, params: Dict) -> Dict:
        """Cambia input source del display"""
        source = params.get("source")  # "HDMI1", "HDMI2", etc.
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/input",
                json={"source": source}
            ) as resp:
                if resp.status == 200:
                    return {
                        "status": "success",
                        "source": source
                    }
                else:
                    error = await resp.text()
                    return {
                        "status": "error",
                        "message": error
                    }
    
    async def _samsung_volume(self, params: Dict) -> Dict:
        """Imposta volume del display"""
        volume = params.get("volume", 50)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/volume",
                json={"volume": volume}
            ) as resp:
                if resp.status == 200:
                    return {
                        "status": "success",
                        "volume": volume
                    }
                else:
                    return {
                        "status": "error",
                        "message": await resp.text()
                    }
    
    async def _take_screenshot(self) -> Dict:
        """Cattura screenshot del display (se implementato)"""
        # TODO: Implementa cattura screenshot
        return {
            "status": "error",
            "message": "Screenshot non ancora implementato"
        }
    
    async def _system_reboot(self, params: Dict) -> Dict:
        """Riavvia il sistema"""
        delay = params.get("delay", 10)  # secondi
        
        logger.warning(f"⚠️  Sistema si riavvierà tra {delay} secondi")
        
        # Schedule reboot
        asyncio.create_task(self._delayed_reboot(delay))
        
        return {
            "status": "success",
            "message": f"Reboot schedulato tra {delay}s"
        }
    
    async def _delayed_reboot(self, delay: int):
        """Reboot con delay"""
        await asyncio.sleep(delay)
        import subprocess
        subprocess.run(["sudo", "reboot"])
    
    async def _get_logs(self, params: Dict) -> Dict:
        """Ottiene ultimi log del sistema"""
        lines = params.get("lines", 100)
        
        try:
            import subprocess
            result = subprocess.run(
                ["docker-compose", "logs", "--tail", str(lines)],
                capture_output=True,
                text=True,
                cwd="/app"  # Adatta al tuo path
            )
            
            return {
                "status": "success",
                "logs": result.stdout[-10000:]  # Max 10KB
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _send_command_result(self, command_id: str, result: Dict):
        """Invia risultato comando alla dashboard"""
        try:
            async with self.session.post(
                f"{self.dashboard_url}/api/commands/{command_id}/result",
                json={
                    "status": result.get("status"),
                    "result": result,
                    "executed_at": datetime.utcnow().isoformat()
                }
            ) as resp:
                if resp.status == 200:
                    logger.info(f"✅ Risultato comando {command_id} inviato")
                else:
                    logger.warning(f"⚠️  Invio risultato fallito: {resp.status}")
                    
        except Exception as e:
            logger.error(f"❌ Errore invio risultato: {e}")
    
    def _get_tailscale_ip(self) -> Optional[str]:
        """Ottiene IP Tailscale del device"""
        try:
            import subprocess
            result = subprocess.run(
                ["tailscale", "ip", "-4"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.debug(f"Tailscale IP non disponibile: {e}")
        
        return None
    
    async def cleanup(self):
        """Cleanup risorse"""
        logger.info("🧹 Cleanup...")
        
        if self.session:
            await self.session.close()
        
        logger.info("👋 Agent terminato")


async def main():
    """Entry point"""
    agent = DashboardAgent()
    await agent.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Arrivederci!")
