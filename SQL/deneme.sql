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



USE sustainability;

LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/data-insertion/energy_indicator_details.csv'
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