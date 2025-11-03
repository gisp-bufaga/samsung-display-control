"""
Agent che comunica con Dashboard centralizzata
"""
import asyncio
import aiohttp
import json
import psutil
import socket
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DashboardAgent:
    def __init__(self, dashboard_url: str, device_id: str, api_key: str):
        self.dashboard_url = dashboard_url
        self.device_id = device_id
        self.api_key = api_key
        self.poll_interval = 30
        self.registered = False
        
    async def register(self):
        """Registra questo display con la dashboard"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "device_id": self.device_id,
                    "hostname": socket.gethostname(),
                    "tailscale_ip": self._get_tailscale_ip(),
                    "capabilities": [
                        "samsung_magicinfo",
                        "screenshot",
                        "logs",
                        "system_info"
                    ]
                }
                
                async with session.post(
                    f"{self.dashboard_url}/api/register",
                    json=data,
                    headers={"X-API-Key": self.api_key}
                ) as resp:
                    if resp.status == 200:
                        config = await resp.json()
                        self.poll_interval = config.get("poll_interval", 30)
                        self.registered = True
                        logger.info(f"✅ Registrato con dashboard: {config}")
                        return True
        except Exception as e:
            logger.error(f"❌ Errore registrazione: {e}")
            return False
    
    async def send_heartbeat(self):
        """Invia heartbeat con status del sistema"""
        if not self.registered:
            await self.register()
            
        try:
            status = await self._collect_status()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.dashboard_url}/api/heartbeat",
                    json={
                        "device_id": self.device_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": status
                    },
                    headers={"X-API-Key": self.api_key}
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        # Check se ci sono comandi in attesa
                        if result.get("commands_pending", 0) > 0:
                            await self._fetch_and_execute_commands()
        except Exception as e:
            logger.error(f"❌ Errore heartbeat: {e}")
    
    async def _collect_status(self) -> dict:
        """Raccoglie informazioni di sistema"""
        # Importa il tuo controller Samsung esistente
        from app.services.samsung_service import SamsungService
        samsung = SamsungService()
        
        return {
            "online": True,
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "uptime": int(time.time() - psutil.boot_time()),
            "samsung_display": {
                "connected": samsung.is_connected(),
                "power": samsung.get_power_status(),
                "input": samsung.get_input_source(),
                "volume": samsung.get_volume()
            },
            "services": {
                "fastapi": "running",
                "content_player": self._check_content_player()
            }
        }
    
    async def _fetch_and_execute_commands(self):
        """Recupera ed esegue comandi dalla dashboard"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.dashboard_url}/api/commands",
                    params={"device_id": self.device_id},
                    headers={"X-API-Key": self.api_key}
                ) as resp:
                    if resp.status == 200:
                        commands = await resp.json()
                        
                        for cmd in commands:
                            result = await self._execute_command(cmd)
                            await self._send_command_result(cmd["command_id"], result)
        except Exception as e:
            logger.error(f"❌ Errore fetch commands: {e}")
    
    async def _execute_command(self, command: dict) -> dict:
        """Esegue un comando localmente"""
        from app.services.samsung_service import SamsungService
        samsung = SamsungService()
        
        cmd_type = command["type"]
        params = command.get("params", {})
        
        try:
            if cmd_type == "samsung_power":
                action = params.get("action")
                if action == "on":
                    samsung.power_on()
                elif action == "off":
                    samsung.power_off()
                return {"status": "success", "power": action}
                
            elif cmd_type == "samsung_input":
                source = params.get("source")
                samsung.set_input_source(source)
                return {"status": "success", "input": source}
                
            elif cmd_type == "samsung_volume":
                volume = params.get("volume")
                samsung.set_volume(volume)
                return {"status": "success", "volume": volume}
                
            elif cmd_type == "system_reboot":
                # Implementa reboot sicuro
                return {"status": "success", "message": "Reboot scheduled"}
                
            elif cmd_type == "screenshot":
                # Cattura screenshot del display
                screenshot_path = await self._take_screenshot()
                return {"status": "success", "screenshot": screenshot_path}
                
            else:
                return {"status": "error", "message": f"Unknown command: {cmd_type}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _send_command_result(self, command_id: str, result: dict):
        """Invia risultato comando alla dashboard"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.dashboard_url}/api/commands/{command_id}/result",
                    json={
                        "status": result.get("status"),
                        "result": result,
                        "executed_at": datetime.utcnow().isoformat()
                    },
                    headers={"X-API-Key": self.api_key}
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Risultato comando {command_id} inviato")
        except Exception as e:
            logger.error(f"❌ Errore invio risultato: {e}")
    
    def _get_tailscale_ip(self) -> Optional[str]:
        """Ottiene IP Tailscale del device"""
        try:
            # Leggi da tailscale status
            import subprocess
            result = subprocess.run(
                ["tailscale", "ip", "-4"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except:
            return None
    
    async def run(self):
        """Loop principale agent"""
        logger.info(f"🚀 Agent avviato per device {self.device_id}")
        
        # Registrazione iniziale
        await self.register()
        
        # Loop heartbeat
        while True:
            await self.send_heartbeat()
            await asyncio.sleep(self.poll_interval)


# Avvio agent
if __name__ == "__main__":
    agent = DashboardAgent(
        dashboard_url="http://dashboard.your-tailnet.ts.net:3000",
        device_id="display-office-1",
        api_key="your-api-key-here"
    )
    
    asyncio.run(agent.run())
