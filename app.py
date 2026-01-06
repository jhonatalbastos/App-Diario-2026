import streamlit as st
import pandas as pd
import json
import io
import altair as alt
import time
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq
from fpdf import FPDF
from PIL import Image

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Love Planner 2026", layout="centered", page_icon="❤️")

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

# --- FUNÇÕES DE DADOS ---
def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        data = json.loads(contents.decoded_content.decode())
        if "xp" not in data: data["xp"] = 0
        if "config" not in data: data["config"] = {}
        
        # Defaults Config
        if "modelo_ia" not in data["config"]: data["config"]["modelo_ia"] = "llama-3.3-70b-versatile"
        if "tema" not in data["config"]: data["config"]["tema"] = "Claro (Padrão)"
        if "home_page" not in data["config"]: data["config"]["home_page"] = "Dashboard"
        if "data_inicio" not in data["config"]: data["config"]["data_inicio"] = "2020-01-01" # Default

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
                "home_page": "Dashboard",
                "data_inicio": "2020-01-01"
            }
        }

def save_all(data):
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents("data_2026.json")
        repo.update_file(contents.path, f"Sync {datetime.now()}", json_data, contents.sha)
    except:
        repo.create_file("data_2026.json", "DB Init", json_data)

db = load_data()

# --- LÓGICA DE GAMIFICAÇÃO ---
def get_nivel_info(xp):
    nivel = int((xp / 100) ** 0.5) + 1
    xp_atual_nivel = ((nivel - 1) ** 2) * 100
    xp_prox_nivel = ((nivel) ** 2) * 100
    progresso = (xp - xp_atual_nivel) / (xp_prox_nivel - xp_atual_nivel) if xp_prox_nivel > xp_atual_nivel else 0
    return nivel, xp_prox_nivel, progresso

# Modal de Celebração (Novo Streamlit Dialog)
@st.dialog("🎉 Level Up!")
def show_levelup_modal(nivel):
    st.markdown(f"""
    <div style="text-align: center;">
        <div style="font-size: 80px;">🏆</div>
        <h2>Parabéns!</h2>
        <p>Vocês alcançaram o <strong>Nível {nivel}</strong> de conexão!</p>
        <p>Continuem cultivando esse amor.</p>
    </div>
    """, unsafe_allow_html=True)
    st.balloons()

# Verificar Level Up
nivel_atual, _, _ = get_nivel_info(db["xp"])
if "last_level" not in st.session_state:
    st.session_state["last_level"] = nivel_atual

if nivel_atual > st.session_state["last_level"]:
    show_levelup_modal(nivel_atual)
    st.session_state["last_level"] = nivel_atual

# --- TEMAS ---
TEMAS = {
    "Claro (Padrão)": {
        "primary": "#f42536", "primary_soft": "#ffe5e7", "bg_app": "#fcf8f8", "bg_sidebar": "#ffffff", 
        "bg_card": "#ffffff", "text_main": "#1c0d0e", "text_muted": "#9c4950", "border": "transparent", "input_bg": "#f8f5f6",
        "shadow": "0 4px 20px -2px rgba(244, 37, 54, 0.08)"
    },
    "Escuro (Padrão)": {
        "primary": "#f42536", "primary_soft": "#3f1d20", "bg_app": "#221011", "bg_sidebar": "#2f1b1c", 
        "bg_card": "#2d1517", "text_main": "#fcf8f8", "text_muted": "#dcb8bb", "border": "#4a2326", "input_bg": "#361b1d",
        "shadow": "0 4px 20px -2px rgba(0, 0, 0, 0.3)"
    },
    "Romântico (Rosa)": {
        "primary": "#db2777", "primary_soft": "#fce7f3", "bg_app": "#fff1f2", "bg_sidebar": "#ffffff", "bg_card": "#ffffff", "text_main": "#831843", "text_muted": "#be185d", "border": "transparent", "input_bg": "#fff0f5", "shadow": "0 4px 20px -2px rgba(219, 39, 119, 0.1)"
    },
    "Oceano (Azul)": {
        "primary": "#0284c7", "primary_soft": "#e0f2fe", "bg_app": "#f0f9ff", "bg_sidebar": "#ffffff", "bg_card": "#ffffff", "text_main": "#0c4a6e", "text_muted": "#0369a1", "border": "transparent", "input_bg": "#f0f9ff", "shadow": "0 4px 20px -2px rgba(2, 132, 199, 0.1)"
    },
    "Natureza (Verde)": {
        "primary": "#16a34a", "primary_soft": "#dcfce7", "bg_app": "#f0fdf4", "bg_sidebar": "#ffffff", "bg_card": "#ffffff", "text_main": "#14532d", "text_muted": "#15803d", "border": "transparent", "input_bg": "#f0fdf4", "shadow": "0 4px 20px -2px rgba(22, 163, 74, 0.1)"
    },
    "Noturno (Roxo)": {
        "primary": "#a855f7", "primary_soft": "#312e81", "bg_app": "#1e1b4b", "bg_sidebar": "#312e81", "bg_card": "#2e1065", "text_main": "#e9d5ff", "text_muted": "#c084fc", "border": "#4c1d95", "input_bg": "#1e1b4b", "shadow": "0 4px 20px -2px rgba(0, 0, 0, 0.3)"
    }
}

