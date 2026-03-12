import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.express as px

# Configuração da página - UI Premium e Moderna (Dark Mode via config)
st.set_page_config(page_title="Diabetes Assistant", page_icon="🩸", layout="wide")

st.markdown("""
    <style>
    .main-title {
        font-size: 3rem;
        color: #4A90E2;
        text-align: center;
        font-weight: bold;
    }
    .sub-title {
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>Assistente Pessoal de Diabetes 🩸</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Seu aliado inteligente no controle da glicemia usando Inteligência Artificial</div>", unsafe_allow_html=True)

# Tabs de Navegação
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🧬 Assistente Pesquisador", 
    "📊 Rotina e Perfil", 
    "🔮 Análise Preditiva", 
    "📑 Exames", 
    "🍎 Dieta e Nutrológico", 
    "💪 Treinador de Elite",
    "🛌 Recovery & Biohacking",
    "⌚ Wearable Hub"
])

API_URL = "http://localhost:8000"
# Header padrão para desenvolvimento local (simula o usuário de teste criado no init_db)
HEADERS = {"Authorization": "Bearer mock-token"}

# --- SIDEBAR: INSIGHTS PROATIVOS (MOTOR AUTÔNOMO) ---
with st.sidebar:
    st.header("📢 Insights do Coach")
    try:
        res_ins = requests.get(f"{API_URL}/autonomous/insights", headers=HEADERS)
        if res_ins.status_code == 200:
            insights = res_ins.json()
            if not insights:
                st.write("Nenhum novo insight no momento. Continue treinando!")
            else:
                for ins in insights:
                    with st.container():
                        if ins['severity'] == "critical":
                            st.error(f"**{ins['topic']}**")
                        elif ins['severity'] == "warning":
                            st.warning(f"**{ins['topic']}**")
                        else:
                            st.info(f"**{ins['topic']}**")
                        
                        st.write(ins['message'])
                        if st.button("Lido", key=f"read_{ins['id']}"):
                            requests.post(f"{API_URL}/autonomous/insights/read/{ins['id']}", headers=HEADERS)
                            st.rerun()
                        st.divider()
        else:
            st.error("Erro ao carregar insights.")
    except Exception as e:
        st.sidebar.write("Ligue o servidor para ver seus insights.")

    st.divider()
    st.header("📲 Quick Log (Voz/Texto)")
    voice_cmd = st.text_input("Diga o que fez (ex: 'Comi 1 banana')", key="voice_input")
    if st.button("Processar Log Rápido"):
        with st.spinner("IA interpretando e salvando..."):
            try:
                res_v = requests.post(f"{API_URL}/automation/voice-log", json={"command": voice_cmd}, headers=HEADERS)
                if res_v.status_code == 200:
                    result = res_v.json()
                    if result.get("status") == "success":
                        st.success(f"✅ {result['message']}")
                        st.json(result["data"])
                        st.info("O Motor Autônomo já reanalisou seu perfil.")
                        st.rerun()
                    else:
                        st.error(result.get("message"))
                        st.write("Interpretado como:")
                        st.code(result.get("raw"))
                else:
                    st.error("Falha ao interpretar.")
            except: st.error("Erro de conexão.")

    st.divider()
    st.header("📄 Relatórios Expert")
    if st.button("Gerar Relatório Seleção Elite (PDF)"):
        with st.spinner("Compilando dados metabólicos e de treino..."):
            try:
                res_r = requests.get(f"{API_URL}/reports/expert", headers=HEADERS)
                if res_r.status_code == 200:
                    st.download_button(
                        label="📥 Download Relatório PDF",
                        data=res_r.content,
                        file_name=f"Relatorio_Performance_Leo_{datetime.now().strftime('%d_%m_%Y')}.pdf",
                        mime="application/pdf"
                    )
                    st.success("Relatório gerado com sucesso!")
                else:
                    st.error("Erro ao gerar relatório no servidor.")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")

with tab1:
    st.header("Assistente Pesquisador Médico")
    st.write("Faça perguntas baseadas em literatura científica sobre diabetes tipo 1 e 2.")
    
    question = st.text_input("Qual a sua dúvida hoje?", placeholder="Ex: O uso contínuo de insulina basal X afeta a resistência à insulina?")
    if st.button("Pesquisar", type="primary"):
        if question:
            with st.spinner("Pesquisando nos artigos científicos..."):
                try:
                    res = requests.post(f"{API_URL}/rag/query", json={"question": question})
                    if res.status_code == 200:
                        data = res.json()
                        st.info(data["answer"])
                        with st.expander("Fontes"):
                            st.json(data["sources"])
                    else:
                        st.error("Erro ao consultar a base de dados.")
                except Exception as e:
                    st.error(f"Erro de conexão com o servidor local: {e}")

    st.divider()
    st.subheader("Adicionar novo Artigo (PDF)")
    uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")
    if uploaded_file is not None:
        if st.button("Ingerir no Banco Vetorial"):
            with st.spinner("Processando e avaliando o PDF..."):
                files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                res = requests.post(f"{API_URL}/rag/upload", files=files, data={"title": uploaded_file.name, "year": 2025}, headers=HEADERS)
                if res.status_code == 200:
                    st.success("Documento processado e armazenado com sucesso!")
                else:
                    st.error("Falha ao processar o documento.")

    st.divider()
    st.subheader("🤖 Agente de Pesquisa Autonóma")
    st.write("Acione o robô para buscar novas descobertas mundiais no PubMed e diabetes.org.br sobre um tema específico.")
    search_topic = st.text_input("Tema de pesquisa", value="Type 1 Diabetes treatments 2025")
    if st.button("Iniciar Pesquisa Global"):
        with st.spinner("O Agente está varrendo a literatura médica mundial..."):
            try:
                res = requests.post(f"{API_URL}/rag/autonomous-research", params={"topic": search_topic}, headers=HEADERS)
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"O Agente encontrou e aprendeu com {data['articles_found']} novos estudos sobre '{search_topic}'!")
                else:
                    st.error("Falha na comunicação com o agente de pesquisa.")
            except Exception as e:
                st.error(f"Erro ao acionar agente: {e}")

with tab2:
    st.header("Gerenciamento de Rotina")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Registrar Nova Medição")
        with st.form("log_form"):
            col_data, col_hora = st.columns(2)
            data_reg = col_data.date_input("Data do Registro", value=datetime.today())
            hora_reg = col_hora.time_input("Hora do Registro", value=datetime.now().time())
            
            glicose = st.number_input("Glicemia (mg/dL)", min_value=0, max_value=600, value=100)
            
            opcoes_momento = [
                "Jejum", "Pré-café da manhã", "Pós-café da manhã",
                "Pré-almoço", "Pós-almoço", "Café da tarde", 
                "Pré-janta", "Pós-janta", "Lanche da madrugada",
                "Pré-treino", "Pós-treino"
            ]
            momento = st.selectbox("Momento do dia", opcoes_momento)
            
            carbos = st.number_input("Carboidratos Ingeridos (g) - Opcional", min_value=0, value=0)
            
            col_ins_r, col_ins_b = st.columns(2)
            insulina_rapida = col_ins_r.number_input("Insulina Rápida (UI)", min_value=0.0, value=0.0, format="%.1f")
            insulina_basal = col_ins_b.number_input("Insulina Basal (UI)", min_value=0.0, value=0.0, format="%.1f")
            
            notas = st.text_area("Anotações (Hábito, Estresse, Esportes)", placeholder="Ex: Comi uma pizza e corri 5km no parque.")
            submitted = st.form_submit_button("Salvar Registro")
            
            if submitted:
                dt_combinada = datetime.combine(data_reg, hora_reg)
                payload = {
                    "glicemia": glicose,
                    "momento": momento,
                    "carboidratos": carbos,
                    "dose_insulina": insulina_rapida,
                    "dose_basal": insulina_basal,
                    "notas": notas,
                    "registrado_em": dt_combinada.isoformat()
                }
                try:
                    res = requests.post(f"{API_URL}/profile/logs", json=payload, headers=HEADERS)
                    if res.status_code == 200:
                        st.success("Log registrado com sucesso!")
                    else:
                        st.error(f"Erro ao salvar: {res.text}")
                except Exception as e:
                    st.error(f"Erro na comunicação com a API: {e}")

    with col2:
        st.subheader("Gráficos e Histórico")
        try:
            res_logs = requests.get(f"{API_URL}/profile/logs", headers=HEADERS)
            if res_logs.status_code == 200 and res_logs.json():
                logs_data = res_logs.json()
                df = pd.DataFrame(logs_data)
                
                # Tratamento de dados para gráficos
                df['registrado_em'] = pd.to_datetime(df['registrado_em'], format='ISO8601', errors='coerce').dt.tz_localize(None)
                df = df.dropna(subset=['registrado_em']) # Remove registros com data inválida
                df = df.sort_values(by='registrado_em')
                
                if 'dose_insulina' not in df.columns:
                    df['dose_insulina'] = 0.0
                if 'dose_basal' not in df.columns:
                    df['dose_basal'] = 0.0
                if 'glicemia' not in df.columns:
                    df['glicemia'] = 0.0
                    
                df['dose_insulina'] = df['dose_insulina'].fillna(0.0)
                df['dose_basal'] = df['dose_basal'].fillna(0.0)
                
                # Gráfico de Glicemia
                df_glic = df.dropna(subset=['glicemia'])
                if not df_glic.empty:
                    # Módulo 5: Dashboard Metabólico (TIR)
                    try:
                        res_met = requests.get(f"{API_URL}/predict/user", headers=HEADERS)
                        if res_met.status_code == 200:
                            data_met = res_met.json()
                            metrics = data_met.get("metrics", {})
                            st.subheader("🧠 Dashboard Metabólico (Módulo 5)")
                            
                            c1, c2, c3 = st.columns(3)
                            c1.metric("TIR (Time in Range)", f"{metrics.get('tir', 0)}%", "Meta > 70%")
                            c2.metric("Variabilidade (SD)", f"{metrics.get('std', 0)} mg/dL", "Ideal < 33")
                            c3.metric("Contagem de Logs", metrics.get('count', 0))
                    except: pass

                    fig_glicemia = px.line(df_glic, x='registrado_em', y='glicemia', markers=True, 
                                           title="Glicemia ao Longo do Tempo", 
                                           labels={'registrado_em': 'Data e Hora', 'glicemia': 'Glicemia (mg/dL)'},
                                           color_discrete_sequence=['#E74C3C'])
                    fig_glicemia.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="Meta")
                    st.plotly_chart(fig_glicemia, use_container_width=True)
                else:
                    st.info("Nenhuma leitura de glicemia disponível para o gráfico.")
                
                # Gráfico de Insulinas
                df_ins = df.melt(id_vars=['registrado_em'], value_vars=['dose_insulina', 'dose_basal'], 
                                 var_name='Tipo de Insulina', value_name='Dose (UI)')
                df_ins['Tipo de Insulina'] = df_ins['Tipo de Insulina'].replace({'dose_insulina': 'Ação Rápida', 'dose_basal': 'Basal'})
                fig_insulina = px.bar(df_ins[df_ins['Dose (UI)'] > 0], x='registrado_em', y='Dose (UI)', color='Tipo de Insulina',
                                      title="Aplicações de Insulina", barmode='group',
                                      labels={'registrado_em': 'Data e Hora'})
                st.plotly_chart(fig_insulina, use_container_width=True)
                
                # Tabela de Histórico e Exportação
                with st.expander("Ver Tabela Completa e Exportar"):
                    df_display = df.copy()
                    df_display['registrado_em'] = df_display['registrado_em'].dt.strftime('%d/%m/%Y %H:%M')
                    st.dataframe(df_display.drop(columns=['id', 'user_id'], errors='ignore'), use_container_width=True)
                    
                    csv_export = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Exportar Histórico Completo (CSV)",
                        data=csv_export,
                        file_name='meu_historico_diabetes.csv',
                        mime='text/csv',
                    )
            else:
                st.info("Nenhum registro encontrado ainda. Preencha o formulário ao lado!")
        except Exception as e:
            st.warning(f"Não foi possível carregar os gráficos. Erro interno: {e}")
            
        st.divider()
        st.subheader("Configurações de Elite e Bio")
        with st.form("user_form"):
            col_u1, col_u2 = st.columns(2)
            nome = col_u1.text_input("Nome", value="Leonardo")
            idade = col_u2.number_input("Idade", value=28)
            peso = col_u1.number_input("Peso (kg)", value=85.0)
            objetivo = col_u2.selectbox("Fase Atual", ["Bulking", "Cutting", "Manutenção"])
            estilo = col_u1.selectbox("Estilo de Treino", ["Hipertrofia", "Força/Powerlifting", "HIT (Heavy Duty)", "Funcional"])
            equipos = col_u2.selectbox("Disponibilidade", ["Academia Completa", "Home Gym", "Apenas Halteres"])
            
            btn_user = st.form_submit_button("Salvar Perfil de Atleta")
            if btn_user:
                payload_u = {
                    "name": nome, "email": "leo@atleta.com", "idade": idade, "peso": peso,
                    "tipo_diabetes": 1, "insulina_basal": "Lantus", "insulina_rapida": "Novorapid",
                    "objetivo": objetivo, "training_style": estilo, "equipment": equipos
                }
                requests.post(f"{API_URL}/profile/me", json=payload_u, headers=HEADERS)
                st.success("Perfil atualizado! O Coach agora conhece suas metas.")

with tab3:
    st.header("Motor Analítico e Preditivo")
    st.write("Baseado no seu histórico, nossa IA buscará padrões cruzando glicemia com alimentação e atividades.")
    
    # Busca a quantidade de registros atuais para informar o usuário
    total_registros = 0
    try:
        res_logs = requests.get(f"{API_URL}/profile/logs", headers=HEADERS)
        if res_logs.status_code == 200:
            total_registros = len(res_logs.json())
    except:
        pass
        
    st.metric(label="Registros de Rotina Coletados", value=f"{total_registros} / 15 mínimos")
    if total_registros < 15:
        st.warning(f"O Agente Analítico precisa de no mínimo 15 registros para identificar padrões precisos. Faltam {15 - total_registros} registros.")
        st.progress(total_registros / 15.0)
    else:
        st.success("Você já possui dados suficientes para uma primeira análise preditiva!")
        st.progress(1.0)
        
    st.divider()
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Importador Universal de Laudos e Planilhas")
        st.write("Você pode acelerar o processo enviando um relatório do mySugr, Libre, PDF médico, CSV, Excel ou TXT. Nossa IA analisará e extrairá tudo para o seu histórico.")
        uploaded_csv = st.file_uploader("Selecione o arquivo", type=["csv", "pdf", "txt", "xlsx", "json"])
        if uploaded_csv is not None:
            if st.button("Analisar com IA e Salvar"):
                with st.spinner("Lendo o documento com a inteligência artificial do Gemini e inserindo no banco..."):
                    files = {"file": (uploaded_csv.name, uploaded_csv, uploaded_csv.type)}
                    try:
                        res = requests.post(f"{API_URL}/profile/import-universal", files=files, headers=HEADERS)
                        if res.status_code == 200:
                            st.success(res.json()["message"])
                        else:
                            st.error(f"Erro ao importar: {res.text}")
                    except Exception as e:
                        st.error(f"Erro de conexão com o painel: {e}")
                        
    with col4:
        st.subheader("Iniciar Análise IA")
        btn_predict = st.button("Gerar Relatório de Insights", type="primary", disabled=(total_registros < 15))
        if btn_predict:
            with st.spinner("O Agente Preditivo está analisando seus dados..."):
                try:
                    res = requests.get(f"{API_URL}/predict/user", headers=HEADERS)
                    if res.status_code == 200:
                        data = res.json()
                        st.markdown("### Análise da IA")
                        st.write(data["analysis"])
                    else:
                        st.error("Sem dados de registro suficientes.")
                except Exception as e:
                    st.error("Erro na comunicação com a API preditiva.")

with tab4:
    st.header("Gestão de Exames Laboratoriais")
    st.write("Suba seus laudos em PDF ou foto para que a IA extraia automaticamente os indicadores e acompanhe sua evolução.")
    
    col_up, col_info = st.columns([1, 2])
    
    with col_up:
        st.subheader("Subir Novo Laudo")
        uploaded_exam = st.file_uploader("Selecione o arquivo (PDF ou Imagem)", type=["pdf", "png", "jpg", "jpeg"])
        if uploaded_exam:
            if st.button("Analisar Laudo com I.A."):
                with st.spinner("Extraindo indicadores médicos..."):
                    files = {"file": (uploaded_exam.name, uploaded_exam, uploaded_exam.type)}
                    try:
                        res = requests.post(f"{API_URL}/exams/upload", files=files, headers=HEADERS)
                        if res.status_code == 200:
                            st.success(f"Exame de {res.json()['data']} processado! {res.json()['indicators_count']} indicadores encontrados.")
                            st.rerun()
                        else:
                            st.error(f"Erro ao processar: {res.text}")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")

    with col_info:
        st.subheader("Últimos Indicadores Extraídos")
        try:
            res_sum = requests.get(f"{API_URL}/exams/summary", headers=HEADERS)
            if res_sum.status_code == 200 and isinstance(res_sum.json(), list):
                summaries = res_sum.json()
                for s in summaries:
                    with st.expander(f"Exame em {s['data']} - Lab: {s['laboratorio']}"):
                        cols = st.columns(len(s['indicadores']) if len(s['indicadores']) < 4 else 4)
                        for i, ind in enumerate(s['indicadores']):
                            with cols[i % 4]:
                                st.metric(label=ind['nome'], value=f"{ind['valor']} {ind['unidade'] or ''}", delta=ind['status'])
            else:
                st.info("Nenhum exame cadastrado. Suba seu primeiro laudo ao lado!")
        except:
            st.error("Erro ao carregar resumo de exames.")

    st.divider()
    st.subheader("Evolução Histórica")
    indicador_foco = st.selectbox("Selecione o indicador para ver o gráfico", ["Hba1c", "Glicemia Jejum", "Colesterol Total", "Triglicerídeos", "Vitamina D"])
    
    if indicador_foco:
        try:
            res_evo = requests.get(f"{API_URL}/exams/evolution/{indicador_foco}", headers=HEADERS)
            if res_evo.status_code == 200 and res_evo.json():
                df_evo = pd.DataFrame(res_evo.json())
                df_evo['data'] = pd.to_datetime(df_evo['data'])
                
                fig_evo = px.line(df_evo, x='data', y='valor', markers=True, 
                                  title=f"Evolução de: {indicador_foco}",
                                  labels={'data': 'Data do Exame', 'valor': f'Valor ({df_evo["unidade"].iloc[0] if "unidade" in df_evo.columns else ""})'},
                                  color_discrete_sequence=['#2ecc71'])
                st.plotly_chart(fig_evo, use_container_width=True)
            else:
                st.write(f"Ainda não há dados suficientes para gerar o gráfico de {indicador_foco}.")
        except Exception as e:
            st.error(f"Erro ao gerar gráfico de evolução: {e}")

with tab5:
    st.header("Nutrição e Nutrologia Esportiva")
    
    # Status de Macros
    try:
        res_macro = requests.get(f"{API_URL}/nutrition/status", headers=HEADERS)
        if res_macro.status_code == 200:
            data = res_macro.json()
            targets = data["targets"]
            current = data["current"]
            rem = data["remaining"]
            
            st.subheader(f"Objetivo: {targets['objetivo']}")
            
            # Alerta de IA se houver desvios significativos
            if "guidance" in data and data["guidance"] != "Dentro da faixa. Continue focado no plano!":
                st.warning(f"⚠️ **ALERTA DO COACH:** {data['guidance']}")
            else:
                st.success("✅ Você está seguindo o plano nutricional perfeitamente!")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Proteína", f"{int(current['proteina'])}g / {int(targets['proteina'])}g", f"{int(rem['proteina'])}g", delta_color="inverse")
            m2.metric("Carbo", f"{int(current['carbo'])}g / {int(targets['carbo'])}g", f"{int(rem['carbo'])}g")
            m3.metric("Gordura", f"{int(current['gordura'])}g / {int(targets['gordura'])}g", f"{int(rem['gordura'])}g")
            m4.metric("Calorias", f"{int(current['calorias'])} / {int(targets['calorias'])}", f"{int(rem['calorias'])}")
            
            # Progress bar visual
            st.progress(min(current['calorias'] / targets['calorias'], 1.0))
        else:
            st.info("Configure seus macros no perfil para começar.")
    except:
        st.error("Erro ao carregar dados de nutrição.")

    st.divider()
    st.subheader("Registrar Refeição")
    with st.form("form_nutrition"):
        alimento = st.text_input("O que você comeu?", placeholder="Ex: Frango e Batata Doce")
        col_n1, col_n2, col_n3, col_n4 = st.columns(4)
        c_cal = col_n1.number_input("Kcal", min_value=0, value=300)
        c_prot = col_n2.number_input("Prot (g)", min_value=0, value=25)
        c_carb = col_n3.number_input("Carbo (g)", min_value=0, value=30)
        c_fat = col_n4.number_input("Gord (g)", min_value=0, value=5)
        c_tipo = st.selectbox("Tipo de Refeição", ["Café da Manhã", "Almoço", "Lanche", "Jantar", "Ceia", "Pré-Treino (Jejum)", "Pós-Treino"])
        c_feeling = st.selectbox("Como se sentiu após comer?", ["Energizado", "Pesado", "Fome", "Normal"])
        c_momento = st.text_input("Obs de Momento", value="Geral")
        
        if st.form_submit_button("Lançar Refeição Detalhada"):
            payload = {
                "alimento": alimento,
                "calorias": float(c_cal),
                "proteina": float(c_prot),
                "carbo": float(c_carb),
                "gordura": float(c_fat),
                "meal_type": c_tipo,
                "user_feeling": c_feeling,
                "momento": c_momento
            }
            try:
                res = requests.post(f"{API_URL}/nutrition/log", json=payload, headers=HEADERS)
                if res.status_code == 200:
                    st.success("Refeição salva!")
                    st.info(f"💬 Coach: {res.json()['feedback_coach']}")
                    st.rerun()
                else:
                    st.error("Erro ao salvar refeição.")
            except:
                st.error("Erro de conexão com o servidor.")

with tab6:
    st.header("Treinador de Elite (Bodybuilding)")
    st.write("Baseado nas metodologias de Hany Rambod, Pacholok e Marcelo Cruz.")
    
    # Buscar programa ativo
    try:
        res_work = requests.get(f"{API_URL}/workouts/active", headers=HEADERS)
        if res_work.status_code == 200 and "program_name" in res_work.json():
            data = res_work.json()
            st.subheader(f"Programa Atual: {data['program_name']}")
            
            for ex in data["exercises"]:
                with st.expander(f"🏋️ {ex['nome']} ({ex['series']}x{ex['repeticoes']})"):
                    st.write(f"Descanso: {ex['descanso']}s | Notas: {ex['notas']}")
                    
                    # Logar série
                    with st.form(f"log_ex_{ex['id']}"):
                        c_ex1, c_ex2 = st.columns(2)
                        f_carga = c_ex1.number_input("Carga (kg)", min_value=0.0, step=0.5, key=f"c_{ex['id']}")
                        f_reps = c_ex2.number_input("Reps feitas", min_value=0, value=10, key=f"r_{ex['id']}")
                        f_rpe = st.slider("Esforço (RPE 1-10)", 1, 10, 8, key=f"s_{ex['id']}")
                        
                        st.write("**Feedback de Performance:**")
                        f_feeling = st.selectbox("Humor/Feeling", ["Explosivo", "Cansado", "Foco Total", "Desmotivado"], key=f"f_{ex['id']}")
                        f_prog = st.checkbox("Houve progressão (Carga ou Reps)?", key=f"p_{ex['id']}")
                        f_dur = st.number_input("Duração (segundos) - Opcional", min_value=0, value=45, key=f"d_{ex['id']}")
                        
                        if st.form_submit_button("Registrar Série de Elite"):
                            payload_ex = {
                                "exercise_id": ex['id'],
                                "carga": float(f_carga),
                                "reps_reais": int(f_reps),
                                "rpe": int(f_rpe),
                                "feeling": f_feeling,
                                "progression": f_prog,
                                "duration": f_dur
                            }
                            res_log = requests.post(f"{API_URL}/workouts/log", json=payload_ex, headers=HEADERS)
                            if res_log.status_code == 200:
                                st.success("Série registrada!")
                                st.info(f"💬 Coach Tip: {res_log.json()['coach_tip']}")
                            else:
                                st.error("Erro ao salvar série.")
        else:
            st.info("Ainda não temos um programa ativo para o seu perfil.")
            if st.button("🤖 Sugerir 3 Opções de Treino Profissional"):
                with st.spinner("Analisando seu perfil e bibliografias..."):
                    try:
                        res_opt = requests.get(f"{API_URL}/workouts/options", headers=HEADERS)
                        if res_opt.status_code == 200:
                            opts = res_opt.json()
                            for i, o in enumerate(opts):
                                st.subheader(f"Opção {i+1}: {o['title']}")
                                st.write(o['description'])
                                if st.button(f"Selecionar Plano {i+1}", key=f"sel_{i}"):
                                    st.success("Plano selecionado! (Funcionalidade de troca de ficha em breve)")
                        else:
                            st.error("Erro ao carregar opções.")
                    except: st.error("Erro de conexão.")
    except:
        st.error("Erro ao carregar programas de treino.")

    st.divider()
    st.subheader("🧬 Análise de Padrões de Performance")
    if st.button("Analisar Humor vs. Carga"):
        with st.spinner("Cruzando dados de logs com I.A..."):
            try:
                res_pat = requests.get(f"{API_URL}/workouts/patterns", headers=HEADERS)
                if res_pat.status_code == 200:
                    st.info(res_pat.content.decode('utf-8'))
                else:
                    st.error("Sem dados suficientes.")
            except: st.error("Erro de conexão.")

with tab7:
    st.header("Metabolic Battery & Recovery Engine")
    st.write("Monitore seu sono e HRV para otimizar sua prontidão para o treino de elite.")
    
    # Dashboard de Prontidão
    try:
        res_rec = requests.get(f"{API_URL}/recovery/latest", headers=HEADERS)
        if res_rec.status_code == 200:
            rec_data = res_rec.json()
            if "readiness_score" in rec_data:
                score = rec_data["readiness_score"]
                st.subheader(f"Bateria Metabólica: {score}%")
                
                # Barra de progresso colorida
                st.progress(score / 100)
                st.info(f"💬 **Conselho do Coach:** {rec_data['advice']}")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Sono", f"{rec_data['sleep_hours']}h")
                c2.metric("HRV", f"{rec_data['hrv']}ms")
                c3.metric("Último Log", rec_data['registrado_em'][:10])
            else:
                st.info("Ainda não temos dados de recuperação para hoje.")
    except:
        st.error("Erro ao carregar hub de recuperação.")

    st.divider()
    
    # Formulário de Log
    st.subheader("Registrar Noite de Sono & HRV")
    with st.form("recovery_form"):
        col1, col2 = st.columns(2)
        sleep = col1.number_input("Horas de Sono", min_value=0.0, max_value=24.0, value=8.0)
        deep = col2.number_input("Sono Profundo (h)", min_value=0.0, max_value=sleep, value=1.5)
        
        col3, col4 = st.columns(2)
        hrv_val = col3.number_input("HRV (ms)", min_value=0, max_value=200, value=65)
        rhr = col4.number_input("RHR (Batimentos Repouso)", min_value=30, max_value=120, value=55)
        
        stress = st.slider("Nível de Estresse Percebido (1-10)", 1, 10, 3)
        notes = st.text_area("Notas sobre o despertar/vibe")
        
        if st.form_submit_button("Salvar e Analisar Readiness"):
            payload = {
                "sleep_hours": sleep,
                "deep_sleep_hours": deep,
                "hrv": hrv_val,
                "resting_heart_rate": rhr,
                "stress_level": stress,
                "notas": notes
            }
            try:
                res_log = requests.post(f"{API_URL}/recovery/log", json=payload, headers=HEADERS)
                if res_log.status_code == 200:
                    st.success("Dados de recuperação registrados! O motor autônomo foi notificado.")
                    st.rerun()
                else:
                    st.error("Erro ao salvar dados.")
            except: st.error("Erro de conexão.")

    st.divider()
    st.subheader("🧪 Biohacking Experiments (M11)")
    
    # Lista de Experimentos
    try:
        res_exps = requests.get(f"{API_URL}/experiments/list", headers=HEADERS)
        if res_exps.status_code == 200:
            experiments = res_exps.json()
            if experiments:
                for ex in experiments:
                    with st.expander(f"🔬 {ex['title']} ({ex['status']})"):
                        st.write(f"**Hipótese:** {ex['hypothesis']}")
                        st.write(f"**Métrica Monitorada:** {ex['metric_to_monitor']}")
                        st.write(f"**Início:** {ex['start_date'][:10]}")
                        if ex['status'] == "ativo":
                            if st.button("Finalizar Experimento", key=f"close_{ex['id']}"):
                                requests.post(f"{API_URL}/experiments/close/{ex['id']}?summary=Hipótese validada com sucesso via dados de CGM.", headers=HEADERS)
                                st.rerun()
                        else:
                            st.write(f"**Fim:** {ex['end_date'][:10]}")
                            st.info(f"**Resultado:** {ex['results_summary']}")
            else:
                st.info("Nenhum experimento ativo. Que tal testar uma nova estratégia de timing?")
    except: st.error("Erro ao carregar experimentos.")

    # Criar Novo
    with st.popover("➕ Novo Experimento Biohacking"):
        new_title = st.text_input("Título do Teste", placeholder="Ex: Palatinose Pré-Treino")
        new_hyp = st.text_area("Hipótese", placeholder="Ex: Reduzir a queda glicêmica no meio do treino de pernas.")
        new_metric = st.selectbox("Métrica Principal", ["TIR", "Pico Pós-Prandial", "Glicemia Jejum", "Variabilidade"])
        
        if st.button("Lançar Experimento"):
            try:
                payload_exp = {"title": new_title, "hypothesis": new_hyp, "metric_to_monitor": new_metric}
                res_new = requests.post(f"{API_URL}/experiments/create", json=payload_exp, headers=HEADERS)
                if res_new.status_code == 200:
                    st.success("Experimento lançado! O Motor Autônomo monitorará essa métrica.")
                    st.rerun()
            except: st.error("Erro de conexão.")

with tab8:
    st.header("⌚ Hub de Wearables & Automação")
    st.write("Gerencie a conexão com seus dispositivos de elite para automação total de dados.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg", width=50)
        st.subheader("Apple Health")
        st.write("Status: 🟢 Conectado")
        st.button("Sincronizar Agora", key="sync_apple")
        
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b7/Garmin_logo.svg", width=50)
        st.subheader("Garmin Connect")
        st.write("Status: 🔴 Desconectado")
        st.button("Conectar Garmin", key="conn_garmin")
        
    with col3:
        st.image("https://upload.wikimedia.org/wikipedia/commons/0/03/Dexcom_logo.svg", width=50) # Mock
        st.subheader("CGM (Libre/Dexcom)")
        st.write("Status: 🟡 Aguardando Sensor")
        st.button("Vincular Sensor", key="conn_cgm")

    st.divider()
    st.subheader("🚀 Simulação de Fluxo de Dados (M9)")
    st.info("Esta seção simula a chegada de dados via Webhook/API dos seus dispositivos.")
    
    if st.button("Simular 24h de CGM (Sensor Contínuo)"):
        with st.spinner("Recebendo stream de 288 pontos..."):
            try:
                # Vamos injetar dados aleatórios reais
                import random
                from datetime import datetime, timedelta
                now = datetime.utcnow()
                data_points = []
                curr = 120
                for i in range(288):
                    curr = max(70, min(180, curr + random.randint(-5, 5)))
                    data_points.append({"value": curr, "timestamp": (now - timedelta(minutes=5*i)).isoformat()})
                
                res = requests.post(f"{API_URL}/automation/cgm/ingest", json=data_points, headers=HEADERS)
                if res.status_code == 200:
                    st.success(f"Sucesso! {res.json()['count']} registros processados automaticamente.")
                    st.info("Insights de IA gerados baseados na nova curva glicêmica.")
                else: st.error("Erro na ingestão.")
            except: st.error("Erro de conexão.")

    if st.button("Simular Sincronização de Sono (Garmin/Apple)"):
        with st.spinner("Buscando métricas de HRV e Sono..."):
            try:
                # Simular log de recuperação
                payload = {
                    "sleep_hours": 7.5,
                    "deep_sleep_hours": 1.8,
                    "hrv": 72,
                    "resting_heart_rate": 52,
                    "stress_level": 2,
                    "notas": "Sincronizado via Wearable Hub."
                }
                res = requests.post(f"{API_URL}/recovery/log", json=payload, headers=HEADERS)
                if res.status_code == 200:
                    st.success("Métricas de recuperação atualizadas via Wearable!")
                    st.rerun()
                else: st.error("Erro ao sincronizar.")
            except: st.error("Erro de conexão.")


