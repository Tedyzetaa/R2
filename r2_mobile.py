import flet as ft

def main(page: ft.Page):
    # --- CONFIGURAÇÃO ATMOSFÉRICA ---
    page.title = "R2 // LINK NEURAL"  # Mais moderno, menos militar
    page.bgcolor = "#050508" 
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK
    
    # Cores do Espectro de Fóton
    GLACIAL_BLUE = "#00E5FF"
    DEEP_CYAN = "#004040"
    DIAMOND_WHITE = "#E0F7FA"

    # --- COMPONENTES VISUAIS ---

    # 1. O NÚCLEO (Singularidade Fractal)
    core_orbe = ft.Container(
        # Mantemos o radar, mas agora parece um "coração" digital pulsando
        content=ft.Icon("radio_button_checked", color=GLACIAL_BLUE, size=80), # Ícone mais limpo
        alignment=ft.alignment.center,
        width=150,
        height=150,
        shape=ft.BoxShape.CIRCLE,
        border=ft.border.all(1, GLACIAL_BLUE),
        shadow=ft.BoxShadow(spread_radius=2, blur_radius=20, color=GLACIAL_BLUE),
    )

    # 2. CONSOLE DE DADOS
    chat_display = ft.Column(
        scroll=ft.ScrollMode.ALWAYS,
        expand=True,
        spacing=10
    )

    def send_command(e):
        if not user_input.value: return
        
        chat_display.controls.append(
            ft.Text(
                f"› TEDDY: {user_input.value.upper()}", 
                size=12,
                color=DIAMOND_WHITE, 
                font_family="monospace"
            )
        )
        
        # Resposta do Sistema (Simulada no front, o backend processa o real)
        chat_display.controls.append(
            ft.Container(
                content=ft.Text(
                    "› R2: Deixa comigo...",  # Mudança de tom aqui!
                    size=12, 
                    color=GLACIAL_BLUE,
                    font_family="monospace"
                ),
                padding=ft.padding.only(left=10),
                border=ft.border.only(left=ft.BorderSide(2, GLACIAL_BLUE))
            )
        )
        
        user_input.value = ""
        page.update()

    user_input = ft.TextField(
        label="Digite algo para a R2...", # Mais convidadivo
        label_style=ft.TextStyle(color=DEEP_CYAN, size=10, font_family="monospace"),
        border_color=DEEP_CYAN,
        focused_border_color=GLACIAL_BLUE,
        text_style=ft.TextStyle(color=GLACIAL_BLUE, font_family="monospace"),
        expand=True,
        height=45,
        on_submit=send_command
    )

    # --- LAYOUT HOLOGRÁFICO (PT-BR) ---
    
    page.add(
        ft.Column([
            # Barra de Status
            # Barra de Status (Menos técnica, mais status de "rede social")
            ft.Row([
                ft.Text("ONLINE", color="green", size=10, font_family="monospace", weight="bold"),
                ft.Text("VIBE: ESTÁVEL", color=DIAMOND_WHITE, size=10, font_family="monospace"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Singularidade
            ft.Container(content=core_orbe, padding=20, alignment=ft.alignment.center),
            
            # Painel de Dados
            ft.Container(
                content=chat_display,
                expand=True,
                padding=15,
                bgcolor="#05FFFFFF", 
                border=ft.border.all(0.5, DEEP_CYAN),
                border_radius=10,
            ),
            
            # Área de Input
            ft.Container(
                content=ft.Row([
                    user_input,
                    ft.IconButton(
                        "send", 
                        icon_color=GLACIAL_BLUE,
                        on_click=send_command
                    )
                ]),
                padding=ft.padding.only(top=10)
            )
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)