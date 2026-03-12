import sqlite3

db_path = 'diabetics.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Colunas para a tabela 'users'
user_cols = [
    ('training_style', 'TEXT'),
    ('injuries', 'TEXT'),
    ('equipment', 'TEXT'),
    ('caloric_range_limit', 'FLOAT DEFAULT 0.1')
]

# 2. Colunas para a tabela 'nutrition_logs'
nutrition_cols = [
    ('meal_type', "TEXT DEFAULT 'Outros'"),
    ('user_feeling', 'TEXT')
]

# 3. Colunas para a tabela 'workout_logs'
workout_cols = [
    ('feeling', 'TEXT'),
    ('period', 'TEXT'),
    ('duration', 'INTEGER'),
    ('completed', 'BOOLEAN DEFAULT 1'),
    ('progression', 'BOOLEAN DEFAULT 0')
]

def add_columns(table, cols):
    for col_name, col_def in cols:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
            print(f"[{table}] Coluna {col_name} adicionada.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"[{table}] Coluna {col_name} já existe.")
            else:
                print(f"[{table}] Erro ao adicionar {col_name}: {e}")

add_columns('users', user_cols)
add_columns('nutrition_logs', nutrition_cols)
add_columns('workout_logs', workout_cols)

conn.commit()
conn.close()
print("Migração de refinamento concluída.")
