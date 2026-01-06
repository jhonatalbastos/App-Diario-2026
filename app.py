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

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Love Planner 2026", layout="centered", page_icon="❤️")

# --- SEGURANÇA (SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except Exception:
    st.error("Erro nos Secrets.")
    st.stop()

# Inicialização de APIs
client_groq = Groq(api_key=GROQ_API_KEY)
auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)
repo = g.get_repo(GITHUB_REPO)

# --- FUNÇÕES DE DADOS ---
def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        data = json.loads(contents.decoded_content.decode())
        # Garantir chaves essenciais
        if "xp" not in data: data["xp"] = 0
        if "config" not in data: data["config"] = {"modelo_ia": "llama-3.3-70b-versatile", "tema": "Claro"}
        if "acordos_mestres" not in data: data["acordos_mestres"] = []
        if "metas" not in data: data["metas"] = {"elogios": 3, "qualidade": 2}
        if "configuracoes" not in data:
             data["configuracoes"] = {"opcoes_eu_fiz": ["Elogio", "Tempo de Qualidade"], "opcoes_ela_fez": ["Carinho"]}
        if "tema" not in data["config"]: data["config"]["tema"] = "Claro"
        return data
    except:
        return {
            "registros": {}, "eventos": {}, "acordos_mestres": [], "xp": 0,
            "metas": {"elogios": 3, "qualidade": 2},
            "configuracoes": {"opcoes_eu_fiz": ["Elogio"], "opcoes_ela_fez": ["Carinho"]},
            "config": {"modelo_ia": "llama-3.3-70b-versatile", "tema": "Claro"}
        }

def save_all(data):
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents("data_2026.json")
        repo.update_file(contents.path, f"Sync {datetime.now()}", json_data, contents.sha)
    except:
        repo.create_file("data_2026.json", "DB Init", json_data)

# Carregar dados
db = load_data()
tema_atual = db["config"].get("tema", "Claro")

# --- DEFINIÇÃO DE CORES POR TEMA (CORREÇÃO VISUAL) ---
if tema_atual == "Escuro":
    # Paleta Dark Mode
    cor_bg = "#0e1117"          # Fundo geral do Streamlit Dark
    cor_sidebar = "#262730"     # Fundo da Sidebar Dark
    cor_card = "#1e1e1e"        # Fundo dos Cards
    cor_texto = "#fafafa"       # Texto quase branco
    cor_texto_sec = "#b0b0b0"   # Texto secundário
    cor_border = "#333333"      # Bordas sutis
    cor_input_bg = "#2b2c35"    # Fundo de inputs
else:
    # Paleta Light Mode
    cor_bg = "#fcf8f8"
    cor_sidebar = "#f0f2f6"
    cor_card = "#ffffff"
    cor_texto = "#1c0d0e"
    cor_texto_sec = "#555555"
    cor_border = "#e8ced1"
    cor_input_bg = "#ffffff"

# --- ESTILIZAÇÃO CSS DINÂMICA (CORRIGIDA) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap');

    :root {{
        --primary: #f42536;
        --bg-app: {cor_bg};
        --bg-sidebar: {cor_sidebar};
        --bg-card: {cor_card};
        --text-main: {cor_texto};
        --text-sec: {cor_texto_sec};
        --border-color: {cor_border};
        --input-bg: {cor_input_bg};
    }}

    /* Fonte Global */
    html, body, [class*="css"], .stApp {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: var(--bg-app);
        color: var(--text-main);
    }}

    /* CORREÇÃO SIDEBAR: Forçar cores corretas na barra lateral */
    [data-testid="stSidebar"] {{
        background-color: var(--bg-sidebar);
        border-right: 1px solid var(--border-color);
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div {{
        color: var(--text-main) !important;
    }}
    /* Cor dos Radio Buttons na Sidebar */
    [data-testid="stSidebar"] .stRadio label {{
        color: var(--text-main) !important;
    }}

    /* Estilo dos Containers (Cards) */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 24px;
        box-shadow: 0 4px 20px -2px rgba(244, 37, 54, 0.05);
        padding: 20px;
    }}

    /* Botões */
    div.stButton > button {{
        background-color: var(--primary);
        color: white !important;
        border-radius: 12px;
        border: none;
        padding: 12px 24px;
        font-weight: 700;
        width: 100%;
        transition: all 0.2s;
    }}
    div.stButton > button:hover {{
        background-color: #d11a2a;
        transform: scale(1.01);
    }}
    
    /* Inputs (Correção para ficarem visíveis no escuro) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea, .stDateInput input {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-color);
        border-radius: 12px;
    }}
    
    /* Sliders */
    .stSlider [data-baseweb="slider"] {{
        color: var(--primary);
    }}

    /* Card de XP (Gamificação) */
    .xp-card {{
        background: linear-gradient(135deg, #f42536 0%, #ff5c6a 100%);
        color: white !important;
        border-radius: 24px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(244, 37, 54, 0.4);
        margin-bottom: 20px;
    }}
    .xp-stat {{ font-size: 3rem; font-weight: 800; line-height: 1; color: white !important; }}
    .xp-label {{ font-size: 0.9rem; opacity: 0.9; font-weight: 500; color: white !important; }}
    
    /* Títulos */
    h1, h2, h3, h4 {{ color: var(--text-main) !important; }}
    p, label, span {{ color: var(--text-main); }}
    .stMarkdown p {{ color: var(--text-main) !important; }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background-color: var(--bg-card);
        color: var(--text-main);
    }}
