CREATE DATABASE IF NOT EXISTS modshah_scholarship;
USE modshah_scholarship;
CREATE TABLE IF NOT EXISTS users(
 id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(120) NOT NULL,
 email VARCHAR(190) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL,
 role ENUM('student','admin') NOT NULL DEFAULT 'student',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS students(
 id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL UNIQUE,
 education VARCHAR(120), marks DECIMAL(5,2), annual_income DECIMAL(12,2),
 location VARCHAR(120), category VARCHAR(60),
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS scholarships(
 id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(180) NOT NULL,
 provider VARCHAR(180) NOT NULL, description TEXT, amount DECIMAL(12,2),
 deadline DATE NULL, official_url VARCHAR(500), minimum_marks DECIMAL(5,2),
 income_limit DECIMAL(12,2), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS applications(
 id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, scholarship_id INT NOT NULL,
 status ENUM('Interested','Preparing','Submitted','Approved','Rejected') DEFAULT 'Interested',
 applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE KEY unique_application(user_id,scholarship_id),
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(scholarship_id) REFERENCES scholarships(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS documents(
 id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, original_name VARCHAR(255) NOT NULL,
 stored_name VARCHAR(255) NOT NULL, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
INSERT INTO scholarships(title,provider,description,official_url)
SELECT 'National Scholarship Portal opportunities','Government of India',
'Demo listing only. Check the official portal for current schemes and eligibility.',
'https://scholarships.gov.in/'
WHERE NOT EXISTS(SELECT 1 FROM scholarships WHERE title='National Scholarship Portal opportunities');
