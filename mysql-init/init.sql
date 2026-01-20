-- Initial sample schema for local development

-- Ensure main database exists (also created via MYSQL_DATABASE)
CREATE DATABASE IF NOT EXISTS sampledb;

USE sampledb;

CREATE TABLE IF NOT EXISTS categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  description TEXT,
  category_id INT NULL,
  CONSTRAINT fk_products_category
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Optional second database referenced in docs
CREATE DATABASE IF NOT EXISTS okul;

USE okul;

CREATE TABLE IF NOT EXISTS ogrenciler (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ad VARCHAR(100) NOT NULL,
  soyad VARCHAR(100) NOT NULL,
  yas INT NOT NULL
);
