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
st.set_page_config(page_title="Love Planner 4.12 - Full Edition", layout="wide", page_icon="❤️")

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

# --- GAMIFICAÇÃO ---
def get_nivel_info(xp):
    nivel = int((xp / 100) ** 0.5) + 1
    progresso = (xp % 100) / 100
    return nivel, progresso

# --- FUNÇÃO EXPORTAR PDF (CORRIGIDA PARA BYTES) ---
def gerar_pdf_com_capa(dados_mes, nome_mes, imagem_bytes=None):
    pdf = FPDF()
    pdf.add_page()
    
    # Capa
    if imagem_bytes:
        try:
            img_io = io.BytesIO(imagem_bytes)
            pdf.image(img_io, x=15, y=60, w=180)
        except:
            pass
    
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(200, 0, 0)
    pdf.text(60, 30, f"Memórias de {nome_mes}")
    pdf.set_font("Helvetica", "I", 14)
    pdf.text(75, 40, "Jhonata & Katheryn - 2026")
    
    # Conteúdo
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Relatório Mensal", ln=True, align='C')
    pdf.ln(10)
    
    for d, i in sorted(dados_mes.items()):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"Data: {d} | Nota: {i.get('nota')}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        resumo = i.get('resumo', '')
        pdf.multi_cell(0, 5, f"Resumo: {resumo}")
        if i.get('gratidao'):
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 5, f"Gratidão: {i['gratidao']}")
            pdf.set_text_color(0, 0, 0)
        pdf.ln(4)
    
    # RETORNA BYTES (Correção do erro 400/StreamlitAPIException)
    return bytes(pdf.output())

# --- INTERFACE LATERAL ---
nivel, prog = get_nivel_info(db["xp"])
st.sidebar.title(f"❤️ Love Planner 4.12")
st.sidebar.subheader(f"Nível de Conexão: {nivel}")
st.sidebar.progress(prog)
st.sidebar.caption(f"XP Total: {db['xp']}")

menu = st.sidebar.radio("Navegação:", ["📝 Diário", "📊 Painel & Grids", "🤝 Acordos", "⏳ Cápsula do Tempo", "📅 Eventos", "💡 Insights IA", "⚙️ Configurações"])

# --- 1. DIÁRIO ---
if menu == "📝 Diário":
    st.header("📝 Registro Diário")
    selected_date = st.date_input("Data:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    # Termômetro
    notas = [v['nota'] for v in list(db['registros'].values())[-3:] if 'nota' in v]
    if notas and (sum(notas)/len(notas)) < 5:
        st.error("🌡️ Alerta: A média de felicidade está baixa! Que tal um momento especial?")

    if is_locked:
        st.warning("🔒 Este dia está trancado.")
        if st.button("🔓 Destrancar"):
            db["registros"][date_str]["locked"] = False
            save_all(db); st.rerun()

    with st.form("diario_v12"):
        nota = st.select_slider("Nota do Relacionamento:", range(1,11), value=day_data.get("nota", 7), disabled=is_locked)
        gratidao = st.text_input("Gratidão do dia:", value=day_data.get("gratidao", ""), disabled=is_locked)
        
        col1, col2 = st.columns(2)
        with col1:
            eu_fiz = st.multiselect("Eu fiz:", db["configuracoes"]["opcoes_eu_fiz"], day_data.get("eu_fiz", []), disabled=is_locked)
            disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)
            cat_dr = st.selectbox("Motivo da DR:", CATEGORIAS_DR, disabled=not disc or is_locked)
        with col2:
            ela_fez = st.multiselect("Ela fez:", db["configuracoes"]["opcoes_ela_fez"], day_data.get("ela_fez", []), disabled=is_locked)
            sexo = st.radio("Sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)

        with st.expander("💬 WhatsApp"):
            ws_raw = st.text_area("Importar conversa:")
            if day_data.get("whatsapp_txt"): st.code(day_data["whatsapp_txt"])
        
        resumo = st.text_area("Resumo do Dia:", day_data.get("resumo", ""), disabled=is_locked)
        
        if st.form_submit_button("💾 Salvar Registro") and not is_locked:
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
            save_all(db); st.success("Registrado e XP Ganho!"); st.rerun()

# --- 2. PAINEL & EXPORTAÇÃO ---
elif menu == "📊 Painel & Grids":
    st.header("📊 Painel de Controle")
    
    # Exportação PDF
    st.subheader("📥 Exportar Mês em PDF")
    c_pdf1, c_pdf2 = st.columns(2)
    with c_pdf1:
        mes_sel = st.selectbox("Escolha o Mês:", ["01","02","03","04","05","06","07","08","09","10","11","12"])
        up_img = st.file_uploader("Foto de Capa (Opcional):", type=["png","jpg","jpeg"])
    with c_pdf2:
        if st.button("Gerar PDF"):
            dados_mes = {k: v for k, v in db["registros"].items() if k.split("-")[1] == mes_sel}
            if not dados_mes:
                st.warning("Sem dados para este mês.")
            else:
                img_bytes = up_img.read() if up_img else None
                pdf_bytes = gerar_pdf_com_capa(dados_mes, mes_sel, img_bytes)
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"Memorias_Amor_{mes_sel}.pdf",
                    mime="application/pdf"
                )

    st.divider()
    # Gráficos e Grids
    drs = [r.get("cat_dr") for r in db["registros"].values() if r.get("discussao") and r.get("cat_dr")]
    if drs:
        st.subheader("⚠️ Motivos de Discussão")
        st.bar_chart(pd.Series(drs).value_counts())

