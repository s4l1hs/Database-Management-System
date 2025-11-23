from App.db import db
from sqlalchemy.sql import func

# =========================================================
# 1. CORE TABLES AND AUDIT LOGS
# =========================================================

class Region(db.Model):
    __tablename__ = 'regions'
    
    region_id = db.Column(db.Integer, primary_key=True)
    region_name = db.Column(db.String(100), unique=True, nullable=False)
    
    countries = db.relationship('Countries', backref='region_ref')

class Countries(db.Model):
    __tablename__ = 'countries'
    
    country_id = db.Column(db.Integer, primary_key=True)
    country_name = db.Column(db.String(100), unique=True, nullable=False)
    country_code = db.Column(db.String(3), unique=True, nullable=False)
    
    region_id = db.Column(db.Integer, db.ForeignKey('regions.region_id'))
    region = db.Column(db.String(100)) 
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    energy_data = db.relationship('EnergyData', backref='country')
    freshwater_data = db.relationship('FreshwaterData', backref='country')
    health_data = db.relationship('HealthSystem', backref='country')
    ghg_data = db.relationship('GreenhouseEmissions', backref='country')
    sustainability_data = db.relationship('SustainabilityData', backref='country')

class Student(db.Model):
    __tablename__ = 'students'
    
    student_id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    team_no = db.Column(db.Integer, default=1)
    
    # Öğrencinin logları
    logs = db.relationship('AuditLog', backref='student')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    action_type = db.Column(db.String(50)) # CREATE, UPDATE, DELETE
    table_name = db.Column(db.String(50))
    record_id = db.Column(db.Integer)
    action_timestamp = db.Column(db.DateTime, server_default=func.now())


# =========================================================
# 2. DOMAIN: FRESHWATER (Muhammet Tuncer)
# =========================================================

class FreshwaterIndicatorDetails(db.Model):
    __tablename__ = 'freshwater_indicator_details'
    
    freshwater_indicator_id = db.Column(db.Integer, primary_key=True)
    indicator_name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    unit_of_measure = db.Column(db.String(100))
    
    data_points = db.relationship("FreshwaterData", backref="indicator_details")

class FreshwaterData(db.Model):
    __tablename__ = 'freshwater_data'
    
    data_id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.country_id'), nullable=False)
    freshwater_indicator_id = db.Column(db.Integer, db.ForeignKey('freshwater_indicator_details.freshwater_indicator_id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    indicator_value = db.Column(db.Numeric(20, 10))
    source_notes = db.Column(db.String(255))
    
    __table_args__ = (
        db.UniqueConstraint('country_id', 'freshwater_indicator_id', 'year', name='unique_freshwater'),
    )


# =========================================================
# 3. DOMAIN: HEALTH (Gülbahar Karabaş)
# =========================================================

class HealthIndicatorDetails(db.Model):
    __tablename__ = 'health_indicator_details'
    
    health_indicator_id = db.Column(db.Integer, primary_key=True)
    indicator_name = db.Column(db.String(100), nullable=False, unique=True)
    indicator_description = db.Column(db.Text)
    unit_symbol = db.Column(db.String(20))
    
    data_points = db.relationship("HealthSystem", backref="indicator_details")

class HealthSystem(db.Model):
    __tablename__ = 'health_system'
    
    row_id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.country_id'), nullable=False)
    health_indicator_id = db.Column(db.Integer, db.ForeignKey('health_indicator_details.health_indicator_id'), nullable=False)
    indicator_value = db.Column(db.Numeric(12, 4))
    year = db.Column(db.Integer, nullable=False)
    source_notes = db.Column(db.String(255))
    
    __table_args__ = (
        db.UniqueConstraint('country_id', 'health_indicator_id', 'year', name='unique_health'),
    )


# =========================================================
# 4. DOMAIN: GHG EMISSIONS (Fatih Serdar Çakmak)
# =========================================================

class GhgIndicatorDetails(db.Model):
    __tablename__ = 'ghg_indicator_details'
    
    ghg_indicator_id = db.Column(db.Integer, primary_key=True)
    indicator_name = db.Column(db.String(255), nullable=False, unique=True)
    indicator_description = db.Column(db.String(200), nullable=False)
    unit_symbol = db.Column(db.String(20))
    
    data_points = db.relationship("GreenhouseEmissions", backref="indicator_details")

class GreenhouseEmissions(db.Model):
    __tablename__ = 'greenhouse_emissions'
    
    row_id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.country_id'), nullable=False)
    ghg_indicator_id = db.Column(db.Integer, db.ForeignKey('ghg_indicator_details.ghg_indicator_id'), nullable=False)
    indicator_value = db.Column(db.Integer, nullable=False)
    share_of_total_pct = db.Column(db.Integer)
    uncertainty_pct = db.Column(db.Integer)
    year = db.Column(db.Integer, nullable=False)
    source_notes = db.Column(db.String(255))
    
    __table_args__ = (
        db.UniqueConstraint('country_id', 'ghg_indicator_id', 'year', name='unique_ghg'),
    )


# =========================================================
# 5. DOMAIN: ENERGY (Atahan Evintan)
# =========================================================

class EnergyIndicatorDetails(db.Model):
    __tablename__ = 'energy_indicator_details'
    
    energy_indicator_id = db.Column(db.Integer, primary_key=True)
    indicator_name = db.Column(db.String(255), nullable=False, unique=True)
    indicator_code = db.Column(db.String(50), nullable=False, unique=True)
    indicator_description = db.Column(db.Text)
    measurement_unit = db.Column(db.String(50))
    
    data_points = db.relationship("EnergyData", backref="indicator_details")

class EnergyData(db.Model):
    __tablename__ = 'energy_data'
    
    data_id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.country_id'), nullable=False)
    energy_indicator_id = db.Column(db.Integer, db.ForeignKey('energy_indicator_details.energy_indicator_id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    indicator_value = db.Column(db.Float)
    data_source = db.Column(db.String(255))
    
    __table_args__ = (
        db.UniqueConstraint('country_id', 'energy_indicator_id', 'year', name='unique_energy_data'),
    )


# =========================================================
# 6. DOMAIN: SUSTAINABILITY (Salih Sefer)
# =========================================================

class SustainabilityIndicatorDetails(db.Model):
    __tablename__ = 'sustainability_indicator_details'
    
    sus_indicator_id = db.Column(db.Integer, primary_key=True)
    indicator_name = db.Column(db.String(255), nullable=False, unique=True)
    indicator_code = db.Column(db.String(50), nullable=False, unique=True)
    indicator_description = db.Column(db.Text)
    
    data_points = db.relationship("SustainabilityData", backref="indicator_details")

class SustainabilityData(db.Model):
    __tablename__ = 'sustainability_data'
    
    data_id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.country_id'), nullable=False)
    sus_indicator_id = db.Column(db.Integer, db.ForeignKey('sustainability_indicator_details.sus_indicator_id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    indicator_value = db.Column(db.Float)
    source_note = db.Column(db.String(255))
    
    __table_args__ = (
        db.UniqueConstraint('country_id', 'sus_indicator_id', 'year', name='unique_sustainability_data'),
    )