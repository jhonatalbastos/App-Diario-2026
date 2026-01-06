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
        # Garantir integridade dos dados
        if "xp" not in data: data["xp"] = 0
        if "config" not in data: data["config"] = {}
        
        # Defaults Config
        defaults = {
            "modelo_ia": "llama-3.3-70b-versatile",
            "tema": "Claro (Padrão)",
            "home_page": "Dashboard",
            "data_inicio": "2026-01-01" # Para cálculo de dias juntos
        }
        for k, v in defaults.items():
            if k not in data["config"]: data["config"][k] = v

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
                "data_inicio": "2026-01-01"
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

# --- SISTEMA DE TEMAS ---
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
if tema_selecionado not in TEMAS: tema_selecionado = "Claro (Padrão)"
paleta = TEMAS[tema_selecionado]

# --- ESTILIZAÇÃO CSS DINÂMICA ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    /* Import Material Symbols para Ícones */
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

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

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: var(--bg-sidebar);
        border-right: none;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }}
    [data-testid="stSidebar"] * {{ color: var(--text-main) !important; }}

    /* Cards */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 24px;
        box-shadow: var(--shadow-soft);
        padding: 24px;
    }}
    
    /* Botões */
    div.stButton > button {{
        background-color: var(--primary);
        color: white !important;
        border-radius: 16px;
        border: none;
        padding: 14px 28px;
        font-weight: 700;
        width: 100%;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: all 0.2s;
    }}
    div.stButton > button:hover {{
        filter: brightness(110%);
        transform: translateY(-2px);
    }}
    
    /* Inputs */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea, .stDateInput input, .stNumberInput input {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid transparent;
        border-radius: 16px;
        padding: 12px 16px;
    }}
    
    /* Headers */
    h1, h2, h3, h4, p, span, div, label {{ color: var(--text-main) !important; }}
    
    /* Ícones Material Symbols (Classe Auxiliar) */
    .material-icons {{
        font-family: 'Material Symbols Outlined';
        font-weight: normal;
        font-style: normal;
        font-size: 24px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
    }}
    
    /* Card XP */
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
    .xp-card * {{ color: white !important; }}
    
    /* Badge de Conquista */
    .achievement-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        margin-right: 16px;
    }}
