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
st.set_page_config(page_title="Love Planner 4.11 - Full Edition", layout="wide", page_icon="❤️")

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
        return data
    except:
        return {
            "registros": {}, "eventos": {}, "acordos_mestres": [], "xp": 0,
            "metas": {"elogios": 3, "qualidade": 2},
            "configuracoes": {"opcoes_eu_fiz": ["Elogio", "Tempo de Qualidade"], "opcoes_ela_fez": ["Carinho"]},
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

# --- GAMIFICAÇÃO (IDEIA 5) ---
def get_nivel_info(xp):
    nivel = int((xp / 100) ** 0.5) + 1
    progresso = (xp % 100) / 100
    return nivel, progresso

# --- FUNÇÃO EXPORTAR PDF (V4.9) ---
def gerar_pdf_com_capa(dados_mes, nome_mes, imagem_bytes=None):
    pdf = FPDF()
    pdf.add_page()
    if imagem_bytes:
        try:
            img = Image.open(io.BytesIO(imagem_bytes))
            pdf.image(io.BytesIO(imagem_bytes), x=15, y=50, w=180)
        except: pass
    
    pdf.set_font("Arial", "B", 24)
    pdf.set_text_color(200, 0, 0)
    pdf.text(60, 30, f"Memórias de {nome_mes}")
    pdf.set_font("Arial", "I", 14)
    pdf.text(75, 40, "Jhonata & Katheryn - 2026")
    
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Relatório Detalhado", ln=True, align='C')
    pdf.ln(10)
    
    for d, i in sorted(dados_mes.items()):
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, f"Data: {d} | Nota: {i.get('nota')}", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, f"Resumo: {i.get('resumo', '')}")
        if i.get('gratidao'):
            pdf.set_font("Arial", "I", 10)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 5, f"Gratidão: {i['gratidao']}")
            pdf.set_text_color(0, 0, 0)
        pdf.ln(4)
    return pdf.output()

# --- BARRA LATERAL (IDEIA 5) ---
nivel, prog = get_nivel_info(db["xp"])
st.sidebar.title(f"❤️ Love Planner 4.11")
st.sidebar.subheader(f"Nível de Conexão: {nivel}")
st.sidebar.progress(prog)
st.sidebar.caption(f"XP Total: {db['xp']}")

menu = st.sidebar.radio("Navegação:", ["📝 Diário", "📊 Painel & Grids", "🤝 Acordos", "⏳ Cápsula do Tempo", "📅 Eventos", "💡 Insights IA", "⚙️ Configurações"])

