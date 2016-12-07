DROP TABLE IF EXISTS boroughs;
CREATE TABLE boroughs (
    id INTEGER PRIMARY KEY,
    name text
);
INSERT INTO boroughs VALUES (0, "");

DROP TABLE IF EXISTS cuisines;
CREATE TABLE cuisines (
    id INTEGER PRIMARY KEY,
    name text
);
INSERT INTO cuisines VALUES (100, "");

DROP TABLE IF EXISTS violations;
CREATE TABLE violations (
    id INTEGER PRIMARY KEY,
    code text NOT NULL,
    description text
);
INSERT INTO violations VALUES (200, "", "");
