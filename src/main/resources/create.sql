CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Availabilities (
    Time date,
    Username varchar(255) REFERENCES Caregivers,
    PRIMARY KEY (Time, Username)
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);

CREATE TABLE Patients (
    Patientsname varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Patientsname)
);

CREATE TABLE Reservation (
    Patientsname varchar(255) REFERENCES Patients,
    Username varchar(255) REFERENCES Caregivers,
    appointment_id int,
    Time date,
    Name varchar(255) REFERENCES Vaccines,
    PRIMARY KEY (appointment_id)
);