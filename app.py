import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
from github import Github
from groq import Groq

# Configuração da página
st.set_page_config(page_title="Diário Katheryn & Jhonata 2026", layout="wide")

# --- CONFIGURAÇÃO DE SEGURANÇA (SECRETS) ---
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

client_groq = Groq(api_key=GROQ_API_KEY)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)

# --- FUNÇÕES DE DADOS ---
def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        return json.loads(contents.decoded_content.decode())
    except:
        return {}

def save_data(date_key, new_data):
    file_path = "data_2026.json"
    all_data = load_data()
    all_data[date_key] = new_data
    json_data = json.dumps(all_data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, f"Registro {date_key}", json_data, contents.sha)
    except:
        repo.create_file(file_path, "Initial commit", json_data)

data_history = load_data()

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["📝 Registrar/Editar", "📊 Painel 2026 (Grid)", "💡 Insights IA"])

# --- ABA 1: REGISTRO COM TRAVA ---
if menu == "📝 Registrar/Editar":
    selected_date = st.date_input("Selecione o dia:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # Carregar dados do dia se existirem
    day_data = data_history.get(date_str, {})
    is_locked = day_data.get("locked", False)

    st.header(f"Registro de {selected_date.strftime('%d/%b/%Y')}")

    if is_locked:
        st.warning("🔒 Este dia está TRANCADO. Para editar, clique em 'Destrancar' abaixo.")
        if st.button("🔓 Destrancar Dia"):
            day_data["locked"] = False
            save_data(date_str, day_data)
            st.rerun()
    
    # Interface de formulário (desabilitada se estiver trancada)
    with st.container():
        st.subheader("Checklist Rápido")
        q_cols = st.columns(3)
        q1 = q_cols[0].toggle("Conversamos?", day_data.get("q1", False), disabled=is_locked)
        q2 = q_cols[1].toggle("Rimos juntos?", day_data.get("q2", False), disabled=is_locked)
        q3 = q_cols[2].toggle("Elogio feito?", day_data.get("q3", False), disabled=is_locked)

        col_a, col_b = st.columns(2)
        with col_a:
            eu_fiz = st.multiselect("Eu fiz:", ["Flores", "Elogios", "Ajuda", "Ouvir", "Cozinhar"], day_data.get("eu_fiz", []), disabled=is_locked)
            teve_disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)
            motivo_disc = st.text_input("Motivo discussão:", day_data.get("motivo_disc", ""), disabled=is_locked or not teve_disc)

        with col_b:
            recebi = st.multiselect("Katheryn fez:", ["Carinho", "Apoio", "Cuidado", "Beijos"], day_data.get("recebi", []), disabled=is_locked)
            teve_sexo = st.radio("Sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)
            motivo_n_sexo = st.text_input("Motivo ausência:", day_data.get("motivo_nao_sexo", ""), disabled=is_locked or teve_sexo=="Sim")

        resumo = st.text_area("Resumo do dia:", day_data.get("resumo", ""), disabled=is_locked)
        acordos = st.text_area("Acordos/Melhorias:", day_data.get("acordos", ""), disabled=is_locked)

        if not is_locked:
            if st.button("💾 Salvar e TRANCAR"):
                new_payload = {
                    "q1": q1, "q2": q2, "q3": q3,
                    "eu_fiz": eu_fiz, "recebi": recebi,
                    "discussao": teve_disc, "motivo_disc": motivo_disc,
                    "sexo": teve_sexo == "Sim", "motivo_nao_sexo": motivo_n_sexo,
                    "resumo": resumo, "acordos": acordos,
                    "locked": True
                }
                save_data(date_str, new_payload)
                st.success("Dia salvo e trancado!")
                st.rerun()

# --- ABA 2: GRID ESTILO GITHUB ---
elif menu == "📊 Painel 2026 (Grid)":
    st.header("📅 Retrospectiva 2026")
    
    def generate_grid(data, metric_key, color_on, label):
        st.write(f"### {label}")
        # Criar datas para o ano de 2026
        all_days = pd.date_range(start="2026-01-01", end="2026-12-31")
        
        # Criar HTML para o Grid
        html_grid = '<div style="display: flex; flex-wrap: wrap; gap: 3px; max-width: 700px;">'
        for d in all_days:
            d_str = d.strftime("%Y-%m-%d")
            day_info = data.get(d_str, {})
            
            # Lógica de cor
            color = "#ebedf0" # Cinza vazio
            if d_str in data:
                if metric_key == "preenchido":
                    color = "#216e39" if day_info.get("resumo") else "#9be9a8"
                elif metric_key == "sexo":
                    color = "#e91e63" if day_info.get("sexo") else "#ebedf0"
                elif metric_key == "discussao":
                    color = "#f44336" if day_info.get("discussao") else "#ebedf0"
            
            tooltip = f"{d_str}: {day_info.get('resumo', 'Sem registro')[:30]}..."
            html_grid += f'<div title="{tooltip}" style="width: 12px; height: 12px; background-color: {color}; border-radius: 2px;"></div>'
        html_grid += '</div>'
        st.markdown(html_grid, unsafe_allow_html=True)

    generate_grid(data_history, "preenchido", "green", "Dinamismo de Preenchimento (Verde Escuro = Com Comentário)")
    generate_grid(data_history, "sexo", "pink", "Frequência Sexual (Rosa = Sim)")
    generate_grid(data_history, "discussao", "red", "Conflitos (Vermelho = Discussão)")

# --- ABA 3: INSIGHTS ---
elif menu == "💡 Insights IA":
    st.header("Especialista Groq")
    if st.button("Gerar Insight Aleatório"):
        if data_history:
            recent = str(list(data_history.items())[-5:])
            prompt = f"Dados: {recent}. Dê um conselho curto e sábio para o relacionamento de Jhonata e Katheryn."
            resp = client_groq.chat.completions.create(model="llama3-70b-8192", messages=[{"role":"user","content":prompt}])
            st.info(resp.choices[0].message.content)
        else:
            st.warning("Sem dados suficientes.")
