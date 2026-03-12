from backend.core.database import engine, Base, SessionLocal
from backend.models.user import User

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Inserir usuário de teste padrão para desenvolvimento local
db = SessionLocal()
try:
    if not db.query(User).filter(User.id == "leo_mock_id").first():
        test_user = User(
            id="leo_mock_id",
            name="Leonardo Atleta",
            email="leonardo@atleta.com",
            idade=30,
            peso=85.0,
            tipo_diabetes=1,
            insulina_basal="Lantus",
            insulina_rapida="Novorapid",
            nivel_atividade="Atleta",
            training_style="Hipertrofia"
        )
        db.add(test_user)
        db.commit()
        print("Usuário de teste 'leo_mock_id' criado.")
except Exception as e:
    print(f"Erro ao criar usuário inicial: {e}")
finally:
    db.close()

print("Banco de dados inicializado com sucesso!")
