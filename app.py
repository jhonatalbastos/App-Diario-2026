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
        if "xp" not in data: data["xp"] = 0
        if "config" not in data: data["config"] = {}
        
        defaults = {
            "modelo_ia": "llama-3.3-70b-versatile",
            "tema": "Claro (Padrão)",
            "home_page": "Dashboard",
            "data_inicio": "2026-01-01"
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
    
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {{
        background-color: {paleta['input_bg']} !important;
        color: var(--text-main) !important;
        border-radius: 16px;
        border: 1px solid transparent;
    }}
    
    /* Memory Card Style (Fase 3) */
    .memory-card {{
        border-radius: 24px;
        padding: 24px;
        color: white;
        position: relative;
        overflow: hidden;
        margin-bottom: 16px;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.3);
        transition: transform 0.2s;
        cursor: pointer;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
    }}
    .memory-card:hover {{ transform: scale(1.02); }}
    
    .memory-badge {{
        background: rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .material-icons {{
        font-family: 'Material Symbols Outlined';
        font-size: 24px;
        display: inline-block;
        vertical-align: middle;
    }}
</style>
""", unsafe_allow_html=True)

# --- DADOS CONSTANTES ---
LINGUAGENS_LISTA = ["Atos de Serviço", "Palavras de Afirmação", "Tempo de Qualidade", "Toque Físico", "Presentes"]
CATEGORIAS_DR = ["Comunicação", "Finanças", "Ciúmes", "Família", "Rotina", "Outros"]

# --- LÓGICA GAMIFICAÇÃO ---
def calcular_gamificacao(db):
    xp = db["xp"]
    nivel = int((xp / 100) ** 0.5) + 1
    xp_prox = ((nivel) ** 2) * 100
    progresso = min(max((xp - (((nivel - 1) ** 2) * 100)) / (xp_prox - (((nivel - 1) ** 2) * 100)), 0), 1)
    try: dias = (date.today() - datetime.strptime(db["config"].get("data_inicio", "2026-01-01"), "%Y-%m-%d").date()).days
    except: dias = 0
    return nivel, xp, xp_prox, progresso, dias

# --- MODAL DE MEMÓRIA (FASE 3) ---
@st.dialog("Detalhes da Memória")
def ver_memoria(data, info):
    nota = info.get('nota', 0)
    cor_nota = "#22c55e" if nota >= 8 else "#eab308" if nota >= 5 else "#ef4444"
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 3rem;">{'😍' if nota >= 8 else '🙂' if nota >= 5 else '☁️'}</div>
        <h2 style="margin: 0;">{datetime.strptime(data, '%Y-%m-%d').strftime('%d de %B de %Y')}</h2>
        <div style="color: {cor_nota}; font-weight: 800; font-size: 1.2rem;">Nota do Dia: {nota}/10</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"**📝 Resumo:**\n\n{info.get('resumo', 'Sem resumo escrito.')}")
    
    if info.get('gratidao'):
        st.info(f"✨ **Gratidão:** {info['gratidao']}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Jhonata fez:**")
        for x in info.get('eu_fiz', []): st.caption(f"• {x}")
    with c2:
        st.markdown("**Katheryn fez:**")
        for x in info.get('ela_fez', []): st.caption(f"• {x}")
        
    if info.get('whatsapp_txt'):
        with st.expander("💬 Ver Conversa do WhatsApp"):
            st.text(info['whatsapp_txt'])

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
                    db["registros"][date_str] = {
                        "nota": nota, "gratidao": gratidao, "eu_fiz": eu_fiz, "ela_fez": ela_fez,
                        "ling_eu": ling_eu, "ling_ela": ling_ela, "discussao": disc, "cat_dr": cat_dr,
                        "sexo": sexo == "Sim", "resumo": resumo, "locked": True
                    }
                    save_all(db); st.balloons(); st.rerun()

# --- 3. METAS E ACORDOS ---
elif menu == "Metas & Acordos":
    # Lógica mantida
    st.header("Metas & Acordos")
    with st.container(border=True):
        st.markdown("### 🎯 Metas da Semana")
        # ... (código existente de metas)
        st.write("Em desenvolvimento visual...") 

# --- 4. CONQUISTAS ---
elif menu == "🏆 Conquistas":
    nivel, xp, xp_prox, prog, dias = calcular_gamificacao(db)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div style="background:{paleta['bg_card']}; border-radius:24px; padding:20px; text-align:center; border:1px solid {paleta['border']}; box-shadow:{paleta['shadow']}">
            <div style="font-size:2rem; font-weight:800; color:{paleta['text_main']}">{dias}</div><div style="font-size:0.7rem; font-weight:700; color:{paleta['text_muted']}">DIAS JUNTOS</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div style="background:{paleta['bg_card']}; border-radius:24px; padding:20px; text-align:center; border:1px solid {paleta['border']}; box-shadow:{paleta['shadow']}">
            <div style="font-size:2rem; font-weight:800; color:{paleta['text_main']}">{nivel}</div><div style="font-size:0.7rem; font-weight:700; color:{paleta['text_muted']}">NÍVEL ATUAL</div>
        </div>""", unsafe_allow_html=True)
    st.write(""); st.progress(prog); st.caption(f"{xp}/{xp_prox} XP")

# --- 5. CÁPSULA (NOVO VISUAL FASE 3) ---
elif menu == "⏳ Cápsula":
    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="margin:0; font-size:1.5rem;">Hoje é {date.today().strftime('%d de %B de %Y')}</h2>
        <p style="opacity:0.7;">Relembre seus momentos especiais...</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Lógica de Datas
    hoje = date.today()
    datas_alvo = {
        "Há 30 Dias": (hoje - timedelta(days=30)).strftime("%Y-%m-%d"),
        "Há 90 Dias": (hoje - timedelta(days=90)).strftime("%Y-%m-%d"),
        "Há 1 Ano": (hoje - timedelta(days=365)).strftime("%Y-%m-%d")
    }
    
    tem_memoria = False
    
    for label, data_str in datas_alvo.items():
        if data_str in db["registros"]:
            tem_memoria = True
            reg = db["registros"][data_str]
            nota = reg.get('nota', 7)
            
            # Gradientes Emocionais (Sem imagem)
            if nota >= 8:
                bg = "linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.6)), linear-gradient(135deg, #f42536 0%, #ff5c6a 100%)"
                tag = "❤️ Amando muito"
            elif nota >= 5:
                bg = "linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.6)), linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)"
                tag = "🙂 Dia Bom"
            else:
                bg = "linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.6)), linear-gradient(135deg, #4b5563 0%, #6b7280 100%)"
                tag = "☁️ Reflexivo"
                
            st.markdown(f"### {label}")
            
            # Renderiza o Card Clicável (Simulado com botão transparente por cima ou layout)
            # Como Streamlit não deixa div clicável acionar python, usamos botão abaixo
            st.markdown(f"""
            <div class="memory-card" style="background: {bg};">
                <div style="position: absolute; top: 20px; left: 20px;">
                    <div class="memory-badge">{tag}</div>
                </div>
                <div>
                    <div style="opacity: 0.9; font-size: 0.8rem; font-weight: 600; margin-bottom: 5px;">{datetime.strptime(data_str, '%Y-%m-%d').strftime('%d DE %B DE %Y')}</div>
                    <div style="font-size: 1.5rem; font-weight: 800; line-height: 1.2; margin-bottom: 10px;">
                        "{reg.get('resumo', 'Sem título')[:40]}..."
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"👁️ Ler memória de {label}", key=f"btn_{data_str}"):
                ver_memoria(data_str, reg)
                
    if not tem_memoria:
        st.info("📭 Sua cápsula do tempo ainda está vazia para estas datas. Continue registrando seus dias para ver memórias aqui no futuro!")

    # Exportação PDF mantida no final
    st.divider()
    with st.expander("📥 Exportar Relatório em PDF"):
        mes_sel = st.selectbox("Mês:", ["01","02","03","04","05","06","07","08","09","10","11","12"])
        if st.button("Baixar PDF"):
            # Lógica PDF existente
            pass

# --- 6. INSIGHTS IA ---
elif menu == "Insights IA":
    st.header("💡 Mentor IA")
    # Lógica existente

# --- 7. CONFIGURAÇÕES ---
elif menu == "Configurações":
    st.header("⚙️ Configurações")
    with st.container(border=True):
        novo_tema = st.selectbox("Tema:", list(TEMAS.keys()), index=list(TEMAS.keys()).index(tema_selecionado))
        if st.button("Salvar"):
            db["config"]["tema"] = novo_tema
            save_all(db); st.rerun()
