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

# --- ESTILIZAÇÃO CSS (O SEGREDO DO VISUAL) ---
st.markdown("""
<style>
    /* Importando Fonte do HTML original */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap');

    /* Variáveis de Cores */
    :root {
        --primary: #f42536;
        --primary-soft: #ffe5e7;
        --bg-light: #fcf8f8;
        --card-bg: #ffffff;
        --text-main: #1c0d0e;
        --shadow: 0 4px 20px -2px rgba(244, 37, 54, 0.08);
    }

    /* Aplicando Fonte e Fundo */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .stApp {
        background-color: var(--bg-light);
    }

    /* Estilo dos Cards (Container) */
    .css-card {
        background-color: var(--card-bg);
        border-radius: 24px;
        padding: 24px;
        box-shadow: var(--shadow);
        border: 1px solid #e8ced1;
        margin-bottom: 20px;
    }

    /* Botões Personalizados */
    div.stButton > button {
        background-color: var(--primary);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 12px 24px;
        font-weight: 700;
        width: 100%;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #d11a2a;
        transform: scale(1.02);
        color: white;
    }
    
    /* Botão Secundário (Outline) */
    div.stButton > button.secondary {
        background-color: transparent;
        border: 2px solid var(--primary);
        color: var(--primary);
    }

    /* Inputs e Sliders */
    .stSlider [data-baseweb="slider"] {
        color: var(--primary);
    }
    
    /* Cabeçalhos */
    h1, h2, h3 {
        color: var(--text-main);
        font-weight: 800;
    }
    
    /* Custom XP Card Style */
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

# --- SEGURANÇA (SECRETS) ---
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
def gerar_pdf(dados_mes, nome_mes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(244, 37, 54) # Cor primária
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
# Simular a Bottom Nav do HTML com o menu lateral, mas estilizado
st.sidebar.markdown("### ❤️ Menu")
menu = st.sidebar.radio("", ["Dashboard", "Registrar Dia", "Metas & Acordos", "Cápsula", "Insights IA", "Configurações"])

# --- HEADER DE GAMIFICAÇÃO (SEMPRE VISÍVEL NO TOPO DO DASH) ---
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
    # Container estilo Card
    with st.container():
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.markdown("### 📈 Humor da Semana")
        
        # Gráfico Altair (Estilo Chart.js suave do HTML)
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

    # Cards de Resumo Recente
    st.markdown("### 📅 Histórico Recente")
    recentes = sorted(list(db["registros"].items()), reverse=True)[:3]
    for d, i in recentes:
        cor_nota = "#22c55e" if i['nota'] >= 8 else "#eab308" if i['nota'] >= 5 else "#ef4444"
        st.markdown(f"""
        <div class="css-card" style="padding: 15px; display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
            <div style="background-color: {cor_nota}; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                {i['nota']}
            </div>
            <div>
                <div style="font-weight: bold; font-size: 0.9rem;">{datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m")}</div>
                <div style="font-size: 0.8rem; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px;">
                    {i.get('resumo', 'Sem resumo')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 2. REGISTRAR DIA ---
elif menu == "Registrar Dia":
    st.markdown("## 📝 Registrar Dia")
    
    # Card Principal
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
                st.caption("O que rolou?")
                # Mistura de tags eu/ela em uma visualização única se quiser, ou separado
                eu_fiz = st.multiselect("Eu fiz:", db["configuracoes"]["opcoes_eu_fiz"], day_data.get("eu_fiz", []))
                disc = st.checkbox("Teve DR?", day_data.get("discussao", False))
                if disc: cat_dr = st.selectbox("Motivo:", CATEGORIAS_DR)
                else: cat_dr = None
            with c2:
                st.caption("Interações")
                ela_fez = st.multiselect("Ela fez:", db["configuracoes"]["opcoes_ela_fez"], day_data.get("ela_fez", []))
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
                    "discussao": disc, "cat_dr": cat_dr, "sexo": sexo == "Sim", "resumo": resumo, "locked": True
                }
                save_all(db)
                st.success(f"Salvo! +{xp_ganho} XP")
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 3. METAS E ACORDOS ---
elif menu == "Metas & Acordos":
    st.markdown("## 🎯 Metas & Acordos")
    
    # Card de Metas
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### Metas da Semana")
    
    hoje = date.today()
    inicio_sem = hoje - timedelta(days=hoje.weekday())
    reg_semana = [db["registros"].get((inicio_sem + timedelta(days=i)).strftime("%Y-%m-%d"), {}) for i in range(7)]
    
    c_elogios = sum(1 for r in reg_semana if "Elogio" in str(r.get("eu_fiz", [])))
    meta_elog = db['metas']['elogios']
    
    st.write(f"**Elogios** ({c_elogios}/{meta_elog})")
    st.progress(min(c_elogios/meta_elog, 1.0))
    
    c_qual = sum(1 for r in reg_semana if "Tempo de Qualidade" in str(r.get("eu_fiz", [])))
    meta_qual = db['metas']['qualidade']
    st.write(f"**Tempo de Qualidade** ({c_qual}/{meta_qual})")
    st.progress(min(c_qual/meta_qual, 1.0))
    st.markdown('</div>', unsafe_allow_html=True)

    # Card de Acordos
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### Acordos Ativos")
    
    # Checkbox visual apenas para leitura ou form para editar
    for ac in db["acordos_mestres"]:
        status = "🟢" if ac.get('monitorar') else "⚪"
        st.markdown(f"**{status} {ac['titulo']}**")
        st.caption(f"Criado em: {ac['data']}")
        st.divider()
    
    with st.expander("Gerenciar Acordos"):
        with st.form("novo_acordo"):
            t = st.text_input("Novo Acordo")
            if st.form_submit_button("Adicionar"):
                db["acordos_mestres"].append({"titulo": t, "nome_curto": t[:10], "monitorar": True, "data": str(date.today())})
                save_all(db); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. CÁPSULA ---
elif menu == "Cápsula":
    st.markdown("## ⏳ Cápsula do Tempo")
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.info("O que aconteceu há um mês?")
    alvo = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    if alvo in db["registros"]:
        r = db["registros"][alvo]
        st.markdown(f"**Data:** {alvo} | **Nota:** {r['nota']}")
        st.write(f"_{r.get('resumo', 'Sem resumo')}_")
    else:
        st.caption("Nenhum registro encontrado há exatos 30 dias.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Exportação PDF simples
    if st.button("Baixar PDF deste Mês"):
        mes_atual = date.today().strftime("%m")
        dados_mes = {k: v for k, v in db["registros"].items() if k.split("-")[1] == mes_atual}
        pdf_bytes = gerar_pdf(dados_mes, date.today().strftime("%B"))
        st.download_button("Download", pdf_bytes, "memorias.pdf", "application/pdf")

# --- 5. CONFIGURAÇÕES ---
elif menu == "Configurações":
    st.markdown("## ⚙️ Ajustes")
    with st.container():
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        new_eu = st.text_input("Adicionar opção 'Eu fiz':")
        if st.button("Adicionar Opção"):
            db["configuracoes"]["opcoes_eu_fiz"].append(new_eu)
            save_all(db); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with st.container():
         st.markdown('<div class="css-card">', unsafe_allow_html=True)
         st.caption("Área Perigosa")
         if st.button("Resetar Cache do App"):
             st.cache_data.clear()
         st.markdown('</div>', unsafe_allow_html=True)

# --- 6. INSIGHTS IA ---
elif menu == "Insights IA":
    st.header("💡 Mentor IA")
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    if st.button("Gerar Análise Semanal"):
        ctx = str(list(db["registros"].items())[-7:])
        try:
            prompt = f"Aja como um mentor de relacionamento empático. Analise estes dados do casal (Jhonata e Katheryn): {ctx}. Dê 1 conselho curto e 1 elogio."
            resp = client_groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
            st.success(resp.choices[0].message.content)
        except Exception as e:
            st.error(f"Erro: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
