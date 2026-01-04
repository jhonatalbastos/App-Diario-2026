import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from github import Github, Auth
from groq import Groq

# Configuração da página - Versão 3.5
st.set_page_config(page_title="Love Planner 3.5", layout="wide", page_icon="❤️")

# --- CONFIGURAÇÃO DE SEGURANÇA (SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
except:
    st.error("Erro nos Secrets. Verifique as chaves no Streamlit Cloud.")
    st.stop()

# Inicialização de APIs
client_groq = Groq(api_key=GROQ_API_KEY)
auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)
repo = g.get_repo(GITHUB_REPO)

# --- FUNÇÕES DE PERSISTÊNCIA ---
def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        data = json.loads(contents.decoded_content.decode())
        # Garantir estrutura
        if "registros" not in data: data["registros"] = {}
        if "eventos" not in data: data["eventos"] = {}
        if "acordos_mestres" not in data: data["acordos_mestres"] = []
        if "configuracoes" not in data: data["configuracoes"] = {
            "opcoes_eu_fiz": ["Flores", "Elogios", "Ajuda", "Ouvir", "Cozinhar"],
            "opcoes_ela_fez": ["Carinho", "Apoio", "Cuidado", "Beijos"]
        }
        return data
    except:
        return {
            "registros": {}, "eventos": {}, "acordos_mestres": [],
            "configuracoes": {
                "opcoes_eu_fiz": ["Flores", "Elogios", "Ajuda", "Ouvir", "Cozinhar"],
                "opcoes_ela_fez": ["Carinho", "Apoio", "Cuidado", "Beijos"]
            }
        }

def save_all(data):
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    file_path = "data_2026.json"
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, f"Sincronização {datetime.now()}", json_data, contents.sha)
    except:
        repo.create_file(file_path, "Início do Banco de Dados", json_data)

db = load_data()

# --- NAVEGAÇÃO ---
st.sidebar.title("❤️ Love Planner 2026")
menu = st.sidebar.radio("Navegação:", ["📝 Diário", "🤝 Central de Acordos", "📊 Painel & Grids", "⏳ Cápsula do Tempo", "📅 Eventos", "⚙️ Configurações"])

