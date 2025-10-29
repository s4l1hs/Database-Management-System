
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



CREATE TABLE countries (
    country_id INT AUTO_INCREMENT PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    country_code VARCHAR(3) NOT NULL UNIQUE, 
    region VARCHAR(100),
    income_group VARCHAR(50) -- 'High income', 'Low income' etc.
);


CREATE TABLE freshwater_indicator_details (
    indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    source_note TEXT
);

CREATE TABLE freshwater_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,   
    indicator_id INT NOT NULL,  
    year INT NOT NULL,
    value DECIMAL(20, 10),     
    
    CONSTRAINT fk_freshwater_country FOREIGN KEY (country_id) 
        REFERENCES countries(country_id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_freshwater_indicator FOREIGN KEY (indicator_id) 
        REFERENCES freshwater_indicator_details(indicator_id) 
        ON DELETE CASCADE,

    UNIQUE(country_id, indicator_id, year)
);


CREATE TABLE healthcare_indicator_details (
    indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    source_note TEXT
);


CREATE TABLE healthcare_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    indicator_id INT NOT NULL,
    year INT NOT NULL,
    value DECIMAL(20, 10),
    

    CONSTRAINT fk_healthcare_country FOREIGN KEY (country_id) 
        REFERENCES countries(country_id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_healthcare_indicator FOREIGN KEY (indicator_id) 
        REFERENCES healthcare_indicator_details(indicator_id) 
        ON DELETE CASCADE,
        
    UNIQUE(country_id, indicator_id, year)
);


CREATE TABLE ghg_indicator_details (
    indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    source_note TEXT
);

CREATE TABLE ghg_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    indicator_id INT NOT NULL,
    year INT NOT NULL,
    value DECIMAL(20, 10),
    
    CONSTRAINT fk_ghg_country FOREIGN KEY (country_id) 
        REFERENCES countries(country_id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_ghg_indicator FOREIGN KEY (indicator_id) 
        REFERENCES ghg_indicator_details(indicator_id) 
        ON DELETE CASCADE,
        
    -- Veri tekilliği
    UNIQUE(country_id, indicator_id, year)
);


CREATE TABLE energy_indicator_details (
    indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    source_note TEXT
);

CREATE TABLE energy_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    indicator_id INT NOT NULL,
    year INT NOT NULL,
    value DECIMAL(20, 10),
    
    CONSTRAINT fk_energy_country FOREIGN KEY (country_id) 
        REFERENCES countries(country_id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_energy_indicator FOREIGN KEY (indicator_id) 
        REFERENCES energy_indicator_details(indicator_id) 
        ON DELETE CASCADE,
        
    UNIQUE(country_id, indicator_id, year)
);

CREATE TABLE sustainability_indicator_details (
    indicator_id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_name VARCHAR(255) NOT NULL UNIQUE,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,
    source_note TEXT
);

CREATE TABLE sustainability_data (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    indicator_id INT NOT NULL,
    year INT NOT NULL,
    value DECIMAL(20, 10),
    
    CONSTRAINT fk_sustainability_country FOREIGN KEY (country_id) 
        REFERENCES countries(country_id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_sustainability_indicator FOREIGN KEY (indicator_id) 
        REFERENCES sustainability_indicator_details(indicator_id) 
        ON DELETE CASCADE,
        
    -- Veri tekilliği
    UNIQUE(country_id, indicator_id, year)
);


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