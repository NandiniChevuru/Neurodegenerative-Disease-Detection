DROP DATABASE IF EXISTS db;
CREATE DATABASE db;
USE db;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT, 
    name VARCHAR(50), 
    email VARCHAR(50), 
    password VARCHAR(50),
    phone VARCHAR(15)  -- Added phone column (with a length of 15 for phone numbers)
);

create table prediction (
    id INT PRIMARY KEY AUTO_INCREMENT, 
    email VARCHAR(225),
    name VARCHAR(50),
    disease VARCHAR(1000)
    );