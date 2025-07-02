import mysql.connector

def main():
    # MariaDB'ye bağlanma
    conn = mysql.connector.connect(
        host='mysql',          # Docker network içerisindeki servis adı
        user='root',
        password='rootpassword',
        database='okul'
    )
    cursor = conn.cursor()
    
    # Örnek tablo oluşturma (yoksa oluşturur)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        age INT NOT NULL
    )
    ''')
    conn.commit()
    
    # Örnek veri ekleme
    sample_students = [
        ('Ali', 20),
        ('Ayşe', 22),
        ('Mehmet', 19)
    ]
    cursor.executemany('INSERT INTO students (name, age) VALUES (%s, %s)', sample_students)
    conn.commit()
    
    print(f"{cursor.rowcount} satır eklendi.")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
