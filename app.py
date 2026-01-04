import streamlit as st
import pandas as pd
import json
import random
from datetime import datetime
from github import Github
from groq import Groq

# Configuração da página
st.set_page_config(page_title="Diário Katheryn & Jhonata 2026", layout="wide")

# Inicialização de APIs via Secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

client_groq = Groq(api_key=GROQ_API_KEY)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)

def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        return json.loads(contents.decoded_content.decode())
    except:
        return {}

def save_data(new_data):
    file_path = "data_2026.json"
    all_data = load_data()
    date_str = datetime.now().strftime("%Y-%m-%d")
    all_data[date_str] = new_data
    json_data = json.dumps(all_data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, f"Registro {date_str}", json_data, contents.sha)
    except:
        repo.create_file(file_path, f"Initial commit", json_data)

data_history = load_data()

# --- SIDEBAR / NAVEGAÇÃO ---
st.sidebar.title("❤️ Menu Principal")
menu = st.sidebar.radio("Ir para:", ["Registrar Dia", "Insights e Dicas", "Histórico e Gráficos"])

if menu == "Registrar Dia":
    st.header(f"📝 Registro Diário - {datetime.now().strftime('%d/%m/%Y')}")
    
    with st.form("diario_form"):
        st.subheader("⚡ Quick Check (Sim/Não)")
        c1, c2, c3 = st.columns(3)
        q1 = c1.radio("Conversamos sem telas?", ["Sim", "Não"])
        q2 = c2.radio("Rimos juntos hoje?", ["Sim", "Não"])
        q3 = c3.radio("Fiz um elogio hoje?", ["Sim", "Não"])
        q4 = c1.radio("Demonstramos afeto?", ["Sim", "Não"])
        q5 = c2.radio("Estresse externo alto?", ["Sim", "Não"])
        q6 = c3.radio("Saímos da rotina?", ["Sim", "Não"])

        st.divider()
        
        col_a, col_b = st.columns(2)
        with col_a:
            eu_fiz = st.multiselect("O que eu fiz por ela:", ["Flores", "Elogios", "Ajuda em casa", "Presente", "Ouvir", "Cozinhar", "Massagem"])
            recebi = st.multiselect("O que ela fez por mim:", ["Carinho", "Apoio emocional", "Presente", "Cuidado", "Elogio", "Beijos"])
        
        with col_b:
            fizemos = st.multiselect("O que fizemos juntos:", ["Jantar fora", "Filme/Série", "Passeio", "Conversa profunda", "Treino/Esporte"])
            
            # Discussão Dinâmica
            teve_disc = st.checkbox("Houve discussão?")
            motivo_disc = ""
            if teve_disc:
                motivos_existentes = list(set([v.get("motivo_disc", "") for v in data_history.values() if v.get("motivo_disc")]))
                motivo_disc = st.selectbox("Motivo:", ["Selecione ou digite abaixo"] + motivos_existentes)
                novo_motivo = st.text_input("Novo motivo (se não estiver na lista):")
                motivo_disc = novo_motivo if novo_motivo else motivo_disc

            # Sexo Dinâmico
            teve_sexo = st.radio("Houve sexo?", ["Sim", "Não"])
            motivo_nao_sexo = ""
            if teve_sexo == "Não":
                m_sexo_ex = list(set([v.get("motivo_nao_sexo", "") for v in data_history.values() if v.get("motivo_nao_sexo")]))
                motivo_nao_sexo = st.selectbox("Por que não houve?", ["Selecione"] + m_sexo_ex + ["Cansaço", "Falta de Tempo", "Saúde", "Indisposição"])
                n_m_sexo = st.text_input("Outro motivo para ausência de sexo:")
                motivo_nao_sexo = n_m_sexo if n_m_sexo else motivo_nao_sexo

        st.divider()
        acordos = st.text_area("Novos combinados / O que devo passar a fazer:")
        resumo = st.text_area("Resumo livre do dia:")

        submitted = st.form_submit_button("Salvar Dia")
        if submitted:
            payload = {
                "quick_check": [q1, q2, q3, q4, q5, q6],
                "eu_fiz": eu_fiz, "recebi": recebi, "fizemos": fizemos,
                "discussao": teve_disc, "motivo_disc": motivo_disc,
                "sexo": teve_sexo == "Sim", "motivo_nao_sexo": motivo_nao_sexo,
                "acordos": acordos, "resumo": resumo
            }
            save_data(payload)
            st.success("Dados enviados ao GitHub!")

elif menu == "Insights e Dicas":
    st.header("💡 Insights da IA para amanhã")
    
    if not data_history:
        st.info("Aguardando dados para gerar insights.")
    else:
        if st.button("🔄 Gerar nova sugestão/insight"):
            contexto = str(list(data_history.items())[-7:]) # Última semana
            prompt = f"Com base nestes dados de relacionamento: {contexto}. Sugira UMA ação prática, criativa e específica para o Jhonata fazer amanhã para surpreender a Katheryn ou melhorar a relação. Seja breve e direto."
            
            completion = client_groq.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9 # Mais alto para variar as sugestões no reload
            )
            st.info(completion.choices[0].message.content)

elif menu == "Histórico e Gráficos":
    st.header("📊 Análise de Padrões")
    if data_history:
        df = pd.DataFrame.from_dict(data_history, orient='index')
        
        st.subheader("Gráfico de Recorrência")
        # Criando uma visualização simples de colunas
        chart_data = df[['discussao', 'sexo']].astype(int)
        st.bar_chart(chart_data)
        
        st.subheader("Motivos Recorrentes de Discussão")
        st.write(df[df['discussao'] == True]['motivo_disc'].value_counts())
        
        st.subheader("Log Completo")
        st.write(df)
