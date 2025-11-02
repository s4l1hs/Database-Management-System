
/*
 ============================================================================
 World Development Indicators (WDI) Project - Master SQL Schema
 This script creates the project's 11 tables (1 central, 5 domains, 5 indicator)
 ============================================================================
*/

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS freshwater_data;
DROP TABLE IF EXISTS healthcare_data;
DROP TABLE IF EXISTS ghg_data;
DROP TABLE IF EXISTS energy_data;
DROP TABLE IF EXISTS sustainability_data;

DROP TABLE IF EXISTS freshwater_indicator_details;
DROP TABLE IF EXISTS healthcare_indicator_details;
DROP TABLE IF EXISTS ghg_indicator_details;
DROP TABLE IF EXISTS energy_indicator_details;
DROP TABLE IF EXISTS sustainability_indicator_details;

DROP TABLE IF EXISTS countries;

SET FOREIGN_KEY_CHECKS = 1;

-- =================================================================
-- Main 'countries' table referenced by all domain data tables.
-- This table will be populated manually (as before).
-- =================================================================
CREATE TABLE countries (
    country_id INT AUTO_INCREMENT PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    country_code VARCHAR(3) NOT NULL UNIQUE,
    region VARCHAR(100),
    income_group VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =================================================================
-- 2. DOMAIN: Freshwater Usage
-- =================================================================

CREATE TABLE freshwater_indicator_details (
    indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    source_note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE freshwater_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    indicator_id INT NOT NULL,
    year INT NOT NULL,
    value DECIMAL(20,10),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_freshwater_year CHECK (year BETWEEN 1900 AND 2100),
    CONSTRAINT fk_freshwater_country FOREIGN KEY (country_id)
        REFERENCES countries(country_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_freshwater_indicator FOREIGN KEY (indicator_id)
        REFERENCES freshwater_indicator_details(indicator_id)
        ON DELETE CASCADE,
    UNIQUE(country_id, indicator_id, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_freshwater_year ON freshwater_data(year);

-- =================================================================
-- 3. DOMAIN: Healthcare Systems
-- =================================================================

CREATE TABLE health_indicator_details (
    indicator_id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    indicator_name        VARCHAR(100) NOT NULL,
    indicator_description TEXT,
    unit_symbol           VARCHAR(20),
    UNIQUE (indicator_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE health_system (
    row_id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    country_id      INT UNSIGNED NOT NULL,
    indicator_id    INT UNSIGNED NOT NULL,
    indicator_value DECIMAL(20,10),
    year            INT NOT NULL,
    source_notes    VARCHAR(255),

    CONSTRAINT chk_health_year CHECK (year BETWEEN 1900 AND 2100),

    CONSTRAINT fk_health_country
        FOREIGN KEY (country_id)
        REFERENCES countries(country_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_health_indicator
        FOREIGN KEY (indicator_id)
        REFERENCES health_indicator_details(indicator_id)
        ON DELETE CASCADE,

    UNIQUE (country_id, indicator_id, year),
    INDEX idx_health_country   (country_id),
    INDEX idx_health_indicator (indicator_id),
    INDEX idx_health_year      (year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_health_year ON health_system(year);

-- =================================================================
-- 4. DOMAIN: Greenhouse Gas Emissions
-- =================================================================

CREATE TABLE ghg_indicator_details (
    indicator_id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    indicator_name        VARCHAR(255) NOT NULL,
    indicator_code        VARCHAR(50) NOT NULL,
    source_note           TEXT,
    UNIQUE (indicator_name),
    UNIQUE (indicator_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ghg_data (
    row_id         INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    country_id     INT UNSIGNED NOT NULL,
    indicator_id   INT UNSIGNED NOT NULL,
    indicator_value DECIMAL(20,10),
    year           INT NOT NULL,
    source_notes   VARCHAR(255),

    CONSTRAINT chk_ghg_year CHECK (year BETWEEN 1900 AND 2100),

    CONSTRAINT fk_ghg_country
        FOREIGN KEY (country_id)
        REFERENCES countries(country_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_ghg_indicator
        FOREIGN KEY (indicator_id)
        REFERENCES ghg_indicator_details(indicator_id)
        ON DELETE CASCADE,

    UNIQUE (country_id, indicator_id, year),
    INDEX idx_ghg_country   (country_id),
    INDEX idx_ghg_indicator (indicator_id),
    INDEX idx_ghg_year      (year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_ghg_year ON ghg_data(year);
-- =================================================================
-- 5. DOMAIN: Sustainable Energy
-- =================================================================

CREATE TABLE energy_indicator_details (
    indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    source_note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE energy_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    indicator_id INT NOT NULL,
    year INT NOT NULL,
    value DECIMAL(20,10),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_energy_year CHECK (year BETWEEN 1900 AND 2100),
    CONSTRAINT fk_energy_country FOREIGN KEY (country_id)
        REFERENCES countries(country_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_energy_indicator FOREIGN KEY (indicator_id)
        REFERENCES energy_indicator_details(indicator_id)
        ON DELETE CASCADE,
    UNIQUE(country_id, indicator_id, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_energy_year ON energy_data(year);

-- =================================================================
-- 6. DOMAIN: General Sustainability
-- =================================================================

CREATE TABLE sustainability_indicator_details (
    indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    source_note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sustainability_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    indicator_id INT NOT NULL,
    year INT NOT NULL,
    value DECIMAL(20,10),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_sustainability_year CHECK (year BETWEEN 1900 AND 2100),
    CONSTRAINT fk_sustainability_country FOREIGN KEY (country_id)
        REFERENCES countries(country_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_sustainability_indicator FOREIGN KEY (indicator_id)
        REFERENCES sustainability_indicator_details(indicator_id)
        ON DELETE CASCADE,
    UNIQUE(country_id, indicator_id, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_sustainability_year ON sustainability_data(year);

-- =================================================================
-- 7. SAMPLE DATA (for quick verification)
-- The countries table is intended to be filled manually
-- =================================================================

INSERT INTO countries (country_name, country_code, region, income_group)
VALUES
('Turkey', 'TUR', 'Europe & Central Asia', 'Upper middle income'),
('United States', 'USA', 'North America', 'High income'),
('Germany', 'DEU', 'Europe & Central Asia', 'High income'),
('Brazil', 'BRA', 'Latin America & Caribbean', 'Upper middle income'),
('India', 'IND', 'South Asia', 'Lower middle income');

INSERT INTO healthcare_indicator_details (indicator_name, indicator_code, source_note)
VALUES
('Life expectancy at birth, total (years)', 'SP.DYN.LE00.IN', 'Life expectancy at birth indicates the number of years a newborn infant would live...'),
('Hospital beds (per 1,000 people)', 'SH.MED.BEDS.ZS', 'Hospital beds include inpatient beds available in public, private, general, and specialized hospitals...'),
('Current health expenditure per capita (current US$)', 'SH.XPD.CHEX.PC.CD', 'Total health expenditure is the sum of public and private health expenditures...');

INSERT INTO energy_indicator_details (indicator_name, indicator_code, source_note)
VALUES
('Renewable energy consumption (% of total final energy consumption)', 'EG.FEC.RNEW.ZS', '...'),
('Access to electricity (% of population)', 'EG.ELC.ACCS.ZS', '...');

SELECT * FROM countries;
SELECT * FROM healthcare_indicator_details;
