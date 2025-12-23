USE sustainability;

LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/Data-insertion/ghg_indicator_details.csv'
INTO TABLE ghg_indicator_details
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(ghg_indicator_id, indicator_name, indicator_description, unit_symbol);
