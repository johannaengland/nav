CREATE TABLE manage.oui (
    id SERIAL PRIMARY KEY,
    vendor VARCHAR NOT NULL,
    oui CHAR(6) NOT NULL UNIQUE
);
