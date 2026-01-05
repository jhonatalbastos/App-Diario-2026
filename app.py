import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Love Planner 4.4", layout="wide", page_icon="❤️")

# --- SEGURANÇA (SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except:
    st.error("Erro nos Secrets. Verifique no painel do Streamlit Cloud.")
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
        if "registros" not in data: data["registros"] = {}
        if "eventos" not in data: data["eventos"] = {}
        if "acordos_mestres" not in data: data["acordos_mestres"] = []
        if "metas" not in data: data["metas"] = {"elogios": 3, "qualidade": 2}
        if "configuracoes" not in data:
            data["configuracoes"] = {
                "opcoes_eu_fiz": ["Elogio", "Tempo de Qualidade", "Ajuda"],
                "opcoes_ela_fez": ["Carinho", "Apoio"]
            }
        return data
    except:
        return {"registros": {}, "eventos": {}, "acordos_mestres": [], 
                "metas": {"elogios": 3, "qualidade": 2},
                "configuracoes": {"opcoes_eu_fiz": ["Elogio"], "opcoes_ela_fez": ["Carinho"]}}

def save_all(data):
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents("data_2026.json")
        repo.update_file(contents.path, f"Sync {datetime.now()}", json_data, contents.sha)
    except:
        repo.create_file("data_2026.json", "DB Init", json_data)

db = load_data()

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("❤️ Love Planner 4.4")
menu = st.sidebar.radio("Navegação:", ["📝 Diário", "🤝 Central de Acordos", "📊 Painel & Grids", "⏳ Cápsula do Tempo", "📅 Eventos", "⚙️ Configurações", "💡 Insights da IA"])

# --- 1. DIÁRIO ---
if menu == "📝 Diário":
    st.header("📝 Registro")
    selected_date = st.date_input("Data do Registro:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    if is_locked:
        st.warning("🔒 Dia trancado.")
        if st.button("🔓 Destrancar"):
            db["registros"][date_str]["locked"] = False
            save_all(db); st.rerun()

    with st.form("form_v44"):
        nota = st.select_slider("Nota do Relacionamento:", options=range(1,11), value=day_data.get("nota", 7), disabled=is_locked)
        
        acordos_ativos = [a for a in db["acordos_mestres"] if a.get("monitorar")]
        checks_acordos_hoje = {}
        if acordos_ativos:
            st.subheader("🎯 Acordos")
            cols_ac = st.columns(len(acordos_ativos))
            for i, ac in enumerate(acordos_ativos):
                label = ac['nome_curto']
                checks_acordos_hoje[label] = cols_ac[i].checkbox(label, value=day_data.get("checks_acordos", {}).get(label, False), disabled=is_locked)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Jhonata")
            op_eu = db["configuracoes"]["opcoes_eu_fiz"] + ["Outro"]
            eu_fiz = st.multiselect("Eu fiz:", op_eu, [x for x in day_data.get("eu_fiz", []) if x in op_eu], disabled=is_locked)
            novo_eu = st.text_input("Novo (Eu):") if "Outro" in eu_fiz else ""
            ling_eu = st.multiselect("Minhas Linguagens:", LINGUAGENS_LISTA, day_data.get("ling_eu", []), disabled=is_locked)
            disc = st.checkbox("Discussão?", day_data.get("discussao", False), disabled=is_locked)
        with col2:
            st.subheader("Katheryn")
            op_ela = db["configuracoes"]["opcoes_ela_fez"] + ["Outro"]
            ela_fez = st.multiselect("Ela fez:", op_ela, [x for x in day_data.get("ela_fez", []) if x in op_ela], disabled=is_locked)
            novo_ela = st.text_input("Novo (Ela):") if "Outro" in ela_fez else ""
            ling_ela = st.multiselect("Linguagens dela:", LINGUAGENS_LISTA, day_data.get("ling_ela", []), disabled=is_locked)
            sexo = st.radio("Sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)

        with st.expander("💬 Importar WhatsApp"):
            ws_raw = st.text_area("Cole a conversa aqui.")
        
        resumo = st.text_area("Resumo do dia:", day_data.get("resumo", ""), disabled=is_locked)
        
        if st.form_submit_button("💾 Salvar e Trancar") and not is_locked:
            f_eu = [i for i in eu_fiz if i != "Outro"]
            if novo_eu and novo_eu not in db["configuracoes"]["opcoes_eu_fiz"]:
                db["configuracoes"]["opcoes_eu_fiz"].append(novo_eu)
                f_eu.append(novo_eu)
            
            f_ela = [i for i in ela_fez if i != "Outro"]
            if novo_ela and novo_ela not in db["configuracoes"]["opcoes_ela_fez"]:
                db["configuracoes"]["opcoes_ela_fez"].append(novo_ela)
                f_ela.append(novo_ela)

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
            save_all(db); st.rerun()

# --- 2. PAINEL & GRIDS ---
elif menu == "📊 Painel & Grids":
    st.header("📊 Retrospectiva & Metas")
    
    # Metas Semanais
    hoje = date.today()
    inicio_sem = hoje - timedelta(days=hoje.weekday())
    c_elogios = sum(1 for i in range(7) if "Elogio" in str(db["registros"].get((inicio_sem + timedelta(days=i)).strftime("%Y-%m-%d"), {}).get("eu_fiz", [])))
    c_qualidade = sum(1 for i in range(7) if "Tempo de Qualidade" in str(db["registros"].get((inicio_sem + timedelta(days=i)).strftime("%Y-%m-%d"), {}).get("eu_fiz", [])))
    
    st.subheader("🚀 Metas da Semana")
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Elogios", f"{c_elogios}/{db['metas']['elogios']}")
    col_m2.metric("Qualidade", f"{c_qualidade}/{db['metas']['qualidade']}")

    st.divider()
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
                else: c = color if reg.get(metric) else "#ebedf0"
            grid += f'<div title="{ds}" style="width: 12px; height: 12px; background-color: {c}; border-radius: 2px;"></div>'
        st.markdown(grid + '</div>', unsafe_allow_html=True)

    draw_grid("⭐ Nota Geral", "nota", "")
    draw_grid("🔥 Sexo", "sexo", "#e91e63")
    draw_grid("⚠️ Discussões", "discussao", "#f44336")

# --- 6. INSIGHTS IA (CORRIGIDO) ---
elif menu == "💡 Insights da IA":
    st.header("💡 Análise do Especialista")
    if st.button("Gerar Análise"):
        registros_recentes = list(db["registros"].items())[-5:]
        ctx = ""
        for d, info in registros_recentes:
            ctx += f"\nData: {d} | Nota: {info.get('nota')} | Resumo: {info.get('resumo')[:100]}"
            if info.get('whatsapp_txt'): ctx += f" | WhatsApp: {info.get('whatsapp_txt')[:150]}"
        
        if not ctx:
            st.warning("Adicione registros primeiro!")
        else:
            prompt = f"Como terapeuta de casais, analise o relacionamento de Jhonata e Katheryn: {ctx}"
            try:
                resp = client_groq.chat.completions.create(model="llama3-70b-8192", messages=[{"role":"user","content":prompt}], max_tokens=400)
                st.info(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"Erro na análise: {e}")

# (Demais abas: Central de Acordos, Cápsula, Eventos e Configs mantidas conforme v4.3)