</style>
""", unsafe_allow_html=True)

# --- DADOS CONSTANTES ---
LINGUAGENS_LISTA = ["Atos de Serviço", "Palavras de Afirmação", "Tempo de Qualidade", "Toque Físico", "Presentes"]
CATEGORIAS_DR = ["Comunicação", "Finanças", "Ciúmes", "Família", "Rotina", "Outros"]

# --- LÓGICA DE GAMIFICAÇÃO ---
def calcular_gamificacao(db):
    xp = db["xp"]
    nivel = int((xp / 100) ** 0.5) + 1
    xp_prox_nivel = ((nivel) ** 2) * 100
    xp_atual_nivel = xp - (((nivel - 1) ** 2) * 100)
    xp_necessario_nivel = xp_prox_nivel - (((nivel - 1) ** 2) * 100)
    progresso = min(max(xp_atual_nivel / xp_necessario_nivel, 0), 1)
    
    # Dias Juntos
    try:
        d_inicio = datetime.strptime(db["config"].get("data_inicio", "2026-01-01"), "%Y-%m-%d").date()
        dias_juntos = (date.today() - d_inicio).days
    except:
        dias_juntos = 0
        
    return nivel, xp, xp_prox_nivel, progresso, dias_juntos

# --- LISTA DE CONQUISTAS (LÓGICA) ---
def verificar_conquistas(db):
    registros = db["registros"]
    total_logs = len(registros)
    
    # Lógica simples de "Streak" (Dias seguidos)
    datas_sorted = sorted([datetime.strptime(k, "%Y-%m-%d") for k in registros.keys()])
    streak = 0
    if datas_sorted:
        streak = 1
        for i in range(len(datas_sorted)-1, 0, -1):
            if (datas_sorted[i] - datas_sorted[i-1]).days == 1:
                streak += 1
            else:
                break
    
    conquistas = [
        {
            "titulo": "Primeiros Passos",
            "desc": "Faça seu primeiro registro no diário.",
            "icon": "edit_note",
            "done": total_logs >= 1,
            "progress": f"{min(total_logs, 1)}/1",
            "color": "bg-blue-500"
        },
        {
            "titulo": "Hábito de Amor",
            "desc": "Complete 10 registros no total.",
            "icon": "favorite",
            "done": total_logs >= 10,
            "progress": f"{min(total_logs, 10)}/10",
            "color": "bg-red-500"
        },
        {
            "titulo": "Constância",
            "desc": "Mantenha uma sequência de 7 dias.",
            "icon": "local_fire_department",
            "done": streak >= 7,
            "progress": f"{min(streak, 7)}/7",
            "color": "bg-orange-500"
        },
        {
            "titulo": "Mês Perfeito",
            "desc": "Registre 30 dias no total.",
            "icon": "calendar_month",
            "done": total_logs >= 30,
            "progress": f"{min(total_logs, 30)}/30",
            "color": "bg-purple-500"
        },
        {
            "titulo": "Mestre da Gratidão",
            "desc": "Escreva 50 motivos de gratidão.",
            "icon": "hotel_class",
            "done": sum(1 for r in registros.values() if r.get('gratidao')) >= 50,
            "progress": f"{sum(1 for r in registros.values() if r.get('gratidao'))}/50",
            "color": "bg-yellow-500"
        }
    ]
    return conquistas

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
MENU_OPTIONS = ["Dashboard", "Registrar Dia", "Metas & Acordos", "🏆 Conquistas", "Cápsula", "Insights IA", "Configurações"]
home_preferida = db["config"].get("home_page", "Dashboard")
try: default_idx = MENU_OPTIONS.index(home_preferida)
except: default_idx = 0

st.sidebar.markdown("### ❤️ Menu")
menu = st.sidebar.radio("", MENU_OPTIONS, index=default_idx)

# --- DADOS GLOBAIS DE GAMIFICAÇÃO ---
nivel, xp_total, xp_prox, progresso_nivel, dias_juntos = calcular_gamificacao(db)

# --- HEADER XP (DASHBOARD) ---
if menu == "Dashboard":
    st.markdown(f"""
    <div class="xp-card">
        <div style="position: relative; z-index: 10;">
            <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9; margin-bottom: 5px;">Nível de Conexão</div>
            <div style="font-size: 3.5rem; font-weight: 800; line-height: 1; margin-bottom: 10px;">{nivel}</div>
            <div style="background: rgba(0,0,0,0.2); height: 8px; border-radius: 4px; overflow: hidden; margin-top: 15px;">
                <div style="background: white; width: {progresso_nivel*100}%; height: 100%; border-radius: 4px;"></div>
            </div>
            <div style="font-size: 0.8rem; margin-top: 8px; opacity: 0.9; font-weight: 600;">{xp_total} / {xp_prox} XP</div>
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

                resumo = st.text_area("Diário de Bordo:", day_data.get("resumo", ""), height=100)
                gratidao = st.text_input("Gratidão do dia:", day_data.get("gratidao", ""))

                if st.form_submit_button("Salvar Registro"):
                    xp_ganho = 0
                    if date_str not in db["registros"]: xp_ganho = 20
                    if gratidao: xp_ganho += 5
                    db["xp"] += xp_ganho
                    db["registros"][date_str] = {
                        "nota": nota, "gratidao": gratidao, "eu_fiz": eu_fiz, "ela_fez": ela_fez,
                        "ling_eu": ling_eu, "ling_ela": ling_ela,
                        "discussao": disc, "cat_dr": cat_dr, "sexo": sexo == "Sim", 
                        "resumo": resumo, "locked": True
                    }
                    save_all(db)
                    st.balloons() # Celebração nativa do Streamlit
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