tema_selecionado = db["config"].get("tema", "Claro (Padrão)")
if tema_selecionado not in TEMAS: tema_selecionado = "Claro (Padrão)"
paleta = TEMAS[tema_selecionado]

# --- CSS GLOBAL ---
st.markdown(f"""
<style>
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

    html, body, [class*="css"], .stApp {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: var(--bg-app);
        color: var(--text-main);
    }}

    [data-testid="stSidebar"] {{
        background-color: var(--bg-sidebar);
        border-right: none;
    }}
    [data-testid="stSidebar"] * {{ color: var(--text-main) !important; }}

    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 24px;
        box-shadow: var(--shadow-soft);
        padding: 24px;
    }}
    
    div.stButton > button {{
        background-color: var(--primary);
        color: white !important;
        border-radius: 16px;
        border: none;
        padding: 14px 28px;
        font-weight: 700;
        width: 100%;
        transition: all 0.2s;
    }}
    div.stButton > button:hover {{
        filter: brightness(110%);
        transform: translateY(-2px);
    }}
    
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea, .stDateInput input, .stNumberInput input {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid transparent;
        border-radius: 16px;
    }}
    
    h1, h2, h3, h4, p, label, span, div {{ color: var(--text-main); }}
    
    .achievement-card {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        padding: 16px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: var(--shadow-soft);
        margin-bottom: 12px;
        transition: transform 0.2s;
    }}
    .achievement-icon {{
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        flex-shrink: 0;
    }}
    .locked {{ filter: grayscale(100%); opacity: 0.6; }}
    
    .xp-card {{
        background: linear-gradient(135deg, var(--primary) 0%, #ff5c6a 100%);
        color: white !important;
        border-radius: 24px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 10px 30px -10px var(--primary);
        margin-bottom: 24px;
    }}
</style>
""", unsafe_allow_html=True)

# --- DADOS CONSTANTES ---
LINGUAGENS_LISTA = ["Atos de Serviço", "Palavras de Afirmação", "Tempo de Qualidade", "Toque Físico", "Presentes"]
CATEGORIAS_DR = ["Comunicação", "Finanças", "Ciúmes", "Família", "Rotina", "Outros"]

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
MENU_OPTIONS = ["Dashboard", "Registrar Dia", "Conquistas", "Metas & Acordos", "Cápsula", "Insights IA", "Configurações"]
home_preferida = db["config"].get("home_page", "Dashboard")
try: default_idx = MENU_OPTIONS.index(home_preferida)
except: default_idx = 0

st.sidebar.markdown("### ❤️ Menu")
menu = st.sidebar.radio("", MENU_OPTIONS, index=default_idx)

