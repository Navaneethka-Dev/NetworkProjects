#!/usr/bin/env python3
"""
Network Monitoring Dashboard - Database Models
SQLAlchemy models for storing network monitoring data.

Author: Navaneethraj KA
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

Base = declarative_base()
engine = None
Session = None


def init_db(db_path=None):
    """Initialize the database."""
    global engine, Session
    
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'network.db')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    
    # Create tables
    Base.metadata.create_all(engine)
    
    # Add sample data if database is empty
    session = Session()
    if session.query(Device).count() == 0:
        _add_sample_data(session)
    session.close()
    
    print(f"[INFO] Database initialized: {db_path}")


def get_session():
    """Get a database session."""
    global Session
    if Session is None:
        init_db()
    return Session()


def _add_sample_data(session):
    """Add sample devices for demonstration."""
    sample_devices = [
        Device(name='Core-Router-1', ip_address='192.168.1.1', device_type='router', status='online'),
        Device(name='Core-Switch-1', ip_address='192.168.1.2', device_type='switch', status='online'),
        Device(name='Firewall-1', ip_address='192.168.1.3', device_type='firewall', status='online'),
        Device(name='Edge-Router-1', ip_address='192.168.1.4', device_type='router', status='warning'),
        Device(name='Distribution-SW-1', ip_address='192.168.1.5', device_type='switch', status='online'),
        Device(name='AP-Floor-1', ip_address='192.168.1.10', device_type='access_point', status='online'),
        Device(name='AP-Floor-2', ip_address='192.168.1.11', device_type='access_point', status='offline'),
    ]
    
    for device in sample_devices:
        session.add(device)
    
    session.commit()
    print("[INFO] Sample devices added to database")


class Device(Base):
    """Network device model."""
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False, unique=True)
    device_type = Column(String(50), default='unknown')
    snmp_community = Column(String(100), default='public')
    snmp_version = Column(String(10), default='2c')
    status = Column(String(20), default='unknown')
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    metrics = relationship('Metric', back_populates='device', cascade='all, delete-orphan')
    alerts = relationship('Alert', back_populates='device', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'device_type': self.device_type,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }


class Metric(Base):
    """Device metrics model."""
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    unit = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    device = relationship('Device', back_populates='metrics')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat()
        }


class Alert(Base):
    """Alert model."""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    severity = Column(String(20), default='info')  # critical, warning, info
    title = Column(String(200), nullable=False)
    message = Column(Text)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    device = relationship('Device', back_populates='alerts')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'acknowledged': self.acknowledged,
            'timestamp': self.timestamp.isoformat()
        }


class PollingResult(Base):
    """Polling result model for tracking poll status."""
    __tablename__ = 'polling_results'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    success = Column(Boolean, default=True)
    response_time = Column(Float)  # in milliseconds
    error_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
