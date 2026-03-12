from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True) # Firebase UID
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    idade = Column(Integer)
    peso = Column(Float)
    tipo_diabetes = Column(Integer) # 1 or 2
    insulina_basal = Column(String)
    insulina_rapida = Column(String)
    objetivo = Column(String, default="Manutenção") # Cutting, Bulking, Manutenção
    calorias_alvo = Column(Float, default=2000.0)
    proteina_alvo = Column(Float, default=150.0)
    carbo_alvo = Column(Float, default=200.0)
    gordura_alvo = Column(Float, default=60.0)
    nivel_atividade = Column(String, default="Moderado")
    
    # Relacionamentos
    daily_logs = relationship("DailyLog", back_populates="user")
    nutrition_logs = relationship("NutritionLog", back_populates="user")
    workout_logs = relationship("WorkoutLog", back_populates="user")
    medical_exams = relationship("MedicalExam", back_populates="user")
    insights = relationship("Insight", back_populates="user")
    recovery_logs = relationship("RecoveryLog", back_populates="user")
    experiments = relationship("Experiment", back_populates="user")
    training_style = Column(String, nullable=True) # HIT, Volume, Powerlifting, etc
    injuries = Column(String, nullable=True)
    equipment = Column(String, nullable=True) # Full Gym, Home, etc
    caloric_range_limit = Column(Float, default=0.1) # 10%
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    glicemia = Column(Float) # Glicemia medida
    momento = Column(String) # ex: "jejum", "pos-prandial", "madrugada"
    carboidratos = Column(Float, nullable=True) # qtd de carbo ingerido 
    dose_insulina = Column(Float, nullable=True) # unidades aplicadas ação rápida
    dose_basal = Column(Float, nullable=True) # unidades aplicadas ação lenta/basal
    notas = Column(String, nullable=True)
    registrado_em = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="daily_logs")

class MedicalExam(Base):
    __tablename__ = "medical_exams"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    data_exame = Column(DateTime)
    laboratorio = Column(String, nullable=True)
    laudo_bruto = Column(String, nullable=True) # Texto extraído do PDF/Imagem
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="medical_exams")

class ExamIndicator(Base):
    __tablename__ = "exam_indicators"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("medical_exams.id"))
    nome = Column(String, index=True) # ex: "Hba1c", "Glicemia Jejum"
    valor = Column(Float)
    unidade = Column(String) # ex: "%", "mg/dL"
    referencia = Column(String, nullable=True) # ex: "4.0 - 5.6"
    status = Column(String, nullable=True) # ex: "Normal", "Alto", "Baixo"

class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    alimento = Column(String)
    calorias = Column(Float)
    proteina = Column(Float)
    carbo = Column(Float)
    gordura = Column(Float)
    momento = Column(String) # ex: "Pré-treino", "Almoço"
    meal_type = Column(String, default="Outros") # Café, Almoço, Janta, etc
    user_feeling = Column(String, nullable=True) # humor ao comer
    registrado_em = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="nutrition_logs")

class WorkoutProgram(Base):
    __tablename__ = "workout_programs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    nome = Column(String) # ex: "Push/Pull/Legs - Elite"
    objetivo = Column(String) # ex: "Hipertrofia", "Força"
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("workout_programs.id"))
    nome = Column(String)
    series = Column(Integer)
    repeticoes = Column(String) # ex: "8-12" ou "falha"
    descanso = Column(Integer) # segundos
    ordem = Column(Integer)
    notas = Column(String, nullable=True)

class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    carga = Column(Float) # kg
    reps_reais = Column(Integer)
    rpe = Column(Integer, nullable=True) # 1-10 esforço percebido
    feeling = Column(String, nullable=True) # como se sentiu no dia
    period = Column(String, nullable=True) # manhã, tarde, noite
    duration = Column(Integer, nullable=True) # minutos totais da sessão ou exercício
    completed = Column(Boolean, default=True)
    progression = Column(Boolean, default=False)
    user = relationship("User", back_populates="workout_logs")
    registrado_em = Column(DateTime(timezone=True), server_default=func.now())

class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    topic = Column(String) # Ex: "Metabólico", "Treino", "Dieta"
    message = Column(Text)
    severity = Column(String) # "info", "warning", "critical"
    read = Column(Boolean, default=False)
    registrado_em = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="insights")

class RecoveryLog(Base):
    __tablename__ = "recovery_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    sleep_hours = Column(Float)
    deep_sleep_hours = Column(Float, nullable=True)
    hrv = Column(Integer, nullable=True) # Heart Rate Variability
    resting_heart_rate = Column(Integer, nullable=True)
    stress_level = Column(Integer, nullable=True) # 1-10
    readiness_score = Column(Integer, nullable=True) # 0-100
    notas = Column(Text, nullable=True)
    registrado_em = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="recovery_logs")

class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String) # Ex: "Palatinose no Intra-treino"
    hypothesis = Column(Text) # Ex: "Reduzir picos reativos"
    status = Column(String, default="ativo") # ativo, concluído, arquivado
    metric_to_monitor = Column(String) # "TIR", "Pico Pós-Treino", "Glicemia Jejum"
    start_date = Column(DateTime, server_default=func.now())
    end_date = Column(DateTime, nullable=True)
    results_summary = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="experiments")
