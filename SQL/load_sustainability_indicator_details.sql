USE sustainability;
-- Dosya yolunu kendi bilgisayarına göre güncellemeyi unutma!
LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/data-insertion/sustainability_indicator_details.csv'
INTO TABLE sustainability_indicator_details
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(sus_indicator_id, indicator_name, indicator_code, indicator_description, unit_symbol);