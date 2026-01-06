import streamlit as st
import pandas as pd
import json
import io
import altair as alt
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq
from fpdf import FPDF
from PIL import Image

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Love Planner 2026", layout="centered", page_icon="❤️")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap');

    :root {
        --primary: #f42536;
        --bg-light: #fcf8f8;
        --card-bg: #ffffff;
        --shadow: 0 4px 20px -2px rgba(244, 37, 54, 0.08);
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: var(--bg-light);
    }

    .css-card {
        background-color: var(--card-bg);
        border-radius: 24px;
        padding: 24px;
        box-shadow: var(--shadow);
        border: 1px solid #e8ced1;
        margin-bottom: 20px;
    }

    div.stButton > button {
        background-color: var(--primary);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 12px 24px;
        font-weight: 700;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #d11a2a;
        color: white;
    }
    
    /* Botão de Excluir (Visual Diferente) */
    div.stButton > button.delete-btn {
        background-color: #ef4444;
    }

    .xp-card {
        background: linear-gradient(135deg, #f42536 0%, #ff5c6a 100%);
        color: white;
        border-radius: 24px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(244, 37, 54, 0.4);
        margin-bottom: 20px;
    }
    .xp-stat { font-size: 3rem; font-weight: 800; line-height: 1; }
    .xp-label { font-size: 0.9rem; opacity: 0.9; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# --- SEGURANÇA ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except Exception:
    st.error("Erro nos Secrets.")
    st.stop()

# APIs
client_groq = Groq(api_key=GROQ_API_KEY)
auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)
repo = g.get_repo(GITHUB_REPO)

# --- DADOS ---
LINGUAGENS_LISTA = ["Atos de Serviço", "Palavras de Afirmação", "Tempo de Qualidade", "Toque Físico", "Presentes"]
CATEGORIAS_DR = ["Comunicação", "Finanças", "Ciúmes", "Família", "Rotina", "Outros"]

def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        data = json.loads(contents.decoded_content.decode())
        if "xp" not in data: data["xp"] = 0
        if "config" not in data: data["config"] = {"modelo_ia": "llama-3.3-70b-versatile"}
        if "acordos_mestres" not in data: data["acordos_mestres"] = []
        if "metas" not in data: data["metas"] = {"elogios": 3, "qualidade": 2}
        if "configuracoes" not in data:
             data["configuracoes"] = {"opcoes_eu_fiz": ["Elogio", "Tempo de Qualidade"], "opcoes_ela_fez": ["Carinho"]}
        return data
    except:
        return {"registros": {}, "eventos": {}, "acordos_mestres": [], "xp": 0, "metas": {"elogios": 3, "qualidade": 2}, "configuracoes": {"opcoes_eu_fiz": ["Elogio"], "opcoes_ela_fez": ["Carinho"]}, "config": {"modelo_ia": "llama-3.3-70b-versatile"}}

def save_all(data):
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents("data_2026.json")
        repo.update_file(contents.path, f"Sync {datetime.now()}", json_data, contents.sha)
    except:
        repo.create_file("data_2026.json", "DB Init", json_data)

db = load_data()

# --- HELPER GAMIFICAÇÃO ---
def get_nivel_info(xp):
    nivel = int((xp / 100) ** 0.5) + 1
    prox_nivel_xp = ((nivel) ** 2) * 100
    return nivel, prox_nivel_xp

# --- HELPER PDF ---
def gerar_pdf(dados_mes, nome_mes, img_bytes=None):
    pdf = FPDF()
    pdf.add_page()
    
    if img_bytes:
        try:
            img_io = io.BytesIO(img_bytes)
            pdf.image(img_io, x=15, y=60, w=180)
        except: pass

    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(244, 37, 54)
    pdf.cell(0, 10, f"Planner {nome_mes}", ln=True, align='C')
    pdf.ln(10)
    for d, i in sorted(dados_mes.items()):
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"{d} | Nota: {i.get('nota')}", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, i.get('resumo', ''))
        pdf.ln(5)
    return bytes(pdf.output())

# --- NAVEGAÇÃO ---
st.sidebar.markdown("### ❤️ Menu")
menu = st.sidebar.radio("", ["Dashboard", "Registrar Dia", "Metas & Acordos", "Cápsula", "Insights IA", "Configurações"])