# --- 1. DIÁRIO (IDEIA 1, 2, 3) ---
if menu == "📝 Diário":
    st.header("📝 Registro Diário")
    selected_date = st.date_input("Data:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    # IDEIA 1: Alerta do Termômetro
    notas = [v['nota'] for v in list(db['registros'].values())[-3:] if 'nota' in v]
    if notas and (sum(notas)/len(notas)) < 5:
        st.error("🌡️ Alerta: A média de felicidade caiu! Que tal uma conversa carinhosa hoje?")

    if is_locked:
        st.warning("🔒 Este dia está trancado.")
        if st.button("🔓 Destrancar"):
            db["registros"][date_str]["locked"] = False
            save_all(db); st.rerun()

    with st.form("diario_v11"):
        nota = st.select_slider("Nota do Relacionamento:", range(1,11), value=day_data.get("nota", 7), disabled=is_locked)
        # IDEIA 2: Gratidão
        gratidao = st.text_input("Gratidão do dia (O que ela fez de bom?):", value=day_data.get("gratidao", ""), disabled=is_locked)
        
        col1, col2 = st.columns(2)
        with col1:
            eu_fiz = st.multiselect("Eu fiz:", db["configuracoes"]["opcoes_eu_fiz"], day_data.get("eu_fiz", []), disabled=is_locked)
            disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)
            # IDEIA 3: Categorização DR
            cat_dr = st.selectbox("Motivo da DR:", CATEGORIAS_DR, disabled=not disc or is_locked)
            
        with col2:
            ela_fez = st.multiselect("Ela fez:", db["configuracoes"]["opcoes_ela_fez"], day_data.get("ela_fez", []), disabled=is_locked)
            sexo = st.radio("Sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)

        with st.expander("💬 WhatsApp"):
            ws_raw = st.text_area("Importar conversa:")
            if day_data.get("whatsapp_txt"): st.code(day_data["whatsapp_txt"])
        
        resumo = st.text_area("Resumo do Dia:", day_data.get("resumo", ""), disabled=is_locked)
        
        if st.form_submit_button("💾 Salvar Registro") and not is_locked:
            # Gamificação (IDEIA 5)
            if date_str not in db["registros"]: db["xp"] += 15
            if gratidao: db["xp"] += 5
            if not disc: db["xp"] += 10
            
            ws_final = day_data.get("whatsapp_txt", "")
            if ws_raw:
                target = selected_date.strftime("%d/%m/%y")
                ws_final = "\n".join([l for l in ws_raw.split('\n') if target in l])

            db["registros"][date_str] = {
                "nota": nota, "gratidao": gratidao, "eu_fiz": eu_fiz, "ela_fez": ela_fez,
                "discussao": disc, "cat_dr": cat_dr if disc else None, "sexo": sexo == "Sim",
                "resumo": resumo, "whatsapp_txt": ws_final, "locked": True
            }
            save_all(db); st.success("XP Ganho!"); st.rerun()

# --- 2. PAINEL (IDEIA 1, 3) ---
elif menu == "📊 Painel & Grids":
    st.header("📊 Painel de Controle 2026")
    
    # IDEIA 3: Gráfico de DR
    drs = [r.get("cat_dr") for r in db["registros"].values() if r.get("discussao") and r.get("cat_dr")]
    if drs:
        col_dr, col_term = st.columns(2)
        with col_dr:
            st.subheader("⚠️ Motivos de Conflito")
            st.bar_chart(pd.Series(drs).value_counts())
        with col_term:
            st.subheader("🌡️ Tendência de Felicidade")
            df_notas = pd.DataFrame([{"Data": k, "Nota": v["nota"]} for k, v in db["registros"].items()])
            if not df_notas.empty: st.line_chart(df_notas.set_index("Data"))

    # Exportação PDF (V4.9)
    st.divider()
    st.subheader("📥 Exportar Mês")
    col_pdf1, col_pdf2 = st.columns(2)
    with col_pdf1:
        mes_sel = st.selectbox("Mês:", ["01","02","03","04","05","06","07","08","09","10","11","12"])
        up_img = st.file_uploader("Foto de Capa:", type=["png","jpg"])
    with col_pdf2:
        if st.button("Gerar PDF"):
            dados_mes = {k: v for k, v in db["registros"].items() if k.split("-")[1] == mes_sel}
            img_bytes = up_img.read() if up_img else None
            pdf_out = gerar_pdf_com_capa(dados_mes, mes_sel, img_bytes)
            st.download_button("Download PDF", pdf_out, f"Amor_{mes_sel}.pdf")

# --- 3. INSIGHTS IA ---
elif menu == "💡 Insights IA":
    st.header("💡 Análise do Especialista")
    if st.button("Analisar registros"):
        ctx = "".join([f"\nData: {d} | Nota: {i.get('nota')} | DR: {i.get('cat_dr')} | Gratidão: {i.get('gratidao')}" for d, i in list(db["registros"].items())[-5:]])
        try:
            resp = client_groq.chat.completions.create(model=db["config"]["modelo_ia"], messages=[{"role":"user","content":f"Como terapeuta, analise Jhonata e Katheryn: {ctx}"}], max_tokens=800)
            st.info(resp.choices[0].message.content)
        except Exception as e: st.error(f"Erro: {e}")

# --- DEMAIS ABAS (ACORDOS, CONFIGS, EVENTOS) ---
elif menu == "🤝 Acordos":
    st.header("🤝 Acordos")
    with st.form("ac"):
        t = st.text_input("Acordo:"); c = st.text_input("Nome Curto:"); m = st.checkbox("Monitorar?")
        if st.form_submit_button("Firmar"):
            db["acordos_mestres"].append({"titulo":t, "nome_curto":c, "monitorar":m, "data":str(date.today())})
            save_all(db); st.rerun()
    for i, ac in enumerate(db["acordos_mestres"]):
        st.write(f"- {ac['nome_curto']}: {ac['titulo']}")
        if st.button("Remover", key=f"del_{i}"): db["acordos_mestres"].pop(i); save_all(db); st.rerun()

elif menu == "⚙️ Configurações":
    st.header("⚙️ Configs")
    db["config"]["modelo_ia"] = st.text_input("Modelo Groq:", value=db["config"].get("modelo_ia"))
    if st.button("Salvar"): save_all(db); st.success("Ok!")

elif menu == "📅 Eventos":
    st.header("📅 Calendário")
    with st.form("ev"):
        dt = st.date_input("Data:"); ev = st.text_input("Evento:")
        if st.form_submit_button("Salvar"): db["eventos"][str(dt)] = ev; save_all(db); st.rerun()
    for d, e in db["eventos"].items(): st.write(f"**{d}:** {e}")

elif menu == "⏳ Cápsula do Tempo":
    st.header("⏳ Memórias Antigas")
    for d in [30, 90]:
        alvo = (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")
        if alvo in db["registros"]: st.info(f"Há {d} dias: {db['registros'][alvo].get('resumo')}")
