#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLAlchemy Models for EAA Payment System
----------------------------------------
Database models using SQLAlchemy ORM.
Author: Lil Claudy Flossy
"""

from sqlalchemy import create_engine, Column, Integer, String, DECIMAL, DateTime, Date, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

Base = declarative_base()


class EAAPayment(Base):
    """Model for EAA payment records."""
    __tablename__ = 'eaa_payments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ssn = Column(String(9), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    company = Column(String(255), nullable=False)
    report_date = Column(Date, nullable=False)
    import_date = Column(DateTime, default=datetime.utcnow)
    clientID = Column(Integer, nullable=True)
    payment_id = Column(String(15), nullable=False, unique=True, index=True)
    payment_applied = Column(Integer, default=0)
    date_applied = Column(DateTime, nullable=True)
    
    # Add fulltext index for name (MySQL specific)
    __table_args__ = (
        Index('idx_name', 'name', mysql_prefix='FULLTEXT'),
    )
    
    def __repr__(self):
        return f"<EAAPayment(id={self.id}, name='{self.name}', ssn='{self.ssn}', amount={self.amount})>"


class Customer(Base):
    """Model for customer records."""
    __tablename__ = 'customers'
    
    PrimaryClientID = Column(Integer, primary_key=True)
    SocSec = Column(String(9), index=True)
    FirstName = Column(String(100))
    LastName = Column(String(100))
    EmployerID = Column(Integer, index=True)
    
    def __repr__(self):
        return f"<Customer(id={self.PrimaryClientID}, name='{self.FirstName} {self.LastName}')>"


class PaymentAZ(Base):
    """Model for applied payments."""
    __tablename__ = 'payments_az'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, nullable=False, index=True)
    payment_amount = Column(DECIMAL(10, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_type = Column(String(50))
    reference_number = Column(String(50))
    notes = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PaymentAZ(id={self.id}, client_id={self.client_id}, amount={self.payment_amount})>"


def get_database_url(environment='dev'):
    """
    Get database URL for SQLAlchemy.
    
    Args:
        environment (str): Database environment ('dev' or 'prod')
        
    Returns:
        str: Database URL
    """
    env_prefix = f"SPIDERSYNC_{environment.upper()}_"
    
    host = os.getenv(f"{env_prefix}HOST", 'localhost')
    database = os.getenv(f"{env_prefix}DATABASE", 'spider_sync_DEV')
    user = os.getenv(f"{env_prefix}USER")
    password = os.getenv(f"{env_prefix}PASSWORD")
    port = os.getenv(f"{env_prefix}PORT", '3306')
    
    if not user or not password:
        raise ValueError(f"Database credentials not found for {environment} environment")
    
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


def get_engine(environment='dev'):
    """
    Create SQLAlchemy engine.
    
    Args:
        environment (str): Database environment
        
    Returns:
        Engine instance
    """
    database_url = get_database_url(environment)
    return create_engine(database_url, echo=False, pool_pre_ping=True)


def get_session(environment='dev'):
    """
    Create SQLAlchemy session.
    
    Args:
        environment (str): Database environment
        
    Returns:
        Session instance
    """
    engine = get_engine(environment)
    Session = sessionmaker(bind=engine)
    return Session()


def create_tables(environment='dev'):
    """
    Create all tables in the database.
    
    Args:
        environment (str): Database environment
    """
    engine = get_engine(environment)
    Base.metadata.create_all(engine)