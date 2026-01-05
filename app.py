import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq
from fpdf import FPDF
from PIL import Image

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Love Planner 4.13 - Full Edition", layout="wide", page_icon="❤️")

# --- SEGURANÇA (SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except Exception:
    st.error("Erro nos Secrets. Verifique o painel do Streamlit Cloud.")
    st.stop()

# Inicialização de APIs
client_groq = Groq(api_key=GROQ_API_KEY)
auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)
repo = g.get_repo(GITHUB_REPO)

# --- CONSTANTES ---
LINGUAGENS_LISTA = ["Atos de Serviço", "Palavras de Afirmação", "Tempo de Qualidade", "Toque Físico", "Presentes"]
CATEGORIAS_DR = ["Comunicação", "Finanças", "Tempo Juntos", "Ciúmes/Insegurança", "Família", "Tarefas Domésticas", "Outros"]

# --- FUNÇÕES DE DADOS ---
def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        data = json.loads(contents.decoded_content.decode())
        if "xp" not in data: data["xp"] = 0
        if "config" not in data: data["config"] = {"modelo_ia": "llama-3.3-70b-versatile"}
        if "acordos_mestres" not in data: data["acordos_mestres"] = []
        if "metas" not in data: data["metas"] = {"elogios": 3, "qualidade": 2}
        if "configuracoes" not in data:
            data["configuracoes"] = {
                "opcoes_eu_fiz": ["Elogio", "Tempo de Qualidade", "Ajuda", "Cozinhar"],
                "opcoes_ela_fez": ["Carinho", "Apoio", "Cuidado"]
            }
        return data
    except:
        return {
            "registros": {}, "eventos": {}, "acordos_mestres": [], "xp": 0,
            "metas": {"elogios": 3, "qualidade": 2},
            "configuracoes": {"opcoes_eu_fiz": ["Elogio"], "opcoes_ela_fez": ["Carinho"]},
            "config": {"modelo_ia": "llama-3.3-70b-versatile"}
        }

def save_all(data):
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents("data_2026.json")
        repo.update_file(contents.path, f"Sync {datetime.now()}", json_data, contents.sha)
    except:
        repo.create_file("data_2026.json", "DB Init", json_data)

db = load_data()

# --- GAMIFICAÇÃO ---
def get_nivel_info(xp):
    nivel = int((xp / 100) ** 0.5) + 1
    progresso = (xp % 100) / 100
    return nivel, progresso

# --- FUNÇÃO EXPORTAR PDF ---
def gerar_pdf_com_capa(dados_mes, nome_mes, imagem_bytes=None):
    pdf = FPDF()
    pdf.add_page()
    if imagem_bytes:
        try:
            img_io = io.BytesIO(imagem_bytes)
            pdf.image(img_io, x=15, y=60, w=180)
        except: pass
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(200, 0, 0)
    pdf.text(60, 30, f"Memórias de {nome_mes}")
    pdf.set_font("Helvetica", "I", 14)
    pdf.text(75, 40, "Jhonata & Katheryn - 2026")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Relatório Mensal", ln=True, align='C')
    pdf.ln(10)
    for d, i in sorted(dados_mes.items()):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"Data: {d} | Nota: {i.get('nota')}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, f"Resumo: {i.get('resumo', '')}")
        if i.get('gratidao'):
            pdf.set_font("Helvetica", "I", 10); pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 5, f"Gratidão: {i['gratidao']}")
            pdf.set_text_color(0, 0, 0)
        pdf.ln(4)
    return bytes(pdf.output())

# --- BARRA LATERAL ---
nivel, prog = get_nivel_info(db["xp"])
st.sidebar.title(f"❤️ Love Planner 4.13")
st.sidebar.subheader(f"Nível de Conexão: {nivel}")
st.sidebar.progress(prog)

menu = st.sidebar.radio("Navegação:", ["📝 Diário", "📊 Painel & Grids", "🤝 Acordos", "⏳ Cápsula do Tempo", "📅 Eventos", "💡 Insights IA", "⚙️ Configurações"])

