import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq

# Configuração da página - Versão 2.2
st.set_page_config(page_title="Love Planner 2026 V2.2", layout="wide", page_icon="❤️")

# --- CONFIGURAÇÃO DE SEGURANÇA (SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except Exception as e:
    st.error("Erro ao carregar Secrets no Streamlit Cloud.")
    st.stop()

# Inicialização das APIs
client_groq = Groq(api_key=GROQ_API_KEY)
auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)
repo = g.get_repo(GITHUB_REPO)

# --- FUNÇÕES DE PERSISTÊNCIA ---
def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        return json.loads(contents.decoded_content.decode())
    except Exception:
        return {"registros": {}, "eventos": {}}

def save_all(data):
    file_path = "data_2026.json"
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, f"Atualização {datetime.now()}", json_data, contents.sha)
    except Exception:
        repo.create_file(file_path, "Criação do Banco de Dados", json_data)

# Carregamento do Banco de Dados
db = load_data()

# --- INTERFACE LATERAL (MENU) ---
st.sidebar.title("❤️ Love Planner 2026")
menu = st.sidebar.radio("Navegação:", ["📝 Diário", "📅 Planejar Eventos", "📊 Painel 2026 (Grids)", "💡 Insights da IA"])

# --- 1. ABA DE REGISTRO (DIÁRIO) ---
if menu == "📝 Diário":
    st.header("O que aconteceu entre você e Katheryn?")
    
    selected_date = st.date_input("Data do Registro:", date.today(), min_value=date(2026,1,1), max_value=date(2026,12,31))
    date_str = selected_date.strftime("%Y-%m-%d")
    
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    if is_locked:
        st.warning(f"🔒 Registro de {selected_date.strftime('%d/%m/%Y')} trancado.")
        if st.button("🔓 Destrancar para Editar"):
            db["registros"][date_str]["locked"] = False
            save_all(db)
            st.rerun()
    
    with st.form("registro_dia"):
        st.subheader("Nota do Dia (1 a 10)")
        nota_dia = st.select_slider("Como você avalia o relacionamento hoje?", options=list(range(1, 11)), value=day_data.get("nota", 7), disabled=is_locked)
        
        st.divider()
        st.subheader("Checklist Rápido")
        c1, c2, c3 = st.columns(3)
        q1 = c1.toggle("Conversamos sem telas?", day_data.get("q1", False), disabled=is_locked)
        q2 = c2.toggle("Rimos juntos hoje?", day_data.get("q2", False), disabled=is_locked)
        q3 = c3.toggle("Fiz um elogio?", day_data.get("q3", False), disabled=is_locked)
        
        col_a, col_b = st.columns(2)
        with col_a:
            eu_fiz = st.multiselect("Eu fiz:", ["Flores", "Elogios", "Ajuda", "Ouvir", "Cozinhar", "Massagem"], day_data.get("eu_fiz", []), disabled=is_locked)
            disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)
            motivo_disc = st.text_input("Motivo da discussão:", day_data.get("motivo_disc", ""), disabled=is_locked or not disc)
        
        with col_b:
            recebi = st.multiselect("Ela fez:", ["Carinho", "Apoio", "Cuidado", "Beijos", "Elogio"], day_data.get("recebi", []), disabled=is_locked)
            sexo = st.radio("Houve sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)
            motivo_n_sexo = st.text_input("Por que não?", day_data.get("motivo_nao_sexo", ""), disabled=is_locked or sexo=="Sim")

        resumo = st.text_area("Resumo livre do dia:", day_data.get("resumo", ""), disabled=is_locked)
        acordos = st.text_area("Acordos estabelecidos:", day_data.get("acordos", ""), disabled=is_locked)

        if not is_locked:
            if st.form_submit_button("💾 Salvar e Trancar"):
                db["registros"][date_str] = {
                    "nota": nota_dia, "q1": q1, "q2": q2, "q3": q3,
                    "eu_fiz": eu_fiz, "recebi": recebi,
                    "discussao": disc, "motivo_disc": motivo_disc,
                    "sexo": sexo == "Sim", "motivo_nao_sexo": motivo_n_sexo,
                    "resumo": resumo, "acordos": acordos, "locked": True
                }
                save_all(db)
                st.success("Dados salvos e trancados!")
                st.rerun()

# --- 2. ABA DE GRIDS (VISUALIZAÇÃO CATEGORIZADA) ---
elif menu == "📊 Painel 2026 (Grids)":
    st.header("📊 Retrospectiva Visual 2026")
    
    def draw_grid(title, metric_type):
        st.subheader(title)
        all_days = pd.date_range(start="2026-01-01", end="2026-12-31")
        html_grid = '<div style="display: flex; flex-wrap: wrap; gap: 3px; max-width: 900px; margin-bottom: 20px;">'
        
        for d in all_days:
            d_str = d.strftime("%Y-%m-%d")
            reg = db["registros"].get(d_str, {})
            color = "#ebedf0" # Padrão vazio
            
            if d_str in db["registros"]:
                if metric_type == "nota":
                    val = reg.get("nota", 0)
                    if val >= 8: color = "#216e39" # Verde forte
                    elif val >= 5: color = "#f9d71c" # Amarelo/Ouro
                    else: color = "#f44336" # Vermelho
                elif metric_type == "rir":
                    color = "#2196f3" if reg.get("q2") else "#ebedf0" # Azul se riram
                elif metric_type == "discussao":
                    color = "#f44336" if reg.get("discussao") else "#ebedf0" # Vermelho se houve
                elif metric_type == "sexo":
                    color = "#e91e63" if reg.get("sexo") else "#ebedf0" # Rosa se houve
            
            html_grid += f'<div title="{d_str}" style="width: 13px; height: 13px; background-color: {color}; border-radius: 2px;"></div>'
        
        html_grid += '</div>'
        st.markdown(html_grid, unsafe_allow_html=True)

    draw_grid("⭐ Nota do Relacionamento (Semáforo: Vermelho 🔴 -> Amarelo 🟡 -> Verde 🟢)", "nota")
    draw_grid("😂 Rimos Juntos? (Azul = Sim)", "rir")
    draw_grid("🔥 Frequência Sexual (Rosa = Sim)", "sexo")
    draw_grid("⚠️ Discussões (Vermelho = Houve Conflito)", "discussao")

# --- 3. PLANEJADOR E INSIGHTS (CONTEÚDO MANTIDO) ---
elif menu == "📅 Planejar Eventos":
    st.header("Eventos Futuros")
    with st.form("evento_form"):
        ev_data = st.date_input("Data:", date.today() + timedelta(days=1))
        ev_nome = st.text_input("Nome do Evento:")
        if st.form_submit_button("Agendar"):
            db["eventos"][ev_data.strftime("%Y-%m-%d")] = {"titulo": ev_nome}
            save_all(db)
            st.success("Evento agendado!")

elif menu == "💡 Insights da IA":
    st.header("Especialista IA")
    if st.button("Gerar Análise"):
        contexto = str(list(db["registros"].items())[-7:])
        prompt = f"Dados da semana: {contexto}. Dê uma dica para Jhonata melhorar o relacionamento com Katheryn."
        completion = client_groq.chat.completions.create(model="llama3-70b-8192", messages=[{"role":"user","content":prompt}])
        st.info(completion.choices[0].message.content)