# --- 1. ABA DIÁRIO (REGISTRO + WHATSAPP) ---
if menu == "📝 Diário":
    st.header("📝 Registro do Dia")
    selected_date = st.date_input("Selecione a data:", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = db["registros"].get(date_str, {})
    is_locked = day_data.get("locked", False)

    if is_locked:
        st.warning(f"🔒 Este registro está trancado.")
        if st.button("🔓 Destrancar"):
            db["registros"][date_str]["locked"] = False
            save_all(db); st.rerun()

    with st.form("form_diario"):
        nota = st.select_slider("Nota do Dia (Semáforo):", options=range(1, 11), value=day_data.get("nota", 7), disabled=is_locked)
        
        # Monitoramento de Acordos Ativos
        acordos_check = [a for a in db["acordos_mestres"] if a.get("monitorar_diariamente")]
        checks_preenchidos = {}
        if acordos_check:
            st.subheader("🎯 Acompanhamento de Acordos")
            cols = st.columns(len(acordos_check))
            for i, ac in enumerate(acordos_check):
                label = ac['nome_curto']
                checks_preenchidos[label] = cols[i].checkbox(label, value=day_data.get("acordos_vivos", {}).get(label, False), disabled=is_locked)

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            opcoes_eu = db["configuracoes"]["opcoes_eu_fiz"] + ["Outro"]
            eu_fiz = st.multiselect("Eu fiz para ela:", opcoes_eu, [x for x in day_data.get("eu_fiz", []) if x in opcoes_eu], disabled=is_locked)
            nova_opcao = st.text_input("Se marcou 'Outro', digite aqui:", disabled=is_locked) if "Outro" in eu_fiz else ""
            disc = st.checkbox("Houve discussão?", day_data.get("discussao", False), disabled=is_locked)
        with col2:
            recebi = st.multiselect("Ela fez para mim:", db["configuracoes"]["opcoes_ela_fez"], day_data.get("recebi", []), disabled=is_locked)
            sexo = st.radio("Houve sexo?", ["Sim", "Não"], index=0 if day_data.get("sexo", True) else 1, disabled=is_locked)

        st.subheader("💬 Contexto (WhatsApp)")
        ws_input = st.text_area("Cole trechos de conversas do WhatsApp (opcional):", value=day_data.get("whatsapp_txt", ""), height=100, disabled=is_locked)
        
        resumo = st.text_area("Resumo do dia:", value=day_data.get("resumo", ""), disabled=is_locked)

        if not is_locked and st.form_submit_button("💾 Salvar e Trancar"):
            # Lógica 'Outro'
            final_eu_fiz = [i for i in eu_fiz if i != "Outro"]
            if nova_opcao and nova_opcao not in db["configuracoes"]["opcoes_eu_fiz"]:
                db["configuracoes"]["opcoes_eu_fiz"].append(nova_opcao)
                final_eu_fiz.append(nova_opcao)

            db["registros"][date_str] = {
                "nota": nota, "eu_fiz": final_eu_fiz, "recebi": recebi,
                "discussao": disc, "sexo": sexo == "Sim", "resumo": resumo,
                "whatsapp_txt": ws_input, "acordos_vivos": checks_preenchidos, "locked": True
            }
            save_all(db); st.success("Salvo!"); st.rerun()

# --- 2. CENTRAL DE ACORDOS ---
elif menu == "🤝 Central de Acordos":
    st.header("🤝 Nossos Acordos e Combinados")
    with st.form("novo_acordo"):
        tit = st.text_input("Descrição do Acordo:")
        curto = st.text_input("Nome curto (para o Checklist diário):")
        monitorar = st.checkbox("Deseja monitorar este acordo diariamente no Diário?")
        if st.form_submit_button("Firmar Acordo"):
            db["acordos_mestres"].append({"titulo": tit, "nome_curto": curto, "monitorar_diariamente": monitorar, "data": str(date.today())})
            save_all(db); st.success("Acordo registrado!"); st.rerun()

    st.subheader("Acordos Firmados")
    for i, ac in enumerate(db["acordos_mestres"]):
        st.write(f"- **{ac['nome_curto']}**: {ac['titulo']} (Início: {ac['data']})")
        if st.button("Excluir", key=f"del_ac_{i}"):
            db["acordos_mestres"].pop(i)
            save_all(db); st.rerun()

# --- 3. PAINEL & GRIDS ---
elif menu == "📊 Painel & Grids":
    st.header("📊 Retrospectiva 2026")
    def draw_grid(title, key, c_on, c_off="#ebedf0"):
        st.write(f"### {title}")
        days = pd.date_range("2026-01-01", "2026-12-31")
        grid_html = '<div style="display: flex; flex-wrap: wrap; gap: 3px; max-width: 900px;">'
        for d in days:
            ds = d.strftime("%Y-%m-%d")
            reg = db["registros"].get(ds, {})
            color = c_off
            if ds in db["registros"]:
                if key == "nota":
                    n = reg.get("nota", 0)
                    color = "#216e39" if n >= 8 else "#f9d71c" if n >= 5 else "#f44336"
                elif key == "sexo": color = "#e91e63" if reg.get("sexo") else c_off
                elif key == "disc": color = "#f44336" if reg.get("discussao") else c_off
                elif key == "rir": color = "#2196f3" if reg.get("q2") else c_off
            grid_html += f'<div title="{ds}" style="width: 12px; height: 12px; background-color: {color}; border-radius: 2px;"></div>'
        st.markdown(grid_html + '</div>', unsafe_allow_html=True)

    draw_grid("⭐ Nota do Dia (Semáforo)", "nota", "")
    draw_grid("🔥 Frequência Sexual", "sexo", "")
    draw_grid("⚠️ Discussões", "disc", "")

# --- 4. CÁPSULA DO TEMPO ---
elif menu == "⏳ Cápsula do Tempo":
    st.header("⏳ Memórias de Outros Tempos")
    col_a, col_b = st.columns(2)
    for i, label in enumerate(["Há 30 dias", "Há 90 dias"]):
        d_alvo = date.today() - timedelta(days=30 if i==0 else 90)
        d_str = d_alvo.strftime("%Y-%m-%d")
        with col_a if i==0 else col_b:
            st.subheader(label)
            if d_str in db["registros"]:
                st.info(f"Em {d_alvo.strftime('%d/%m/%Y')}: {db['registros'][d_str].get('resumo')}")
            else: st.write("Sem registros nesta data.")

# --- 5. DEMAIS FUNÇÕES ---
elif menu == "📅 Eventos":
    st.header("📅 Eventos e Planejamento")
    with st.form("ev"):
        dt = st.date_input("Data do Evento:")
        tit = st.text_input("O que vamos fazer?")
        if st.form_submit_button("Agendar"):
            db["eventos"][dt.strftime("%Y-%m-%d")] = tit
            save_all(db); st.success("Agendado!")

elif menu == "💡 Insights da IA":
    st.header("💡 Insights do Especialista")
    if st.button("Analisar Semana"):
        ctx = str(list(db["registros"].items())[-7:])
        prompt = f"Analise estes dados e as conversas de WhatsApp (se houver) para dar dicas de saúde emocional para o casal Jhonata e Katheryn: {ctx}"
        res = client_groq.chat.completions.create(model="llama3-70b-8192", messages=[{"role":"user", "content":prompt}])
        st.write(res.choices[0].message.content)

elif menu == "⚙️ Configurações":
    st.header("⚙️ Gerenciar Sistema")
    # Lógica de descarte de opções multiselect (conforme v2.3)
    if st.button("Limpar Opções 'Eu Fiz'"):
        db["configuracoes"]["opcoes_eu_fiz"] = ["Flores", "Elogios", "Ajuda"]
        save_all(db); st.success("Resetado!")
