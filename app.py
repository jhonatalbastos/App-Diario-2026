import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq

# Configuração da página - Versão 2.1
st.set_page_config(page_title="Love Planner 2026 V2.1", layout="wide", page_icon="❤️")

# --- CONFIGURAÇÃO DE SEGURANÇA (SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except Exception as e:
    st.error("Erro ao carregar Secrets. Verifique as configurações no Streamlit Cloud.")
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
        # Retorna estrutura inicial se o arquivo não existir
        return {"registros": {}, "eventos": {}}

def save_all(data):
    file_path = "data_2026.json"
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, f"Atualização {datetime.now()}", json_data, contents.sha)
    except Exception:
        # Cria o arquivo se ele não existir
        repo.create_file(file_path, "Criação do Banco de Dados", json_data)

# Carregamento do Banco de Dados
db = load_data()
if "registros" not in db: db["registros"] = {}
if "eventos" not in db: db["eventos"] = {}

# --- INTERFACE LATERAL (MENU) ---
st.sidebar.title("❤️ Love Planner 2026")
st.sidebar.write(f"Usuário: {GITHUB_REPO.split('/')[0]}")
menu = st.sidebar.radio("Navegação:", ["📝 Diário (Registro)", "📅 Planejar Eventos", "📊 Painel 2026 (Grid)", "💡 Insights da IA"])

# --- 1. ABA DE REGISTRO DIÁRIO ---
if menu == "📝 Diário (Registro)":
    st.header("O que aconteceu entre você e Katheryn?")
    
    selected_date = st.date_input("Selecione a data:", date.today(), min_value=date(2026,1,1), max_value=date(2026,12,31))
    date_str = selected_date.strftime("%Y-%m-%d")
    
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    if is_locked:
        st.warning(f"🔒 O dia {selected_date.strftime('%d/%m/%Y')} está trancado.")
        if st.button("🔓 Destrancar para Editar"):
            db["registros"][date_str]["locked"] = False
            save_all(db)
            st.rerun()
    
    with st.form("registro_dia"):
        st.subheader("Checklist Rápido")
        c1, c2, c3 = st.columns(3)
        q1 = c1.toggle("Conversamos sem telas?", day_data.get("q1", False), disabled=is_locked)
        q2 = c2.toggle("Rimos juntos hoje?", day_data.get("q2", False), disabled=is_locked)
        q3 = c3.toggle("Fiz um elogio?", day_data.get("q3", False), disabled=is_locked)
        
        st.divider()
        
        col_a, col_b = st.columns(2)
        with col_a:
            eu_fiz = st.multiselect("Eu fiz:", ["Flores", "Elogios", "Ajuda", "Ouvir", "Cozinhar", "Massagem"], day_data.get("eu_fiz", []), disabled=is_locked)
            recebi = st.multiselect("Ela fez:", ["Carinho", "Apoio", "Cuidado", "Beijos", "Elogio"], day_data.get("recebi", []), disabled=is_locked)
        
        with col_b:
            disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)
            motivo_disc = st.text_input("Motivo da discussão:", day_data.get("motivo_disc", ""), disabled=is_locked or not disc)
            
            sexo = st.radio("Houve sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)
            motivo_n_sexo = st.text_input("Por que não?", day_data.get("motivo_nao_sexo", ""), disabled=is_locked or sexo=="Sim")

        resumo = st.text_area("Resumo livre do dia:", day_data.get("resumo", ""), disabled=is_locked)
        acordos = st.text_area("Acordos estabelecidos:", day_data.get("acordos", ""), disabled=is_locked)

        if not is_locked:
            if st.form_submit_button("💾 Salvar e Trancar Dia"):
                db["registros"][date_str] = {
                    "q1": q1, "q2": q2, "q3": q3,
                    "eu_fiz": eu_fiz, "recebi": recebi,
                    "discussao": disc, "motivo_disc": motivo_disc,
                    "sexo": sexo == "Sim", "motivo_nao_sexo": motivo_n_sexo,
                    "resumo": resumo, "acordos": acordos,
                    "locked": True
                }
                save_all(db)
                st.success("Dados salvos e trancados no GitHub!")
                st.rerun()

# --- 2. ABA DE PLANEJAMENTO ---
elif menu == "📅 Planejar Eventos":
    st.header("Eventos Futuros")
    with st.form("novo_evento"):
        ev_data = st.date_input("Data do Evento:", date.today() + timedelta(days=1))
        ev_nome = st.text_input("Nome do Evento (ex: Jantar Romântico)")
        ev_obs = st.text_area("Observações/Ideias")
        if st.form_submit_button("Agendar"):
            db["eventos"][ev_data.strftime("%Y-%m-%d")] = {"titulo": ev_nome, "obs": ev_obs}
            save_all(db)
            st.success("Evento agendado!")
            st.rerun()

    if db["eventos"]:
        st.subheader("Seu Calendário")
        st.table(pd.DataFrame.from_dict(db["eventos"], orient='index').sort_index())

# --- 3. ABA DE GRID (GITHUB STYLE) ---
elif menu == "📊 Painel 2026 (Grid)":
    st.header("Resumo Visual de 2026")
    all_days = pd.date_range(start="2026-01-01", end="2026-12-31")
    
    html_grid = '<div style="display: flex; flex-wrap: wrap; gap: 3px; max-width: 800px;">'
    for d in all_days:
        d_str = d.strftime("%Y-%m-%d")
        color = "#ebedf0" # Cinza (sem dado)
        if d_str in db["registros"]:
            reg = db["registros"][d_str]
            if reg.get("sexo"): color = "#e91e63" # Rosa (Sexo)
            elif reg.get("discussao"): color = "#f44336" # Vermelho (Discussão)
            else: color = "#216e39" # Verde (Dia normal registrado)
        if d_str in db["eventos"]: color = "#ff9800" # Laranja (Evento)
        
        html_grid += f'<div title="{d_str}" style="width: 12px; height: 12px; background-color: {color}; border-radius: 2px;"></div>'
    
    html_grid += '</div>'
    st.markdown(html_grid, unsafe_allow_html=True)
    st.info("Legenda: Cinza (Vazio) | Verde (Registro) | Rosa (Sexo) | Vermelho (Discussão) | Laranja (Evento)")

# --- 4. ABA DE INSIGHTS IA ---
elif menu == "💡 Insights da IA":
    st.header("Especialista em Relacionamentos")
    if st.button("🔄 Gerar Nova Dica/Análise"):
        hoje = date.today()
        # Verifica eventos nos próximos 7 dias
        prox_ev = {k:v for k,v in db["eventos"].items() if hoje <= datetime.strptime(k, "%Y-%m-%d").date() <= hoje + timedelta(days=7)}
        contexto = str(list(db["registros"].items())[-5:])
        
        prompt = f"Dados recentes: {contexto}. Próximos eventos: {prox_ev}. Como especialista, dê um conselho prático para Jhonata sobre o relacionamento com Katheryn."
        
        with st.spinner("Analisando padrões..."):
            completion = client_groq.chat.completions.create(model="llama3-70b-8192", messages=[{"role":"user","content":prompt}])
            st.info(completion.choices[0].message.content)
