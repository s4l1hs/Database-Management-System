USE sustainability;

LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/data-insertion/energy_data.csv'
INTO TABLE energy_data
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    country_id, 
    energy_indicator_id, 
    year, 
    @raw_value,   
    data_source
)
SET indicator_value = NULLIF(@raw_value, '');
