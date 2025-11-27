USE sustainability;

LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/data-insertion/freshwater_indicators.csv'
INTO TABLE freshwater_indicator_details
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(freshwater_indicator_id, indicator_name, description, unit_of_measure);
