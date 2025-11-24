USE sustainability;

LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/Data-insertion/health_system.csv'
INTO TABLE health_system
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(country_id, health_indicator_id, @raw_value, year, source_notes)
SET indicator_value = NULLIF(@raw_value, '');
