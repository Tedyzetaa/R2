"""
History management system for tracking all system activities
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

class EventType(str, Enum):
    CHAT = "chat"
    VOICE = "voice"
    COMMAND = "command"
    ALERT = "alert"
    SYSTEM = "system"
    TRADE = "trade"
    ERROR = "error"

@dataclass
class HistoryEvent:
    """Represents a single historical event"""
    id: str
    timestamp: float
    event_type: EventType
    data: Dict[str, Any]
    source: str = "system"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def datetime(self) -> datetime:
        """Get datetime object from timestamp"""
        return datetime.fromtimestamp(self.timestamp)
    
    @property
    def formatted_time(self) -> str:
        """Get formatted time string"""
        return self.datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'datetime': self.datetime.isoformat(),
            'event_type': self.event_type.value,
            'data': self.data,
            'source': self.source,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryEvent':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            timestamp=data['timestamp'],
            event_type=EventType(data['event_type']),
            data=data['data'],
            source=data.get('source', 'system'),
            metadata=data.get('metadata', {})
        )

class HistoryManager:
    """Manages system history with persistence and retrieval"""
    
    def __init__(self, max_size: int = 1000, persist_file: Optional[Path] = None):
        self.max_size = max_size
        self.persist_file = persist_file
        self.events: List[HistoryEvent] = []
        self._load_from_file()
    
    def _generate_id(self) -> str:
        """Generate unique event ID"""
        return f"evt_{int(time.time() * 1000)}_{len(self.events)}"
    
    def add_event(self, event_type: EventType, data: Dict[str, Any], 
                  source: str = "system", metadata: Optional[Dict] = None) -> str:
        """Add a new event to history"""
        event = HistoryEvent(
            id=self._generate_id(),
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            source=source,
            metadata=metadata or {}
        )
        
        self.events.append(event)
        
        # Trim history if needed
        if len(self.events) > self.max_size:
            self.events = self.events[-self.max_size:]
        
        # Auto-save if persist file is set
        if self.persist_file:
            self._save_to_file()
        
        return event.id
    
    def add_chat_message(self, role: str, message: str, 
                        metadata: Optional[Dict] = None) -> str:
        """Add chat message to history"""
        return self.add_event(
            event_type=EventType.CHAT,
            data={'role': role, 'message': message},
            source='chat',
            metadata=metadata
        )
    
    def add_voice_command(self, command: str, 
                         confidence: Optional[float] = None) -> str:
        """Add voice command to history"""
        metadata = {'confidence': confidence} if confidence else {}
        return self.add_event(
            event_type=EventType.VOICE,
            data={'command': command},
            source='voice',
            metadata=metadata
        )
    
    def add_system_command(self, command: str, result: str,
                          module: Optional[str] = None) -> str:
        """Add system command to history"""
        metadata = {'module': module} if module else {}
        return self.add_event(
            event_type=EventType.COMMAND,
            data={'command': command, 'result': result},
            source='system',
            metadata=metadata
        )
    
    def add_alert(self, level: str, title: str, message: str,
                 source: str = "system") -> str:
        """Add alert to history"""
        return self.add_event(
            event_type=EventType.ALERT,
            data={'level': level, 'title': title, 'message': message},
            source=source
        )
    
    def add_trade(self, symbol: str, side: str, quantity: float,
                 price: float, result: Dict[str, Any]) -> str:
        """Add trade to history"""
        return self.add_event(
            event_type=EventType.TRADE,
            data={
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'result': result
            },
            source='trading'
        )
    
    def get_events(self, event_type: Optional[EventType] = None,
                  source: Optional[str] = None, limit: int = 100) -> List[HistoryEvent]:
        """Retrieve events with optional filtering"""
        events = self.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if source:
            events = [e for e in events if e.source == source]
        
        return events[-limit:] if limit else events
    
    def get_recent_chat(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent chat messages"""
        chat_events = self.get_events(event_type=EventType.CHAT, limit=limit)
        return [e.data for e in chat_events]
    
    def get_recent_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        alert_events = self.get_events(event_type=EventType.ALERT, limit=limit)
        return [e.data for e in alert_events]
    
    def search_events(self, query: str, 
                     event_types: Optional[List[EventType]] = None) -> List[HistoryEvent]:
        """Search events by content"""
        results = []
        
        for event in self.events:
            if event_types and event.event_type not in event_types:
                continue
            
            # Search in data and metadata
            search_text = json.dumps(event.data) + json.dumps(event.metadata)
            if query.lower() in search_text.lower():
                results.append(event)
        
        return results
    
    def clear(self, event_type: Optional[EventType] = None):
        """Clear history, optionally by event type"""
        if event_type:
            self.events = [e for e in self.events if e.event_type != event_type]
        else:
            self.events.clear()
        
        if self.persist_file:
            self._save_to_file()
    
    def export_to_file(self, filepath: Path, 
                      event_types: Optional[List[EventType]] = None,
                      limit: Optional[int] = None):
        """Export history to JSON file"""
        events_to_export = self.events
        
        if event_types:
            events_to_export = [e for e in events_to_export if e.event_type in event_types]
        
        if limit:
            events_to_export = events_to_export[-limit:]
        
        data = [e.to_dict() for e in events_to_export]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_to_file(self):
        """Save history to persist file"""
        if not self.persist_file:
            return
        
        try:
            data = [e.to_dict() for e in self.events]
            with open(self.persist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving history: {e}")
    
    def _load_from_file(self):
        """Load history from persist file"""
        if not self.persist_file or not self.persist_file.exists():
            return
        
        try:
            with open(self.persist_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.events = [HistoryEvent.from_dict(item) for item in data]
            
            # Trim to max size
            if len(self.events) > self.max_size:
                self.events = self.events[-self.max_size:]
                
        except Exception as e:
            print(f"⚠️ Error loading history: {e}")
            self.events = []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about history"""
        stats = {
            'total_events': len(self.events),
            'events_by_type': {},
            'events_by_source': {},
            'time_range': None
        }
        
        if self.events:
            # Count by type
            for event_type in EventType:
                count = len([e for e in self.events if e.event_type == event_type])
                if count > 0:
                    stats['events_by_type'][event_type.value] = count
            
            # Count by source
            sources = set(e.source for e in self.events)
            for source in sources:
                count = len([e for e in self.events if e.source == source])
                stats['events_by_source'][source] = count
            
            # Time range
            oldest = min(e.timestamp for e in self.events)
            newest = max(e.timestamp for e in self.events)
            stats['time_range'] = {
                'oldest': datetime.fromtimestamp(oldest).isoformat(),
                'newest': datetime.fromtimestamp(newest).isoformat(),
                'duration_hours': (newest - oldest) / 3600
            }
        
        return stats