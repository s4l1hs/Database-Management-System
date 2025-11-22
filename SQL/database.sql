
/*
 World Development Indicators (WDI) Project - Master SQL Schema
 This script creates the project's 11 tables (1 central,5 domains,5 indicator)
*/

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS freshwater_data;
DROP TABLE IF EXISTS health_system;
DROP TABLE IF EXISTS greenhouse_emissions;
DROP TABLE IF EXISTS energy_data;
DROP TABLE IF EXISTS sustainability_data;

DROP TABLE IF EXISTS freshwater_indicator_details;
DROP TABLE IF EXISTS health_indicator_details;
DROP TABLE IF EXISTS ghg_indicator_details;
DROP TABLE IF EXISTS energy_indicator_details;
DROP TABLE IF EXISTS sustainability_indicator_details;

DROP TABLE IF EXISTS countries;

SET FOREIGN_KEY_CHECKS = 1;

-- =================================================================
-- Main 'countries' table referenced by all domain data tables.
-- This table will be populated manually (Gülbahar Karabaş).
-- =================================================================
CREATE TABLE countries (
    country_id INT AUTO_INCREMENT PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    country_code VARCHAR(3) NOT NULL UNIQUE,
    region VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =================================================================
-- 2. DOMAIN: Freshwater Usage (MUHAMMET TUNCER, 820230314)
-- =================================================================

CREATE TABLE freshwater_indicator_details (
    freshwater_indicator_id   INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    unit_of_measure       VARCHAR(100),
    created_at            TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE freshwater_data (
    data_id      INT AUTO_INCREMENT PRIMARY KEY,
    country_id   INT NOT NULL,
    freshwater_indicator_id INT NOT NULL,
    year         INT NOT NULL,
    indicator_value        DECIMAL(20,10),
    source_notes VARCHAR(255) NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

   
    CONSTRAINT chk_freshwater_year CHECK (year BETWEEN 1900 AND 2100),
    
    CONSTRAINT fk_freshwater_country 
        FOREIGN KEY (country_id)
        REFERENCES countries(country_id)
        ON DELETE CASCADE,
        
    CONSTRAINT fk_freshwater_indicator 
        FOREIGN KEY (freshwater_indicator_id)
        REFERENCES freshwater_indicator_details(freshwater_indicator_id)
        ON DELETE CASCADE,
    
        UNIQUE(country_id, freshwater_indicator_id, year)
    
);

 
CREATE INDEX idx_freshwater_country ON freshwater_data(country_id);
CREATE INDEX idx_freshwater_indicator ON freshwater_data(freshwater_indicator_id);
CREATE INDEX idx_freshwater_year ON freshwater_data(year); 
CREATE INDEX idx_freshwater_country_indicator ON freshwater_data(country_id,freshwater_indicator_id);

-- ================================================================
-- 3. DOMAIN: Healthcare Systems (Gülbahar Karabaş)
-- ================================================================

CREATE TABLE health_indicator_details (
    health_indicator_id   INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    indicator_name        VARCHAR(100) NOT NULL,
    indicator_description TEXT,
    unit_symbol           VARCHAR(20),
    UNIQUE (indicator_name)
);

CREATE TABLE health_system (
    row_id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    country_id      INT NOT NULL,
    health_indicator_id    INT UNSIGNED NOT NULL,
    indicator_value DECIMAL(12,4),
    year            INT NOT NULL,
    source_notes    VARCHAR(255),

    CONSTRAINT chk_health_year CHECK (year BETWEEN 1900 AND 2100),

    CONSTRAINT fk_health_country
        FOREIGN KEY (country_id)
        REFERENCES countries(country_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_health_indicator
        FOREIGN KEY (health_indicator_id)
        REFERENCES health_indicator_details(health_indicator_id)
        ON DELETE CASCADE,

    UNIQUE (country_id,health_indicator_id, year)
);

CREATE INDEX idx_health_year ON health_system(year);

-- =================================================================
-- 4. DOMAIN: Greenhouse Gas Emissions
-- =================================================================

CREATE TABLE ghg_indicator_details (
    ghg_indicator_id      INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    indicator_name        VARCHAR(255) NOT NULL,
    indicator_description VARCHAR(200) NOT NULL,
    unit_symbol           VARCHAR(20),
    UNIQUE (indicator_name)
);

CREATE TABLE greenhouse_emissions  (
    row_id         INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    country_id     INT NOT NULL,
    ghg_indicator_id    INT UNSIGNED NOT NULL,
    indicator_value INT NOT NULL,
    share_of_total_pct INT,
    uncertainty_pct    INT,
    year           INT NOT NULL,
    source_notes   VARCHAR(255),

    CONSTRAINT chk_ghg_year CHECK (year BETWEEN 1900 AND 2100),

    CONSTRAINT fk_ghg_country
        FOREIGN KEY (country_id)
        REFERENCES countries(country_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_ghg_indicator
        FOREIGN KEY (ghg_indicator_id)
        REFERENCES ghg_indicator_details(ghg_indicator_id)
        ON DELETE CASCADE,

    UNIQUE (country_id, ghg_indicator_id, year),
    INDEX idx_ghg_country   (country_id),
    INDEX idx_ghg_indicator (ghg_indicator_id),
    INDEX idx_ghg_year      (year)
);

-- =================================================================
-- 5. DOMAIN: Sustainable Energy
-- =================================================================

CREATE TABLE energy_indicator_details (
    energy_indicator_id    INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name        VARCHAR(255) NOT NULL UNIQUE,
    indicator_code        VARCHAR(50) NOT NULL UNIQUE,
    indicator_description TEXT,
    measurement_unit       VARCHAR(50)
);

CREATE TABLE energy_data (
    data_id         INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    country_id     INT NOT NULL,
    energy_indicator_id    INT NOT NULL,
    year           INT NOT NULL,
    indicator_value FLOAT,
    data_source VARCHAR(255),
    CONSTRAINT chk_energy_year CHECK (year BETWEEN 1900 AND 2100),
    
    CONSTRAINT fk_energy_country 
        FOREIGN KEY (country_id) 
        REFERENCES countries(country_id) 
        ON DELETE CASCADE,
        
    CONSTRAINT fk_energy_indicator 
        FOREIGN KEY (energy_indicator_id) 
        REFERENCES energy_indicator_details(energy_indicator_id) 
        ON DELETE CASCADE,
 
    UNIQUE(country_id,energy_indicator_id, year)
 
);

CREATE INDEX idx_energy_country ON energy_data (country_id);
CREATE INDEX idx_energy_indicator ON energy_data (energy_indicator_id);
CREATE INDEX idx_energy_year ON energy_data(year);
CREATE INDEX idx_country_indicator ON energy_data (country_id, energy_indicator_id);

-- =================================================================
-- 6. DOMAIN: General Sustainability
-- =================================================================

CREATE TABLE sustainability_indicator_details (
    sus_indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    indicator_description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE sustainability_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    sus_indicator_id INT NOT NULL,
    year INT NOT NULL,
    indicator_value FLOAT,
    source_note VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_sustainability_year CHECK (year BETWEEN 1900 AND 2100),
    CONSTRAINT fk_sustainability_country FOREIGN KEY (country_id)
        REFERENCES countries(country_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_sustainability_indicator FOREIGN KEY (sus_indicator_id)
        REFERENCES sustainability_indicator_details(sus_indicator_id)
        ON DELETE CASCADE,
    UNIQUE(country_id,sus_indicator_id, year)
);

CREATE INDEX idx_sustainability_year ON sustainability_data(year);

