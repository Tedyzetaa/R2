"""
Weather Panel component for R2 Assistant V2.1
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any
import threading

class WeatherPanel(ctk.CTkFrame):
    """Weather information panel"""
    
    def __init__(self, parent, weather_service=None, theme=None, refresh_callback: Optional[Callable] = None):
        super().__init__(parent)
        
        self.weather_service = weather_service
        self.theme = theme
        self.refresh_callback = refresh_callback
        self.current_weather = None
        
        # Colors
        if theme:
            self.colors = theme.colors
        else:
            self.colors = {
                'bg_dark': '#0a0a12',
                'bg_panel': '#0d0d1a',
                'primary': '#00ffff',
                'text': '#ffffff',
                'text_dim': '#8888aa',
                'info': '#0099ff',
                'success': '#00ff88'
            }
        
        self._setup_ui()
        
        # Load default location
        self.location_var.set("São Paulo, BR")
    
    def _setup_ui(self):
        """Setup weather panel UI"""
        self.configure(
            fg_color=self.colors['bg_panel'],
            corner_radius=8,
            border_width=1,
            border_color=self.colors['primary']
        )
        
        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            title_frame,
            text="🌤️ WEATHER",
            font=("Consolas", 14, "bold"),
            text_color=self.colors['primary']
        ).pack(side="left")
        
        # Last update
        self.update_label = ctk.CTkLabel(
            title_frame,
            text="",
            font=("Consolas", 9),
            text_color=self.colors['text_dim']
        )
        self.update_label.pack(side="right")
        
        # Location input
        location_frame = ctk.CTkFrame(self, fg_color="transparent")
        location_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            location_frame,
            text="Location:",
            font=("Consolas", 10),
            text_color=self.colors['text_dim']
        ).pack(side="left", padx=(0, 5))
        
        self.location_var = ctk.StringVar()
        self.location_entry = ctk.CTkEntry(
            location_frame,
            textvariable=self.location_var,
            font=("Consolas", 11),
            height=30
        )
        self.location_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        refresh_btn = ctk.CTkButton(
            location_frame,
            text="↻",
            width=30,
            height=30,
            font=("Consolas", 12),
            fg_color=self.colors['info'],
            command=self._refresh_weather
        )
        refresh_btn.pack(side="right")
        
        # Weather display
        self.weather_display = ctk.CTkTextbox(
            self,
            height=180,
            font=("Consolas", 10),
            text_color=self.colors['text'],
            fg_color=self.colors['bg_dark'],
            border_width=0,
            wrap="word"
        )
        self.weather_display.pack(fill="both", expand=True, padx=10, pady=5)
        self.weather_display.configure(state="disabled")
        
        # Initial message
        self._update_display("Weather information will appear here.\nEnter location and click refresh.")
    
    def _refresh_weather(self):
        """Refresh weather data"""
        location = self.location_var.get().strip()
        if not location:
            self._update_display("Please enter a location.")
            return
        
        self._update_display(f"Fetching weather for {location}...")
        
        # Call callback if provided
        if self.refresh_callback:
            self.refresh_callback(location)
        
        # Fetch weather if service available
        if self.weather_service:
            threading.Thread(target=self._fetch_weather, args=(location,), daemon=True).start()
    
    def _fetch_weather(self, location: str):
        """Fetch weather data"""
        try:
            import asyncio
            
            async def get_weather():
                return await self.weather_service.get_weather(location)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            weather_data = loop.run_until_complete(get_weather())
            loop.close()
            
            if weather_data:
                self.current_weather = weather_data
                self._update_weather_display(weather_data)
            else:
                self._update_display("Could not fetch weather data.")
                
        except Exception as e:
            self._update_display(f"Error fetching weather: {str(e)}")
    
    def _update_weather_display(self, weather_data):
        """Update display with weather data"""
        from datetime import datetime
        
        current = weather_data.current
        
        display_text = f"""
📍 {weather_data.location}, {weather_data.country}
🕐 Last updated: {weather_data.fetched_at.strftime('%H:%M')}

🌡️ Temperature: {current.temperature:.1f}°C
💨 Feels like: {current.feels_like:.1f}°C
💧 Humidity: {current.humidity}%
🌬️ Wind: {current.wind_speed} m/s
📊 Pressure: {current.pressure} hPa
☁️  Conditions: {current.description.title()}

🌅 Sunrise: {current.sunrise.strftime('%H:%M')}
🌇 Sunset: {current.sunset.strftime('%H:%M')}
"""
        
        self._update_display(display_text)
        self.update_label.configure(text=f"Updated: {weather_data.fetched_at.strftime('%H:%M')}")
    
    def _update_display(self, text: str):
        """Update display text"""
        self.weather_display.configure(state="normal")
        self.weather_display.delete("1.0", "end")
        self.weather_display.insert("1.0", text)
        self.weather_display.configure(state="disabled")
    
    def set_weather_service(self, weather_service):
        """Set weather service"""
        self.weather_service = weather_service
    
    def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """Get current weather data"""
        return self.current_weather.to_dict() if self.current_weather else None
    
    def refresh(self):
        """Refresh weather data"""
        self._refresh_weather()