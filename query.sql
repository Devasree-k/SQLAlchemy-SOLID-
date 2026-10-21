CREATE TABLE drivers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE
);

CREATE TABLE transport_collection (
    id SERIAL PRIMARY KEY,
    driver_id INTEGER NOT NULL REFERENCES drivers(id),
    vehicle_number VARCHAR(20) NOT NULL,
    collection_date DATE NOT NULL,
    morning_trips INTEGER NOT NULL,
    evening_trips INTEGER NOT NULL,
    morning_collection NUMERIC(10, 2) NOT NULL,
    evening_collection NUMERIC(10, 2) NOT NULL,
    fuel_expense NUMERIC(10, 2) NOT NULL,
    other_expense NUMERIC(10, 2) NOT NULL,
    total_trips INTEGER NOT NULL,
    total_collection NUMERIC(10, 2) NOT NULL,
    total_expense NUMERIC(10, 2) NOT NULL,
    net_collection NUMERIC(10, 2) NOT NULL
);



