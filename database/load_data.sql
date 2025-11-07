-- Load CSVs into the tables
COPY training_data (salary, credit_score, employment_years, loan_amount, target, source)
FROM '/docker-entrypoint-initdb.d/training_data.csv'
DELIMITER ','
CSV HEADER;

COPY users (full_name, email, password_hash, role)
FROM '/docker-entrypoint-initdb.d/users.csv'
DELIMITER ','
CSV HEADER;

COPY rules_config (name, field, operator, value, message)
FROM '/docker-entrypoint-initdb.d/rules_config.csv'
DELIMITER ','
CSV HEADER;