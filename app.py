import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq

# Configuração da página - Versão 2.3
st.set_page_config(page_title="Love Planner 2026 V2.3", layout="wide", page_icon="❤️")

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
        # Estrutura inicial com lista de opções padrão
        return {
            "registros": {}, 
            "eventos": {}, 
            "configuracoes": {
                "opcoes_eu_fiz": ["Flores", "Elogios", "Ajuda", "Ouvir", "Cozinhar", "Massagem"],
                "opcoes_ela_fez": ["Carinho", "Apoio", "Cuidado", "Beijos", "Elogio"]
            }
        }

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

# Garantir integridade das configurações
if "configuracoes" not in db:
    db["configuracoes"] = {
        "opcoes_eu_fiz": ["Flores", "Elogios", "Ajuda", "Ouvir", "Cozinhar", "Massagem"],
        "opcoes_ela_fez": ["Carinho", "Apoio", "Cuidado", "Beijos", "Elogio"]
    }

# --- INTERFACE LATERAL ---
st.sidebar.title("❤️ Love Planner 2026")
menu = st.sidebar.radio("Navegação:", ["📝 Diário", "📅 Planejar Eventos", "📊 Painel 2026 (Grids)", "💡 Insights da IA", "⚙️ Configurações"])

# --- 1. ABA DE REGISTRO (DIÁRIO) ---
if menu == "📝 Diário":
    st.header("O que aconteceu entre você e Katheryn?")
    selected_date = st.date_input("Data do Registro:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    if is_locked:
        st.warning(f"🔒 Registro de {selected_date.strftime('%d/%m/%Y')} trancado.")
        if st.button("🔓 Destrancar"):
            db["registros"][date_str]["locked"] = False
            save_all(db)
            st.rerun()
    
    with st.form("registro_dia"):
        nota_dia = st.select_slider("Nota do Relacionamento:", options=list(range(1, 11)), value=day_data.get("nota", 7), disabled=is_locked)
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        q1 = c1.toggle("Conversamos?", day_data.get("q1", False), disabled=is_locked)
        q2 = c2.toggle("Rimos juntos?", day_data.get("q2", False), disabled=is_locked)
        q3 = c3.toggle("Fiz um elogio?", day_data.get("q3", False), disabled=is_locked)
        
        col_a, col_b = st.columns(2)
        with col_a:
            # Opção "Outro" adicionada à lista
            lista_eu = db["configuracoes"]["opcoes_eu_fiz"] + ["Outro"]
            eu_fiz = st.multiselect("Eu fiz:", lista_eu, [x for x in day_data.get("eu_fiz", []) if x in db["configuracoes"]["opcoes_eu_fiz"]], disabled=is_locked)
            
            nova_opcao = ""
            if "Outro" in eu_fiz:
                nova_opcao = st.text_input("Qual nova opção deseja adicionar?", placeholder="Ex: Fiz uma surpresa")

            disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)
            mot_disc = st.text_input("Motivo:", day_data.get("motivo_disc", ""), disabled=is_locked or not disc)
        
        with col_b:
            recebi = st.multiselect("Ela fez:", db["configuracoes"]["opcoes_ela_fez"], day_data.get("recebi", []), disabled=is_locked)
            sexo = st.radio("Sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)
            mot_n_sexo = st.text_input("Por que não?", day_data.get("motivo_nao_sexo", ""), disabled=is_locked or sexo=="Sim")

        resumo = st.text_area("Resumo livre:", day_data.get("resumo", ""), disabled=is_locked)

        if not is_locked:
            if st.form_submit_button("💾 Salvar e Trancar"):
                # Lógica para salvar nova opção do "Outro"
                final_eu_fiz = [item for item in eu_fiz if item != "Outro"]
                if nova_opcao:
                    if nova_opcao not in db["configuracoes"]["opcoes_eu_fiz"]:
                        db["configuracoes"]["opcoes_eu_fiz"].append(nova_opcao)
                    if nova_opcao not in final_eu_fiz:
                        final_eu_fiz.append(nova_opcao)

                db["registros"][date_str] = {
                    "nota": nota_dia, "q1": q1, "q2": q2, "q3": q3,
                    "eu_fiz": final_eu_fiz, "recebi": recebi,
                    "discussao": disc, "motivo_disc": mot_disc,
                    "sexo": sexo == "Sim", "motivo_nao_sexo": mot_n_sexo,
                    "resumo": resumo, "locked": True
                }
                save_all(db)
                st.success("Salvo com sucesso!")
                st.rerun()

# --- 2. ABA DE CONFIGURAÇÕES (GERENCIAMENTO) ---
elif menu == "⚙️ Configurações":
    st.header("⚙️ Gerenciar Opções de Checklist")
    st.write("Desmarque as opções que deseja remover e clique no botão de descartar.")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Minhas Ações (Eu Fiz)")
        opcoes_eu = db["configuracoes"]["opcoes_eu_fiz"]
        mantidos_eu = []
        for opt in opcoes_eu:
            if st.checkbox(opt, value=True, key=f"check_eu_{opt}"):
                mantidos_eu.append(opt)
        
        if st.button("Descartar Selecionados (Eu Fiz)"):
            db["configuracoes"]["opcoes_eu_fiz"] = mantidos_eu
            save_all(db)
            st.rerun()

    with c2:
        st.subheader("Ações dela (Ela Fez)")
        opcoes_ela = db["configuracoes"]["opcoes_ela_fez"]
        mantidos_ela = []
        for opt in opcoes_ela:
            if st.checkbox(opt, value=True, key=f"check_ela_{opt}"):
                mantidos_ela.append(opt)
        
        if st.button("Descartar Selecionados (Ela Fez)"):
            db["configuracoes"]["opcoes_ela_fez"] = mantidos_ela
            save_all(db)
            st.rerun()

# --- MANTENDO DEMAIS FUNCIONALIDADES (GRIDS, PLANEJADOR, IA) ---
elif menu == "📊 Painel 2026 (Grids)":
    # (Código da aba de Grids da versão anterior...)
    st.header("📊 Retrospectiva Visual 2026")
    def draw_grid(title, metric_type):
        st.subheader(title)
        all_days = pd.date_range(start="2026-01-01", end="2026-12-31")
        html_grid = '<div style="display: flex; flex-wrap: wrap; gap: 3px; max-width: 900px; margin-bottom: 20px;">'
        for d in all_days:
            d_str = d.strftime("%Y-%m-%d")
            reg = db["registros"].get(d_str, {})
            color = "#ebedf0"
            if d_str in db["registros"]:
                if metric_type == "nota":
                    val = reg.get("nota", 0)
                    color = "#216e39" if val >= 8 else "#f9d71c" if val >= 5 else "#f44336"
                elif metric_type == "rir": color = "#2196f3" if reg.get("q2") else "#ebedf0"
                elif metric_type == "discussao": color = "#f44336" if reg.get("discussao") else "#ebedf0"
                elif metric_type == "sexo": color = "#e91e63" if reg.get("sexo") else "#ebedf0"
            html_grid += f'<div title="{d_str}" style="width: 13px; height: 13px; background-color: {color}; border-radius: 2px;"></div>'
        html_grid += '</div>'
        st.markdown(html_grid, unsafe_allow_html=True)
    draw_grid("⭐ Nota do Relacionamento", "nota")
    draw_grid("😂 Rimos Juntos?", "rir")
    draw_grid("🔥 Frequência Sexual", "sexo")
    draw_grid("⚠️ Discussões", "discussao")

elif menu == "📅 Planejar Eventos":
    st.header("Eventos Futuros")
    with st.form("ev"):
        ev_data = st.date_input("Data:", date.today())
        ev_nome = st.text_input("Evento:")
        if st.form_submit_button("Agendar"):
            db["eventos"][ev_data.strftime("%Y-%m-%d")] = {"titulo": ev_nome}
            save_all(db)
            st.success("Agendado!")

elif menu == "💡 Insights da IA":
    st.header("Análise IA")
    if st.button("Gerar"):
        ctx = str(list(db["registros"].items())[-7:])
        completion = client_groq.chat.completions.create(model="llama3-70b-8192", messages=[{"role":"user","content":f"Dê uma dica para Jhonata com base em: {ctx}"}])
        st.info(completion.choices[0].message.content)
