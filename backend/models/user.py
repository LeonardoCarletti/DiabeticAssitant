from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True) # Firebase UID
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="student") # coach, student, health_pro, admin
    coach_id = Column(String, ForeignKey("users.id"), nullable=True) # If managed by a coach
    workspace_id = Column(String, nullable=True) # For workspace-based management
    
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
    protocols = relationship("TrainingProtocol", back_populates="user")
    feedbacks = relationship("TrainingFeedback", back_populates="user", foreign_keys="[TrainingFeedback.user_id]")
    
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

# --- NOVO MODULO DE TREINAMENTO ---

class TrainingProtocol(Base):
    __tablename__ = "training_protocols"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String) # ex: "Fase 1 - Hipertrofia Base"
    objective = Column(String, nullable=True)
    freq_weekly = Column(Integer, nullable=True)
    duration_weeks = Column(Integer, nullable=True)
    observations = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(String, ForeignKey("users.id"), nullable=True) # Coach who created it
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="protocols", foreign_keys=[user_id])
    sessions = relationship("TrainingSession", back_populates="protocol", cascade="all, delete-orphan")

class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    protocol_id = Column(Integer, ForeignKey("training_protocols.id"))
    name = Column(String) # ex: "Treino A - Inferiores"
    order = Column(Integer)
    day_of_week = Column(String, nullable=True) # ex: "Segunda", ou "Dia 1"
    observations = Column(Text, nullable=True)
    
    # Componentes complementares
    warmup_notes = Column(Text, nullable=True)
    mobility_notes = Column(Text, nullable=True)
    cardio_notes = Column(Text, nullable=True)
    post_workout_notes = Column(Text, nullable=True)

    protocol = relationship("TrainingProtocol", back_populates="sessions")
    exercises = relationship("Exercise", back_populates="session", cascade="all, delete-orphan")

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"))
    name = Column(String)
    photo_url = Column(String, nullable=True)
    stimulus_type = Column(String, nullable=True) # ex: "Hipertrofia", "Método Rest-Pause"
    order = Column(Integer)
    is_locked = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    session = relationship("TrainingSession", back_populates="exercises")
    sets = relationship("ExerciseSet", back_populates="exercise", cascade="all, delete-orphan")
    logs = relationship("WorkoutLog", back_populates="exercise")

class ExerciseSet(Base):
    __tablename__ = "exercise_sets"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    set_number = Column(Integer)
    set_type = Column(String) # "warmup", "feeder", "valid"
    planned_reps = Column(String, nullable=True) # ex: "8-12"
    planned_weight = Column(Float, nullable=True)
    
    exercise = relationship("Exercise", back_populates="sets")
    logs = relationship("WorkoutLog", back_populates="set")

class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    set_id = Column(Integer, ForeignKey("exercise_sets.id"), nullable=True)
    
    weight = Column(Float) # actual kg
    reps = Column(Integer) # actual reps
    rpe = Column(Integer, nullable=True) # 1-10
    feeling = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="workout_logs")
    exercise = relationship("Exercise", back_populates="logs")
    set = relationship("ExerciseSet", back_populates="logs")

class TrainingFeedback(Base):
    __tablename__ = "training_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    coach_id = Column(String, ForeignKey("users.id"))
    protocol_id = Column(Integer, ForeignKey("training_protocols.id"), nullable=True)
    session_log_id = Column(Integer, nullable=True) # Could link to a specific session execution group
    
    content = Column(Text)
    feedback_type = Column(String) # "daily", "periodic"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="feedbacks", foreign_keys=[user_id])

# --- OUTROS MODELS ---

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
