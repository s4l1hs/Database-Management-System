from App.db import db 
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, UniqueConstraint

class EnergyIndicatorDetails(db.Model):
    __tablename__ = 'energy_indicator_details'
    
    indicator_id = db.Column(db.Integer, primary_key=True)
    indicator_name = db.Column(db.String(255), nullable=False, unique=True)
    indicator_code = db.Column(db.String(50), nullable=False, unique=True)
    source_note = db.Column(db.Text)
    unit_of_measure = db.Column(db.String(50))
    
    data_points = db.relationship("EnergyData", backref="indicator_details")

class EnergyData(db.Model):
    __tablename__ = 'energy_data'
    
    row_id = db.Column(db.Integer, primary_key=True) 
    country_id = db.Column(db.Integer, db.ForeignKey('countries.country_id'), nullable=False)
    indicator_id = db.Column(db.Integer, db.ForeignKey('energy_indicator_details.indicator_id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Float)
    
    __table_args__ = (
        db.UniqueConstraint('country_id', 'indicator_id', 'year', name='unique_energy_data'),
    )

class SustainabilityIndicatorDetails(db.Model):
    __tablename__ = 'sustainability_indicator_details'
    
    indicator_id = db.Column(db.Integer, primary_key=True)
    indicator_name = db.Column(db.String(255), nullable=False, unique=True)
    indicator_code = db.Column(db.String(50), nullable=False, unique=True)
    source_note = db.Column(db.Text)
    unit_of_measure = db.Column(db.String(50))
    
    data_points = db.relationship("SustainabilityData", backref="indicator_details")

class SustainabilityData(db.Model):
    __tablename__ = 'sustainability_data'
    
    data_id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.country_id'), nullable=False)
    indicator_id = db.Column(db.Integer, db.ForeignKey('sustainability_indicator_details.indicator_id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Float)
    
    __table_args__ = (
        db.UniqueConstraint('country_id', 'indicator_id', 'year', name='unique_sustainability_data'),
    )