# --- HEADER DE GAMIFICAÇÃO ---
nivel, meta_xp = get_nivel_info(db["xp"])
if menu == "Dashboard":
    st.markdown(f"""
    <div class="xp-card">
        <div class="xp-label">NÍVEL DE CONEXÃO</div>
        <div class="xp-stat">{nivel}</div>
        <div style="background: rgba(255,255,255,0.3); height: 6px; border-radius: 3px; margin-top: 10px; overflow: hidden;">
            <div style="background: white; width: {(db['xp']/meta_xp)*100}%; height: 100%;"></div>
        </div>
        <div style="font-size: 0.8rem; margin-top: 5px; opacity: 0.8;">{db['xp']} / {meta_xp} XP</div>
    </div>
    """, unsafe_allow_html=True)

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    with st.container():
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.markdown("### 📈 Humor da Semana")
        
        df_notas = pd.DataFrame([
            {"Data": datetime.strptime(k, "%Y-%m-%d"), "Nota": v["nota"]} 
            for k, v in db["registros"].items() if "nota" in v
        ]).sort_values("Data")
        
        if not df_notas.empty:
            chart = alt.Chart(df_notas).mark_line(
                interpolate='monotone', 
                color='#f42536',
                strokeWidth=3
            ).encode(
                x=alt.X('Data', axis=alt.Axis(format='%d/%m')),
                y=alt.Y('Nota', scale=alt.Scale(domain=[0, 10])),
                tooltip=['Data', 'Nota']
            ).properties(height=200)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Registre seu primeiro dia para ver o gráfico!")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 🔥 Mapas de Calor")
    def draw_grid(title, metric, color):
        st.caption(title)
        days = pd.date_range("2026-01-01", "2026-12-31")
        grid = '<div style="display: flex; flex-wrap: wrap; gap: 3px; max-width: 800px; margin-bottom: 20px;">'
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
            grid += f'<div title="{ds}" style="width: 10px; height: 10px; background-color: {c}; border-radius: 2px;"></div>'
        st.markdown(grid + '</div>', unsafe_allow_html=True)

    draw_grid("Frequência Sexual", "sexo", "#e91e63")
    draw_grid("Discussões", "discussao", "#f44336")