# --- 1. DIÁRIO ---
if menu == "📝 Diário":
    st.header("📝 Registro Diário")
    selected_date = st.date_input("Data:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    if is_locked:
        st.warning("🔒 Trancado.")
        if st.button("🔓 Destrancar"):
            db["registros"][date_str]["locked"] = False
            save_all(db); st.rerun()

    with st.form("diario_v13"):
        nota = st.select_slider("Nota do Relacionamento:", range(1,11), value=day_data.get("nota", 7), disabled=is_locked)
        gratidao = st.text_input("Gratidão do dia:", value=day_data.get("gratidao", ""), disabled=is_locked)
        
        col1, col2 = st.columns(2)
        with col1:
            eu_fiz = st.multiselect("Eu fiz:", db["configuracoes"]["opcoes_eu_fiz"], day_data.get("eu_fiz", []), disabled=is_locked)
            ling_eu = st.multiselect("Minhas Linguagens:", LINGUAGENS_LISTA, day_data.get("ling_eu", []), disabled=is_locked)
            disc = st.checkbox("Discussão?", day_data.get("discussao", False), disabled=is_locked)
            cat_dr = st.selectbox("Motivo DR:", CATEGORIAS_DR, disabled=not disc or is_locked)
        with col2:
            ela_fez = st.multiselect("Ela fez:", db["configuracoes"]["opcoes_ela_fez"], day_data.get("ela_fez", []), disabled=is_locked)
            ling_ela = st.multiselect("Linguagens dela:", LINGUAGENS_LISTA, day_data.get("ling_ela", []), disabled=is_locked)
            sexo = st.radio("Sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)

        with st.expander("💬 WhatsApp"):
            ws_raw = st.text_area("Importar conversa:")
            if day_data.get("whatsapp_txt"): st.code(day_data["whatsapp_txt"])
        
        resumo = st.text_area("Resumo:", day_data.get("resumo", ""), disabled=is_locked)
        
        if st.form_submit_button("💾 Salvar") and not is_locked:
            if date_str not in db["registros"]: db["xp"] += 20
            if gratidao: db["xp"] += 5
            ws_final = day_data.get("whatsapp_txt", "")
            if ws_raw:
                target = selected_date.strftime("%d/%m/%y")
                ws_final = "\n".join([l for l in ws_raw.split('\n') if target in l])
            db["registros"][date_str] = {
                "nota": nota, "gratidao": gratidao, "eu_fiz": eu_fiz, "ela_fez": ela_fez,
                "ling_eu": ling_eu, "ling_ela": ling_ela, "discussao": disc, "cat_dr": cat_dr if disc else None,
                "sexo": sexo == "Sim", "resumo": resumo, "whatsapp_txt": ws_final, "locked": True
            }
            save_all(db); st.rerun()

# --- 2. PAINEL & GRIDS (REINTEGRADO) ---
elif menu == "📊 Painel & Grids":
    st.header("📊 Painel de Controle")
    
    # Metas Semanais
    hoje = date.today()
    inicio_sem = hoje - timedelta(days=hoje.weekday())
    reg_semana = [db["registros"].get((inicio_sem + timedelta(days=i)).strftime("%Y-%m-%d"), {}) for i in range(7)]
    c_elogios = sum(1 for r in reg_semana if "Elogio" in str(r.get("eu_fiz", [])))
    c_qualidade = sum(1 for r in reg_semana if "Tempo de Qualidade" in str(r.get("eu_fiz", [])))
    
    m1, m2 = st.columns(2)
    m1.metric("Elogios (Semana)", f"{c_elogios}/{db['metas']['elogios']}")
    m2.metric("Qualidade (Semana)", f"{c_qualidade}/{db['metas']['qualidade']}")

    # Exportação PDF
    st.divider()
    st.subheader("📥 Exportar Mês em PDF")
    c_pdf1, c_pdf2 = st.columns(2)
    with c_pdf1:
        mes_sel = st.selectbox("Escolha o Mês:", ["01","02","03","04","05","06","07","08","09","10","11","12"])
        up_img = st.file_uploader("Foto de Capa:", type=["png","jpg"])
    with c_pdf2:
        if st.button("Gerar PDF"):
            dados_mes = {k: v for k, v in db["registros"].items() if k.split("-")[1] == mes_sel}
            if dados_mes:
                pdf_bytes = gerar_pdf_com_capa(dados_mes, mes_sel, up_img.read() if up_img else None)
                st.download_button("Download PDF", pdf_bytes, f"Amor_{mes_sel}.pdf", "application/pdf")

    # FUNÇÃO DE GRID
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
    cols_ling = ["#ff5722", "#3f51b5", "#00bcd4", "#9c27b0", "#8bc34a"]
    for i, l in enumerate(LINGUAGENS_LISTA): draw_grid(l, l, cols_ling[i])

# --- DEMAIS ABAS ---
elif menu == "🤝 Acordos":
    st.header("🤝 Acordos")
    with st.form("ac"):
        t = st.text_input("Acordo:"); c = st.text_input("Nome Curto:"); m = st.checkbox("Monitorar?")
        if st.form_submit_button("Firmar"):
            db["acordos_mestres"].append({"titulo":t, "nome_curto":c, "monitorar":m, "data":str(date.today())})
            save_all(db); st.rerun()
    for i, ac in enumerate(db["acordos_mestres"]):
        st.write(f"- {ac['nome_curto']}: {ac['titulo']}")
        if st.button("Remover", key=f"d_{i}"): db["acordos_mestres"].pop(i); save_all(db); st.rerun()

elif menu == "💡 Insights IA":
    st.header("💡 Insights")
    if st.button("Analisar"):
        ctx = str(list(db["registros"].items())[-5:])
        resp = client_groq.chat.completions.create(model=db["config"]["modelo_ia"], messages=[{"role":"user","content":f"Analise: {ctx}"}], max_tokens=800)
        st.info(resp.choices[0].message.content)

elif menu == "⚙️ Configurações":
    st.header("⚙️ Configurações")
    db["config"]["modelo_ia"] = st.text_input("Modelo Groq:", value=db["config"].get("modelo_ia"))
    db["metas"]["elogios"] = st.number_input("Meta Elogios:", value=db["metas"]["elogios"])
    db["metas"]["qualidade"] = st.number_input("Meta Qualidade:", value=db["metas"]["qualidade"])
    if st.button("Salvar"): save_all(db); st.success("Salvo!")

elif menu == "📅 Eventos":
    st.header("📅 Calendário")
    with st.form("ev"):
        dt = st.date_input("Data:"); ev = st.text_input("Evento:")
        if st.form_submit_button("Salvar"): db["eventos"][str(dt)] = ev; save_all(db); st.rerun()
    for d, e in db["eventos"].items(): st.write(f"**{d}:** {e}")

elif menu == "⏳ Cápsula do Tempo":
    st.header("⏳ Memórias")
    for d in [30, 90]:
        alvo = (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")
        if alvo in db["registros"]: st.info(f"Há {d} dias: {db['registros'][alvo].get('resumo')}")
