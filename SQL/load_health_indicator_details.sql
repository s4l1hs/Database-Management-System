USE sustainability;

LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/Data-insertion/health_indicator_details.csv'
INTO TABLE health_indicator_details
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(health_indicator_id, indicator_name, indicator_description, unit_symbol);
