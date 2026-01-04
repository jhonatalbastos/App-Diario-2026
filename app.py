import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Love Planner 4.0", layout="wide", page_icon="❤️")

# --- SEGURANÇA (SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except Exception as e:
    st.error("Erro nos Secrets. Verifique as chaves no Streamlit Cloud.")
    st.stop()

# Inicialização de APIs
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
        # Garantir chaves básicas
        if "registros" not in data: data["registros"] = {}
        if "eventos" not in data: data["eventos"] = {}
        if "acordos_mestres" not in data: data["acordos_mestres"] = []
        if "configuracoes" not in data:
            data["configuracoes"] = {
                "opcoes_eu_fiz": ["Flores", "Elogios", "Ajuda", "Ouvir"],
                "opcoes_ela_fez": ["Carinho", "Apoio", "Cuidado", "Beijos"]
            }
        return data
    except:
        return {
            "registros": {}, "eventos": {}, "acordos_mestres": [],
            "configuracoes": {
                "opcoes_eu_fiz": ["Flores", "Elogios"],
                "opcoes_ela_fez": ["Carinho", "Beijos"]
            }
        }

def save_all(data):
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    file_path = "data_2026.json"
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, f"Sincronização {datetime.now()}", json_data, contents.sha)
    except:
        repo.create_file(file_path, "Início do Banco de Dados", json_data)

db = load_data()

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("❤️ Love Planner 4.0")
menu = st.sidebar.radio("Navegação:", ["📝 Diário", "🤝 Central de Acordos", "📊 Painel & Grids", "⏳ Cápsula do Tempo", "📅 Eventos", "⚙️ Configurações", "💡 Insights da IA"])

