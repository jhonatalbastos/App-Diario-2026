import streamlit as st
import pandas as pd
import json
import io
import base64
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
        if "xp" not in data: data["xp"] = 0
        if "config" not in data: data["config"] = {}
        
        defaults = {
            "modelo_ia": "llama-3.3-70b-versatile",
            "tema": "Claro (Padrão)",
            "home_page": "Dashboard",
            "data_inicio": "2026-01-01",
            "nomes_casal": "Jhonata & Katheryn",
            "foto_perfil": None, 
            "notificacoes": True,
            "dicas_mentor": True,
            "biometria": False
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
                "data_inicio": "2026-01-01",
                "nomes_casal": "Jhonata & Katheryn"
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
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

    :root {{
        --primary: {paleta['primary']};
        --bg-app: {paleta['bg_app']};
        --bg-card: {paleta['bg_card']};
        --text-main: {paleta['text_main']};
        --text-muted: {paleta['text_muted']};
    }}

    html, body, [class*="css"], .stApp {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: var(--bg-app);
        color: var(--text-main);
    }}

    [data-testid="stSidebar"] {{
        background-color: {paleta['bg_sidebar']};
        border-right: none;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }}
    [data-testid="stSidebar"] * {{ color: var(--text-main) !important; }}

    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: var(--bg-card);
        border: 1px solid {paleta['border']};
        border-radius: 24px;
        box-shadow: {paleta['shadow']};
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
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: all 0.2s;
    }}
    
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea, .stDateInput input {{
        background-color: {paleta['input_bg']} !important;
        color: var(--text-main) !important;
        border-radius: 16px;
        border: 1px solid transparent;
    }}
    
    .profile-header {{
        display: flex; align-items: center; gap: 20px; padding-bottom: 20px;
        border-bottom: 1px solid {paleta['border']}; margin-bottom: 20px;
    }}
    .profile-pic-container {{
        width: 80px; height: 80px; border-radius: 50%; overflow: hidden;
        border: 3px solid var(--primary); display: flex;
        align-items: center; justify-content: center; background-color: {paleta['input_bg']};
    }}
    
    .memory-card {{
        border-radius: 24px; padding: 24px; color: white; position: relative;
        overflow: hidden; margin-bottom: 16px; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.3);
        display: flex; flex-direction: column; justify-content: flex-end; min-height: 200px;
    }}
    .memory-badge {{
        background: rgba(255,255,255,0.2); backdrop-filter: blur(10px);
        padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
        display: inline-block; margin-bottom: 8px; text-transform: uppercase;
    }}
    
    .agreement-card {{
        display: flex; align-items: flex-start; gap: 15px; padding: 15px;
        border-bottom: 1px solid {paleta['border']}; margin-bottom: 10px;
    }}
    .agreement-icon {{
        width: 40px; height: 40px; border-radius: 12px;
        background: {paleta['primary']}15; color: {paleta['primary']};
        display: flex; align-items: center; justify-content: center;
        font-size: 20px; flex-shrink: 0;
    }}
    .agreement-tag {{
        font-size: 0.65rem; padding: 2px 8px; border-radius: 8px;
        font-weight: 700; text-transform: uppercase;
        background: {paleta['input_bg']}; color: {paleta['text_muted']};
        margin-left: auto;
    }}
    
    .material-icons {{ font-family: 'Material Symbols Outlined'; font-size: 20px; vertical-align: middle; margin-right: 8px; }}