# --- HEADER XP (Visível em todas menos Conquistas que já tem o próprio) ---
nivel, meta_xp, progresso = get_nivel_info(db["xp"])
if menu == "Dashboard":
    st.markdown(f"""
    <div class="xp-card">
        <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">Nível de Conexão</div>
        <div style="font-size: 3.5rem; font-weight: 800; line-height: 1; margin: 10px 0;">{nivel}</div>
        <div style="background: rgba(0,0,0,0.2); height: 8px; border-radius: 4px; overflow: hidden;">
            <div style="background: white; width: {progresso*100}%; height: 100%;"></div>
        </div>
        <div style="font-size: 0.8rem; margin-top: 8px; opacity: 0.9;">{db['xp']} / {meta_xp} XP</div>
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
            ).properties(height=220).configure_view(strokeWidth=0)
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
            c = "#e2e8f0" if "Claro" in tema_selecionado else "#333333"
            if ds in db["registros"]:
                if metric == "nota":
                    n = reg.get("nota", 0)
                    c = "#22c55e" if n >= 8 else "#eab308" if n >= 5 else "#ef4444"
                elif metric in LINGUAGENS_LISTA:
                    c = color if metric in reg.get("ling_eu", []) or metric in reg.get("ling_ela", []) else c
                else: c = color if reg.get(metric) else c
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
                
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("JHONATA (EU)")
                    eu_fiz = st.multiselect("Eu fiz:", db["configuracoes"]["opcoes_eu_fiz"], day_data.get("eu_fiz", []))
                    ling_eu = st.multiselect("Linguagens:", LINGUAGENS_LISTA, day_data.get("ling_eu", []))
                    disc = st.checkbox("Teve DR?", day_data.get("discussao", False))
                    if disc: cat_dr = st.selectbox("Motivo:", CATEGORIAS_DR)
                    else: cat_dr = None
                with c2:
                    st.caption("KATHERYN (ELA)")
                    ela_fez = st.multiselect("Ela fez:", db["configuracoes"]["opcoes_ela_fez"], day_data.get("ela_fez", []))
                    ling_ela = st.multiselect("Linguagens:", LINGUAGENS_LISTA, day_data.get("ling_ela", []))
                    sexo = st.radio("Intimidade:", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, horizontal=True)

                with st.expander("WhatsApp"):
                    ws_raw = st.text_area("Cole conversa:")
                    if day_data.get("whatsapp_txt"): st.code(day_data["whatsapp_txt"][:100]+"...")

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

# --- 3. CONQUISTAS (NOVO: FASE 2) ---
elif menu == "Conquistas":
    st.markdown("## 🏆 Conquistas")
    
    # Cálculo de Dias Juntos
    data_inicio = datetime.strptime(db["config"].get("data_inicio", "2020-01-01"), "%Y-%m-%d").date()
    dias_juntos = (date.today() - data_inicio).days
    
    # Stats Grid
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div style="background: {paleta['bg_card']}; border: 1px solid {paleta['border']}; border-radius: 20px; padding: 20px; text-align: center; box-shadow: {paleta['shadow']};">
            <div style="font-size: 24px; margin-bottom: 5px;">📅</div>
            <div style="font-size: 32px; font-weight: 800; line-height: 1;">{dias_juntos}</div>
            <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7;">Dias Juntos</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background: {paleta['bg_card']}; border: 1px solid {paleta['border']}; border-radius: 20px; padding: 20px; text-align: center; box-shadow: {paleta['shadow']};">
            <div style="font-size: 24px; margin-bottom: 5px;">❤️</div>
            <div style="font-size: 32px; font-weight: 800; line-height: 1;">Lvl {nivel}</div>
            <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7;">Nível Casal</div>
        </div>
        """, unsafe_allow_html=True)

    # XP Progress Detail
    st.markdown("###") # Spacer
    st.markdown(f"""
    <div style="background: {paleta['bg_card']}; border: 1px solid {paleta['border']}; border-radius: 20px; padding: 20px; box-shadow: {paleta['shadow']};">
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-weight: bold;">
            <span>Progresso Próximo Nível</span>
            <span style="color: {paleta['primary']};">{int(progresso*100)}%</span>
        </div>
        <div style="background: #eee; height: 10px; border-radius: 5px; overflow: hidden;">
            <div style="background: {paleta['primary']}; width: {progresso*100}%; height: 100%; border-radius: 5px;"></div>
        </div>
        <div style="text-align: right; font-size: 12px; margin-top: 5px; opacity: 0.6;">{meta_xp - db['xp']} XP restantes</div>
    </div>
    """, unsafe_allow_html=True)

    # Lista de Conquistas (Lógica + Visual)
    st.markdown("### Galeria de Troféus")
    
    total_logs = len(db["registros"])
    total_gratidao = sum(1 for r in db["registros"].values() if r.get("gratidao"))
    
    conquistas = [
        {"titulo": "Primeiro Passo", "desc": "Fez o 1º registro", "icon": "🏁", "feito": total_logs >= 1},
        {"titulo": "Consistência", "desc": "10 Registros totais", "icon": "🔥", "feito": total_logs >= 10},
        {"titulo": "Diário de Bordo", "desc": "100 Registros totais", "icon": "📖", "feito": total_logs >= 100},
        {"titulo": "Coração Grato", "desc": "5 Gratidões registradas", "icon": "✨", "feito": total_gratidao >= 5},
        {"titulo": "Nível 5", "desc": "Alcançou o nível 5", "icon": "💎", "feito": nivel >= 5},
        {"titulo": "Nível 10", "desc": "Alcançou o nível 10", "icon": "👑", "feito": nivel >= 10},
    ]
    
    for c in conquistas:
        opacity = "1" if c['feito'] else "0.5"
        filter_gray = "none" if c['feito'] else "grayscale(100%)"
        bg_icon = f"{paleta['primary']}20" if c['feito'] else "#eee" # 20 is hex opacity
        status_text = "DESBLOQUEADO" if c['feito'] else "BLOQUEADO"
        color_status = paleta['primary'] if c['feito'] else "#999"
        
        st.markdown(f"""
        <div class="achievement-card" style="opacity: {opacity};">
            <div class="achievement-icon" style="background: {bg_icon}; filter: {filter_gray};">
                {c['icon']}
            </div>
            <div style="flex: 1;">
                <div style="font-weight: bold; font-size: 16px;">{c['titulo']}</div>
                <div style="font-size: 12px; opacity: 0.7;">{c['desc']}</div>
            </div>
            <div style="font-size: 10px; font-weight: bold; color: {color_status}; border: 1px solid {color_status}; padding: 2px 6px; border-radius: 10px;">
                {status_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 4. METAS E ACORDOS ---
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

# --- 5. CÁPSULA (PDF) ---
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

# --- 6. INSIGHTS IA ---
elif menu == "Insights IA":
    st.header("💡 Mentor de Relacionamento")
    with st.container(border=True):
        periodo = st.select_slider("Período:", options=["7 Dias", "15 Dias", "30 Dias", "Tudo"])
        dias_map = {"7 Dias": 7, "15 Dias": 15, "30 Dias": 30, "Tudo": 365}
        
        if st.button("✨ Gerar Análise"):
            regs = list(db["registros"].items())[-dias_map[periodo]:]
            if regs:
                try:
                    with st.spinner("Analisando..."):
                        resp = client_groq.chat.completions.create(
                            model=db["config"]["modelo_ia"], 
                            messages=[{"role":"user","content":f"Analise como terapeuta: {str(regs)}"}],
                            temperature=0.7
                        )
                        st.success(resp.choices[0].message.content)
                except Exception as e: st.error(f"Erro: {e}")
            else: st.warning("Sem dados.")

# --- 7. CONFIGURAÇÕES ---
elif menu == "Configurações":
    st.markdown("## ⚙️ Configurações")
    
    with st.container(border=True):
        st.markdown("### 🎨 Aparência & Dados")
        novo_tema = st.selectbox("Tema:", list(TEMAS.keys()), index=list(TEMAS.keys()).index(tema_selecionado))
        nova_home = st.selectbox("Tela Inicial:", MENU_OPTIONS, index=MENU_OPTIONS.index(home_preferida))
        data_ini = st.date_input("Início do Relacionamento:", datetime.strptime(db["config"].get("data_inicio", "2020-01-01"), "%Y-%m-%d"))
        
        if st.button("Salvar Preferências"):
            db["config"]["tema"] = novo_tema
            db["config"]["home_page"] = nova_home
            db["config"]["data_inicio"] = str(data_ini)
            save_all(db); st.success("Salvo!"); st.rerun()
    
    # Gerenciamento de Opções
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("### 'Eu Fiz'")
            new_eu = st.text_input("Novo:", key="new_eu")
            if st.button("Add Eu"):
                if new_eu: db["configuracoes"]["opcoes_eu_fiz"].append(new_eu); save_all(db); st.rerun()
            if db["configuracoes"]["opcoes_eu_fiz"]:
                sel = st.selectbox("Edit:", db["configuracoes"]["opcoes_eu_fiz"], key="s_eu")
                if st.button("Del Eu"): db["configuracoes"]["opcoes_eu_fiz"].remove(sel); save_all(db); st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown("### 'Ela Fez'")
            new_ela = st.text_input("Novo:", key="new_ela")
            if st.button("Add Ela"):
                if new_ela: db["configuracoes"]["opcoes_ela_fez"].append(new_ela); save_all(db); st.rerun()
            if db["configuracoes"]["opcoes_ela_fez"]:
                sel = st.selectbox("Edit:", db["configuracoes"]["opcoes_ela_fez"], key="s_ela")
                if st.button("Del Ela"): db["configuracoes"]["opcoes_ela_fez"].remove(sel); save_all(db); st.rerun()