# --- 3. INSIGHTS IA ---
elif menu == "💡 Insights IA":
    st.header("💡 Análise do Especialista")
    if st.button("Analisar registros"):
        ctx = "".join([f"\nData: {d} | Nota: {i.get('nota')} | DR: {i.get('cat_dr')}" for d, i in list(db["registros"].items())[-5:]])
        try:
            resp = client_groq.chat.completions.create(model=db["config"]["modelo_ia"], messages=[{"role":"user","content":f"Analise Jhonata e Katheryn: {ctx}"}], max_tokens=800)
            st.info(resp.choices[0].message.content)
        except Exception as e: st.error(f"Erro na IA: {e}")

# --- DEMAIS ABAS ---
elif menu == "🤝 Acordos":
    st.header("🤝 Acordos")
    with st.form("ac"):
        t = st.text_input("Acordo:"); c = st.text_input("Nome Curto:"); m = st.checkbox("Monitorar?")
        if st.form_submit_button("Firmar"):
            db["acordos_mestres"].append({"titulo":t, "nome_curto":c, "monitorar":m, "data":str(date.today())})
            save_all(db); st.rerun()
    for i, ac in enumerate(db["acordos_mestres"]):
        st.write(f"- **{ac['nome_curto']}**: {ac['titulo']}")
        if st.button("Remover", key=f"del_{i}"):
            db["acordos_mestres"].pop(i); save_all(db); st.rerun()

elif menu == "⚙️ Configurações":
    st.header("⚙️ Configurações")
    db["config"]["modelo_ia"] = st.text_input("Modelo Groq:", value=db["config"].get("modelo_ia"))
    if st.button("Salvar Configs"):
        save_all(db); st.success("Configurações atualizadas!")

elif menu == "📅 Eventos":
    st.header("📅 Eventos")
    with st.form("ev"):
        dt = st.date_input("Data:"); ev = st.text_input("Evento:")
        if st.form_submit_button("Salvar"):
            db["eventos"][str(dt)] = ev; save_all(db); st.rerun()
    for d, e in db["eventos"].items(): st.write(f"**{d}:** {e}")

elif menu == "⏳ Cápsula do Tempo":
    st.header("⏳ Memórias")
    for d in [30, 90]:
        alvo = (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")
        if alvo in db["registros"]: st.info(f"Há {d} dias: {db['registros'][alvo].get('resumo')}")
