USE sustainability;
-- Dosya yolunu kendi bilgisayarına göre güncellemeyi unutma!
LOAD DATA LOCAL INFILE '/Users/fahrettin/Desktop/Data-insertion/sustainability_system.csv'
INTO TABLE sustainability_data
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(country_id, sus_indicator_id, year, @raw_value, source_note)
SET indicator_value = NULLIF(@raw_value, '');