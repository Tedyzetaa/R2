# network_map.py corrigido
"""
Network map visualization component
"""

import customtkinter as ctk
import random
import math
import time
from typing import Dict, List, Optional, Tuple, Any  # Adicionei Any
from dataclasses import dataclass

@dataclass
class NetworkNode:
    """Network node representation"""
    id: str
    x: float
    y: float
    label: str
    type: str  # 'server', 'client', 'router', 'sensor'
    status: str  # 'online', 'offline', 'warning'
    data_rate: float
    connections: List[str]

class NetworkMap(ctk.CTkCanvas):
    """Network map visualization"""
    
    def __init__(self, parent, width: int = 300, height: int = 200, 
                 theme=None, **kwargs):
        self.width = width
        self.height = height
        
        super().__init__(
            parent,
            width=width,
            height=height,
            bg='#0a0a12',
            highlightthickness=0,
            **kwargs
        )
        
        # Colors
        if theme:
            self.colors = theme.colors
        else:
            self.colors = {
                'primary': '#00ffff',
                'secondary': '#0099ff',
                'accent': '#ff00ff',
                'success': '#00ff88',
                'warning': '#ffaa00',
                'danger': '#ff0066',
                'bg_dark': '#0a0a12',
                'text': '#ffffff'
            }
        
        # Node colors by type
        self.node_colors = {
            'server': self.colors['primary'],
            'client': self.colors['secondary'],
            'router': self.colors['accent'],
            'sensor': self.colors['success']
        }
        
        # Node colors by status
        self.status_colors = {
            'online': self.colors['success'],
            'warning': self.colors['warning'],
            'offline': self.colors['danger']
        }
        
        # Network nodes
        self.nodes: Dict[str, NetworkNode] = {}
        self.node_elements: Dict[str, Dict[str, int]] = {}  # canvas element IDs
        self.connection_elements: List[int] = []
        
        # Animation
        self.animation_angle = 0
        self.data_packets: List[Dict[str, Any]] = []
        
        # Create sample network
        self._create_sample_network()
        
        # Start animation
        self._animate()
        
    def _create_sample_network(self):
        """Create a sample network for demonstration"""
        # Create nodes
        nodes_data = [
            NetworkNode(
                id="server_1",
                x=0.5,
                y=0.3,
                label="MAIN SERVER",
                type="server",
                status="online",
                data_rate=1000,
                connections=["router_1", "router_2"]
            ),
            NetworkNode(
                id="router_1",
                x=0.3,
                y=0.6,
                label="ROUTER A",
                type="router",
                status="online",
                data_rate=500,
                connections=["server_1", "client_1", "client_2"]
            ),
            NetworkNode(
                id="router_2",
                x=0.7,
                y=0.6,
                label="ROUTER B",
                type="router",
                status="warning",
                data_rate=300,
                connections=["server_1", "sensor_1", "client_3"]
            ),
            NetworkNode(
                id="client_1",
                x=0.1,
                y=0.8,
                label="CLIENT 1",
                type="client",
                status="online",
                data_rate=100,
                connections=["router_1"]
            ),
            NetworkNode(
                id="client_2",
                x=0.3,
                y=0.9,
                label="CLIENT 2",
                type="client",
                status="online",
                data_rate=80,
                connections=["router_1"]
            ),
            NetworkNode(
                id="client_3",
                x=0.7,
                y=0.9,
                label="CLIENT 3",
                type="client",
                status="offline",
                data_rate=0,
                connections=["router_2"]
            ),
            NetworkNode(
                id="sensor_1",
                x=0.9,
                y=0.8,
                label="SENSOR",
                type="sensor",
                status="online",
                data_rate=50,
                connections=["router_2"]
            )
        ]
        
        for node in nodes_data:
            self.add_node(node)
        
        # Create initial data packets
        for _ in range(5):
            self._create_data_packet()
    
    def add_node(self, node: NetworkNode):
        """Add a node to the network"""
        self.nodes[node.id] = node
        self.node_elements[node.id] = {}
        
        # Draw node
        self._draw_node(node)
        
        # Draw connections
        for connected_id in node.connections:
            if connected_id in self.nodes:
                self._draw_connection(node.id, connected_id)
    
    def _draw_node(self, node: NetworkNode):
        """Draw a network node"""
        # Calculate screen coordinates
        x = node.x * self.width
        y = node.y * self.height
        
        # Node size based on type
        if node.type == 'server':
            size = 20
        elif node.type == 'router':
            size = 16
        else:
            size = 12
        
        # Node color based on type and status
        base_color = self.node_colors.get(node.type, self.colors['primary'])
        status_color = self.status_colors.get(node.status, self.colors['text'])
        
        # Draw node (outer circle)
        outer = self.create_oval(
            x - size, y - size,
            x + size, y + size,
            fill=base_color,
            outline=status_color,
            width=2
        )
        
        # Draw inner circle (status indicator)
        inner_size = size - 4
        inner = self.create_oval(
            x - inner_size, y - inner_size,
            x + inner_size, y + inner_size,
            fill=status_color,
            outline=""
        )
        
        # Draw label
        label = self.create_text(
            x, y + size + 10,
            text=node.label,
            font=("Consolas", 8),
            fill=self.colors['text'],
            justify="center"
        )
        
        # Store element IDs
        self.node_elements[node.id] = {
            'outer': outer,
            'inner': inner,
            'label': label,
            'x': x,
            'y': y,
            'size': size
        }
        
        # Add pulse effect for online nodes
        if node.status == 'online' and node.data_rate > 0:
            self._add_node_pulse(node.id)
    
    def _draw_connection(self, node1_id: str, node2_id: str):
        """Draw connection between two nodes"""
        if node1_id not in self.node_elements or node2_id not in self.node_elements:
            return
        
        node1 = self.node_elements[node1_id]
        node2 = self.node_elements[node2_id]
        
        # Get node statuses
        status1 = self.nodes[node1_id].status
        status2 = self.nodes[node2_id].status
        
        # Connection color based on status
        if status1 == 'online' and status2 == 'online':
            color = self.colors['primary']
            width = 2
        elif 'warning' in [status1, status2]:
            color = self.colors['warning']
            width = 1
        else:
            color = self.colors['text']
            width = 1
        
        # Draw connection line
        connection = self.create_line(
            node1['x'], node1['y'],
            node2['x'], node2['y'],
            fill=color,
            width=width,
            dash=(5, 3) if width == 1 else None
        )
        
        self.connection_elements.append(connection)
        
        # Add data flow animation for active connections
        if status1 == 'online' and status2 == 'online':
            self._add_connection_animation(node1_id, node2_id)
    
    def _add_node_pulse(self, node_id: str):
        """Add pulsing animation to a node"""
        node_elements = self.node_elements[node_id]
        
        def pulse_animation(step: int = 0):
            if node_id not in self.node_elements:
                return
            
            # Calculate pulse size
            pulse_size = node_elements['size'] + 5 + 3 * math.sin(self.animation_angle + step)
            
            # Remove old pulse if exists
            if 'pulse' in node_elements:
                self.delete(node_elements['pulse'])
            
            # Draw new pulse
            pulse = self.create_oval(
                node_elements['x'] - pulse_size,
                node_elements['y'] - pulse_size,
                node_elements['x'] + pulse_size,
                node_elements['y'] + pulse_size,
                outline=self.colors['primary'],
                width=1,
                stipple="gray50"
            )
            
            node_elements['pulse'] = pulse
            
            # Schedule next pulse
            self.after(50, lambda: pulse_animation((step + 1) % 10))
        
        # Start pulse animation
        pulse_animation()
    
    def _add_connection_animation(self, node1_id: str, node2_id: str):
        """Add data flow animation to a connection"""
        node1 = self.node_elements[node1_id]
        node2 = self.node_elements[node2_id]
        
        def create_packet():
            # Create data packet
            packet_id = f"packet_{len(self.data_packets)}"
            
            packet = {
                'id': packet_id,
                'from_node': node1_id,
                'to_node': node2_id,
                'progress': 0.0,
                'element': None,
                'direction': random.choice([-1, 1])  # Random direction
            }
            
            self.data_packets.append(packet)
            
            # Create packet element
            x = node1['x']
            y = node1['y']
            
            packet_element = self.create_oval(
                x - 3, y - 3,
                x + 3, y + 3,
                fill=self.colors['accent'],
                outline=self.colors['primary'],
                width=1
            )
            
            packet['element'] = packet_element
            
            # Remove packet after animation completes
            def remove_packet():
                if packet['element']:
                    self.delete(packet['element'])
                self.data_packets = [p for p in self.data_packets if p['id'] != packet_id]
            
            self.after(3000, remove_packet)
        
        # Create packets periodically
        def schedule_packet():
            create_packet()
            # Schedule next packet
            interval = random.randint(500, 2000)
            self.after(interval, schedule_packet)
        
        schedule_packet()
    
    def _create_data_packet(self):
        """Create a random data packet"""
        if len(self.nodes) < 2:
            return
        
        # Random source and destination
        node_ids = list(self.nodes.keys())
        from_node = random.choice(node_ids)
        to_node = random.choice([n for n in node_ids if n != from_node])
        
        # Only create packets between online nodes
        if (self.nodes[from_node].status == 'online' and 
            self.nodes[to_node].status == 'online'):
            
            packet_id = f"packet_{len(self.data_packets)}"
            
            packet = {
                'id': packet_id,
                'from_node': from_node,
                'to_node': to_node,
                'progress': 0.0,
                'element': None,
                'speed': random.uniform(0.01, 0.03)
            }
            
            self.data_packets.append(packet)
    
    def _animate(self):
        """Main animation loop"""
        # Update animation angle
        self.animation_angle += 0.1
        
        # Update data packets
        self._update_data_packets()
        
        # Update node statuses (random changes for demo)
        if random.random() < 0.01:
            self._randomize_node_status()
        
        # Schedule next frame
        self.after(50, self._animate)
    
    def _update_data_packets(self):
        """Update data packet positions"""
        packets_to_remove = []
        
        for packet in self.data_packets:
            if packet['element']:
                # Remove old element
                self.delete(packet['element'])
            
            # Update progress
            packet['progress'] += packet.get('speed', 0.02)
            
            if packet['progress'] >= 1.0:
                packets_to_remove.append(packet['id'])
                continue
            
            # Calculate position
            from_node = self.node_elements.get(packet['from_node'])
            to_node = self.node_elements.get(packet['to_node'])
            
            if not from_node or not to_node:
                packets_to_remove.append(packet['id'])
                continue
            
            # Interpolate position
            x = from_node['x'] + (to_node['x'] - from_node['x']) * packet['progress']
            y = from_node['y'] + (to_node['y'] - from_node['y']) * packet['progress']
            
            # Create new element
            packet_size = 3 + 2 * math.sin(self.animation_angle * 3)
            
            packet_element = self.create_oval(
                x - packet_size, y - packet_size,
                x + packet_size, y + packet_size,
                fill=self.colors['accent'],
                outline=self.colors['primary'],
                width=1
            )
            
            packet['element'] = packet_element
        
        # Remove completed packets
        self.data_packets = [p for p in self.data_packets if p['id'] not in packets_to_remove]
    
    def _randomize_node_status(self):
        """Randomly change a node's status (for demo)"""
        if not self.nodes:
            return
        
        node_id = random.choice(list(self.nodes.keys()))
        node = self.nodes[node_id]
        
        # Don't change server status
        if node.type == 'server':
            return
        
        # Cycle through statuses
        statuses = ['online', 'warning', 'offline']
        current_index = statuses.index(node.status) if node.status in statuses else 0
        new_index = (current_index + 1) % len(statuses)
        
        node.status = statuses[new_index]
        
        # Update node display
        self._update_node_display(node_id)
    
    def _update_node_display(self, node_id: str):
        """Update a node's display"""
        if node_id not in self.nodes or node_id not in self.node_elements:
            return
        
        node = self.nodes[node_id]
        elements = self.node_elements[node_id]
        
        # Update inner circle color
        status_color = self.status_colors.get(node.status, self.colors['text'])
        self.itemconfig(elements['inner'], fill=status_color)
        
        # Update outer circle outline
        self.itemconfig(elements['outer'], outline=status_color)
        
        # Update or remove pulse effect
        if node.status == 'online' and node.data_rate > 0:
            if 'pulse' not in elements:
                self._add_node_pulse(node_id)
        elif 'pulse' in elements:
            self.delete(elements['pulse'])
            del elements['pulse']
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        total_nodes = len(self.nodes)
        online_nodes = sum(1 for n in self.nodes.values() if n.status == 'online')
        
        # Calculate total connections
        total_connections = 0
        for node in self.nodes.values():
            total_connections += len(node.connections)
        
        # Average data rate
        avg_data_rate = sum(n.data_rate for n in self.nodes.values()) / max(1, total_nodes)
        
        return {
            'total_nodes': total_nodes,
            'online_nodes': online_nodes,
            'offline_nodes': total_nodes - online_nodes,
            'total_connections': total_connections // 2,  # Each connection counted twice
            'active_packets': len(self.data_packets),
            'avg_data_rate': avg_data_rate
        }
    
    def set_node_status(self, node_id: str, status: str):
        """Set a node's status"""
        if node_id in self.nodes:
            self.nodes[node_id].status = status
            self._update_node_display(node_id)