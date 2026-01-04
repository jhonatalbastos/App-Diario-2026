import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from github import Github
from groq import Groq

# Configuração da página
st.set_page_config(page_title="Diário & Planejador Katheryn & Jhonata 2026", layout="wide")

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
        return {"registros": {}, "eventos": {}}

def save_all(data):
    file_path = "data_2026.json"
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, "Atualização de dados", json_data, contents.sha)
    except:
        repo.create_file(file_path, "Initial commit", json_data)

# Carregamento inicial
db = load_data()
if "registros" not in db: db["registros"] = {}
if "eventos" not in db: db["eventos"] = {}

# --- NAVEGAÇÃO ---
st.sidebar.title("❤️ Love Planner 2026")
menu = st.sidebar.radio("Navegação", ["📝 Diário (Retroativo/Hoje)", "📅 Planejar Evento", "📊 Painel 2026", "💡 Insights e Dicas"])

# --- ABA 1: DIÁRIO (PARA DIAS QUE JÁ PASSARAM OU HOJE) ---
if menu == "📝 Diário (Retroativo/Hoje)":
    st.header("Registrar como foi o dia")
    selected_date = st.date_input("Escolha a data para registrar:", date.today(), min_value=date(2026,1,1), max_value=date(2026,12,31))
    date_str = selected_date.strftime("%Y-%m-%d")
    
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    if is_locked:
        st.warning(f"🔒 O dia {date_str} está trancado.")
        if st.button("🔓 Destrancar"):
            db["registros"][date_str]["locked"] = False
            save_all(db)
            st.rerun()
    
    with st.container():
        st.subheader("O que aconteceu?")
        c1, c2, c3 = st.columns(3)
        q1 = c1.toggle("Conversamos?", day_data.get("q1", False), disabled=is_locked)
        q2 = c2.toggle("Rimos juntos?", day_data.get("q2", False), disabled=is_locked)
        q3 = c3.toggle("Elogio feito?", day_data.get("q3", False), disabled=is_locked)

        col_a, col_b = st.columns(2)
        with col_a:
            eu_fiz = st.multiselect("Eu fiz:", ["Flores", "Elogios", "Ajuda", "Ouvir", "Cozinhar"], day_data.get("eu_fiz", []), disabled=is_locked)
            teve_disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)
            mot_disc = st.text_input("Motivo:", day_data.get("motivo_disc", ""), disabled=is_locked or not teve_disc)

        with col_b:
            recebi = st.multiselect("Katheryn fez:", ["Carinho", "Apoio", "Cuidado", "Beijos"], day_data.get("recebi", []), disabled=is_locked)
            sexo = st.radio("Sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)
            mot_n_sexo = st.text_input("Motivo ausência:", day_data.get("motivo_nao_sexo", ""), disabled=is_locked or sexo=="Não")

        resumo = st.text_area("Resumo do dia:", day_data.get("resumo", ""), disabled=is_locked)

        if not is_locked:
            if st.button("💾 Salvar e Trancar Registro"):
                db["registros"][date_str] = {
                    "q1": q1, "q2": q2, "q3": q3, "eu_fiz": eu_fiz, "recebi": recebi,
                    "discussao": teve_disc, "motivo_disc": mot_disc,
                    "sexo": sexo == "Sim", "motivo_nao_sexo": mot_n_sexo,
                    "resumo": resumo, "locked": True
                }
                save_all(db)
                st.success("Salvo com sucesso!")
                st.rerun()

# --- ABA 2: PLANEJAR EVENTO (CALENDÁRIO FUTURO) ---
elif menu == "📅 Planejar Evento":
    st.header("Agendar evento futuro")
    with st.form("evento_form"):
        ev_data = st.date_input("Data do Evento:", date.today() + timedelta(days=1))
        ev_titulo = st.text_input("Nome do Evento (ex: Aniversário, Jantar)")
        ev_desc = st.text_area("Detalhes/Expectativas")
        sub_ev = st.form_submit_button("Agendar")
        
        if sub_ev:
            ev_str = ev_data.strftime("%Y-%m-%d")
            db["eventos"][ev_str] = {"titulo": ev_titulo, "descricao": ev_desc}
            save_all(db)
            st.success(f"Evento '{ev_titulo}' agendado!")

    st.subheader("Próximos Eventos")
    if db["eventos"]:
        ev_df = pd.DataFrame.from_dict(db["eventos"], orient='index').sort_index()
        st.table(ev_df)

# --- ABA 3: PAINEL 2026 (GRID) ---
elif menu == "📊 Painel 2026":
    st.header("Visualização do Ano")
    # Lógica de grid 365 dias (simplificada para o exemplo)
    all_days = pd.date_range(start="2026-01-01", end="2026-12-31")
    html_grid = '<div style="display: flex; flex-wrap: wrap; gap: 3px; max-width: 800px;">'
    for d in all_days:
        d_str = d.strftime("%Y-%m-%d")
        color = "#ebedf0"
        if d_str in db["registros"]:
            color = "#216e39" if db["registros"][d_str].get("sexo") else "#9be9a8"
        if d_str in db["eventos"]:
            color = "#ff9800" # Cor laranja para dias com evento
        html_grid += f'<div title="{d_str}" style="width: 13px; height: 13px; background-color: {color}; border-radius: 2px;"></div>'
    html_grid += '</div>'
    st.markdown(html_grid, unsafe_allow_html=True)
    st.caption("Verde: Registros | Laranja: Eventos Agendados")

# --- ABA 4: INSIGHTS E DICAS ---
elif menu == "💡 Insights e Dicas":
    st.header("Dicas do Especialista Groq")
    
    hoje = date.today()
    proximos_eventos = {k: v for k, v in db["eventos"].items() if hoje <= datetime.strptime(k, "%Y-%m-%d").date() <= hoje + timedelta(days=7)}

    if st.button("🔄 Gerar Dica/Insight"):
        contexto_passado = str(list(db["registros"].items())[-5:])
        
        if proximos_eventos:
            prompt = f"Temos eventos vindo aí: {proximos_eventos}. Com base no histórico {contexto_passado}, me dê dicas de como me preparar para esses eventos e surpreender a Katheryn."
        else:
            prompt = f"Analise nosso histórico recente: {contexto_passado}. Dê uma dica para melhorar nossa conexão amanhã."

        with st.spinner("Analisando..."):
            completion = client_groq.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            st.info(completion.choices[0].message.content)
