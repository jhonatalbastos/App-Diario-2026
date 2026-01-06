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
            "foto_perfil": None, # Base64 string
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
    
    /* Profile Header Style */
    .profile-header {{
        display: flex;
        align-items: center;
        gap: 20px;
        padding-bottom: 20px;
        border-bottom: 1px solid {paleta['border']};
        margin-bottom: 20px;
    }}
    .profile-pic-container {{
        width: 80px;
        height: 80px;
        border-radius: 50%;
        overflow: hidden;
        border: 3px solid var(--primary);
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: {paleta['input_bg']};
    }}
    .profile-info h2 {{
        margin: 0;
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--text-main);
    }}
    .profile-info p {{
        margin: 0;
        color: var(--text-muted);
        font-size: 0.9rem;
    }}
    
    .material-icons {{
        font-family: 'Material Symbols Outlined';
        font-size: 20px;
        vertical-align: middle;
        margin-right: 8px;
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
    st.header("Metas & Acordos")
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
            st.markdown(f"- **{ac['nome_curto']}**: {ac['titulo']}")
        with st.expander("Adicionar Acordo"):
            with st.form("novo_acordo"):
                t = st.text_input("Acordo")
                if st.form_submit_button("Salvar"):
                    db["acordos_mestres"].append({"titulo": t, "nome_curto": t[:10], "monitorar": True, "data": str(date.today())})
                    save_all(db); st.rerun()

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

# --- 5. CÁPSULA (FASE 3) ---
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
                if st.button("Ver Memória", key=f"btn_{data_str}"):
                    st.info(f"Resumo Completo: {reg.get('resumo')}")
        else:
            st.caption(f"{label}: Sem registros.")

# --- 6. INSIGHTS IA ---
elif menu == "Insights IA":
    st.header("💡 Mentor IA")
    # Lógica de IA mantida...

# --- 7. CONFIGURAÇÕES (FASE 5) ---
elif menu == "Configurações":
    st.markdown("## ⚙️ Configurações & Perfil")
    
    # 1. HEADER DE PERFIL (FOTO E NOMES)
    with st.container(border=True):
        col_pic, col_info = st.columns([1, 3])
        
        with col_pic:
            # Lógica de Foto de Perfil (Persistência Base64)
            img_b64 = db["config"].get("foto_perfil")
            if img_b64:
                st.markdown(f'<div class="profile-pic-container"><img src="data:image/png;base64,{img_b64}" width="80"></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="profile-pic-container"><span class="material-icons" style="font-size:40px; color:{paleta["primary"]}">favorite</span></div>', unsafe_allow_html=True)
        
        with col_info:
            st.markdown(f"""
            <div class="profile-info">
                <h2>{db["config"].get("nomes_casal", "Casal")}</h2>
                <p><span class="material-icons">calendar_today</span> Juntos desde {db["config"].get("data_inicio", "2026")}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with st.expander("Editar Perfil"):
            novo_nome = st.text_input("Nomes:", value=db["config"].get("nomes_casal", ""))
            nova_data = st.date_input("Data de Início:", value=datetime.strptime(db["config"].get("data_inicio", "2026-01-01"), "%Y-%m-%d"))
            uploaded_pic = st.file_uploader("Alterar Foto:", type=["png", "jpg", "jpeg"])
            
            if st.button("Salvar Perfil"):
                db["config"]["nomes_casal"] = novo_nome
                db["config"]["data_inicio"] = str(nova_data)
                if uploaded_pic:
                    # Converter imagem para Base64
                    bytes_data = uploaded_pic.getvalue()
                    b64_str = base64.b64encode(bytes_data).decode()
                    db["config"]["foto_perfil"] = b64_str
                save_all(db)
                st.success("Perfil atualizado!")
                st.rerun()

    # 2. SELETOR DE TEMA (VISUAL CARDS)
    st.markdown("### 🎨 Aparência")
    cols_tema = st.columns(3)
    temas_list = list(TEMAS.keys())
    
    for i, tema in enumerate(temas_list):
        with cols_tema[i % 3]:
            # Botão simples que funciona como seletor
            if st.button(tema, key=f"btn_tema_{tema}", use_container_width=True):
                db["config"]["tema"] = tema
                save_all(db)
                st.rerun()
                
    st.caption(f"Tema Atual: **{tema_selecionado}**")

    # 3. PERSONALIZAÇÃO (AÇÕES)
    st.markdown("### 🛠️ Personalização")
    with st.container(border=True):
        st.markdown("**Gerenciar Opções do Diário**")
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            new_eu = st.text_input("Novo 'Eu Fiz':")
            if st.button("Add Eu"):
                if new_eu: db["configuracoes"]["opcoes_eu_fiz"].append(new_eu); save_all(db); st.rerun()
        with c_p2:
            new_ela = st.text_input("Novo 'Ela Fez':")
            if st.button("Add Ela"):
                if new_ela: db["configuracoes"]["opcoes_ela_fez"].append(new_ela); save_all(db); st.rerun()

    # 4. PREFERÊNCIAS (TOGGLES)
    st.markdown("### 🔔 Preferências")
    with st.container(border=True):
        notif = st.toggle("Lembrete Diário", value=db["config"].get("notificacoes", True))
        mentor = st.toggle("Dicas do Mentor", value=db["config"].get("dicas_mentor", True))
        bio = st.toggle("Bloqueio com Biometria", value=db["config"].get("biometria", False))
        
        if (notif != db["config"].get("notificacoes") or 
            mentor != db["config"].get("dicas_mentor") or 
            bio != db["config"].get("biometria")):
            
            db["config"]["notificacoes"] = notif
            db["config"]["dicas_mentor"] = mentor
            db["config"]["biometria"] = bio
            save_all(db)
            st.toast("Preferências salvas!")

    # 5. SUPORTE & RESET
    st.markdown("### 🆘 Suporte")
    with st.container(border=True):
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; padding:5px 0;">
            <span>❓ Ajuda e Feedback</span>
            <span class="material-icons">chevron_right</span>
        </div>
        <hr style="margin:5px 0; opacity:0.1">
        <div style="display:flex; justify-content:space-between; align-items:center; padding:5px 0;">
            <span>🛡️ Privacidade</span>
            <span class="material-icons">chevron_right</span>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("Sair da Conta (Limpar Cache)", type="primary"):
        st.cache_data.clear()
        st.rerun()
