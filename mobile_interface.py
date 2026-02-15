import flet as ft
import requests

# CONFIGURAÇÕES DE DESIGN
API_URL = "http://127.0.0.1:8000"
NEON_CYAN = "#00f0ff"
DARK_BG = "#0d1117"
CARD_BG = "#161b22"
USER_BUBBLE = "#005f73"
R2_BUBBLE = "#21262d"

def main(page: ft.Page):
    page.title = "R2 TACTICAL OS"
    page.bgcolor = DARK_BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    
    chat_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=15)
    url_input = ft.TextField(
        label="UPLINK URL", 
        value=API_URL, 
        border_color=NEON_CYAN, 
        height=45, 
        text_size=12
    )

    def add_message(text, user=True):
        alignment = ft.MainAxisAlignment.END if user else ft.MainAxisAlignment.START
        color = USER_BUBBLE if user else R2_BUBBLE
        label = "SENHOR" if user else "R2"
        
        chat_container.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column([
                            ft.Text(label, size=9, color=NEON_CYAN, weight="bold"),
                            ft.Text(text, color="white", size=14),
                        ], spacing=2),
                        padding=12,
                        bgcolor=color,
                        border_radius=ft.border_radius.only(
                            top_left=15, top_right=15, 
                            bottom_left=0 if user else 15, 
                            bottom_right=15 if user else 0
                        ),
                    )
                ],
                alignment=alignment
            )
        )
        page.update()

    def send_action(cmd_text):
        if not cmd_text: return
        host = url_input.value.strip().rstrip("/")
        add_message(cmd_text, user=True)
        
        try:
            res = requests.post(f"{host}/receber_ordem", json={"comando": cmd_text}, timeout=60)
            if res.status_code == 200:
                add_message(res.json().get("resposta", "Sem resposta do núcleo."), user=False)
            else:
                add_message(f"ERRO DE COMUNICAÇÃO: {res.status_code}", user=False)
        except Exception as e:
            add_message(f"UPLINK DOWN: Verifique o servidor e o Ngrok.", user=False)

    # --- ABA 1: CHAT ---
    chat_tab = ft.Container(
        content=ft.Column([
            ft.Container(content=chat_container, expand=True, padding=20),
            ft.Container(
                content=ft.Row([
                    entry := ft.TextField(
                        hint_text="Digite sua ordem...", 
                        expand=True, 
                        border_radius=25, 
                        bgcolor="#010409",
                        on_submit=lambda _: (send_action(entry.value), setattr(entry, 'value', ""), page.update())
                    ),
                    ft.FloatingActionButton(
                        icon="send",
                        bgcolor=NEON_CYAN, 
                        on_click=lambda _: (send_action(entry.value), setattr(entry, 'value', ""), page.update())
                    )
                ]),
                padding=10, bgcolor=CARD_BG
            )
        ]),
        expand=True
    )

    # --- ABA 2: REMOTO ---
    def quick_btn(title, cmd, icon_name, color=NEON_CYAN):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon_name, color=color, size=30),
                ft.Text(title, size=11, weight="bold")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            width=100, height=100, bgcolor=CARD_BG, border_radius=15,
            on_click=lambda _: send_action(cmd),
            # CORREÇÃO CRÍTICA: Alinhamento numérico direto (x=0, y=0 é o centro)
            alignment=ft.Alignment(0, 0),
        )

    remote_tab = ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("SISTEMA DE ACESSO RÁPIDO", color=NEON_CYAN, weight="bold"),
            ft.Row([
                quick_btn("VOL +", "Aumentar volume", "volume_up"),
                quick_btn("VOL -", "Baixar volume", "volume_down"),
                quick_btn("MUDO", "Mutar áudio", "volume_off"),
            ], wrap=True, spacing=10),
            ft.Row([
                quick_btn("PRINT", "Tirar print", "camera_alt", "yellow"),
                quick_btn("LOCK", "Bloquear PC", "lock", "orange"),
                quick_btn("OFF", "Desligar PC", "power_settings_new", "red"),
            ], wrap=True, spacing=10)
        ], scroll=ft.ScrollMode.AUTO)
    )

    # --- ABA 3: CONFIG ---
    settings_tab = ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("CONFIGURAÇÕES DE UPLINK", color=NEON_CYAN, weight="bold"),
            url_input,
            ft.Divider(color="#333333"),
            ft.Text("STATUS: OPERACIONAL", color="green", size=12),
        ])
    )

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="CHAT", icon="chat_bubble_outline", content=chat_tab),
            ft.Tab(text="REMOTO", icon="settings_remote", content=remote_tab),
            ft.Tab(text="CONFIG", icon="settings", content=settings_tab),
        ],
        expand=1
    )

    page.add(
        ft.Container(
            content=ft.Row([
                ft.Icon("terminal", color=NEON_CYAN),
                ft.Text("R2 TACTICAL TERMINAL", weight="bold", color="white")
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=10, bgcolor=CARD_BG
        ),
        tabs
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)