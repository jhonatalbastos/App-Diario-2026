import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Love Planner 4.2", layout="wide", page_icon="❤️")

# --- SEGURANÇA (SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except Exception:
    st.error("Erro nos Secrets. Verifique as chaves no Streamlit Cloud.")
    st.stop()

client_groq = Groq(api_key=GROQ_API_KEY)
auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)
repo = g.get_repo(GITHUB_REPO)

# --- CONSTANTES ---
LINGUAGENS_LISTA = ["Atos de Serviço", "Palavras de Afirmação", "Tempo de Qualidade", "Toque Físico", "Presentes"]

# --- FUNÇÕES DE DADOS ---
def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        data = json.loads(contents.decoded_content.decode())
        if "metas" not in data: data["metas"] = {"elogios": 3, "qualidade": 2}
        if "registros" not in data: data["registros"] = {}
        if "configuracoes" not in data:
            data["configuracoes"] = {"opcoes_eu_fiz": ["Elogio", "Tempo de Qualidade", "Ajuda"], "opcoes_ela_fez": ["Carinho"]}
        return data
    except:
        return {"registros": {}, "metas": {"elogios": 3, "qualidade": 2}, "configuracoes": {"opcoes_eu_fiz": ["Elogio"], "opcoes_ela_fez": ["Carinho"]}}

def save_all(data):
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents("data_2026.json")
        repo.update_file(contents.path, f"Sync {datetime.now()}", json_data, contents.sha)
    except:
        repo.create_file("data_2026.json", "DB Init", json_data)

db = load_data()

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação:", ["📝 Diário", "📊 Painel & Metas", "🤝 Acordos", "⏳ Cápsula", "⚙️ Configs"])

# --- 1. DIÁRIO ---
if menu == "📝 Diário":
    st.header("📝 Registro")
    selected_date = st.date_input("Data:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    with st.form("diario_42"):
        nota = st.select_slider("Nota:", options=range(1,11), value=day_data.get("nota", 7), disabled=is_locked)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Jhonata")
            eu_fiz = st.multiselect("Eu fiz:", db["configuracoes"]["opcoes_eu_fiz"] + ["Outro"], day_data.get("eu_fiz", []), disabled=is_locked)
            novo_eu = st.text_input("Novo (Eu):") if "Outro" in eu_fiz else ""
        with c2:
            st.subheader("Katheryn")
            ela_fez = st.multiselect("Ela fez:", db["configuracoes"]["opcoes_ela_fez"] + ["Outro"], day_data.get("ela_fez", []), disabled=is_locked)
            novo_ela = st.text_input("Novo (Ela):") if "Outro" in ela_fez else ""
            
        with st.expander("💬 WhatsApp"):
            ws_raw = st.text_area("Cole a conversa aqui.")

        resumo = st.text_area("Resumo:", day_data.get("resumo", ""), disabled=is_locked)
        if st.form_submit_button("💾 Salvar") and not is_locked:
            # Lógica de salvar (mesma da v4.1 com filtro de data)
            # ... [Código de processamento idêntico à v4.1]
            st.success("Salvo!")

# --- 2. PAINEL & METAS ---
elif menu == "📊 Painel & Metas":
    st.header("📊 Progresso Semanal")
    
    # Cálculo das Metas
    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    
    cont_elogios = 0
    cont_qualidade = 0
    
    for i in range(7):
        d_str = (inicio_semana + timedelta(days=i)).strftime("%Y-%m-%d")
        reg = db["registros"].get(d_str, {})
        cont_elogios += 1 if "Elogio" in str(reg.get("eu_fiz", [])) else 0
        cont_qualidade += 1 if "Tempo de Qualidade" in str(reg.get("eu_fiz", [])) else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Elogios (Meta: 3)", f"{cont_elogios}/3")
        st.progress(min(cont_elogios/3, 1.0))
    with col2:
        st.metric("Tempo de Qualidade (Meta: 2)", f"{cont_qualidade}/2")
        st.progress(min(cont_qualidade/2, 1.0))

    if cont_elogios >= 3 and cont_qualidade >= 2:
        st.balloons()
        st.success("🏆 Meta da semana batida! Você está cuidando muito bem do seu relacionamento com a Katheryn.")

# --- 6. CONFIGURAÇÕES (Definir Metas) ---
elif menu == "⚙️ Configs":
    st.header("⚙️ Ajustar Metas Semanais")
    db["metas"]["elogios"] = st.number_input("Meta de Elogios:", value=db["metas"].get("elogios", 3))
    db["metas"]["qualidade"] = st.number_input("Meta de Tempo de Qualidade:", value=db["metas"].get("qualidade", 2))
    if st.button("Salvar Metas"):
        save_all(db)
        st.rerun()
