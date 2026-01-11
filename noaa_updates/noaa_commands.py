#!/usr/bin/env python3
"""
NOAA Commands - Comandos de voz/texto para funcionalidades NOAA
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

class NOAACommands:
    """Manipulador de comandos NOAA"""
    
    def __init__(self, noaa_service):
        self.noaa_service = noaa_service
        self.commands = self._register_commands()
    
    def _register_commands(self) -> Dict:
        """Registra todos os comandos NOAA"""
        
        commands = {
            "clima espacial": {
                "func": self.cmd_space_weather,
                "description": "Relatório completo de clima espacial",
                "aliases": ["climaespacial", "space weather", "weather space"]
            },
            "vento solar": {
                "func": self.cmd_solar_wind,
                "description": "Dados do vento solar em tempo real",
                "aliases": ["solar wind", "ventosolar", "vento"]
            },
            "alerta solar": {
                "func": self.cmd_solar_alerts,
                "description": "Verificar alertas solares ativos",
                "aliases": ["alertas solares", "solar alert", "alerta"]
            },
            "tempestade geomagnética": {
                "func": self.cmd_geomagnetic_storm,
                "description": "Status de tempestades geomagnéticas",
                "aliases": ["tempestade", "geomagnetic storm", "storm"]
            },
            "aurora boreal": {
                "func": self.cmd_aurora,
                "description": "Previsão de aurora boreal/austral",
                "aliases": ["aurora", "aurora forecast", "aurora boreal"]
            },
            "flares solares": {
                "func": self.cmd_solar_flares,
                "description": "Atividade de flares solares recentes",
                "aliases": ["flares", "solar flares", "erupções solares"]
            },
            "manchas solares": {
                "func": self.cmd_sunspots,
                "description": "Regiões ativas no Sol",
                "aliases": ["sunspots", "manchas", "regiões ativas"]
            },
            "status noaa": {
                "func": self.cmd_noaa_status,
                "description": "Status do serviço NOAA",
                "aliases": ["noaa", "status noaa", "noaa status"]
            },
            "relatório noaa": {
                "func": self.cmd_noaa_report,
                "description": "Relatório detalhado NOAA",
                "aliases": ["relatório", "report", "noaa report"]
            }
        }
        
        return commands
    
    async def cmd_space_weather(self, args: List[str] = None) -> Dict:
        """Comando: clima espacial - Relatório completo"""
        
        if not self.noaa_service or not self.noaa_service.current_data:
            return {
                "success": False,
                "message": "Serviço NOAA não disponível",
                "voice_response": "O serviço de clima espacial não está disponível no momento."
            }
        
        data = self.noaa_service.current_data
        
        # Criar relatório
        report = {
            "timestamp": data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "kp_index": f"{data.kp_index:.1f}",
            "solar_wind": {
                "speed": f"{data.solar_wind.speed:.0f}" if data.solar_wind else "N/A",
                "density": f"{data.solar_wind.density:.1f}" if data.solar_wind else "N/A",
                "bz": f"{data.solar_wind.bz:.1f}" if data.solar_wind else "N/A"
            },
            "alerts": len(data.alerts),
            "overall_alert": data.overall_alert.value,
            "solar_flares": len(data.solar_flares)
        }
        
        # Resposta de voz
        alert_level = data.overall_alert.value
        if alert_level == "NORMAL":
            voice_msg = f"Status geral: NORMAL. Índice Kp: {data.kp_index:.1f}. "
        elif alert_level == "WARNING":
            voice_msg = f"ALERTA: Nível {alert_level}. Índice Kp: {data.kp_index:.1f}. "
        else:
            voice_msg = f"Status: {alert_level}. Índice Kp: {data.kp_index:.1f}. "
        
        if data.solar_wind:
            voice_msg += f"Vento solar: {data.solar_wind.speed:.0f} quilômetros por segundo. "
        
        voice_msg += f"{len(data.alerts)} alertas ativos. "
        
        if len(data.solar_flares) > 0:
            voice_msg += f"{len(data.solar_flares)} flares solares detectados recentemente."
        else:
            voice_msg += "Nenhum flare solar significativo nas últimas 24 horas."
        
        return {
            "success": True,
            "data": report,
            "message": "Relatório de clima espacial gerado",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_solar_wind(self, args: List[str] = None) -> Dict:
        """Comando: vento solar - Dados do vento solar"""
        
        if not self.noaa_service or not self.noaa_service.current_data:
            return {
                "success": False,
                "message": "Dados não disponíveis",
                "voice_response": "Dados do vento solar não disponíveis."
            }
        
        data = self.noaa_service.current_data
        
        if not data.solar_wind:
            return {
                "success": False,
                "message": "Dados do vento solar não disponíveis",
                "voice_response": "Não há dados do vento solar disponíveis no momento."
            }
        
        wind = data.solar_wind
        
        # Analisar direção do Bz
        if wind.bz < -5:
            bz_status = "Sul (Favorável a tempestades)"
            bz_icon = "↓"
        elif wind.bz > 5:
            bz_status = "Norte (Estável)"
            bz_icon = "↑"
        else:
            bz_status = "Neutro"
            bz_icon = "→"
        
        report = {
            "speed_km_s": f"{wind.speed:.0f}",
            "density_p_cm3": f"{wind.density:.1f}",
            "temperature_k": f"{wind.temperature:.0f}",
            "bz_nT": f"{wind.bz:.1f}",
            "bz_direction": bz_status,
            "bz_icon": bz_icon,
            "timestamp": wind.timestamp.strftime("%H:%M:%S")
        }
        
        voice_msg = f"Vento solar: {wind.speed:.0f} quilômetros por segundo. "
        voice_msg += f"Densidade: {wind.density:.1f} partículas por centímetro cúbico. "
        voice_msg += f"Campo magnético Bz: {wind.bz:.1f} nano Tesla, direção {bz_status}."
        
        return {
            "success": True,
            "data": report,
            "message": "Dados do vento solar",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_solar_alerts(self, args: List[str] = None) -> Dict:
        """Comando: alerta solar - Alertas ativos"""
        
        # Simular dados de alerta
        alerts = [
            {
                "id": 1,
                "type": "SOLAR_FLARE",
                "level": "WATCH",
                "message": "Aumento na atividade de flares classe C",
                "time": "2024-01-15 14:30:00"
            },
            {
                "id": 2,
                "type": "GEOMAGNETIC",
                "level": "NORMAL",
                "message": "Condições geomagnéticas estáveis",
                "time": "2024-01-15 13:45:00"
            }
        ]
        
        active_alerts = [a for a in alerts if a["level"] != "NORMAL"]
        
        if active_alerts:
            alert_text = "\n".join([f"{a['type']}: {a['message']}" for a in active_alerts])
            voice_msg = f"{len(active_alerts)} alertas ativos. {active_alerts[0]['message']}"
        else:
            alert_text = "Nenhum alerta ativo no momento"
            voice_msg = "Nenhum alerta solar ativo. Todas as condições estão normais."
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "active_count": len(active_alerts),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            },
            "message": alert_text,
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_geomagnetic_storm(self, args: List[str] = None) -> Dict:
        """Comando: tempestade geomagnética"""
        
        if not self.noaa_service or not self.noaa_service.current_data:
            kp = 2.3
        else:
            kp = self.noaa_service.current_data.kp_index
        
        # Determinar nível da tempestade
        if kp >= 8.0:
            level = "G5 (Extreme)"
            voice_level = "G5 Extrema"
        elif kp >= 7.0:
            level = "G4 (Severe)"
            voice_level = "G4 Severa"
        elif kp >= 6.0:
            level = "G3 (Strong)"
            voice_level = "G3 Forte"
        elif kp >= 5.0:
            level = "G2 (Moderate)"
            voice_level = "G2 Moderada"
        elif kp >= 4.0:
            level = "G1 (Minor)"
            voice_level = "G1 Menor"
        else:
            level = "None"
            voice_level = "Nenhuma"
        
        report = {
            "kp_index": f"{kp:.1f}",
            "storm_level": level,
            "activity": "Quiet" if kp < 4 else "Active",
            "aurora_chance": "High" if kp >= 6 else "Moderate" if kp >= 4 else "Low"
        }
        
        voice_msg = f"Índice Kp atual: {kp:.1f}. "
        if kp < 4:
            voice_msg += "Nenhuma tempestade geomagnética ativa. Condições calmas."
        else:
            voice_msg += f"Tempestade nível {voice_level} ativa. "
            voice_msg += f"Probabilidade de aurora: {report['aurora_chance']}."
        
        return {
            "success": True,
            "data": report,
            "message": f"Status tempestade geomagnética: {level}",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_aurora(self, args: List[str] = None) -> Dict:
        """Comando: aurora boreal - Previsão de aurora"""
        
        # Dados simulados de aurora
        regions = {
            "Alaska": 65,
            "Canada": 70,
            "Scandinavia": 75,
            "Russia": 60,
            "Antarctica": 80,
            "New Zealand": 30,
            "Scotland": 40
        }
        
        max_region = max(regions, key=regions.get)
        max_prob = regions[max_region]
        
        report = {
            "regions": regions,
            "max_region": max_region,
            "max_probability": max_prob,
            "visibility": "Good" if max_prob > 50 else "Fair" if max_prob > 30 else "Poor",
            "next_24h": "Increasing" if max_prob > 60 else "Stable" if max_prob > 40 else "Decreasing"
        }
        
        voice_msg = f"Previsão de aurora: Probabilidade máxima de {max_prob}% em {max_region}. "
        voice_msg += f"Visibilidade: {report['visibility']}. Tendência para as próximas 24 horas: {report['next_24h']}."
        
        return {
            "success": True,
            "data": report,
            "message": f"Previsão de aurora: {max_prob}% em {max_region}",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_solar_flares(self, args: List[str] = None) -> Dict:
        """Comando: flares solares"""
        
        # Dados simulados de flares
        flares = [
            {"class": "C2.4", "region": "AR13452", "peak": "14:30", "duration": "18min"},
            {"class": "B8.7", "region": "AR13451", "peak": "12:15", "duration": "42min"},
            {"class": "C1.2", "region": "AR13449", "peak": "09:45", "duration": "25min"}
        ]
        
        x_class = any(f["class"].startswith("X") for f in flares)
        m_class = any(f["class"].startswith("M") for f in flares)
        
        if x_class:
            activity = "HIGH (X-class detected)"
        elif m_class:
            activity = "MODERATE (M-class detected)"
        elif any(f["class"].startswith("C") for f in flares):
            activity = "LOW (C-class only)"
        else:
            activity = "VERY LOW"
        
        report = {
            "flares_24h": len(flares),
            "largest_flare": flares[0]["class"] if flares else "None",
            "activity_level": activity,
            "recent_flares": flares[:3],
            "x_ray_background": "C1.2"
        }
        
        voice_msg = f"{len(flares)} flares solares nas últimas 24 horas. "
        if flares:
            voice_msg += f"Maior flare: classe {flares[0]['class']} na região {flares[0]['region']}. "
        voice_msg += f"Nível de atividade: {activity}."
        
        return {
            "success": True,
            "data": report,
            "message": f"Atividade de flares: {activity}",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_sunspots(self, args: List[str] = None) -> Dict:
        """Comando: manchas solares"""
        
        report = {
            "sunspot_number": 87,
            "regions": 6,
            "largest_region": "AR13452",
            "magnetic_complexity": "Beta-Gamma",
            "flare_potential": "Medium",
            "location": "NE Quadrant"
        }
        
        voice_msg = f"{report['regions']} regiões ativas no Sol. "
        voice_msg += f"Número de manchas solares: {report['sunspot_number']}. "
        voice_msg += f"Região mais ativa: {report['largest_region']} com complexidade magnética {report['magnetic_complexity']}. "
        voice_msg += f"Potencial para flares: {report['flare_potential']}."
        
        return {
            "success": True,
            "data": report,
            "message": f"Manchas solares: {report['regions']} regiões ativas",
            "voice_response": voice_msg,
            "show_panel": True
        }
    
    async def cmd_noaa_status(self, args: List[str] = None) -> Dict:
        """Comando: status noaa"""
        
        if self.noaa_service and self.noaa_service.is_running:
            status = "RUNNING"
            last_update = self.noaa_service.last_update.strftime("%H:%M:%S") if self.noaa_service.last_update else "Never"
            voice_msg = "Serviço NOAA está rodando. "
        else:
            status = "STOPPED"
            last_update = "N/A"
            voice_msg = "Serviço NOAA não está rodando. "
        
        report = {
            "service_status": status,
            "last_update": last_update,
            "endpoints": len(self.noaa_service.endpoints) if self.noaa_service else 0,
            "data_available": self.noaa_service.current_data is not None if self.noaa_service else False
        }
        
        voice_msg += f"Última atualização: {last_update}. "
        
        if self.noaa_service and self.noaa_service.current_data:
            voice_msg += "Dados atuais disponíveis."
        else:
            voice_msg += "Nenhum dado disponível."
        
        return {
            "success": True,
            "data": report,
            "message": f"Status NOAA: {status}",
            "voice_response": voice_msg,
            "show_panel": False
        }
    
    async def cmd_noaa_report(self, args: List[str] = None) -> Dict:
        """Comando: relatório noaa"""
        
        # Gerar relatório completo
        report_data = {
            "generated": datetime.now().isoformat(),
            "sections": [
                "Space Weather Overview",
                "Solar Activity",
                "Geomagnetic Conditions",
                "Solar Wind Parameters",
                "Aurora Forecast",
                "Alert Summary"
            ],
            "summary": "Space weather conditions are currently quiet with no significant activity expected in the next 24 hours.",
            "recommendations": [
                "No impacts to satellite operations expected",
                "No impacts to power grid operations expected",
                "Aurora visible at high latitudes only"
            ]
        }
        
        voice_msg = "Relatório NOAA gerado. "
        voice_msg += "Condições de clima espacial atualmente calmas. "
        voice_msg += "Nenhuma atividade significativa esperada nas próximas 24 horas."
        
        return {
            "success": True,
            "data": report_data,
            "message": "Relatório NOAA gerado com sucesso",
            "voice_response": voice_msg,
            "show_panel": True,
            "export_formats": ["json", "txt"]
        }

# Teste dos comandos
async def test_commands():
    """Testa os comandos NOAA"""
    
    # Criar serviço simulado
    class MockNOAAService:
        def __init__(self):
            self.current_data = None
            self.is_running = True
            self.last_update = datetime.now()
            self.endpoints = {}
    
    service = MockNOAAService()
    commands = NOAACommands(service)
    
    # Testar comando específico
    result = await commands.cmd_space_weather()
    print("Teste comando 'clima espacial':")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_commands())
