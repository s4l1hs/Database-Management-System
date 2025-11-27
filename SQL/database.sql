SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE countries (
    country_id INT AUTO_INCREMENT PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    country_code VARCHAR(3) NOT NULL UNIQUE,
    region VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    student_number VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    team_no INT DEFAULT 1
);

INSERT INTO students (student_number, full_name, team_no) VALUES --students table used for admin control
('820230313', 'Salih Sefer', 1),
('820230334', 'Atahan Evintan', 1),
('820230326', 'Fatih Serdar Çakmak', 1),
('820230314', 'Muhammet Tuncer', 1),
('150210085', 'Gülbahar Karabaş', 1);

-- Audit Logs 
CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    action_type VARCHAR(50),
    table_name VARCHAR(50),
    record_id INT,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE SET NULL
);

-- --- FRESHWATER (Muhammet Tuncer) ---
CREATE TABLE freshwater_indicator_details (
    freshwater_indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    unit_of_measure VARCHAR(100)
);

CREATE TABLE freshwater_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    freshwater_indicator_id INT NOT NULL,
    year INT NOT NULL,
    indicator_value DECIMAL(20,10),
    source_notes VARCHAR(255) NULL,
    
    CONSTRAINT fk_freshwater_country FOREIGN KEY (country_id) REFERENCES countries(country_id) ON DELETE CASCADE,
    CONSTRAINT fk_freshwater_indicator FOREIGN KEY (freshwater_indicator_id) REFERENCES freshwater_indicator_details(freshwater_indicator_id) ON DELETE CASCADE,
    UNIQUE(country_id, freshwater_indicator_id, year)
);

-- --- HEALTH (Gülbahar Karabaş) ---
CREATE TABLE health_indicator_details (
    health_indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(100) NOT NULL UNIQUE,
    indicator_description TEXT,
    unit_symbol VARCHAR(20)
);

CREATE TABLE health_system (
    row_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    health_indicator_id INT NOT NULL,
    indicator_value DECIMAL(12,4),
    year INT NOT NULL,
    source_notes VARCHAR(255),

    CONSTRAINT fk_health_country FOREIGN KEY (country_id) REFERENCES countries(country_id) ON DELETE CASCADE,
    CONSTRAINT fk_health_indicator FOREIGN KEY (health_indicator_id) REFERENCES health_indicator_details(health_indicator_id) ON DELETE CASCADE,
    UNIQUE (country_id, health_indicator_id, year)
);

-- --- GHG EMISSIONS (Fatih Serdar Çakmak) ---
CREATE TABLE ghg_indicator_details (
    ghg_indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_description VARCHAR(200) NOT NULL,
    unit_symbol VARCHAR(20)
);

CREATE TABLE greenhouse_emissions (
    row_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    ghg_indicator_id INT NOT NULL,
    indicator_value INT NOT NULL,
    share_of_total_pct INT,
    uncertainty_pct INT,
    year INT NOT NULL,
    source_notes VARCHAR(255),

    CONSTRAINT fk_ghg_country FOREIGN KEY (country_id) REFERENCES countries(country_id) ON DELETE CASCADE,
    CONSTRAINT fk_ghg_indicator FOREIGN KEY (ghg_indicator_id) REFERENCES ghg_indicator_details(ghg_indicator_id) ON DELETE CASCADE,
    UNIQUE (country_id, ghg_indicator_id, year)
);

-- --- ENERGY (Atahan Evintan) ---
CREATE TABLE energy_indicator_details (
    energy_indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    indicator_description TEXT,
    measurement_unit VARCHAR(50)
);

CREATE TABLE energy_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    energy_indicator_id INT NOT NULL,
    year INT NOT NULL,
    indicator_value FLOAT,
    data_source VARCHAR(255),
    
    CONSTRAINT fk_energy_country FOREIGN KEY (country_id) REFERENCES countries(country_id) ON DELETE CASCADE,
    CONSTRAINT fk_energy_indicator FOREIGN KEY (energy_indicator_id) REFERENCES energy_indicator_details(energy_indicator_id) ON DELETE CASCADE,
    UNIQUE(country_id, energy_indicator_id, year)
);

-- --- SUSTAINABILITY (Salih Sefer) ---
CREATE TABLE sustainability_indicator_details (
    sus_indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    indicator_description TEXT
);

CREATE TABLE sustainability_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    sus_indicator_id INT NOT NULL,
    year INT NOT NULL,
    indicator_value FLOAT,
    source_note VARCHAR(255),
    
    CONSTRAINT fk_sus_country FOREIGN KEY (country_id) REFERENCES countries(country_id) ON DELETE CASCADE,
    CONSTRAINT fk_sus_indicator FOREIGN KEY (sus_indicator_id) REFERENCES sustainability_indicator_details(sus_indicator_id) ON DELETE CASCADE,
    UNIQUE(country_id, sus_indicator_id, year)
);

SET FOREIGN_KEY_CHECKS = 1;