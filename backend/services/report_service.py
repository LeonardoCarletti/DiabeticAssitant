from fpdf import FPDF
from sqlalchemy.orm import Session
from backend.models.user import DailyLog, NutritionLog, WorkoutLog, RecoveryLog, User
from datetime import datetime, timedelta
import os

class ReportService:
    def generate_expert_report(self, db: Session, user_id: str):
        user = db.query(User).filter(User.id == user_id).first()
        since = datetime.utcnow() - timedelta(days=7)
        
        logs = db.query(DailyLog).filter(DailyLog.user_id == user_id, DailyLog.registrado_em >= since).all()
        meals = db.query(NutritionLog).filter(NutritionLog.user_id == user_id, NutritionLog.registrado_em >= since).all()
        workouts = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id, WorkoutLog.registrado_em >= since).all()
        recovery = db.query(RecoveryLog).filter(RecoveryLog.user_id == user_id, RecoveryLog.registrado_em >= since).all()

        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, "Relatório de Performance Elite - Diabetics Assistant", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(190, 10, f"Atleta: {user.name if user else 'Leonardo'} | Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align="C")
        pdf.ln(10)

        # Resumo Metabólico
        pdf.set_font("Arial", "B", 14)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(190, 10, "1. Resumo Metabólico (Últimos 7 dias)", ln=True, fill=True)
        pdf.set_font("Arial", "", 12)
        
        if logs:
            avg_glic = sum([l.glicemia for l in logs]) / len(logs)
            tir = (len([l for l in logs if 70 <= l.glicemia <= 180]) / len(logs)) * 100
            pdf.cell(190, 8, f"- Glicemia Média: {avg_glic:.1f} mg/dL", ln=True)
            pdf.cell(190, 8, f"- Time in Range (TIR): {tir:.1f}%", ln=True)
            pdf.cell(190, 8, f"- Total de Registros: {len(logs)}", ln=True)
        else:
            pdf.cell(190, 8, "Nenhum registro de glicemia nos últimos 7 dias.", ln=True)
        pdf.ln(5)

        # Recuperação
        pdf.set_font("Arial", "B", 14)
        pdf.set_fill_color(220, 255, 220)
        pdf.cell(190, 10, "2. Recuperação & Prontidão", ln=True, fill=True)
        pdf.set_font("Arial", "", 12)
        
        if recovery:
            avg_sleep = sum([r.sleep_hours for r in recovery]) / len(recovery)
            avg_hrv = sum([r.hrv for r in recovery]) / len(recovery)
            pdf.cell(190, 8, f"- Média de Sono: {avg_sleep:.1f}h", ln=True)
            pdf.cell(190, 8, f"- Média de HRV: {avg_hrv:.1f} ms", ln=True)
        else:
            pdf.cell(190, 8, "Sem dados de wearable sincronizados.", ln=True)
        pdf.ln(5)

        # Treino e Nutrição
        pdf.set_font("Arial", "B", 14)
        pdf.set_fill_color(255, 230, 200)
        pdf.cell(190, 10, "3. Atividade e Nutrição", ln=True, fill=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(190, 8, f"- Treinos Realizados: {len(workouts)}", ln=True)
        pdf.cell(190, 8, f"- Refeições Logadas: {len(meals)}", ln=True)
        
        # Footer / Disclaimer
        pdf.ln(20)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(190, 5, "Este relatório foi gerado automaticamente por I.A. e não substitui consulta médica. "
                              "Os dados refletem o histórico inserido pelo usuário no Diabetics Assistant.")

        filename = f"report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join("tmp", filename)
        
        if not os.path.exists("tmp"):
            os.makedirs("tmp")
            
        pdf.output(filepath)
        return filepath
