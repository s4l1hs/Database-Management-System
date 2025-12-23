USE sustainability;

LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/Data-insertion/energy_indicator_details.csv'
INTO TABLE energy_indicator_details
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES 
(
    energy_indicator_id, 
    indicator_name, 
    indicator_code, 
    indicator_description, 
    measurement_unit
);
