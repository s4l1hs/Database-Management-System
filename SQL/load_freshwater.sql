USE sustainability;

LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/data-insertion/freshwater_data.csv'
INTO TABLE freshwater_data
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(country_id, freshwater_indicator_id, indicator_value, year, source_notes);
