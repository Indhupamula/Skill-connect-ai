CREATE DATABASE skillconnect_ai;

USE skillconnect_ai;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    role ENUM('skill_owner','learner'),
    portfolio TEXT
);

CREATE TABLE skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    title VARCHAR(100),
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    skill_id INT,
    title VARCHAR(100),
    description TEXT,
    date DATETIME,
    FOREIGN KEY (skill_id) REFERENCES skills(id)
);

CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT,
    learner_id INT,
    status ENUM('pending','confirmed','completed'),
    payment_status ENUM('pending','paid'),
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (learner_id) REFERENCES users(id)
);
