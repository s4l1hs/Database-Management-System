USE sustainability;

LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/data-insertion/countries.csv'
INTO TABLE countries
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(country_id, country_name, country_code, region);