# --- 4. CONQUISTAS (NOVO - FASE 2) ---
elif menu == "🏆 Conquistas":
    # Header Stats (Visualização de Cards)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="background-color: {paleta['bg_card']}; border: 1px solid {paleta['border']}; border-radius: 24px; padding: 20px; text-align: center; box-shadow: {paleta['shadow']};">
            <span class="material-icons" style="color: {paleta['primary']}; font-size: 32px; display: block; margin: 0 auto 10px;">calendar_today</span>
            <div style="font-size: 2rem; font-weight: 800; line-height: 1;">{dias_juntos}</div>
            <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: {paleta['text_muted']}; margin-top: 5px;">Dias Juntos</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div style="background-color: {paleta['bg_card']}; border: 1px solid {paleta['border']}; border-radius: 24px; padding: 20px; text-align: center; box-shadow: {paleta['shadow']};">
            <span class="material-icons" style="color: {paleta['primary']}; font-size: 32px; display: block; margin: 0 auto 10px;">favorite</span>
            <div style="font-size: 2rem; font-weight: 800; line-height: 1;">Lvl {nivel}</div>
            <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: {paleta['text_muted']}; margin-top: 5px;">Nível do Casal</div>
        </div>
        """, unsafe_allow_html=True)

    # Nível de Progresso
    st.write("")
    with st.container(border=True):
        st.markdown(f"**Progresso do Nível {nivel}**")
        st.progress(progresso_nivel)
        st.caption(f"Faltam {int(xp_prox - xp_total)} XP para o próximo nível!")

    st.write("")
    st.markdown("### Suas Conquistas")
    
    # Renderizar lista de conquistas
    lista_conquistas = verificar_conquistas(db)
    
    for c in lista_conquistas:
        # Definir cores dinamicamente baseado no status
        bg_icon = f"background-color: {paleta['primary']}20;" if c['done'] else "background-color: #e5e7eb;"
        color_icon = f"color: {paleta['primary']};" if c['done'] else "color: #9ca3af;"
        opacity = "opacity: 1;" if c['done'] else "opacity: 0.6;"
        status_text = "DESBLOQUEADO" if c['done'] else "BLOQUEADO"
        status_bg = paleta['primary'] if c['done'] else "#9ca3af"
        
        st.markdown(f"""
        <div style="background-color: {paleta['bg_card']}; border: 1px solid {paleta['border']}; border-radius: 20px; padding: 16px; margin-bottom: 12px; display: flex; align-items: center; box-shadow: {paleta['shadow']}; {opacity}">
            <div class="achievement-badge" style="{bg_icon} {color_icon}">
                <span class="material-icons" style="font-size: 24px;">{c['icon']}</span>
            </div>
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="font-weight: 800; font-size: 1rem; margin-bottom: 4px;">{c['titulo']}</div>
                    <div style="background-color: {status_bg}20; color: {status_bg}; font-size: 0.65rem; padding: 2px 8px; border-radius: 10px; font-weight: 700;">{status_text}</div>
                </div>
                <div style="font-size: 0.85rem; color: {paleta['text_muted']}; margin-bottom: 8px;">{c['desc']}</div>
                <div style="width: 100%; background-color: #f3f4f6; height: 6px; border-radius: 3px; overflow: hidden;">
                    <div style="width: {min(eval(c['progress'])*100, 100)}%; background-color: {status_bg}; height: 100%;"></div>
                </div>
                <div style="font-size: 0.7rem; text-align: right; margin-top: 4px; font-weight: 600;">{c['progress']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 5. CÁPSULA (PDF) ---
elif menu == "Cápsula":
    with st.container(border=True):
        st.markdown("## 📥 Exportar PDF")
        c1, c2 = st.columns(2)
        with c1:
            mes_sel = st.selectbox("Mês:", ["01","02","03","04","05","06","07","08","09","10","11","12"])
            up_img = st.file_uploader("Capa:", type=["png","jpg"])
        with c2:
            st.write(""); st.write("")
            if st.button("Gerar PDF"):
                dados = {k: v for k, v in db["registros"].items() if k.split("-")[1] == mes_sel}
                if dados:
                    pdf = gerar_pdf(dados, mes_sel, up_img.read() if up_img else None)
                    st.download_button("Baixar", pdf, "Planner.pdf", "application/pdf")
                else: st.warning("Sem dados.")

# --- 6. INSIGHTS IA ---
elif menu == "Insights IA":
    st.header("💡 Mentor IA")
    with st.container(border=True):
        periodo = st.select_slider("Período:", ["7 Dias", "15 Dias", "30 Dias", "Tudo"])
        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("📊 Análise Geral"):
            # Exemplo de chamada simplificada
            st.info("Funcionalidade conectada à API Groq (Simulada aqui se não houver chave).")

# --- 7. CONFIGURAÇÕES ---
elif menu == "Configurações":
    st.markdown("## ⚙️ Configurações")
    with st.container(border=True):
        novo_tema = st.selectbox("Tema:", list(TEMAS.keys()), index=list(TEMAS.keys()).index(tema_selecionado))
        nova_home = st.selectbox("Tela Inicial:", MENU_OPTIONS, index=MENU_OPTIONS.index(home_preferida))
        data_inicio = st.date_input("Início do Namoro:", datetime.strptime(db["config"].get("data_inicio", "2026-01-01"), "%Y-%m-%d"))
        
        if st.button("Salvar Tudo"):
            db["config"]["tema"] = novo_tema
            db["config"]["home_page"] = nova_home
            db["config"]["data_inicio"] = str(data_inicio)
            save_all(db); st.rerun()
