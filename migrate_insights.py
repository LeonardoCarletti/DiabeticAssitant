import sqlite3
import os

db_path = "c:\\Users\\leonardo.carletti\\OneDrive\\Documentos\\Diabetics Assitant\\diabetics.db"

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Criando tabela 'insights'...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT,
                message TEXT,
                severity TEXT,
                read BOOLEAN DEFAULT 0,
                registrado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()
        print("Tabela 'insights' criada com sucesso!")
    except Exception as e:
        print(f"Erro ao criar tabela: {e}")
    
    conn.close()

if __name__ == "__main__":
    migrate()
