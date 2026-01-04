import streamlit as st
import pandas as pd
import json
from datetime import datetime
from github import Github
from groq import Groq

# Configuração da página
st.set_page_config(page_title="Diário de Relacionamento 2026", layout="wide")

# Inicialização de APIs via Secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

client_groq = Groq(api_key=GROQ_API_KEY)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)

# Funções de Persistência no GitHub
def load_data():
    try:
        contents = repo.get_contents("data_2026.json")
        return json.loads(contents.decoded_content.decode())
    except:
        return {}

def save_data(new_data):
    file_path = "data_2026.json"
    data = load_data()
    date_str = datetime.now().strftime("%Y-%m-%d")
    data[date_str] = new_data
    
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, f"Update {date_str}", json_data, contents.sha)
    except:
        repo.create_file(file_path, f"Initial commit {date_str}", json_data)

# Interface Principal
st.title("❤️ Diário de Relacionamento 2026")
st.subheader("Katheryn & Jhonata")

menu = ["Registrar Dia", "Visualizar Ano", "Análise do Especialista (IA)"]
choice = st.sidebar.selectbox("Menu", menu)

data_history = load_data()

if choice == "Registrar Dia":
    st.header(f"Registro: {datetime.now().strftime('%d/%m/%Y')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### O que eu fiz")
        eu_fiz = st.multiselect("Selecione:", ["Flores", "Elogios", "Ajuda em casa", "Presente", "Ouvir", "Cozinhar"])
        
        st.write("### O que recebi (Katheryn)")
        recebi = st.multiselect("Ela fez por mim:", ["Carinho", "Apoio emocional", "Presente", "Cuidado", "Elogio"])

    with col2:
        st.write("### O que fizemos juntos")
        fizemos = st.multiselect("Atividades:", ["Jantar fora", "Filme/Série", "Passeio", "Conversa profunda", "Gentilezas"])
        
        # Lógica de Discussão
        teve_discussao = st.checkbox("Houve alguma discussão hoje?")
        motivo_discussao = ""
        if teve_discussao:
            # Busca motivos recorrentes no histórico
            motivos_anteriores = list(set([v.get("motivo_disc", "") for v in data_history.values() if v.get("motivo_disc")]))
            motivo_discussao = st.selectbox("Motivo da discussão:", ["Selecione..."] + motivos_anteriores + ["Outro..."])
            if motivo_discussao == "Outro...":
                motivo_discussao = st.text_input("Descreva o novo motivo:")

        # Lógica de Sexo
        teve_sexo = st.radio("Houve sexo hoje?", ["Sim", "Não"], index=1)
        motivo_nao_sexo = ""
        if teve_sexo == "Não":
            motivos_sexo_ant = list(set([v.get("motivo_nao_sexo", "") for v in data_history.values() if v.get("motivo_nao_sexo")]))
            motivo_nao_sexo = st.selectbox("Motivo da ausência:", ["Selecione..."] + motivos_sexo_ant + ["Cansaço", "Falta de tempo", "Saúde", "Outro..."])
            if motivo_nao_sexo == "Outro...":
                motivo_nao_sexo = st.text_input("Descreva o motivo:")

    st.divider()
    acordos = st.text_area("Novos combinados (A partir de hoje devo...):")
    resumo = st.text_area("Resumo do dia (Breve descrição):")

    if st.button("Salvar Registro"):
        payload = {
            "eu_fiz": eu_fiz,
            "recebi": recebi,
            "fizemos": fizemos,
            "discussao": teve_discussao,
            "motivo_disc": motivo_discussao,
            "sexo": teve_sexo == "Sim",
            "motivo_nao_sexo": motivo_nao_sexo,
            "acordos": acordos,
            "resumo": resumo
        }
        save_data(payload)
        st.success("Dia registrado com sucesso no GitHub!")

elif choice == "Visualizar Ano":
    st.header("📅 Panorama 2026")
    if data_history:
        # Transformar dados para exibição (Grid/Tabela)
        df = pd.DataFrame.from_dict(data_history, orient='index')
        st.write("### Histórico de Registros")
        st.dataframe(df)
        
        # Exemplo de Grid Simples (Pode ser expandido com Plotly para o estilo GitHub)
        st.write("### Dias com Discussão vs Sexo")
        chart_data = df[['discussao', 'sexo']].astype(int)
        st.bar_chart(chart_data)
    else:
        st.info("Nenhum dado registrado ainda.")

elif choice == "Análise do Especialista (IA)":
    st.header("🧠 Análise do Especialista em Relacionamentos")
    
    if len(data_history) < 3:
        st.warning("Registre pelo menos 3 dias para uma análise consistente.")
    else:
        # Prepara o contexto para o Groq
        contexto = str(list(data_history.items())[-10:]) # Últimos 10 dias
        
        prompt = f"""
        Você é um especialista em terapia de casais. Analise os seguintes registros de um relacionamento em 2026 entre Jhonata e Katheryn:
        {contexto}
        
        Com base nos motivos de discussões, frequência de sexo e atos de carinho, dê:
        1. Um resumo da saúde atual do relacionamento.
        2. Identifique padrões de conflito recorrentes.
        3. Dê 3 dicas práticas para Jhonata tornar o relacionamento mais saudável e feliz.
        """
        
        if st.button("Gerar Análise"):
            with st.spinner("O especialista está analisando seus dados..."):
                completion = client_groq.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                st.markdown(completion.choices[0].message.content)
