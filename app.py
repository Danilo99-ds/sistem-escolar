import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection
import traceback

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Controle Prof. Danilo", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LISTA DE ALUNOS (Você pode mudar isso depois) ---
# Aqui simulamos uma turma. No futuro, isso pode vir de outra aba da planilha.
ALUNOS_DB = [
    {"Nome": "Ana Clara", "Turma": "6A"},
    {"Nome": "Bernardo Silva", "Turma": "6A"},
    {"Nome": "Carlos Eduardo", "Turma": "6A"},
    {"Nome": "Daniela Souza", "Turma": "6A"},
    {"Nome": "Enzo Gabriel", "Turma": "6A"},
]
df_alunos = pd.DataFrame(ALUNOS_DB)

# --- FUNÇÕES AUXILIARES ---
def carregar_dados():
    # Lê a planilha para garantir que temos o histórico
    return conn.read(ttl=0)

def salvar_dados(novo_dataframe):
    try:
        data_existente = carregar_dados()
        df_final = pd.concat([data_existente, novo_dataframe], ignore_index=True)
        conn.update(data=df_final)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        # Isso vai imprimir o erro real no terminal do VS Code:
        print("\n\n--- ERRO DETALHADO ---")
        print(e)
        traceback.print_exc()
        print("----------------------\n")
        return False

# --- INTERFACE DO SISTEMA ---
def main():
    st.title("👨‍🏫 Controle de Atividades")

    # Inicializa variáveis de estado (Memória do App enquanto navega)
    if 'passo' not in st.session_state:
        st.session_state.passo = 1
    if 'info_aula' not in st.session_state:
        st.session_state.info_aula = {}

    # ---------------- PASSO 1: DADOS DA AULA ----------------
    if st.session_state.passo == 1:
        st.subheader("1. Configuração da Atividade")
        
        with st.form("form_aula"):
            col1, col2 = st.columns(2)
            materia = col1.selectbox("Matéria", ["Matemática", "Geometria", "Estatística"])
            tipo = col2.radio("Onde foi a atividade?", ["Caderno", "Livro", "Folha Avulsa"])
            
            paginas = st.text_input("Páginas / Detalhes", placeholder="Ex: Pág 42 a 45")
            data_coleta = st.date_input("Data da Coleta", date.today())
            
            submitted = st.form_submit_button("Avançar para Chamada >>")
            
            if submitted:
                # Guarda os dados na memória e vai pro passo 2
                st.session_state.info_aula = {
                    "materia": materia,
                    "origem": tipo,
                    "paginas": paginas,
                    "data_coleta": data_coleta
                }
                st.session_state.passo = 2
                st.rerun()

    # ---------------- PASSO 2: COLETA DOS ALUNOS ----------------
    elif st.session_state.passo == 2:
        info = st.session_state.info_aula
        st.subheader(f"2. Coleta: {info['turma'] if 'turma' in info else '6A'}")
        st.markdown(f"**Matéria:** {info['materia']} | **Ref:** {info['origem']} ({info['paginas']})")

        # Prepara tabela para edição
        df_editor = df_alunos.copy()
        df_editor["Status"] = "Realizada" # Define padrão para agilizar

        st.info("Selecione o status de quem não fez ou faltou:")
        
        # Tabela Editável
        tabela_editada = st.data_editor(
            df_editor,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Situação",
                    options=["Realizada", "Incompleta", "Não Realizada", "Faltou"],
                    required=True,
                    width="medium"
                )
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed" # Impede adicionar linhas novas manuais
        )

        col_b1, col_b2 = st.columns([1, 2])
        
        if col_b1.button("<< Voltar"):
            st.session_state.passo = 1
            st.rerun()
            
        if col_b2.button("💾 FINALIZAR E SALVAR", type="primary"):
            with st.spinner("Enviando para a nuvem..."):
                # Prepara os dados para o formato do Banco
                pacote_salvamento = tabela_editada.copy()
                pacote_salvamento["data_coleta"] = info["data_coleta"]
                pacote_salvamento["materia"] = info["materia"]
                pacote_salvamento["origem"] = info["origem"]
                pacote_salvamento["paginas"] = info["paginas"]
                
                # Renomeia para bater com o Google Sheets
                pacote_salvamento = pacote_salvamento.rename(columns={
                    "Nome": "aluno", 
                    "Turma": "turma", 
                    "Status": "status"
                })
                
                # Seleciona apenas as colunas certas na ordem certa
                ordem_colunas = ["data_coleta", "materia", "origem", "paginas", "aluno", "turma", "status"]
                pacote_salvamento = pacote_salvamento[ordem_colunas]
                
                # Salva
                sucesso = salvar_dados(pacote_salvamento)
                
                if sucesso:
                    st.success("Dados salvos com sucesso!")
                    st.balloons()
                    # Botão para recomeçar
                    if st.button("Nova Coleta"):
                        st.session_state.passo = 1
                        st.rerun()

if __name__ == "__main__":
    main()