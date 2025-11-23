USE sustainability;--use your own schema name here

LOAD DATA LOCAL INFILE '../Data/health_system.csv'
INTO TABLE health_system
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(country_id, health_indicator_id, indicator_value, year, source_notes);
