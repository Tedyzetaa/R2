#!/usr/bin/env python3
"""
Sistema de animações Sci-Fi avançadas
Funciona SEM numpy - usando apenas math e tkinter
"""

import math
import time
import random
from typing import List, Tuple, Dict, Optional
import customtkinter as ctk

class SciFiAnimations:
    """Sistema completo de animações Sci-Fi"""
    
    def __init__(self):
        self.animations = {}
        self.active_effects = []
        self.performance_mode = "balanced"  # balanced, performance, quality
        
    def create_wave_animation(self, canvas, width=200, height=200, center_x=100, center_y=100):
        """Cria animação de onda complexa sem numpy"""
        
        class WaveAnimation:
            def __init__(self, canvas, width, height, center_x, center_y):
                self.canvas = canvas
                self.width = width
                self.height = height
                self.center_x = center_x
                self.center_y = center_y
                self.radius = min(width, height) // 2.5
                
                # Parâmetros da animação
                self.angle = 0
                self.amplitude = 15
                self.frequency = 0.1
                self.speed = 0.05
                self.wave_points = []
                
                # Cores Sci-Fi
                self.colors = {
                    'primary': '#00ffff',
                    'secondary': '#0099ff',
                    'glow': '#ffffff',
                    'core': '#0066ff',
                    'pulse': '#ff00ff'
                }
                
                # Componentes da onda
                self.wave_components = [
                    {'freq': 5, 'amp': 0.5, 'phase': 0},
                    {'freq': 3, 'amp': 0.3, 'phase': math.pi/2},
                    {'freq': 7, 'amp': 0.2, 'phase': math.pi/4}
                ]
                
                # IDs dos elementos gráficos
                self.graphic_ids = []
                
                # Criar elementos iniciais
                self._create_base_elements()
                
            def _create_base_elements(self):
                """Cria elementos base da animação"""
                
                # Círculos concêntricos
                colors = [self.colors['primary'], self.colors['secondary'], self.colors['core']]
                
                for i, color in enumerate(colors):
                    r = self.radius - (i * 20)
                    
                    # Círculo principal
                    circle = self.canvas.create_oval(
                        self.center_x - r, self.center_y - r,
                        self.center_x + r, self.center_y + r,
                        outline=color,
                        width=2
                    )
                    self.graphic_ids.append(circle)
                    
                    # Efeito de brilho
                    for glow_size in [3, 6]:
                        glow = self.canvas.create_oval(
                            self.center_x - r - glow_size, self.center_y - r - glow_size,
                            self.center_x + r + glow_size, self.center_y + r + glow_size,
                            outline=color,
                            width=1,
                            stipple="gray25"
                        )
                        self.graphic_ids.append(glow)
                
                # Partículas flutuantes
                self._create_particles()
                
            def _create_particles(self):
                """Cria partículas flutuantes"""
                self.particles = []
                num_particles = 20
                
                for _ in range(num_particles):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(self.radius * 0.7, self.radius * 1.3)
                    speed = random.uniform(0.005, 0.02)
                    
                    particle = {
                        'angle': angle,
                        'distance': distance,
                        'speed': speed,
                        'size': random.randint(1, 3),
                        'color': random.choice(['#00ffff', '#0099ff', '#ff00ff', '#ffff00']),
                        'id': None
                    }
                    
                    # Criar partícula visual
                    x = self.center_x + distance * math.cos(angle)
                    y = self.center_y + distance * math.sin(angle)
                    
                    particle_id = self.canvas.create_oval(
                        x - particle['size'], y - particle['size'],
                        x + particle['size'], y + particle['size'],
                        fill=particle['color'],
                        outline=""
                    )
                    
                    particle['id'] = particle_id
                    self.particles.append(particle)
            
            def _calculate_wave_point(self, angle):
                """Calcula um ponto na onda usando math puro"""
                radius_offset = 0
                
                for comp in self.wave_components:
                    # Usando math.sin em vez de numpy.sin
                    wave_value = math.sin(
                        comp['freq'] * self.frequency * angle + comp['phase']
                    )
                    radius_offset += comp['amp'] * self.amplitude * wave_value
                
                return radius_offset
            
            def update(self):
                """Atualiza a animação"""
                # Atualizar ângulo
                self.angle += self.speed
                
                # Gerar novos pontos da onda
                points = []
                num_points = 80  # Reduzido para performance, era 100
                
                for i in range(num_points):
                    # Calcular ângulo do ponto
                    point_angle = (2 * math.pi * i / num_points) + self.angle
                    
                    # Calcular raio com onda
                    radius_offset = self._calculate_wave_point(point_angle)
                    r = self.radius + radius_offset
                    
                    # Converter para coordenadas
                    x = self.center_x + r * math.cos(point_angle)
                    y = self.center_y + r * math.sin(point_angle)
                    points.extend([x, y])
                
                # Remover onda antiga se existir
                if hasattr(self, 'wave_line'):
                    self.canvas.delete(self.wave_line)
                if hasattr(self, 'wave_glow'):
                    self.canvas.delete(self.wave_glow)
                
                # Desenhar nova onda
                self.wave_line = self.canvas.create_line(
                    *points,
                    fill=self.colors['primary'],
                    width=3,
                    smooth=True,
                    tags='wave'
                )
                
                # Efeito de brilho
                self.wave_glow = self.canvas.create_line(
                    *points,
                    fill=self.colors['glow'],
                    width=1,
                    smooth=True,
                    tags='wave_glow'
                )
                
                # Atualizar partículas
                self._update_particles()
                
                # Efeito de pulso nos círculos
                self._pulse_circles()
                
                # Agendar próxima atualização
                self.canvas.after(30, self.update)
            
            def _update_particles(self):
                """Atualiza posição das partículas"""
                for particle in self.particles:
                    # Atualizar ângulo
                    particle['angle'] += particle['speed']
                    
                    # Calcular nova posição
                    x = self.center_x + particle['distance'] * math.cos(particle['angle'])
                    y = self.center_y + particle['distance'] * math.sin(particle['angle'])
                    
                    # Mover partícula
                    self.canvas.coords(
                        particle['id'],
                        x - particle['size'], y - particle['size'],
                        x + particle['size'], y + particle['size']
                    )
                    
                    # Efeito de piscar aleatório
                    if random.random() < 0.1:
                        current_color = self.canvas.itemcget(particle['id'], 'fill')
                        new_color = self.colors['pulse'] if current_color != self.colors['pulse'] else particle['color']
                        self.canvas.itemconfig(particle['id'], fill=new_color)
            
            def _pulse_circles(self):
                """Efeito de pulsação nos círculos"""
                pulse_factor = 1 + 0.1 * math.sin(self.angle * 3)
                
                for i, circle_id in enumerate(self.graphic_ids[:3]):  # Apenas os 3 círculos principais
                    try:
                        # Obter cor atual
                        current_color = self.canvas.itemcget(circle_id, 'outline')
                        
                        # Ajustar brilho
                        new_color = self._adjust_color_brightness(current_color, pulse_factor)
                        self.canvas.itemconfig(circle_id, outline=new_color)
                    except:
                        pass
            
            def _adjust_color_brightness(self, color_hex, factor):
                """Ajusta brilho de uma cor hex"""
                try:
                    # Converter hex para RGB
                    color_hex = color_hex.lstrip('#')
                    if len(color_hex) == 6:
                        r = int(color_hex[0:2], 16)
                        g = int(color_hex[2:4], 16)
                        b = int(color_hex[4:6], 16)
                        
                        # Aplicar fator
                        r = min(255, max(0, int(r * factor)))
                        g = min(255, max(0, int(g * factor)))
                        b = min(255, max(0, int(b * factor)))
                        
                        # Converter de volta para hex
                        return f'#{r:02x}{g:02x}{b:02x}'
                except:
                    pass
                return color_hex
            
            def start(self):
                """Inicia a animação"""
                self.update()
            
            def stop(self):
                """Para a animação"""
                if hasattr(self, 'wave_line'):
                    self.canvas.delete(self.wave_line)
                if hasattr(self, 'wave_glow'):
                    self.canvas.delete(self.wave_glow)
                
                for particle in self.particles:
                    self.canvas.delete(particle['id'])
                
                for graphic_id in self.graphic_ids:
                    self.canvas.delete(graphic_id)
        
        return WaveAnimation(canvas, width, height, center_x, center_y)
    
    def create_data_stream(self, parent, width=300, height=200):
        """Cria efeito de fluxo de dados (Matrix style)"""
        
        class DataStream:
            def __init__(self, parent, width, height):
                self.parent = parent
                self.width = width
                self.height = height
                
                # Canvas para o efeito
                self.canvas = ctk.CTkCanvas(
                    parent,
                    width=width,
                    height=height,
                    bg='#001111',
                    highlightthickness=0
                )
                self.canvas.pack()
                
                # Parâmetros do efeito
                self.chars = "01"
                self.drops = []
                self.speed = 2
                self.font_size = 12
                
                # Inicializar gotas
                self._init_drops()
                
            def _init_drops(self):
                """Inicializa as gotas do efeito Matrix"""
                num_columns = self.width // self.font_size
                self.drops = [0] * num_columns
            
            def update(self):
                """Atualiza o efeito Matrix"""
                # Limpar canvas
                self.canvas.delete("all")
                
                # Desenhar cada coluna
                for i in range(len(self.drops)):
                    # Cor da gota (verde com variação)
                    green_intensity = random.randint(100, 255)
                    color = f'#00{green_intensity:02x}00'
                    
                    # Desenhar caracteres na coluna
                    y = self.drops[i] * self.font_size
                    for j in range(3):  # Desenhar 3 caracteres por coluna
                        if y - j * self.font_size >= 0:
                            char = random.choice(self.chars)
                            char_y = y - j * self.font_size
                            
                            # Intensidade decrescente
                            intensity = 255 - j * 80
                            if intensity < 50:
                                intensity = 50
                            
                            char_color = f'#00{intensity:02x}00'
                            
                            self.canvas.create_text(
                                i * self.font_size, char_y,
                                text=char,
                                fill=char_color,
                                font=('Courier New', self.font_size, 'bold'),
                                anchor='nw'
                            )
                    
                    # Mover gota para baixo
                    self.drops[i] += 1
                    
                    # Resetar gota se sair da tela
                    if self.drops[i] * self.font_size > self.height + 100:
                        self.drops[i] = random.randint(-10, 0)
                
                # Agendar próxima atualização
                self.canvas.after(50, self.update)
            
            def start(self):
                """Inicia o efeito"""
                self.update()
            
            def stop(self):
                """Para o efeito"""
                self.canvas.delete("all")
        
        return DataStream(parent, width, height)
    
    def create_radar_sweep(self, canvas, center_x, center_y, radius=100):
        """Cria efeito de varredura de radar"""
        
        class RadarSweep:
            def __init__(self, canvas, center_x, center_y, radius):
                self.canvas = canvas
                self.center_x = center_x
                self.center_y = center_y
                self.radius = radius
                self.angle = 0
                self.speed = 0.05
                
                # Criar elementos do radar
                self._create_radar_elements()
            
            def _create_radar_elements(self):
                """Cria elementos visuais do radar"""
                # Círculo externo
                self.canvas.create_oval(
                    self.center_x - self.radius, self.center_y - self.radius,
                    self.center_x + self.radius, self.center_y + self.radius,
                    outline='#00ff00',
                    width=2
                )
                
                # Círculos concêntricos
                for i in range(1, 4):
                    r = self.radius * i / 4
                    self.canvas.create_oval(
                        self.center_x - r, self.center_y - r,
                        self.center_x + r, self.center_y + r,
                        outline='#00aa00',
                        width=1,
                        dash=(2, 4)
                    )
                
                # Linhas cruzadas
                self.canvas.create_line(
                    self.center_x, self.center_y - self.radius,
                    self.center_x, self.center_y + self.radius,
                    fill='#00aa00',
                    width=1
                )
                self.canvas.create_line(
                    self.center_x - self.radius, self.center_y,
                    self.center_x + self.radius, self.center_y,
                    fill='#00aa00',
                    width=1
                )
                
                # Linha de varredura
                self.sweep_line = self.canvas.create_line(
                    self.center_x, self.center_y,
                    self.center_x + self.radius, self.center_y,
                    fill='#00ff00',
                    width=2,
                    arrow='last'
                )
            
            def update(self):
                """Atualiza a varredura do radar"""
                # Calcular ponto final da linha
                end_x = self.center_x + self.radius * math.cos(self.angle)
                end_y = self.center_y + self.radius * math.sin(self.angle)
                
                # Atualizar linha de varredura
                self.canvas.coords(
                    self.sweep_line,
                    self.center_x, self.center_y,
                    end_x, end_y
                )
                
                # Adicionar ponto de eco aleatório
                if random.random() < 0.1:
                    echo_dist = random.uniform(0.3, 0.9) * self.radius
                    echo_x = self.center_x + echo_dist * math.cos(self.angle)
                    echo_y = self.center_y + echo_dist * math.sin(self.angle)
                    
                    echo = self.canvas.create_oval(
                        echo_x - 3, echo_y - 3,
                        echo_x + 3, echo_y + 3,
                        fill='#ffff00',
                        outline=''
                    )
                    
                    # Remover eco após um tempo
                    self.canvas.after(1000, lambda e=echo: self.canvas.delete(e))
                
                # Atualizar ângulo
                self.angle += self.speed
                if self.angle > 2 * math.pi:
                    self.angle = 0
                
                # Agendar próxima atualização
                self.canvas.after(30, self.update)
            
            def start(self):
                """Inicia a varredura"""
                self.update()
            
            def stop(self):
                """Para a varredura"""
                self.canvas.delete(self.sweep_line)
        
        return RadarSweep(canvas, center_x, center_y, radius)
    
    def create_particle_system(self, canvas, width, height, num_particles=100):
        """Cria sistema de partículas"""
        
        class ParticleSystem:
            def __init__(self, canvas, width, height, num_particles):
                self.canvas = canvas
                self.width = width
                self.height = height
                self.num_particles = num_particles
                self.particles = []
                
                # Cores Sci-Fi
                self.colors = ['#00ffff', '#0099ff', '#ff00ff', '#ffff00', '#00ff00']
                
                # Inicializar partículas
                self._init_particles()
            
            def _init_particles(self):
                """Inicializa partículas"""
                for _ in range(self.num_particles):
                    particle = {
                        'x': random.uniform(0, self.width),
                        'y': random.uniform(0, self.height),
                        'vx': random.uniform(-1, 1),
                        'vy': random.uniform(-1, 1),
                        'size': random.uniform(1, 3),
                        'color': random.choice(self.colors),
                        'life': random.uniform(0.5, 2.0),
                        'max_life': random.uniform(2, 5),
                        'id': None
                    }
                    
                    # Criar partícula visual
                    particle['id'] = self.canvas.create_oval(
                        particle['x'] - particle['size'],
                        particle['y'] - particle['size'],
                        particle['x'] + particle['size'],
                        particle['y'] + particle['size'],
                        fill=particle['color'],
                        outline=''
                    )
                    
                    self.particles.append(particle)
            
            def update(self):
                """Atualiza sistema de partículas"""
                for particle in self.particles[:]:  # Copia para permitir remoção
                    # Atualizar posição
                    particle['x'] += particle['vx']
                    particle['y'] += particle['vy']
                    
                    # Reduzir vida
                    particle['life'] -= 0.02
                    
                    # Verificar limites
                    if (particle['x'] < 0 or particle['x'] > self.width or
                        particle['y'] < 0 or particle['y'] > self.height or
                        particle['life'] <= 0):
                        
                        # Remover partícula morta
                        self.canvas.delete(particle['id'])
                        self.particles.remove(particle)
                        
                        # Adicionar nova partícula
                        self._add_new_particle()
                    else:
                        # Atualizar posição visual
                        self.canvas.coords(
                            particle['id'],
                            particle['x'] - particle['size'],
                            particle['y'] - particle['size'],
                            particle['x'] + particle['size'],
                            particle['y'] + particle['size']
                        )
                        
                        # Efeito de fade out
                        if particle['life'] < particle['max_life'] * 0.3:
                            alpha = int(255 * (particle['life'] / (particle['max_life'] * 0.3)))
                            color = particle['color'].lstrip('#')
                            r = int(color[0:2], 16)
                            g = int(color[2:4], 16)
                            b = int(color[4:6], 16)
                            faded_color = f'#{r:02x}{g:02x}{b:02x}'
                            self.canvas.itemconfig(particle['id'], fill=faded_color)
                
                # Agendar próxima atualização
                self.canvas.after(40, self.update)
            
            def _add_new_particle(self):
                """Adiciona nova partícula"""
                particle = {
                    'x': random.uniform(0, self.width),
                    'y': random.uniform(0, self.height),
                    'vx': random.uniform(-1, 1),
                    'vy': random.uniform(-1, 1),
                    'size': random.uniform(1, 3),
                    'color': random.choice(self.colors),
                    'life': random.uniform(0.5, 2.0),
                    'max_life': random.uniform(2, 5),
                    'id': None
                }
                
                particle['id'] = self.canvas.create_oval(
                    particle['x'] - particle['size'],
                    particle['y'] - particle['size'],
                    particle['x'] + particle['size'],
                    particle['y'] + particle['size'],
                    fill=particle['color'],
                    outline=''
                )
                
                self.particles.append(particle)
            
            def start(self):
                """Inicia o sistema de partículas"""
                self.update()
            
            def stop(self):
                """Para o sistema de partículas"""
                for particle in self.particles:
                    self.canvas.delete(particle['id'])
                self.particles.clear()
        
        return ParticleSystem(canvas, width, height, num_particles)