</style>
""", unsafe_allow_html=True)

# --- DADOS CONSTANTES ---
LINGUAGENS_LISTA = ["Atos de Serviço", "Palavras de Afirmação", "Tempo de Qualidade", "Toque Físico", "Presentes"]
CATEGORIAS_DR = ["Comunicação", "Finanças", "Ciúmes", "Família", "Rotina", "Outros"]

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

# --- HEADER XP ---
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
    with st.container(border=True):
        st.markdown("### 📈 Humor da Semana")
        df_notas = pd.DataFrame([
            {"Data": datetime.strptime(k, "%Y-%m-%d"), "Nota": v["nota"]} 
            for k, v in db["registros"].items() if "nota" in v
        ]).sort_values("Data")
        
        if not df_notas.empty:
            chart = alt.Chart(df_notas).mark_line(
                interpolate='monotone', color='#f42536', strokeWidth=3
            ).encode(
                x=alt.X('Data', axis=alt.Axis(format='%d/%m')),
                y=alt.Y('Nota', scale=alt.Scale(domain=[0, 10])),
                tooltip=['Data', 'Nota']
            ).properties(height=200)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Registre seu primeiro dia!")

    st.markdown("### 🔥 Mapas de Calor")
    def draw_grid(title, metric, color):
        st.caption(title)
        days = pd.date_range("2026-01-01", "2026-12-31")
        grid = '<div style="display: flex; flex-wrap: wrap; gap: 3px; max-width: 800px; margin-bottom: 20px;">'
        for d in days:
            ds = d.strftime("%Y-%m-%d")
            reg = db["registros"].get(ds, {})
            c = "#ebedf0"
            if tema_atual == "Escuro": c = "#333333"
            
            if ds in db["registros"]:
                if metric == "nota":
                    n = reg.get("nota", 0)
                    c = "#216e39" if n >= 8 else "#f9d71c" if n >= 5 else "#f44336"
                elif metric in LINGUAGENS_LISTA:
                    c = color if metric in reg.get("ling_eu", []) or metric in reg.get("ling_ela", []) else c
                else: c = color if reg.get(metric) else c
            grid += f'<div title="{ds}" style="width: 10px; height: 10px; background-color: {c}; border-radius: 2px;"></div>'
        st.markdown(grid + '</div>', unsafe_allow_html=True)

    draw_grid("Frequência Sexual", "sexo", "#e91e63")
    draw_grid("Discussões", "discussao", "#f44336")

# --- 2. REGISTRAR DIA ---
elif menu == "Registrar Dia":
    with st.container(border=True):
        st.markdown("## 📝 Registrar Dia")
        
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

# --- 3. METAS E ACORDOS ---
elif menu == "Metas & Acordos":
    with st.container(border=True):
        st.markdown("### 🎯 Metas da Semana")
        hoje = date.today()
        inicio_sem = hoje - timedelta(days=hoje.weekday())
        reg_semana = [db["registros"].get((inicio_sem + timedelta(days=i)).strftime("%Y-%m-%d"), {}) for i in range(7)]
        
        c_elogios = sum(1 for r in reg_semana if "Elogio" in str(r.get("eu_fiz", [])))
        st.write(f"**Elogios** ({c_elogios}/{db['metas']['elogios']})")
        st.progress(min(c_elogios/db['metas']['elogios'], 1.0))

    with st.container(border=True):
        st.markdown("### 🤝 Acordos Ativos")
        for ac in db["acordos_mestres"]:
            status = "🟢" if ac.get('monitorar') else "⚪"
            st.markdown(f"**{status} {ac['titulo']}**")
        
        with st.expander("Adicionar Acordo"):
            with st.form("novo_acordo"):
                t = st.text_input("Acordo")
                if st.form_submit_button("Salvar"):
                    db["acordos_mestres"].append({"titulo": t, "nome_curto": t[:10], "monitorar": True, "data": str(date.today())})
                    save_all(db); st.rerun()

# --- 4. CÁPSULA (PDF) ---
elif menu == "Cápsula":
    with st.container(border=True):
        st.markdown("## 📥 Exportar PDF")
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

# --- 5. CONFIGURAÇÕES ---
elif menu == "Configurações":
    st.markdown("## ⚙️ Configurações")
    
    with st.container(border=True):
        st.markdown("### 🎨 Aparência")
        novo_tema = st.radio("Tema do App:", ["Claro", "Escuro"], index=0 if tema_atual == "Claro" else 1, horizontal=True)
        if novo_tema != tema_atual:
            db["config"]["tema"] = novo_tema
            save_all(db)
            st.rerun()
    
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("### 'Eu Fiz' (Jhonata)")
            new_eu = st.text_input("Novo:", key="new_eu")
            if st.button("Adicionar (Eu)"):
                if new_eu and new_eu not in db["configuracoes"]["opcoes_eu_fiz"]:
                    db["configuracoes"]["opcoes_eu_fiz"].append(new_eu)
                    save_all(db); st.rerun()
            st.divider()
            opts_eu = db["configuracoes"]["opcoes_eu_fiz"]
            if opts_eu:
                sel_eu = st.selectbox("Editar item:", opts_eu, key="sel_eu")
                rename_eu = st.text_input("Renomear para:", value=sel_eu, key="ren_eu")
                ce1, ce2 = st.columns(2)
                if ce1.button("Salvar Nome", key="sn_eu"):
                    idx = opts_eu.index(sel_eu)
                    db["configuracoes"]["opcoes_eu_fiz"][idx] = rename_eu
                    save_all(db); st.rerun()
                if ce2.button("Excluir", key="del_eu"):
                    db["configuracoes"]["opcoes_eu_fiz"].remove(sel_eu)
                    save_all(db); st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown("### 'Ela Fez' (Katheryn)")
            new_ela = st.text_input("Novo:", key="new_ela")
            if st.button("Adicionar (Ela)"):
                if new_ela and new_ela not in db["configuracoes"]["opcoes_ela_fez"]:
                    db["configuracoes"]["opcoes_ela_fez"].append(new_ela)
                    save_all(db); st.rerun()
            st.divider()
            opts_ela = db["configuracoes"]["opcoes_ela_fez"]
            if opts_ela:
                sel_ela = st.selectbox("Editar item:", opts_ela, key="sel_ela")
                rename_ela = st.text_input("Renomear para:", value=sel_ela, key="ren_ela")
                ce3, ce4 = st.columns(2)
                if ce3.button("Salvar Nome", key="sn_ela"):
                    idx = opts_ela.index(sel_ela)
                    db["configuracoes"]["opcoes_ela_fez"][idx] = rename_ela
                    save_all(db); st.rerun()
                if ce4.button("Excluir", key="del_ela"):
                    db["configuracoes"]["opcoes_ela_fez"].remove(sel_ela)
                    save_all(db); st.rerun()

# --- 6. INSIGHTS IA ---
elif menu == "Insights IA":
    st.header("💡 Mentor de Relacionamento")
    
    with st.container(border=True):
        st.subheader("1. Defina o Período")
        periodo = st.select_slider("Quanto tempo analisar?", options=["7 Dias", "15 Dias", "30 Dias", "Tudo"])
        
        dias_map = {"7 Dias": 7, "15 Dias": 15, "30 Dias": 30, "Tudo": 365}
        dias = dias_map[periodo]
        
        # Filtrar dados pelo periodo
        registros_filtrados = list(db["registros"].items())[-dias:]
        if not registros_filtrados:
            st.warning("Sem dados suficientes para este período.")
        
        st.divider()
        st.subheader("2. Escolha o Tipo de Consultoria")
        
        c_ia1, c_ia2 = st.columns(2)
        prompt_prefix = ""
        executar = False
        
        if c_ia1.button("📊 Análise Geral"):
            prompt_prefix = "Aja como um terapeuta de casais. Faça um resumo analítico sobre como foi o relacionamento neste período. Aponte pontos altos e baixos."
            executar = True
            
        if c_ia2.button("⚖️ Coach de Conflitos"):
            conflitos = [r for d, r in registros_filtrados if r.get('discussao')]
            registros_filtrados = [(d, r) for d, r in registros_filtrados if r.get('discussao')]
            prompt_prefix = "Analise apenas os conflitos e discussões que ocorreram. Identifique padrões (ex: financeiro, ciúmes) e sugira uma solução prática."
            executar = True
            if not conflitos:
                st.success("Nenhum conflito registrado neste período! 🎉")
                executar = False

        c_ia3, c_ia4 = st.columns(2)
        if c_ia3.button("💘 Guru Romântico"):
            prompt_prefix = "Sugira 3 ideias criativas de encontros ou gestos para a próxima semana."
            executar = True
        if c_ia4.button("🔮 Previsão de Tendência"):
            prompt_prefix = "Analise a tendência das notas e do humor. O relacionamento está em ascensão ou declínio?"
            executar = True

        if executar and registros_filtrados:
            ctx = str(registros_filtrados)
            if len(ctx) > 15000: ctx = ctx[-15000:]
            try:
                with st.spinner("Consultando o Mentor IA..."):
                    prompt_final = f"{prompt_prefix} Dados do Casal (Jhonata e Katheryn): {ctx}"
                    resp = client_groq.chat.completions.create(
                        model=db["config"]["modelo_ia"], 
                        messages=[{"role":"user","content":prompt_final}],
                        temperature=0.7
                    )
                    st.success(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"Erro na IA: {e}")
