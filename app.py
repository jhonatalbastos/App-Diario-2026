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
        if "config" not in data: data["config"] = {}
        
        # Defaults Config
        if "modelo_ia" not in data["config"]: data["config"]["modelo_ia"] = "llama-3.3-70b-versatile"
        if "tema" not in data["config"]: data["config"]["tema"] = "Claro (Padrão)"
        if "home_page" not in data["config"]: data["config"]["home_page"] = "Dashboard"

        if "acordos_mestres" not in data: data["acordos_mestres"] = []
        if "metas" not in data: data["metas"] = {"elogios": 3, "qualidade": 2}
        if "configuracoes" not in data:
             data["configuracoes"] = {"opcoes_eu_fiz": ["Elogio", "Tempo de Qualidade"], "opcoes_ela_fez": ["Carinho"]}
        return data
    except:
        return {
            "registros": {}, "eventos": {}, "acordos_mestres": [], "xp": 0,
            "metas": {"elogios": 3, "qualidade": 2},
            "configuracoes": {"opcoes_eu_fiz": ["Elogio"], "opcoes_ela_fez": ["Carinho"]},
            "config": {
                "modelo_ia": "llama-3.3-70b-versatile", 
                "tema": "Claro (Padrão)",
                "home_page": "Dashboard"
            }
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

# --- SISTEMA DE TEMAS (ATUALIZADO COM CORES DO DESIGN HTML) ---
# Extraído dos arquivos HTML/Tailwind enviados
TEMAS = {
    "Claro (Padrão)": {
        "primary": "#f42536",       # Vermelho Love Planner
        "primary_soft": "#ffe5e7",  # Rosa Suave
        "bg_app": "#fcf8f8",        # Off-white quente (background-light)
        "bg_sidebar": "#ffffff",    # Sidebar branca limpa
        "bg_card": "#ffffff",       # Cartão branco
        "text_main": "#1c0d0e",     # Texto quase preto (warm)
        "text_muted": "#9c4950",    # Texto secundário avermelhado
        "border": "transparent",    # Sem bordas duras (shadow only)
        "input_bg": "#f8f5f6",      # Input levemente cinza/rosa
        "shadow": "0 4px 20px -2px rgba(244, 37, 54, 0.08)" # Shadow Soft
    },
    "Escuro (Padrão)": {
        "primary": "#f42536",
        "primary_soft": "#3f1d20",
        "bg_app": "#221011",        # Dark Chocolate (background-dark)
        "bg_sidebar": "#2f1b1c",    # Sidebar Dark
        "bg_card": "#2d1517",       # Card Dark (surface-dark)
        "text_main": "#fcf8f8",     # Texto claro
        "text_muted": "#dcb8bb",    # Texto secundário claro
        "border": "#4a2326",        # Borda sutil avermelhada
        "input_bg": "#361b1d",      # Input dark
        "shadow": "0 4px 20px -2px rgba(0, 0, 0, 0.3)"
    },
    # Mantendo os outros temas como variações harmônicas
    "Romântico (Rosa)": {
        "primary": "#db2777", "primary_soft": "#fce7f3", "bg_app": "#fff1f2", "bg_sidebar": "#ffffff", 
        "bg_card": "#ffffff", "text_main": "#831843", "text_muted": "#be185d", "border": "transparent", "input_bg": "#fff0f5",
        "shadow": "0 4px 20px -2px rgba(219, 39, 119, 0.1)"
    },
    "Oceano (Azul)": {
        "primary": "#0284c7", "primary_soft": "#e0f2fe", "bg_app": "#f0f9ff", "bg_sidebar": "#ffffff", 
        "bg_card": "#ffffff", "text_main": "#0c4a6e", "text_muted": "#0369a1", "border": "transparent", "input_bg": "#f0f9ff",
        "shadow": "0 4px 20px -2px rgba(2, 132, 199, 0.1)"
    },
    "Natureza (Verde)": {
        "primary": "#16a34a", "primary_soft": "#dcfce7", "bg_app": "#f0fdf4", "bg_sidebar": "#ffffff", 
        "bg_card": "#ffffff", "text_main": "#14532d", "text_muted": "#15803d", "border": "transparent", "input_bg": "#f0fdf4",
        "shadow": "0 4px 20px -2px rgba(22, 163, 74, 0.1)"
    },
    "Noturno (Roxo)": {
        "primary": "#a855f7", "primary_soft": "#312e81", "bg_app": "#1e1b4b", "bg_sidebar": "#312e81", 
        "bg_card": "#2e1065", "text_main": "#e9d5ff", "text_muted": "#c084fc", "border": "#4c1d95", "input_bg": "#1e1b4b",
        "shadow": "0 4px 20px -2px rgba(0, 0, 0, 0.3)"
    }
}

tema_selecionado = db["config"].get("tema", "Claro (Padrão)")
if tema_selecionado not in TEMAS: tema_selecionado = "Claro (Padrão)" # Fallback
paleta = TEMAS[tema_selecionado]

# --- ESTILIZAÇÃO CSS DINÂMICA (BASEADA NO DESIGN DO STITCH) ---
st.markdown(f"""
<style>
    /* Fonte Oficial do Design */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    :root {{
        --primary: {paleta['primary']};
        --primary-soft: {paleta['primary_soft']};
        --bg-app: {paleta['bg_app']};
        --bg-sidebar: {paleta['bg_sidebar']};
        --bg-card: {paleta['bg_card']};
        --text-main: {paleta['text_main']};
        --text-muted: {paleta['text_muted']};
        --border-color: {paleta['border']};
        --input-bg: {paleta['input_bg']};
        --shadow-soft: {paleta['shadow']};
    }}

    /* Reset Global */
    html, body, [class*="css"], .stApp {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: var(--bg-app);
        color: var(--text-main);
    }}

    /* Sidebar Estilizada */
    [data-testid="stSidebar"] {{
        background-color: var(--bg-sidebar);
        border-right: none;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }}
    [data-testid="stSidebar"] * {{
        color: var(--text-main) !important;
    }}

    /* Cards (Containers Nativos Transformados) */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 24px; /* Arredondamento maior do design */
        box-shadow: var(--shadow-soft);
        padding: 24px;
        transition: transform 0.2s ease;
    }}
    
    /* Botões (Pill Shape) */
    div.stButton > button {{
        background-color: var(--primary);
        color: white !important;
        border-radius: 16px; /* Pill shape */
        border: none;
        padding: 14px 28px;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.02em;
        width: 100%;
        box-shadow: 0 4px 12px rgba(244, 37, 54, 0.2); /* Glow sutil */
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    div.stButton > button:hover {{
        filter: brightness(110%);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(244, 37, 54, 0.3);
    }}
    
    /* Inputs Modernos */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea, .stDateInput input, .stNumberInput input {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid transparent;
        border-radius: 16px;
        padding: 12px 16px;
        transition: all 0.2s;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: var(--primary);
        box-shadow: 0 0 0 2px var(--primary-soft);
    }}
    
    /* Headers e Textos */
    h1, h2, h3, h4 {{ 
        color: var(--text-main) !important; 
        font-weight: 800 !important; 
        letter-spacing: -0.02em;
    }}
    p, label, span, div {{ 
        color: var(--text-main); 
    }}
    .stMarkdown p {{ color: var(--text-main) !important; }}
    
    /* Sliders */
    .stSlider [data-baseweb="slider"] {{
        --thumb-color: var(--primary);
        --track-color: var(--primary-soft);
    }}

    /* Card de XP (Gamificação 2.0) */
    .xp-card {{
        background: linear-gradient(135deg, var(--primary) 0%, #ff5c6a 100%);
        color: white !important;
        border-radius: 24px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 10px 30px -10px var(--primary);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }}
    .xp-card::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 60%);
        opacity: 0.5;
    }}
    
    .streamlit-expanderHeader {{
        background-color: var(--input-bg);
        border-radius: 12px;
        color: var(--text-main) !important;
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
    pdf.set_text_color(244, 37, 54) # Vermelho primário
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

# --- NAVEGAÇÃO COM TELA INICIAL DEFINIDA ---
MENU_OPTIONS = ["Dashboard", "Registrar Dia", "Metas & Acordos", "Cápsula", "Insights IA", "Configurações"]
home_preferida = db["config"].get("home_page", "Dashboard")

# Tenta encontrar o índice da página preferida, senão 0
try:
    default_idx = MENU_OPTIONS.index(home_preferida)
except:
    default_idx = 0

st.sidebar.markdown("### ❤️ Menu")
menu = st.sidebar.radio("", MENU_OPTIONS, index=default_idx)

# --- HEADER XP ---
nivel, meta_xp = get_nivel_info(db["xp"])
if menu == "Dashboard":
    # HTML Puro para o Card de XP (Design System)
    st.markdown(f"""
    <div class="xp-card">
        <div style="position: relative; z-index: 10;">
            <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9; margin-bottom: 5px;">Nível de Conexão</div>
            <div style="font-size: 3.5rem; font-weight: 800; line-height: 1; margin-bottom: 10px;">{nivel}</div>
            <div style="background: rgba(0,0,0,0.2); height: 8px; border-radius: 4px; overflow: hidden; margin-top: 15px;">
                <div style="background: white; width: {(db['xp']/meta_xp)*100}%; height: 100%; border-radius: 4px;"></div>
            </div>
            <div style="font-size: 0.8rem; margin-top: 8px; opacity: 0.9; font-weight: 600;">{db['xp']} / {meta_xp} XP para o próximo nível</div>
        </div>
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
                interpolate='monotone', color=paleta['primary'], strokeWidth=4
            ).encode(
                x=alt.X('Data', axis=alt.Axis(format='%d/%m', labelColor=paleta['text_muted'])),
                y=alt.Y('Nota', scale=alt.Scale(domain=[0, 10]), axis=alt.Axis(labelColor=paleta['text_muted'])),
                tooltip=['Data', 'Nota']
            ).properties(height=220).configure_view(strokeWidth=0) # Remove borda do gráfico
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Registre seu primeiro dia!")

    st.markdown("### 🔥 Mapas de Calor")
    def draw_grid(title, metric, color):
        st.caption(title)
        days = pd.date_range("2026-01-01", "2026-12-31")
        grid = '<div style="display: flex; flex-wrap: wrap; gap: 4px; max-width: 800px; margin-bottom: 24px;">'
        for d in days:
            ds = d.strftime("%Y-%m-%d")
            reg = db["registros"].get(ds, {})
            # Cores baseadas no tema (mais sutil para vazio)
            c = "#e2e8f0" if "Claro" in tema_selecionado else "#333333"
            
            if ds in db["registros"]:
                if metric == "nota":
                    n = reg.get("nota", 0)
                    c = "#22c55e" if n >= 8 else "#eab308" if n >= 5 else "#ef4444"
                elif metric in LINGUAGENS_LISTA:
                    c = color if metric in reg.get("ling_eu", []) or metric in reg.get("ling_ela", []) else c
                else: c = color if reg.get(metric) else c
            # Quadrados arredondados (Rounded-sm do Tailwind)
            grid += f'<div title="{ds}" style="width: 12px; height: 12px; background-color: {c}; border-radius: 4px;"></div>'
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
        novo_tema = st.radio("Tema do App:", ["Claro (Padrão)", "Escuro (Padrão)", "Romântico (Rosa)", "Oceano (Azul)", "Natureza (Verde)", "Noturno (Roxo)"], index=list(TEMAS.keys()).index(tema_selecionado))
        
        nova_home = st.selectbox("Tela Inicial Padrão:", MENU_OPTIONS, index=MENU_OPTIONS.index(home_preferida))
        
        if st.button("Salvar Preferências"):
            db["config"]["tema"] = novo_tema
            db["config"]["home_page"] = nova_home
            save_all(db)
            st.success("Salvo! Recarregue a página.")
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
                sel_eu = st.selectbox("Editar:", opts_eu, key="sel_eu")
                rename_eu = st.text_input("Renomear para:", value=sel_eu, key="ren_eu")
                ce1, ce2 = st.columns(2)
                if ce1.button("Salvar", key="sn_eu"):
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
                sel_ela = st.selectbox("Editar:", opts_ela, key="sel_ela")
                rename_ela = st.text_input("Renomear para:", value=sel_ela, key="ren_ela")
                ce3, ce4 = st.columns(2)
                if ce3.button("Salvar", key="sn_ela"):
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
        
        registros_filtrados = list(db["registros"].items())[-dias_map[periodo]:]
        if not registros_filtrados: st.warning("Sem dados suficientes.")
        
        st.divider()
        st.subheader("2. Escolha o Tipo de Consultoria")
        
        c_ia1, c_ia2 = st.columns(2)
        prompt = ""
        executar = False
        
        if c_ia1.button("📊 Análise Geral"):
            prompt = "Aja como um terapeuta. Resuma o relacionamento neste período. Pontos altos e baixos."
            executar = True
        if c_ia2.button("⚖️ Coach de Conflitos"):
            regs_conf = [(d,r) for d,r in registros_filtrados if r.get('discussao')]
            prompt = "Analise apenas conflitos. Identifique padrões e dê soluções."
            registros_filtrados = regs_conf
            executar = True
            if not regs_conf: st.success("Sem conflitos! 🎉"); executar = False

        c_ia3, c_ia4 = st.columns(2)
        if c_ia3.button("💘 Guru Romântico"):
            prompt = "Sugira 3 ideias criativas de encontros baseadas no perfil do casal."
            executar = True
        if c_ia4.button("🔮 Tendências"):
            prompt = "Analise matematicamente a tendência das notas. Ascensão ou declínio?"
            executar = True

        if executar and registros_filtrados:
            ctx = str(registros_filtrados)
            if len(ctx) > 15000: ctx = ctx[-15000:]
            try:
                with st.spinner("Analisando..."):
                    resp = client_groq.chat.completions.create(
                        model=db["config"]["modelo_ia"], 
                        messages=[{"role":"user","content":f"{prompt} Dados: {ctx}"}],
                        temperature=0.7
                    )
                    st.success(resp.choices[0].message.content)
            except Exception as e: st.error(f"Erro: {e}")
