from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

def test_conn():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    print(f"Testando conexão para: {url[:20]}...")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"Sucesso! Resultado: {result.fetchone()}")
    except Exception as e:
        print(f"Erro na conexão: {e}")

if __name__ == "__main__":
    test_conn()
