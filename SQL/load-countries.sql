USE wdi_project;

LOAD DATA LOCAL INFILE '/Users/salihsefer36/Documents/GitHub/Database-Management-System/Data/countries.csv'
INTO TABLE countries
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(country_id, country_name, country_code, region);