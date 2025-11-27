USE sustainability;

LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/Data-insertion/greenhouse_emissions.csv'
INTO TABLE greenhouse_emissions
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(country_id, ghg_indicator_id, @raw_value, @raw_share, @raw_uncertainty, year, source_notes)
SET indicator_value = NULLIF(@raw_value, ''),
    share_of_total_pct = NULLIF(@raw_share, ''),
    uncertainty_pct = NULLIF(@raw_uncertainty, '');
