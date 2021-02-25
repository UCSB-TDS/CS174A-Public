-- To make HW5 easier we provide the table schema for you.
PRAGMA foreign_keys=ON;
PRAGMA serializable = true;
CREATE TABLE Carriers (
    cid VARCHAR(7) PRIMARY KEY, 
    name VARCHAR(83)
);

CREATE TABLE Months (
    mid INT PRIMARY KEY,
    month VARCHAR(9)
);

CREATE TABLE Weekdays(
    did INT PRIMARY KEY,
    day_of_week VARCHAR(9)
);

CREATE TABLE Flights (
    fid INT PRIMARY KEY, 
    month_id INT,        -- 1-12
    day_of_month INT,    -- 1-31 
    day_of_week_id INT,  -- 1-7, 1 = Monday, 2 = Tuesday, etc
    carrier_id VARCHAR(7), 
    flight_num INT,
    origin_city VARCHAR(34), 
    origin_state VARCHAR(47), 
    dest_city VARCHAR(34), 
    dest_state VARCHAR(46), 
    departure_delay INT, -- in mins
    taxi_out INT,        -- in mins
    arrival_delay INT,   -- in mins
    canceled INT,        -- 1 means canceled
    actual_time INT,     -- in mins
    distance INT,        -- in miles
    capacity INT, 
    price INT,           -- in $
    FOREIGN KEY (carrier_id) REFERENCES Carriers(cid),
    FOREIGN KEY (month_id) REFERENCES Months(mid),
    FOREIGN KEY (day_of_week_id) REFERENCES Weekdays(did)
);

CREATE TABLE Customers(
    username VARCHAR(256),
    password VARCHAR(256),
    balance INT,
    PRIMARY KEY (username)
);

CREATE TABLE Itineraries(
    direct INT, -- 1 or 0 stands for direct or one-hop flights
    fid1 INT,
    fid2 INT -- -1 means that this is a direct flight and has no second flight
);

CREATE TABLE Reservations(
    rid INT,
    price INT,
    fid INT,
    paid INT,
    canceled INT,
    username VARCHAR(256),
    day_of_month INT,
    PRIMARY KEY (rid)
);

CREATE TABLE ReservationsId(
    rid INT
);
INSERT INTO ReservationsId VALUES (1);
.mode csv
.import carriers.csv Carriers
.import months.csv Months
.import weekdays.csv Weekdays
.import flights-small.csv Flights