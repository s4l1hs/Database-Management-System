USE sustainability;--use your own schema name here

LOAD DATA LOCAL INFILE '../Data/countries.csv'
INTO TABLE countries
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(country_id, country_name, country_code);