# --- 2. REGISTRAR DIA ---
elif menu == "Registrar Dia":
    st.markdown("## 📝 Registrar Dia")
    
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    
    selected_date = st.date_input("Data:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = db["registros"].get(date_str, {})
    
    if day_data.get("locked"):
        st.warning("🔒 Dia registrado!")
        if st.button("🔓 Editar"):
            db["registros"][date_str]["locked"] = False
            save_all(db); st.rerun()
    else:
        with st.form("form_registro"):
            st.subheader("Como foi hoje?")
            nota = st.slider("", 1, 10, value=day_data.get("nota", 8))
            
            st.write("---")
            c1, c2 = st.columns(2)
            with c1:
                st.caption("JHONATA (EU)")
                eu_fiz = st.multiselect("Eu fiz:", db["configuracoes"]["opcoes_eu_fiz"], day_data.get("eu_fiz", []))
                ling_eu = st.multiselect("Minhas Linguagens:", LINGUAGENS_LISTA, day_data.get("ling_eu", []))
                
                disc = st.checkbox("Teve DR?", day_data.get("discussao", False))
                if disc: cat_dr = st.selectbox("Motivo:", CATEGORIAS_DR)
                else: cat_dr = None
            with c2:
                st.caption("KATHERYN (ELA)")
                ela_fez = st.multiselect("Ela fez:", db["configuracoes"]["opcoes_ela_fez"], day_data.get("ela_fez", []))
                ling_ela = st.multiselect("Linguagens Dela:", LINGUAGENS_LISTA, day_data.get("ling_ela", []))
                
                sexo = st.radio("Intimidade:", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, horizontal=True)

            with st.expander("Importar WhatsApp"):
                ws_raw = st.text_area("Cole a conversa aqui:")
                if day_data.get("whatsapp_txt"): st.code(day_data["whatsapp_txt"][:200]+"...")

            resumo = st.text_area("Diário de Bordo:", day_data.get("resumo", ""), height=100)
            gratidao = st.text_input("Gratidão do dia:", day_data.get("gratidao", ""))

            if st.form_submit_button("Salvar Registro"):
                xp_ganho = 0
                if date_str not in db["registros"]: xp_ganho = 20
                if gratidao: xp_ganho += 5
                
                ws_final = day_data.get("whatsapp_txt", "")
                if ws_raw:
                    target = selected_date.strftime("%d/%m/%y")
                    ws_final = "\n".join([l for l in ws_raw.split('\n') if target in l])

                db["xp"] += xp_ganho
                db["registros"][date_str] = {
                    "nota": nota, "gratidao": gratidao, "eu_fiz": eu_fiz, "ela_fez": ela_fez,
                    "ling_eu": ling_eu, "ling_ela": ling_ela,
                    "discussao": disc, "cat_dr": cat_dr, "sexo": sexo == "Sim", 
                    "resumo": resumo, "whatsapp_txt": ws_final, "locked": True
                }
                save_all(db)
                st.success(f"Salvo! +{xp_ganho} XP")
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 3. METAS E ACORDOS ---
elif menu == "Metas & Acordos":
    st.markdown("## 🎯 Metas & Acordos")
    
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### Metas da Semana")
    hoje = date.today()
    inicio_sem = hoje - timedelta(days=hoje.weekday())
    reg_semana = [db["registros"].get((inicio_sem + timedelta(days=i)).strftime("%Y-%m-%d"), {}) for i in range(7)]
    
    c_elogios = sum(1 for r in reg_semana if "Elogio" in str(r.get("eu_fiz", [])))
    st.write(f"**Elogios** ({c_elogios}/{db['metas']['elogios']})")
    st.progress(min(c_elogios/db['metas']['elogios'], 1.0))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### Acordos Ativos")
    for ac in db["acordos_mestres"]:
        status = "🟢" if ac.get('monitorar') else "⚪"
        st.markdown(f"**{status} {ac['titulo']}**")
    
    with st.expander("Adicionar Acordo"):
        with st.form("novo_acordo"):
            t = st.text_input("Acordo")
            if st.form_submit_button("Salvar"):
                db["acordos_mestres"].append({"titulo": t, "nome_curto": t[:10], "monitorar": True, "data": str(date.today())})
                save_all(db); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. CÁPSULA (PDF) ---
elif menu == "Cápsula":
    st.markdown("## ⏳ Cápsula & Exportação")
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    
    st.markdown("### 📥 Exportar PDF")
    c_pdf1, c_pdf2 = st.columns(2)
    with c_pdf1:
        mes_sel = st.selectbox("Mês:", ["01","02","03","04","05","06","07","08","09","10","11","12"])
        up_img = st.file_uploader("Capa (Opcional):", type=["png","jpg"])
    with c_pdf2:
        st.write("") 
        st.write("")
        if st.button("Gerar PDF"):
            dados_mes = {k: v for k, v in db["registros"].items() if k.split("-")[1] == mes_sel}
            if dados_mes:
                img_bytes = up_img.read() if up_img else None
                pdf_bytes = gerar_pdf(dados_mes, mes_sel, img_bytes)
                st.download_button("Baixar", pdf_bytes, f"Amor_{mes_sel}.pdf", "application/pdf")
            else:
                st.warning("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. CONFIGURAÇÕES (GERENCIAMENTO COMPLETO) ---
elif menu == "Configurações":
    st.markdown("## ⚙️ Ajustes")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.markdown("### Gerenciar 'Eu Fiz'")
        
        # Adicionar
        new_eu = st.text_input("Novo:", key="new_eu")
        if st.button("Adicionar (Eu)"):
            if new_eu and new_eu not in db["configuracoes"]["opcoes_eu_fiz"]:
                db["configuracoes"]["opcoes_eu_fiz"].append(new_eu)
                save_all(db); st.rerun()
        
        st.divider()
        
        # Editar/Excluir
        opts_eu = db["configuracoes"]["opcoes_eu_fiz"]
        if opts_eu:
            sel_eu = st.selectbox("Editar/Excluir:", opts_eu, key="sel_eu")
            edit_eu = st.text_input("Renomear para:", value=sel_eu, key="ren_eu")
            
            ce1, ce2 = st.columns(2)
            if ce1.button("Renomear", key="btn_ren_eu"):
                idx = opts_eu.index(sel_eu)
                db["configuracoes"]["opcoes_eu_fiz"][idx] = edit_eu
                save_all(db); st.rerun()
            if ce2.button("Excluir", key="btn_del_eu"):
                db["configuracoes"]["opcoes_eu_fiz"].remove(sel_eu)
                save_all(db); st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.markdown("### Gerenciar 'Ela Fez'")
        
        # Adicionar
        new_ela = st.text_input("Novo:", key="new_ela")
        if st.button("Adicionar (Ela)"):
            if new_ela and new_ela not in db["configuracoes"]["opcoes_ela_fez"]:
                db["configuracoes"]["opcoes_ela_fez"].append(new_ela)
                save_all(db); st.rerun()
        
        st.divider()
        
        # Editar/Excluir
        opts_ela = db["configuracoes"]["opcoes_ela_fez"]
        if opts_ela:
            sel_ela = st.selectbox("Editar/Excluir:", opts_ela, key="sel_ela")
            edit_ela = st.text_input("Renomear para:", value=sel_ela, key="ren_ela")
            
            ce3, ce4 = st.columns(2)
            if ce3.button("Renomear", key="btn_ren_ela"):
                idx = opts_ela.index(sel_ela)
                db["configuracoes"]["opcoes_ela_fez"][idx] = edit_ela
                save_all(db); st.rerun()
            if ce4.button("Excluir", key="btn_del_ela"):
                db["configuracoes"]["opcoes_ela_fez"].remove(sel_ela)
                save_all(db); st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        if st.button("Limpar Cache (Se der erro visual)"):
             st.cache_data.clear()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. INSIGHTS IA ---
elif menu == "Insights IA":
    st.header("💡 Mentor IA")
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    if st.button("Analisar Semana"):
        ctx = str(list(db["registros"].items())[-7:])
        try:
            prompt = f"Seja um mentor amoroso. Analise: {ctx}. Dê conselhos."
            resp = client_groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
            st.success(resp.choices[0].message.content)
        except Exception as e:
            st.error(f"Erro: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
