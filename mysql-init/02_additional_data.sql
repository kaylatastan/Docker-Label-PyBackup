-- Seed data for local development

USE sampledb;

INSERT INTO categories (name) VALUES
  ('Electronics'),
  ('Books')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- If this script is re-run, avoid duplicating product rows by checking existing ids
INSERT INTO products (id, name, price, description, category_id) VALUES
  (1, 'Laptop', 1200.00, 'High performance laptop', 1),
  (2, 'Smartphone', 800.00, 'Latest model smartphone', 1),
  (3, 'Docker Book', 35.00, 'Intro to containers', 2)
ON DUPLICATE KEY UPDATE
  name=VALUES(name),
  price=VALUES(price),
  description=VALUES(description),
  category_id=VALUES(category_id);

USE okul;

INSERT INTO ogrenciler (id, ad, soyad, yas) VALUES
  (1, 'Ali', 'Yilmaz', 20),
  (2, 'Ayse', 'Kaya', 22),
  (3, 'Mehmet', 'Demir', 19)
ON DUPLICATE KEY UPDATE
  ad=VALUES(ad),
  soyad=VALUES(soyad),
  yas=VALUES(yas);