# --- 1. ABA DIÁRIO ---
if menu == "📝 Diário":
    st.header("📝 Registro Diário")
    selected_date = st.date_input("Data do Registro:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    if is_locked:
        st.warning("🔒 Este dia está trancado.")
        if st.button("🔓 Destrancar"):
            db["registros"][date_str]["locked"] = False
            save_all(db)
            st.rerun()

    with st.form("form_diario"):
        nota = st.select_slider("Como foi o dia? (1-Vermelho, 10-Verde):", options=range(1, 11), value=day_data.get("nota", 7), disabled=is_locked)
        
        # Checkbox de Acordos Firmados
        acordos_ativos = [a for a in db["acordos_mestres"] if a.get("monitorar")]
        checks_acordos_hoje = {}
        if acordos_ativos:
            st.subheader("🎯 Cumprimento de Acordos")
            cols_ac = st.columns(len(acordos_ativos))
            for i, ac in enumerate(acordos_ativos):
                label = ac['nome_curto']
                checks_acordos_hoje[label] = cols_ac[i].checkbox(label, value=day_data.get("checks_acordos", {}).get(label, False), disabled=is_locked)

        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Jhonata (Eu)")
            op_eu = db["configuracoes"]["opcoes_eu_fiz"] + ["Outro"]
            eu_fiz = st.multiselect("O que eu fiz por ela:", op_eu, [x for x in day_data.get("eu_fiz", []) if x in op_eu], disabled=is_locked)
            novo_eu = st.text_input("Adicionar nova opção (Eu):") if "Outro" in eu_fiz else ""
            
            ling_eu = st.multiselect("Minhas Linguagens hoje:", LINGUAGENS_LISTA, day_data.get("ling_eu", []), disabled=is_locked)
            disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)

        with col2:
            st.subheader("Katheryn (Ela)")
            op_ela = db["configuracoes"]["opcoes_ela_fez"] + ["Outro"]
            ela_fez = st.multiselect("O que ela fez por mim:", op_ela, [x for x in day_data.get("ela_fez", []) if x in op_ela], disabled=is_locked)
            novo_ela = st.text_input("Adicionar nova opção (Ela):") if "Outro" in ela_fez else ""
            
            ling_ela = st.multiselect("Linguagens dela hoje:", LINGUAGENS_LISTA, day_data.get("ling_ela", []), disabled=is_locked)
            sexo = st.radio("Houve sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)

        st.divider()
        with st.expander("💬 Importar Conversa do WhatsApp (Opcional)"):
            ws_raw = st.text_area("Cole a conversa aqui (apenas mensagens do dia serão salvas):")
        
        resumo = st.text_area("Resumo livre/Notas importantes:", day_data.get("resumo", ""), disabled=is_locked)

        if not is_locked and st.form_submit_button("💾 Salvar e Trancar Registro"):
            # Processar 'Outros'
            f_eu = [i for i in eu_fiz if i != "Outro"]
            if novo_eu and novo_eu not in db["configuracoes"]["opcoes_eu_fiz"]:
                db["configuracoes"]["opcoes_eu_fiz"].append(novo_eu)
                f_eu.append(novo_eu)
            
            f_ela = [i for i in ela_fez if i != "Outro"]
            if novo_ela and novo_ela not in db["configuracoes"]["opcoes_ela_fez"]:
                db["configuracoes"]["opcoes_ela_fez"].append(novo_ela)
                f_ela.append(novo_ela)

            # Filtrar WhatsApp por data (ex: 04/01/26)
            ws_final = day_data.get("whatsapp_txt", "")
            if ws_raw:
                target = selected_date.strftime("%d/%m/%y")
                ws_final = "\n".join([line for line in ws_raw.split('\n') if target in line])

            db["registros"][date_str] = {
                "nota": nota, "eu_fiz": f_eu, "ela_fez": f_ela,
                "ling_eu": ling_eu, "ling_ela": ling_ela,
                "discussao": disc, "sexo": sexo == "Sim", "resumo": resumo,
                "whatsapp_txt": ws_final, "checks_acordos": checks_acordos_hoje, "locked": True
            }
            save_all(db)
            st.success("Salvo com sucesso!")
            st.rerun()

# --- 2. CENTRAL DE ACORDOS ---
elif menu == "🤝 Central de Acordos":
    st.header("🤝 Gestão de Acordos")
    with st.form("novo_ac"):
        t = st.text_input("Descrição do Acordo:")
        c = st.text_input("Nome Curto (Checklist):")
        m = st.checkbox("Monitorar diariamente no Diário?")
        if st.form_submit_button("Firmar Acordo"):
            db["acordos_mestres"].append({"titulo": t, "nome_curto": c, "monitorar": m, "data": str(date.today())})
            save_all(db)
            st.rerun()

    st.subheader("Acordos Firmados")
    for i, ac in enumerate(db["acordos_mestres"]):
        st.write(f"- **{ac['nome_curto']}**: {ac['titulo']} (Desde: {ac['data']})")
        if st.button("Remover", key=f"del_{i}"):
            db["acordos_mestres"].pop(i)
            save_all(db)
            st.rerun()

# --- 3. PAINEL & GRIDS ---
elif menu == "📊 Painel & Grids":
    st.header("📊 Retrospectiva 2026")
    def draw_grid(title, metric, color):
        st.write(f"#### {title}")
        days = pd.date_range("2026-01-01", "2026-12-31")
        grid = '<div style="display: flex; flex-wrap: wrap; gap: 3px; max-width: 900px; margin-bottom: 20px;">'
        for d in days:
            ds = d.strftime("%Y-%m-%d")
            reg = db["registros"].get(ds, {})
            c = "#ebedf0"
            if ds in db["registros"]:
                if metric == "nota":
                    n = reg.get("nota", 0)
                    c = "#216e39" if n >= 8 else "#f9d71c" if n >= 5 else "#f44336"
                elif metric in LINGUAGENS_LISTA:
                    c = color if metric in reg.get("ling_eu", []) or metric in reg.get("ling_ela", []) else "#ebedf0"
                else:
                    c = color if reg.get(metric) else "#ebedf0"
            grid += f'<div title="{ds}" style="width: 12px; height: 12px; background-color: {c}; border-radius: 2px;"></div>'
        st.markdown(grid + '</div>', unsafe_allow_html=True)

    draw_grid("⭐ Nota Geral (Semáforo)", "nota", "")
    draw_grid("🔥 Intimidade (Sexo)", "sexo", "#e91e63")
    draw_grid("⚠️ Discussões", "discussao", "#f44336")
    st.divider()
    st.subheader("🧬 Linguagens do Amor no Ano")
    cols_ling = ["#ff5722", "#3f51b5", "#00bcd4", "#9c27b0", "#8bc34a"]
    for i, l in enumerate(LINGUAGENS_LISTA):
        draw_grid(f"Frequência: {l}", l, cols_ling[i])

# --- 4. CÁPSULA DO TEMPO ---
elif menu == "⏳ Cápsula do Tempo":
    st.header("⏳ Memórias")
    for d in [30, 90, 180]:
        alvo = (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")
        if alvo in db["registros"]:
            st.info(f"📅 Há {d} dias ({alvo}): {db['registros'][alvo].get('resumo')}")

# --- 5. EVENTOS ---
elif menu == "📅 Eventos":
    st.header("📅 Planejamento")
    with st.form("ev"):
        dt = st.date_input("Data:")
        nome = st.text_input("Evento:")
        if st.form_submit_button("Agendar"):
            db["eventos"][dt.strftime("%Y-%m-%d")] = nome
            save_all(db)
            st.success("Agendado!")

# --- 6. CONFIGURAÇÕES ---
elif menu == "⚙️ Configurações":
    st.header("⚙️ Gestão de Opções")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Opções: Eu Fiz")
        for o in db["configuracoes"]["opcoes_eu_fiz"]:
            if not st.checkbox(o, value=True, key=f"e_{o}"):
                db["configuracoes"]["opcoes_eu_fiz"].remove(o)
                save_all(db); st.rerun()
    with c2:
        st.subheader("Opções: Ela Fez")
        for o in db["configuracoes"]["opcoes_ela_fez"]:
            if not st.checkbox(o, value=True, key=f"k_{o}"):
                db["configuracoes"]["opcoes_ela_fez"].remove(o)
                save_all(db); st.rerun()

# --- 7. IA INSIGHTS ---
elif menu == "💡 Insights da IA":
    st.header("💡 Análise do Especialista")
    if st.button("Gerar Insights"):
        recent = str(list(db["registros"].items())[-7:])
        prompt = f"Analise o relacionamento de Jhonata e Katheryn com base nisso: {recent}. Foque em Linguagens do Amor e Acordos."
        resp = client_groq.chat.completions.create(model="llama3-70b-8192", messages=[{"role":"user","content":prompt}])
        st.write(resp.choices[0].message.content)
