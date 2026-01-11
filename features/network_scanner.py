import subprocess
import re

class NetworkScanner:
    def scan(self):
        try:
            # Executa o comando ARP do Windows
            # O flag CREATE_NO_WINDOW esconde a tela preta do cmd
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            output = subprocess.check_output("arp -a", startupinfo=startupinfo).decode('latin-1')
            
            dispositivos = []
            # Regex para encontrar IPs (ex: 192.168.1.5)
            pattern = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F-]{17})")
            
            for line in output.split('\n'):
                match = pattern.search(line)
                if match:
                    ip = match.group(1)
                    mac = match.group(2)
                    # Filtra IPs de broadcast (255 ou 224)
                    if not ip.startswith("224") and not ip.endswith("255"):
                        dispositivos.append(f"📡 IP: {ip} | MAC: {mac}")

            if dispositivos:
                lista = "\n".join(dispositivos)
                return f"📶 **DISPOSITIVOS NA REDE:**\n\n{lista}"
            else:
                return "⚠️ Nenhum dispositivo identificado no scanner ARP."

        except Exception as e:
            return f"❌ Erro no Scanner: {e}"