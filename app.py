import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Love Planner 4.3 - Edição Completa", layout="wide", page_icon="❤️")

# --- SEGURANÇA (SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except Exception:
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
        # Garantir integridade de todas as chaves
        if "registros" not in data: data["registros"] = {}
        if "eventos" not in data: data["eventos"] = {}
        if "acordos_mestres" not in data: data["acordos_mestres"] = []
        if "metas" not in data: data["metas"] = {"elogios": 3, "qualidade": 2}
        if "configuracoes" not in data:
            data["configuracoes"] = {
                "opcoes_eu_fiz": ["Elogio", "Tempo de Qualidade", "Ajuda em casa", "Cozinhar"],
                "opcoes_ela_fez": ["Carinho", "Apoio", "Cuidado", "Beijos"]
            }
        return data
    except:
        return {
            "registros": {}, "eventos": {}, "acordos_mestres": [],
            "metas": {"elogios": 3, "qualidade": 2},
            "configuracoes": {"opcoes_eu_fiz": ["Elogio"], "opcoes_ela_fez": ["Carinho"]}
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
st.sidebar.title("❤️ Love Planner 4.3")
menu = st.sidebar.radio("Navegação:", ["📝 Diário", "🤝 Central de Acordos", "📊 Painel & Grids", "⏳ Cápsula do Tempo", "📅 Eventos", "⚙️ Configurações", "💡 Insights da IA"])

# --- 1. ABA DIÁRIO (COMPLETA) ---
if menu == "📝 Diário":
    st.header("📝 Registro Diário")
    selected_date = st.date_input("Data do Registro:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    if is_locked:
        st.warning(f"🔒 Este dia ({selected_date.strftime('%d/%m/%Y')}) está trancado.")
        if st.button("🔓 Destrancar para Editar"):
            db["registros"][date_str]["locked"] = False
            save_all(db); st.rerun()

    with st.form("form_completo"):
        nota = st.select_slider("Nota do Dia (1-Vermelho, 10-Verde):", options=range(1, 11), value=day_data.get("nota", 7), disabled=is_locked)
        
        # Checkbox de Acordos Ativos
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
            novo_eu = st.text_input("Nova opção (Eu):", key="new_eu") if "Outro" in eu_fiz else ""
            ling_eu = st.multiselect("Minhas Linguagens hoje:", LINGUAGENS_LISTA, day_data.get("ling_eu", []), disabled=is_locked)
            disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)

        with col2:
            st.subheader("Katheryn (Ela)")
            op_ela = db["configuracoes"]["opcoes_ela_fez"] + ["Outro"]
            ela_fez = st.multiselect("O que ela fez por mim:", op_ela, [x for x in day_data.get("ela_fez", []) if x in op_ela], disabled=is_locked)
            novo_ela = st.text_input("Nova opção (Ela):", key="new_ela") if "Outro" in ela_fez else ""
            ling_ela = st.multiselect("Linguagens dela hoje:", LINGUAGENS_LISTA, day_data.get("ling_ela", []), disabled=is_locked)
            sexo = st.radio("Houve sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)

        st.divider()
        with st.expander("💬 Importar Conversa do WhatsApp (Opcional)"):
            ws_raw = st.text_area("Cole a conversa aqui. Filtrará apenas mensagens deste dia.")
        
        resumo = st.text_area("Resumo livre/Notas importantes:", day_data.get("resumo", ""), disabled=is_locked)
        btn_salvar = st.form_submit_button("💾 Salvar e Trancar Registro")

        if btn_salvar and not is_locked:
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

# --- 2. CENTRAL DE ACORDOS ---
elif menu == "🤝 Central de Acordos":
    st.header("🤝 Gestão de Acordos")
    with st.form("acordo_mestre"):
        t = st.text_input("Descrição do Acordo:")
        c = st.text_input("Nome Curto (Checklist):")
        m = st.checkbox("Monitorar diariamente no Diário?")
        if st.form_submit_button("Firmar Acordo"):
            db["acordos_mestres"].append({"titulo": t, "nome_curto": c, "monitorar": m, "data": str(date.today())})
            save_all(db); st.rerun()

    st.subheader("Acordos Firmados")
    for i, ac in enumerate(db["acordos_mestres"]):
        st.write(f"- **{ac['nome_curto']}**: {ac['titulo']} (Desde: {ac['data']})")
        if st.button("Remover", key=f"del_{i}"):
            db["acordos_mestres"].pop(i); save_all(db); st.rerun()

# --- 3. PAINEL, GRIDS E METAS ---
elif menu == "📊 Painel & Grids":
    st.header("📊 Retrospectiva & Metas")
    
    # --- METAS SEMANAIS ---
    st.subheader("🚀 Metas de Carinho da Semana")
    hoje = date.today()
    inicio_sem = hoje - timedelta(days=hoje.weekday())
    c_elogios = sum(1 for i in range(7) if "Elogio" in str(db["registros"].get((inicio_sem + timedelta(days=i)).strftime("%Y-%m-%d"), {}).get("eu_fiz", [])))
    c_qualidade = sum(1 for i in range(7) if "Tempo de Qualidade" in str(db["registros"].get((inicio_sem + timedelta(days=i)).strftime("%Y-%m-%d"), {}).get("eu_fiz", [])))
    
    m1, m2 = st.columns(2)
    m1.metric("Elogios", f"{c_elogios}/{db['metas']['elogios']}")
    m1.progress(min(c_elogios/db['metas']['elogios'], 1.0))
    m2.metric("Qualidade", f"{c_qualidade}/{db['metas']['qualidade']}")
    m2.progress(min(c_qualidade/db['metas']['qualidade'], 1.0))
    if c_elogios >= db['metas']['elogios'] and c_qualidade >= db['metas']['qualidade']:
        st.success("🏆 Metas batidas! Katheryn está feliz!")

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
    st.subheader("🧬 Linguagens do Amor")
    cols = ["#ff5722", "#3f51b5", "#00bcd4", "#9c27b0", "#8bc34a"]
    for i, l in enumerate(LINGUAGENS_LISTA): draw_grid(l, l, cols[i])

# --- 4. CÁPSULA DO TEMPO ---
elif menu == "⏳ Cápsula do Tempo":
    st.header("⏳ Memórias")
    for d in [30, 90, 180]:
        alvo = (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")
        if alvo in db["registros"]: st.info(f"📅 Há {d} dias: {db['registros'][alvo].get('resumo')}")

# --- 5. CONFIGURAÇÕES (GERENCIAMENTO) ---
elif menu == "⚙️ Configurações":
    st.header("⚙️ Gestão do Sistema")
    st.subheader("Ajustar Metas Semanais")
    db["metas"]["elogios"] = st.number_input("Meta Elogios:", value=db["metas"]["elogios"])
    db["metas"]["qualidade"] = st.number_input("Meta Qualidade:", value=db["metas"]["qualidade"])
    if st.button("Salvar Metas"): save_all(db); st.rerun()
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Eu Fiz")
        for o in list(db["configuracoes"]["opcoes_eu_fiz"]):
            if not st.checkbox(o, value=True, key=f"e_{o}"):
                db["configuracoes"]["opcoes_eu_fiz"].remove(o); save_all(db); st.rerun()
    with c2:
        st.subheader("Ela Fez")
        for o in list(db["configuracoes"]["opcoes_ela_fez"]):
            if not st.checkbox(o, value=True, key=f"k_{o}"):
                db["configuracoes"]["opcoes_ela_fez"].remove(o); save_all(db); st.rerun()

# --- 6. INSIGHTS IA ---
elif menu == "💡 Insights da IA":
    st.header("💡 Análise do Especialista")
    if st.button("Gerar Análise"):
        recent = str(list(db["registros"].items())[-5:])
        prompt = f"Analise o relacionamento de Jhonata e Katheryn com base nisso: {recent}."
        resp = client_groq.chat.completions.create(model="llama3-70b-8192", messages=[{"role":"user","content":prompt}])
        st.info(resp.choices[0].message.content)

# --- 7. EVENTOS ---
elif menu == "📅 Eventos":
    st.header("📅 Calendário")
    with st.form("ev"):
        dt = st.date_input("Data:"); n = st.text_input("Evento:")
        if st.form_submit_button("Agendar"):
            db["eventos"][dt.strftime("%Y-%m-%d")] = n; save_all(db); st.rerun()