</style>
""", unsafe_allow_html=True)

# --- DADOS CONSTANTES ---
LINGUAGENS_LISTA = ["Atos de Serviço", "Palavras de Afirmação", "Tempo de Qualidade", "Toque Físico", "Presentes"]
CATEGORIAS_DR = ["Comunicação", "Finanças", "Ciúmes", "Família", "Rotina", "Outros"]
ICONES_ACORDOS = ["❤️", "🤝", "💰", "🏠", "📅", "🔥", "🙏", "✈️", "🥗", "💪", "🐶", "👶", "🚫", "🍷", "🎮"]
FREQ_ACORDOS = ["Diário", "Semanal", "Mensal", "Anual", "Único", "Sem Data"]

# --- LÓGICA GAMIFICAÇÃO AVANÇADA (VERSÃO 6.8) ---
def calcular_gamificacao(db):
    xp = db["xp"]
    nivel = int((xp / 100) ** 0.5) + 1
    xp_prox = ((nivel) ** 2) * 100
    progresso = min(max((xp - (((nivel - 1) ** 2) * 100)) / (xp_prox - (((nivel - 1) ** 2) * 100)), 0), 1)
    try: dias = (date.today() - datetime.strptime(db["config"].get("data_inicio", "2026-01-01"), "%Y-%m-%d").date()).days
    except: dias = 0
    return nivel, xp, xp_prox, progresso, dias

def verificar_conquistas_robustas(db):
    regs = db["registros"]
    total_logs = len(regs)
    
    # Cálculos Estatísticos
    datas = sorted([datetime.strptime(k, "%Y-%m-%d") for k in regs.keys()])
    streak = 0
    if datas:
        streak = 1
        for i in range(len(datas)-1, 0, -1):
            if (datas[i] - datas[i-1]).days == 1: streak += 1
            else: break
            
    total_sexo = sum(1 for r in regs.values() if r.get('sexo'))
    total_gratidao = sum(1 for r in regs.values() if r.get('gratidao'))
    total_sem_dr = sum(1 for r in regs.values() if not r.get('discussao'))
    
    total_acordos_cumpridos = 0
    for r in regs.values():
        total_acordos_cumpridos += sum(1 for v in r.get('checks_acordos', {}).values() if v)

    # Definição das Conquistas (Lista Robusta)
    trofeus = {
        "🔥 Constância": [
            {"t": "Primeiro Passo", "d": "1 Registro", "i": "flag", "m": 1, "v": total_logs},
            {"t": "Hábito", "d": "7 Dias Seguidos", "i": "local_fire_department", "m": 7, "v": streak},
            {"t": "Mensalista", "d": "30 Dias Registrados", "i": "calendar_month", "m": 30, "v": total_logs},
            {"t": "Chama Eterna", "d": "30 Dias Seguidos", "i": "volcano", "m": 30, "v": streak},
            {"t": "Bodas de Papel", "d": "365 Dias Registrados", "i": "history_edu", "m": 365, "v": total_logs},
        ],
        "💖 Intimidade & Amor": [
            {"t": "Lua de Mel", "d": "10x Amor", "i": "favorite", "m": 10, "v": total_sexo},
            {"t": "Pimenta", "d": "50x Amor", "i": "sentiment_very_satisfied", "m": 50, "v": total_sexo},
            {"t": "Poeta", "d": "Escreva 10 Elogios", "i": "edit_note", "m": 10, "v": sum(1 for r in regs.values() if any('Elogio' in str(x) for x in [r.get('eu_fiz', []), r.get('ela_fez', [])]))},
        ],
        "☮️ Harmonia": [
            {"t": "Paz Interior", "d": "7 Dias sem Discussão", "i": "spa", "m": 7, "v": total_sem_dr}, # Simplificado para total
            {"t": "Coração Grato", "d": "10 Gratidões", "i": "volunteer_activism", "m": 10, "v": total_gratidao},
            {"t": "Alma Iluminada", "d": "50 Gratidões", "i": "diamond", "m": 50, "v": total_gratidao},
        ],
        "🤝 Compromisso": [
            {"t": "De Palavra", "d": "10 Acordos Cumpridos", "i": "handshake", "m": 10, "v": total_acordos_cumpridos},
            {"t": "Guardião", "d": "50 Acordos Cumpridos", "i": "shield", "m": 50, "v": total_acordos_cumpridos},
            {"t": "Lendário", "d": "100 Acordos Cumpridos", "i": "verified", "m": 100, "v": total_acordos_cumpridos},
        ]
    }
    return trofeus

# --- CALCULAR CUMPRIMENTO DE ACORDOS ---
def calcular_stats_acordo(titulo_acordo):
    total_dias = len(db["registros"])
    if total_dias == 0: return 0, 0
    
    cumpridos = 0
    for reg in db["registros"].values():
        checks = reg.get("checks_acordos", {})
        if checks.get(titulo_acordo):
            cumpridos += 1
            
    return cumpridos, total_dias

# --- MODAL DE MEMÓRIA ---
@st.dialog("Detalhes da Memória")
def ver_memoria(data, info):
    nota = info.get('nota', 0)
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 3rem;">{'😍' if nota >= 8 else '🙂' if nota >= 5 else '☁️'}</div>
        <h2 style="margin: 0;">{datetime.strptime(data, '%Y-%m-%d').strftime('%d de %B de %Y')}</h2>
        <div>Nota do Dia: {nota}/10</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"**📝 Resumo:**\n\n{info.get('resumo', 'Sem resumo.')}")
    if info.get('gratidao'): st.info(f"✨ **Gratidão:** {info['gratidao']}")
    if info.get('whatsapp_txt'): st.text_area("WhatsApp:", info['whatsapp_txt'], disabled=True)

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
MENU_OPTIONS = ["Dashboard", "Registrar Dia", "Metas & Acordos", "🏆 Conquistas", "⏳ Cápsula", "Insights IA", "Configurações"]
home_preferida = db["config"].get("home_page", "Dashboard")
try: idx = MENU_OPTIONS.index(home_preferida)
except: idx = 0

st.sidebar.markdown("### ❤️ Menu")
menu = st.sidebar.radio("", MENU_OPTIONS, index=idx)

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    nivel, xp, xp_prox, prog, _ = calcular_gamificacao(db)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {paleta['primary']} 0%, #ff5c6a 100%); color: white; border-radius: 24px; padding: 24px; text-align: center; box-shadow: 0 10px 30px -10px {paleta['primary']}; margin-bottom: 24px;">
        <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">Nível de Conexão</div>
        <div style="font-size: 3.5rem; font-weight: 800; line-height: 1; margin: 10px 0;">{nivel}</div>
        <div style="background: rgba(0,0,0,0.2); height: 8px; border-radius: 4px; overflow: hidden;">
            <div style="background: white; width: {prog*100}%; height: 100%;"></div>
        </div>
        <div style="font-size: 0.8rem; margin-top: 8px; opacity: 0.9; font-weight: 600;">{xp} / {xp_prox} XP</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("### 📈 Humor da Semana")
        df_notas = pd.DataFrame([{"Data": datetime.strptime(k, "%Y-%m-%d"), "Nota": v["nota"]} for k, v in db["registros"].items() if "nota" in v]).sort_values("Data")
        if not df_notas.empty:
            chart = alt.Chart(df_notas).mark_line(interpolate='monotone', color=paleta['primary'], strokeWidth=4).encode(
                x=alt.X('Data', axis=alt.Axis(format='%d/%m')), y=alt.Y('Nota', scale=alt.Scale(domain=[0, 10]))
            ).properties(height=200).configure_view(strokeWidth=0)
            st.altair_chart(chart, use_container_width=True)
        else: st.info("Registre seu primeiro dia!")

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
            if st.button("🔓 Editar"): db["registros"][date_str]["locked"] = False; save_all(db); st.rerun()
        else:
            with st.form("form_registro"):
                st.subheader("Como foi hoje?")
                nota = st.slider("", 1, 10, value=day_data.get("nota", 8))
                
                if db["acordos_mestres"]:
                    st.divider()
                    st.caption("✅ CUMPRIMENTO DE ACORDOS")
                    checks_hoje = day_data.get("checks_acordos", {})
                    cols_ac = st.columns(2)
                    novos_checks = {}
                    for i, ac in enumerate(db["acordos_mestres"]):
                        label = f"{ac.get('icone', '🔹')} {ac['titulo']}"
                        check = cols_ac[i % 2].checkbox(label, value=checks_hoje.get(ac['titulo'], False))
                        novos_checks[ac['titulo']] = check
                    st.divider()

                c1, c2 = st.columns(2)
                with c1:
                    st.caption("JHONATA (EU)")
                    eu_fiz = st.multiselect("Eu fiz:", db["configuracoes"]["opcoes_eu_fiz"], day_data.get("eu_fiz", []))
                    ling_eu = st.multiselect("Minhas Linguagens:", LINGUAGENS_LISTA, day_data.get("ling_eu", []))
                    disc = st.checkbox("Teve DR?", day_data.get("discussao", False))
                    cat_dr = st.selectbox("Motivo:", CATEGORIAS_DR) if disc else None
                with c2:
                    st.caption("KATHERYN (ELA)")
                    ela_fez = st.multiselect("Ela fez:", db["configuracoes"]["opcoes_ela_fez"], day_data.get("ela_fez", []))
                    ling_ela = st.multiselect("Linguagens:", LINGUAGENS_LISTA, day_data.get("ling_ela", []))
                    sexo = st.radio("Intimidade:", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, horizontal=True)
                
                resumo = st.text_area("Diário de Bordo:", day_data.get("resumo", ""))
                gratidao = st.text_input("Gratidão do dia:", day_data.get("gratidao", ""))
                
                if st.form_submit_button("Salvar"):
                    if date_str not in db["registros"]: db["xp"] += 20
                    if gratidao: db["xp"] += 5
                    
                    acordos_cumpridos_count = sum(1 for v in novos_checks.values() if v) if 'novos_checks' in locals() else 0
                    db["xp"] += (acordos_cumpridos_count * 2)

                    db["registros"][date_str] = {
                        "nota": nota, "gratidao": gratidao, "eu_fiz": eu_fiz, "ela_fez": ela_fez,
                        "ling_eu": ling_eu, "ling_ela": ling_ela, "discussao": disc, "cat_dr": cat_dr,
                        "sexo": sexo == "Sim", "resumo": resumo, "checks_acordos": novos_checks if 'novos_checks' in locals() else {}, "locked": True
                    }
                    save_all(db); st.balloons(); st.rerun()

# --- 3. METAS E ACORDOS ---
elif menu == "Metas & Acordos":
    st.header("Central de Compromissos")
    with st.expander("✨ Criar Novo Acordo", expanded=False):
        with st.form("form_novo_acordo"):
            c_ic, c_fr = st.columns([1,2])
            icon = c_ic.selectbox("Ícone:", ICONES_ACORDOS)
            freq = c_fr.selectbox("Frequência:", FREQ_ACORDOS)
            titulo = st.text_input("Título:")
            desc = st.text_input("Descrição:")
            if st.form_submit_button("Firmar") and titulo:
                db["acordos_mestres"].append({"titulo": titulo, "icone": icon, "frequencia": freq, "descricao": desc, "data_criacao": str(date.today())})
                save_all(db); st.rerun()

    st.markdown("### 📜 Acordos Ativos")
    if not db["acordos_mestres"]: st.info("Nenhum acordo firmado.")
    
    for i, ac in enumerate(db["acordos_mestres"]):
        cumpridos, total = calcular_stats_acordo(ac["titulo"])
        pct = cumpridos / total if total > 0 else 0
        with st.container(border=True):
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"""
                <div class="agreement-card" style="border-bottom:none; padding:0; margin:0;">
                    <div class="agreement-icon">{ac.get('icone', '🔹')}</div>
                    <div style="flex-grow:1;">
                        <div style="display:flex; align-items:center; justify-content:space-between;">
                            <span style="font-weight:800; font-size:1.1rem;">{ac['titulo']}</span>
                            <span class="agreement-tag">{ac.get('frequencia','Diário')}</span>
                        </div>
                        <div style="font-size:0.85rem; color:{paleta['text_muted']};">{ac.get('descricao','')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(pct)
                st.caption(f"Cumprido {cumpridos}/{total} dias")
            with col_b:
                if st.button("🗑️", key=f"del_{i}"): db["acordos_mestres"].pop(i); save_all(db); st.rerun()

    st.divider()
    st.markdown("### 🎯 Metas da Semana")
    hoje = date.today(); inicio_sem = hoje - timedelta(days=hoje.weekday())
    reg_semana = [db["registros"].get((inicio_sem + timedelta(days=i)).strftime("%Y-%m-%d"), {}) for i in range(7)]
    c_elogios = sum(1 for r in reg_semana if "Elogio" in str(r.get("eu_fiz", [])))
    st.write(f"**Elogios** ({c_elogios}/{db['metas']['elogios']})")
    st.progress(min(c_elogios/db['metas']['elogios'], 1.0))

# --- 4. CONQUISTAS (REFORMULADO VERSÃO 6.8) ---
elif menu == "🏆 Conquistas":
    nivel, xp, xp_prox, prog, dias = calcular_gamificacao(db)
    
    # Header Stats
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div style="background:{paleta['bg_card']}; border-radius:24px; padding:20px; text-align:center; border:1px solid {paleta['border']}; box-shadow:{paleta['shadow']}">
            <div style="font-size:2rem; font-weight:800; color:{paleta['text_main']}">{dias}</div><div style="font-size:0.7rem; font-weight:700; color:{paleta['text_muted']}">DIAS JUNTOS</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div style="background:{paleta['bg_card']}; border-radius:24px; padding:20px; text-align:center; border:1px solid {paleta['border']}; box-shadow:{paleta['shadow']}">
            <div style="font-size:2rem; font-weight:800; color:{paleta['text_main']}">{nivel}</div><div style="font-size:0.7rem; font-weight:700; color:{paleta['text_muted']}">NÍVEL ATUAL</div>
        </div>""", unsafe_allow_html=True)
    
    st.write("")
    with st.container(border=True):
        st.markdown(f"**Progresso para o Nível {nivel+1}**")
        st.progress(prog)
        st.caption(f"Faltam {int(xp_prox - xp)} XP")

    # Galeria de Troféus
    st.divider()
    st.markdown("### 🏛️ Galeria de Troféus")
    
    categorias_conquistas = verificar_conquistas_robustas(db)
    
    for cat_nome, trofeus in categorias_conquistas.items():
        with st.expander(cat_nome, expanded=True):
            cols = st.columns(2)
            for i, t in enumerate(trofeus):
                concluido = t['v'] >= t['m']
                pct = min(t['v'] / t['m'], 1.0)
                
                # Estilo Visual (Cinza se bloqueado, Colorido se desbloqueado)
                cor_icone = paleta['primary'] if concluido else "#9ca3af"
                bg_card = f"{paleta['primary']}10" if concluido else "#f3f4f6"
                if "Escuro" in tema_selecionado and not concluido: bg_card = "#2d2d2d"
                icon_name = "lock" if not concluido else t['i']
                
                with cols[i % 2]:
                    st.markdown(f"""
                    <div style="background-color: {bg_card}; border-radius: 16px; padding: 15px; margin-bottom: 10px; height: 100%;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                            <span class="material-icons" style="color: {cor_icone}; font-size: 24px;">{icon_name}</span>
                            <div style="font-weight: 700; font-size: 0.9rem; line-height: 1.1;">{t['t']}</div>
                        </div>
                        <div style="font-size: 0.75rem; opacity: 0.8; margin-bottom: 8px;">{t['d']}</div>
                        <div style="background: rgba(0,0,0,0.1); height: 4px; border-radius: 2px; overflow: hidden;">
                            <div style="background: {cor_icone}; width: {pct*100}%; height: 100%;"></div>
                        </div>
                        <div style="font-size: 0.7rem; text-align: right; margin-top: 4px;">{t['v']}/{t['m']}</div>
                    </div>
                    """, unsafe_allow_html=True)

# --- 5. CÁPSULA ---
elif menu == "⏳ Cápsula":
    st.markdown("## ⏳ Cápsula do Tempo")
    hoje = date.today()
    datas_alvo = {"Há 30 Dias": (hoje - timedelta(days=30)), "Há 90 Dias": (hoje - timedelta(days=90))}
    for label, data_obj in datas_alvo.items():
        data_str = data_obj.strftime("%Y-%m-%d")
        if data_str in db["registros"]:
            reg = db["registros"][data_str]
            nota = reg.get('nota', 7)
            bg = "#f42536" if nota >= 8 else "#f59e0b" if nota >= 5 else "#4b5563"
            with st.container(border=True):
                st.markdown(f"### {label} ({data_obj.strftime('%d/%m')})")
                st.markdown(f"<div style='background-color:{bg}; color:white; padding:15px; border-radius:12px; margin-bottom:10px;'>Nota: {nota}/10 - {reg.get('resumo', '')[:50]}...</div>", unsafe_allow_html=True)
                if st.button("Ver Memória", key=f"btn_{data_str}"): ver_memoria(data_str, reg)
        else: st.caption(f"{label}: Sem registros.")
    
    st.divider()
    with st.expander("📥 Exportar Relatório em PDF"):
        mes_sel = st.selectbox("Mês:", ["01","02","03","04","05","06","07","08","09","10","11","12"])
        if st.button("Baixar PDF"):
            dados = {k: v for k, v in db["registros"].items() if k.split("-")[1] == mes_sel}
            if dados:
                pdf = gerar_pdf(dados, mes_sel)
                st.download_button("Download", pdf, "Planner.pdf", "application/pdf")

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
        prompt = ""; executar = False
        if c_ia1.button("📊 Análise Geral"): prompt = "Aja como um terapeuta. Resuma o relacionamento."; executar = True
        if c_ia2.button("⚖️ Coach de Conflitos"):
            regs_conf = [(d,r) for d,r in registros_filtrados if r.get('discussao')]
            prompt = "Analise apenas conflitos."; registros_filtrados = regs_conf; executar = True
            if not regs_conf: st.success("Sem conflitos! 🎉"); executar = False
        c_ia3, c_ia4 = st.columns(2)
        if c_ia3.button("💘 Guru Romântico"): prompt = "Sugira 3 ideias criativas de encontros."; executar = True
        if c_ia4.button("🔮 Tendências"): prompt = "Analise a tendência das notas."; executar = True
        if executar and registros_filtrados:
            ctx = str(registros_filtrados)
            if len(ctx) > 15000: ctx = ctx[-15000:]
            try:
                with st.spinner("Analisando..."):
                    resp = client_groq.chat.completions.create(model=db["config"]["modelo_ia"], messages=[{"role":"user","content":f"{prompt} Dados: {ctx}"}], temperature=0.7)
                    st.success(resp.choices[0].message.content)
            except Exception as e: st.error(f"Erro: {e}")

# --- 7. CONFIGURAÇÕES ---
elif menu == "Configurações":
    st.markdown("## ⚙️ Configurações & Perfil")
    with st.container(border=True):
        col_pic, col_info = st.columns([1, 3])
        with col_pic:
            img_b64 = db["config"].get("foto_perfil")
            if img_b64: st.markdown(f'<div class="profile-pic-container"><img src="data:image/png;base64,{img_b64}" width="80"></div>', unsafe_allow_html=True)
            else: st.markdown(f'<div class="profile-pic-container"><span class="material-icons" style="font-size:40px; color:{paleta["primary"]}">favorite</span></div>', unsafe_allow_html=True)
        with col_info: st.markdown(f"""<div class="profile-info"><h2>{db["config"].get("nomes_casal", "Casal")}</h2><p><span class="material-icons">calendar_today</span> Juntos desde {db["config"].get("data_inicio", "2026")}</p></div>""", unsafe_allow_html=True)
        with st.expander("Editar Perfil"):
            novo_nome = st.text_input("Nomes:", value=db["config"].get("nomes_casal", ""))
            nova_data = st.date_input("Data de Início:", value=datetime.strptime(db["config"].get("data_inicio", "2026-01-01"), "%Y-%m-%d"))
            uploaded_pic = st.file_uploader("Alterar Foto:", type=["png", "jpg", "jpeg"])
            if st.button("Salvar Perfil"):
                db["config"]["nomes_casal"] = novo_nome; db["config"]["data_inicio"] = str(nova_data)
                if uploaded_pic: db["config"]["foto_perfil"] = base64.b64encode(uploaded_pic.getvalue()).decode()
                save_all(db); st.rerun()

    st.markdown("### 🎨 Aparência")
    cols_tema = st.columns(3)
    for i, tema in enumerate(TEMAS.keys()):
        with cols_tema[i % 3]:
            if st.button(tema, key=f"btn_tema_{tema}", use_container_width=True): db["config"]["tema"] = tema; save_all(db); st.rerun()
    
    st.markdown("### 🛠️ Personalização do Diário")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("#### 'Eu Fiz' (Jhonata)")
            new_eu = st.text_input("Novo Item:", key="n_eu")
            if st.button("Adicionar (Eu)", key="btn_n_eu") and new_eu: db["configuracoes"]["opcoes_eu_fiz"].append(new_eu); save_all(db); st.rerun()
            st.divider()
            opts_eu = db["configuracoes"]["opcoes_eu_fiz"]
            if opts_eu:
                sel_eu = st.selectbox("Selecione:", opts_eu, key="s_eu")
                ren_eu = st.text_input("Renomear:", value=sel_eu, key="r_eu")
                ce1, ce2 = st.columns(2)
                if ce1.button("Salvar", key="sv_eu"): db["configuracoes"]["opcoes_eu_fiz"][opts_eu.index(sel_eu)] = ren_eu; save_all(db); st.rerun()
                if ce2.button("Excluir", key="dl_eu"): db["configuracoes"]["opcoes_eu_fiz"].remove(sel_eu); save_all(db); st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown("#### 'Ela Fez' (Katheryn)")
            new_ela = st.text_input("Novo Item:", key="n_ela")
            if st.button("Adicionar (Ela)", key="btn_n_ela") and new_ela: db["configuracoes"]["opcoes_ela_fez"].append(new_ela); save_all(db); st.rerun()
            st.divider()
            opts_ela = db["configuracoes"]["opcoes_ela_fez"]
            if opts_ela:
                sel_ela = st.selectbox("Selecione:", opts_ela, key="s_ela")
                ren_ela = st.text_input("Renomear:", value=sel_ela, key="r_ela")
                ce3, ce4 = st.columns(2)
                if ce3.button("Salvar", key="sv_ela"): db["configuracoes"]["opcoes_ela_fez"][opts_ela.index(sel_ela)] = ren_ela; save_all(db); st.rerun()
                if ce4.button("Excluir", key="dl_ela"): db["configuracoes"]["opcoes_ela_fez"].remove(sel_ela); save_all(db); st.rerun()

    st.markdown("### 🔔 Preferências")
    with st.container(border=True):
        notif = st.toggle("Notificações", value=db["config"].get("notificacoes", True))
        mentor = st.toggle("Dicas do Mentor", value=db["config"].get("dicas_mentor", True))
        if notif != db["config"].get("notificacoes") or mentor != db["config"].get("dicas_mentor"):
            db["config"]["notificacoes"] = notif; db["config"]["dicas_mentor"] = mentor; save_all(db); st.toast("Salvo!")
    if st.button("Sair (Limpar Cache)"): st.cache_data.clear(); st.rerun()
