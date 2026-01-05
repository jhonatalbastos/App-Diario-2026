import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq
from fpdf import FPDF
import io
from PIL import Image # Importar Pillow para manipulação de imagem

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Love Planner 4.9 - Jhonata & Katheryn", layout="wide", page_icon="❤️")

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

# --- FUNÇÕES DE DADOS ---
def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        data = json.loads(contents.decoded_content.decode())
        if "config" not in data: data["config"] = {"modelo_ia": "llama-3.3-70b-versatile"}
        return data
    except:
        return {
            "registros": {}, "eventos": {}, "acordos_mestres": [], 
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

# --- FUNÇÃO EXPORTAR PDF COM CAPA ---
def gerar_pdf_com_capa(dados_mes, nome_mes, imagem_bytes=None):
    pdf = FPDF()

    # Adicionar a Capa
    pdf.add_page()
    if imagem_bytes:
        try:
            # Tenta abrir a imagem e redimensionar se for muito grande
            img = Image.open(io.BytesIO(imagem_bytes))
            
            # Manter proporção e ajustar à página
            max_width = 180 # Largura máxima na página
            max_height = 250 # Altura máxima na página

            img_width, img_height = img.size
            aspect_ratio = img_width / img_height

            if img_width > max_width:
                img_width = max_width
                img_height = img_width / aspect_ratio
            if img_height > max_height:
                img_height = max_height
                img_width = img_height * aspect_ratio

            # Centralizar imagem
            x = (210 - img_width) / 2
            y = (297 - img_height) / 2 - 20 # Ajuste para título
            
            pdf.image(io.BytesIO(imagem_bytes), x=x, y=y, w=img_width, h=img_height)
        except Exception as e:
            st.warning(f"Não foi possível processar a imagem. Erro: {e}")
            # Se der erro, continua sem a imagem mas com título
    
    pdf.set_font("Arial", "B", 24)
    pdf.set_text_color(255, 0, 0) # Cor vermelha
    pdf.text(70, 30, f"Nossas Memórias de {nome_mes}")
    pdf.set_text_color(0, 0, 0) # Volta ao preto
    pdf.set_font("Arial", "I", 14)
    pdf.text(80, 40, "Jhonata & Katheryn - 2026")
    pdf.add_page() # Nova página para o conteúdo

    # Conteúdo do Diário
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Detalhes do Mês de {nome_mes}", ln=True, align='C')
    pdf.ln(10)
    
    for data, info in sorted(dados_mes.items()):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Dia: {data} - Nota: {info.get('nota', 'N/A')}", ln=True)
        pdf.set_font("Arial", "", 10)
        resumo = info.get('resumo', 'Sem resumo registrado.')
        pdf.multi_cell(0, 5, f"Resumo: {resumo}")
        
        # Adiciona detalhes do WhatsApp se existirem
        if info.get('whatsapp_txt'):
            pdf.set_font("Arial", "I", 8)
            pdf.multi_cell(0, 4, f"WhatsApp: {info['whatsapp_txt'][:200]}...") # Limita para não sobrecarregar
            pdf.ln(2)
        
        pdf.ln(5)
    
    return pdf.output()

# --- NAVEGAÇÃO ---
st.sidebar.title("❤️ Love Planner 4.9")
menu = st.sidebar.radio("Navegação:", ["📝 Diário", "📊 Painel & Grids", "🤝 Acordos", "⏳ Cápsula do Tempo", "📅 Eventos", "💡 Insights da IA", "⚙️ Configurações"])

# --- 1. ABA DIÁRIO ---
if menu == "📝 Diário":
    st.header("📝 Registro Diário")
    selected_date = st.date_input("Data do Registro:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    if is_locked:
        st.warning("🔒 Dia trancado.")
        if st.button("🔓 Destrancar"):
            db["registros"][date_str]["locked"] = False
            save_all(db); st.rerun()

    with st.form("form_v49"):
        nota = st.select_slider("Nota do Relacionamento:", options=range(1,11), value=day_data.get("nota", 7), disabled=is_locked)
        
        acordos_ativos = [a for a in db.get("acordos_mestres", []) if a.get("monitorar")]
        checks_acordos_hoje = {}
        if acordos_ativos:
            st.subheader("🎯 Acordos")
            cols_ac = st.columns(len(acordos_ativos))
            for i, ac in enumerate(acordos_ativos):
                label = ac['nome_curto']
                checks_acordos_hoje[label] = cols_ac[i].checkbox(label, value=day_data.get("checks_acordos", {}).get(label, False), disabled=is_locked)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Jhonata")
            op_eu = db["configuracoes"]["opcoes_eu_fiz"] + ["Outro"]
            eu_fiz = st.multiselect("Eu fiz:", op_eu, [x for x in day_data.get("eu_fiz", []) if x in op_eu], disabled=is_locked)
            novo_eu = st.text_input("Novo (Eu):") if "Outro" in eu_fiz else ""
            ling_eu = st.multiselect("Minhas Linguagens:", LINGUAGENS_LISTA, day_data.get("ling_eu", []), disabled=is_locked)
            disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)
        with col2:
            st.subheader("Katheryn")
            op_ela = db["configuracoes"]["opcoes_ela_fez"] + ["Outro"]
            ela_fez = st.multiselect("Ela fez:", op_ela, [x for x in day_data.get("ela_fez", []) if x in op_ela], disabled=is_locked)
            novo_ela = st.text_input("Novo (Ela):") if "Outro" in ela_fez else ""
            ling_ela = st.multiselect("Linguagens dela:", LINGUAGENS_LISTA, day_data.get("ling_ela", []), disabled=is_locked)
            sexo = st.radio("Houve sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)

        st.divider()
        with st.expander("💬 Importar WhatsApp"):
            ws_raw = st.text_area("Cole a conversa do WhatsApp aqui:")
            if day_data.get("whatsapp_txt"):
                st.code(day_data["whatsapp_txt"])
        
        resumo = st.text_area("Resumo do dia:", day_data.get("resumo", ""), disabled=is_locked)
        
        if st.form_submit_button("💾 Salvar e Trancar") and not is_locked:
            f_eu = [i for i in eu_fiz if i != "Outro"]; f_ela = [i for i in ela_fez if i != "Outro"]
            if novo_eu and novo_eu not in db["configuracoes"]["opcoes_eu_fiz"]: db["configuracoes"]["opcoes_eu_fiz"].append(novo_eu); f_eu.append(novo_eu)
            if novo_ela and novo_ela not in db["configuracoes"]["opcoes_ela_fez"]: db["configuracoes"]["opcoes_ela_fez"].append(novo_ela); f_ela.append(novo_ela)

            ws_final = day_data.get("whatsapp_txt", "")
            if ws_raw:
                target = selected_date.strftime("%d/%m/%y")
                ws_final = "\n".join([line for line in ws_raw.split('\n') if target in line])

            db["registros"][date_str] = {
                "nota": nota, "eu_fiz": f_eu, "ela_fez": f_ela, "ling_eu": ling_eu, "ling_ela": ling_ela,
                "discussao": disc, "sexo": sexo == "Sim", "resumo": resumo,
                "whatsapp_txt": ws_final, "checks_acordos": checks_acordos_hoje, "locked": True
            }
            save_all(db); st.rerun()

# --- 2. PAINEL & GRIDS (COM UPLOAD DE FOTO) ---
elif menu == "📊 Painel & Grids":
    st.header("📊 Retrospectiva & Exportação")
    
    # Exportação PDF com Capa
    st.subheader("📥 Exportar Diário para PDF")
    meses_dict = {"01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril", "05": "Maio", "06": "Junho", 
                  "07": "Julho", "08": "Agosto", "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"}
    mes_sel = st.selectbox("Selecione o mês para exportar:", list(meses_dict.values()), key="sel_mes_pdf")
    cod_mes = [k for k, v in meses_dict.items() if v == mes_sel][0]

    uploaded_file = st.file_uploader("Escolha uma imagem para a capa (opcional):", type=["jpg", "jpeg", "png"])
    imagem_capa_bytes = None
    if uploaded_file is not None:
        imagem_capa_bytes = uploaded_file.read()
        st.image(uploaded_file, caption='Sua imagem de capa', width=200)
    
    if st.button("Gerar PDF do Mês com Capa"):
        dados_mes = {k: v for k, v in db["registros"].items() if k.split("-")[1] == cod_mes}
        if dados_mes:
            pdf_bytes_output = gerar_pdf_com_capa(dados_mes, mes_sel, imagem_capa_bytes)
            st.download_button(label="⬇️ Baixar PDF com Capa", data=pdf_bytes_output, file_name=f"Memorias_{mes_sel}_2026.pdf", mime="application/pdf")
        else:
            st.warning("Nenhum registro encontrado para este mês.")

    st.divider()
    def draw_grid(title, metric, color):
        st.write(f"#### {title}")
        days = pd.date_range("2026-01-01", "2026-12-31")
        grid = '<div style="display: flex; flex-wrap: wrap; gap: 3px; max-width: 900px; margin-bottom: 20px;">'
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
            grid += f'<div title="{ds}" style="width: 12px; height: 12px; background-color: {c}; border-radius: 2px;"></div>'
        st.markdown(grid + '</div>', unsafe_allow_html=True)
    draw_grid("⭐ Notas", "nota", "")
    draw_grid("🔥 Sexo", "sexo", "#e91e63")
    draw_grid("⚠️ Discussões", "discussao", "#f44336")

# --- DEMAIS ABAS ---
elif menu == "🤝 Acordos":
    st.header("🤝 Central de Acordos")
    with st.form("ac"):
        t = st.text_input("Acordo:"); c = st.text_input("Nome Curto:"); m = st.checkbox("Monitorar?")
        if st.form_submit_button("Firmar"):
            db["acordos_mestres"].append({"titulo":t, "nome_curto":c, "monitorar":m, "data":str(date.today())})
            save_all(db); st.rerun()
    for i, ac in enumerate(db["acordos_mestres"]):
        st.write(f"- {ac['nome_curto']}: {ac['titulo']}")
        if st.button("Excluir", key=f"d_a_{i}"): db["acordos_mestres"].pop(i); save_all(db); st.rerun()

elif menu == "💡 Insights da IA":
    st.header("💡 Análise do Especialista")
    if st.button("Gerar Insights"):
        recentes = list(db["registros"].items())[-5:]
        ctx = "".join([f"\nData: {d} | Nota: {i.get('nota')} | Resumo: {i.get('resumo')[:150]}" for d, i in recentes])
        if not ctx: st.warning("Sem registros!")
        else:
            try:
                resp = client_groq.chat.completions.create(model=db["config"]["modelo_ia"], messages=[{"role":"user","content":f"Analise: {ctx}"}], max_tokens=1000)
                st.markdown(resp.choices[0].message.content)
            except Exception as e: st.error(f"Erro: {e}")

elif menu == "⚙️ Configurações":
    st.header("⚙️ Configurações")
    db["config"]["modelo_ia"] = st.text_input("ID do Modelo Groq:", value=db["config"].get("modelo_ia", "llama-3.3-70b-versatile"))
    if st.button("Salvar Configs"): save_all(db); st.success("Salvo!")

elif menu == "⏳ Cápsula do Tempo":
    st.header("⏳ Memórias")
    for d in [30, 90]:
        alvo = (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")
        if alvo in db["registros"]: st.info(f"📅 Há {d} dias: {db['registros'][alvo].get('resumo')}")

elif menu == "📅 Eventos":
    st.header("📅 Calendário")
    with st.form("e"):
        dt = st.date_input("Data:"); n = st.text_input("Evento:")
        if st.form_submit_button("Agendar"): db["eventos"][dt.strftime("%Y-%m-%d")] = n; save_all(db); st.rerun()
