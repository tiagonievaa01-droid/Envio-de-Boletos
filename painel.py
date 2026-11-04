import streamlit as st
import pandas as pd
import time
import datetime
import os
import re

# IMPORTAÇÕES DA SUA AUTOMAÇÃO EXISTENTE
from freshservice_client import criar_ticket_enviar_boleto

# ==========================================
# CONFIGURAÇÕES DO SISTEMA E SEGURANÇA
# ==========================================
EMAIL_CONFIG_ID = 156000288508 
ARQUIVO_HISTORICO = "historico_envios.txt"
ARQUIVO_ACESSOS = "historico_acessos.txt"
DIR_TEMP = "temp_pdfs"

# SENHA UNIVERSAL DE ACESSO (Pode alterar aqui quando quiser)
SENHA_UNIVERSAL = "sin12345"

os.makedirs(DIR_TEMP, exist_ok=True)

# ==========================================
# FUNÇÕES DE SEGURANÇA, LOGS E LÓGICA
# ==========================================
def limpar_numero_pedido(pedido_str):
    return re.sub(r'(?i)PED[\.\s]*', '', str(pedido_str)).strip()

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return set()
    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
        return set(linha.strip().upper() for linha in f.readlines() if linha.strip())

def registrar_envio_no_historico(pedido):
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f"{pedido.strip().upper()}\n")

def registrar_acesso_usuario(usuario):
    """Regista no ficheiro de auditoria quem acedeu, data e hora."""
    data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(ARQUIVO_ACESSOS, "a", encoding="utf-8") as f:
        f.write(f"Usuário: {usuario} | Acesso em: {data_hora}\n")

# ==========================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==========================================
st.set_page_config(page_title="Painel de Envio - Corporate", page_icon="🏢", layout="wide")

# Inicializa o estado de sessão para o login
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""

# ==========================================
# TELA DE LOGIN (COM LABELS CLARAS E FÁCEIS DE LER)
# ==========================================
if not st.session_state["authenticated"]:
    st.markdown("""
        <style>
        .stApp {
            background-color: #f1f5f9;
        }
        .login-card {
            background-color: #ffffff;
            padding: 40px;
            border-radius: 12px;
            border-top: 4px solid #0284c7;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
            width: 100%;
        }
        /* Estilização para destacar os rótulos de input */
        label {
            font-weight: 600 !important;
            color: #1e293b !important;
            font-size: 0.95rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.3, 1])
    with col_l2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        if os.path.exists("logo.png"):
            c_img1, c_img2, c_img3 = st.columns([1, 2, 1])
            with c_img2:
                st.image("logo.png", width=120)
        
        st.markdown("<h2 style='text-align: center; color: #0f172a; margin-top: 15px; margin-bottom: 5px;'>Acesso Restrito</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.88rem; margin-bottom: 25px;'>Identifique-se para registo e insira a senha corporativa.</p>", unsafe_allow_html=True)
        
        with st.form("form_login"):
            # Labels bem explícitas por cima de cada caixa
            input_usuario = st.text_input("👤 Nome do Utilizador (Login)", placeholder="Digite o seu nome aqui...")
            input_senha = st.text_input("🔑 Senha Universal", type="password", placeholder="Digite a senha corporativa...")
            st.markdown("<br>", unsafe_allow_html=True)
            botao_entrar = st.form_submit_button("Entrar no Painel", use_container_width=True)
            
            if botao_entrar:
                if input_senha == SENHA_UNIVERSAL:
                    nome_final = input_usuario.strip() if input_usuario.strip() else "Utilizador Anónimo"
                    st.session_state["authenticated"] = True
                    st.session_state["usuario_logado"] = nome_final
                    registrar_acesso_usuario(nome_final)
                    st.rerun()
                else:
                    st.error("❌ Senha universal incorreta!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# ==========================================
# PAINEL PRINCIPAL (APÓS LOGIN BEM-SUCEDIDO)
# ==========================================
st.markdown("""
    <style>
    .stApp {
        background-color: #f1f5f9;
        color: #0f172a;
    }
    .sap-header-box {
        background-color: #0f172a;
        color: white;
        padding: 20px 28px;
        border-radius: 8px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .sap-title {
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: #ffffff;
        margin: 0;
    }
    .sap-subtitle {
        font-size: 0.88rem;
        color: #94a3b8;
        margin: 0;
    }
    .sap-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 8px;
        border-top: 4px solid #0284c7;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .stButton > button {
        background-color: #0284c7;
        color: white;
        border-radius: 4px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: background-color 0.2s;
    }
    .stButton > button:hover {
        background-color: #0369a1;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho corporativo com logótipo em destaque e info do utilizador logado
st.markdown('<div class="sap-header-box">', unsafe_allow_html=True)
h_col1, h_col2, h_col3 = st.columns([1.5, 6.5, 4])
with h_col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=125)
with h_col2:
    st.markdown("""
        <div style="padding-top: 8px;">
            <h1 class="sap-title">MÓDULO DE DISTRIBUIÇÃO DE COBRANÇAS</h1>
            <p class="sap-subtitle">Painel de Integração e Envio Automatizado via Freshdesk</p>
        </div>
    """, unsafe_allow_html=True)
with h_col3:
    st.markdown(f"""
        <div style="text-align: right; font-size: 0.82rem; color: #cbd5e1; padding-top: 5px;">
            Utilizador: <b>{st.session_state['usuario_logado']}</b><br>
            Ambiente: <b>Produção / Online</b> | Status: <b style='color: #4ade80;'>Conectado</b>
        </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Organização em duas colunas com blocos corporativos
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown('<div class="sap-card">', unsafe_allow_html=True)
    st.markdown("### 📊 1. Base de Dados de Clientes")
    st.markdown("<p style='color: #475569; font-size: 0.88rem;'>Selecione o ficheiro extrato/CSV contendo os dados cadastrais e pedidos.</p>", unsafe_allow_html=True)
    arquivo_csv = st.file_uploader("Carregar CSV", type=['csv'], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="sap-card">', unsafe_allow_html=True)
    st.markdown("### 📑 2. Repositório de Boletos")
    st.markdown("<p style='color: #475569; font-size: 0.88rem;'>Selecione os ficheiros PDF dos boletos faturados para processamento.</p>", unsafe_allow_html=True)
    arquivos_pdf = st.file_uploader("Carregar PDFs", type=['pdf'], accept_multiple_files=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

if arquivo_csv and arquivos_pdf:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_bt1, col_bt2, col_bt3 = st.columns([1, 2, 1])
    with col_bt2:
        executar_transacao = st.button("⚙️ EXECUTAR PROCESSAMENTO", type="primary", use_container_width=True)

    if executar_transacao:
        try:
            df = pd.read_csv(arquivo_csv, sep=None, engine='python')
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            col_pedido = next((c for c in df.columns if 'pedido' in c), None)
            
            if not col_pedido:
                st.error("❌ O CSV precisa conter uma coluna identificada como 'pedido'.")
            else:
                pedidos_ja_enviados = carregar_historico()
                
                pdf_dict = {}
                for pdf in arquivos_pdf:
                    nome_limpo_pdf = limpar_numero_pedido(pdf.name.upper().replace(".PDF", ""))
                    pdf_dict[nome_limpo_pdf] = pdf
                
                sucessos = []
                falhas = []
                ignorados = []
                
                total = len(df)
                progress_bar = st.progress(0)
                
                data_atual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                linhas_relatorio = [
                    "==================================================",
                    f"RELATÓRIO DE EXECUÇÃO DE BOLETOS - {data_atual}",
                    f"EXECUTADO POR: {st.session_state['usuario_logado']}",
                    "==================================================\n"
                ]
                
                with st.expander("📋 Log de Execução em Tempo Real (Transações)", expanded=True):
                    for index, row in df.iterrows():
                        pedido_bruto = str(row[col_pedido])
                        pedido_limpo = limpar_numero_pedido(pedido_bruto).upper()
                        
                        dados_cliente = row.to_dict()
                        nome_cliente = dados_cliente.get('nome cliente', dados_cliente.get('cliente', 'Cliente'))
                        email_cliente = dados_cliente.get('email', '')
                        
                        dados_cliente['pedido'] = pedido_limpo
                        dados_cliente['Pedido'] = pedido_limpo
                        dados_cliente['PEDIDO'] = pedido_limpo
                        
                        if pedido_limpo in pedidos_ja_enviados:
                            msg_duplicado = "Processo bloqueado: Pedido já consta no histórico de envios."
                            st.warning(f"⚠️ [BLOQUEADO] Pedido {pedido_limpo} ({nome_cliente}) - Registo duplicado detetado.")
                            ignorados.append({"pedido": pedido_limpo, "motivo": msg_duplicado})
                            progress_bar.progress((index + 1) / total)
                            continue
                        
                        if pedido_limpo in pdf_dict:
                            pdf_file = pdf_dict[pedido_limpo]
                            
                            filepath = os.path.join(DIR_TEMP, pdf_file.name)
                            with open(filepath, "wb") as f:
                                f.write(pdf_file.getvalue())
                                
                            try:
                                ticket_id = criar_ticket_enviar_boleto(filepath, dados_cliente, EMAIL_CONFIG_ID)
                                
                                st.success(f"✔ [SUCESSO] Ticket #{ticket_id} gerado para {nome_cliente} (Pedido: {pedido_limpo})")
                                sucessos.append({
                                    "pedido": pedido_limpo,
                                    "cliente": nome_cliente,
                                    "email": email_cliente,
                                    "ticket_id": ticket_id
                                })
                                
                                registrar_envio_no_historico(pedido_limpo)
                                pedidos_ja_enviados.add(pedido_limpo)
                                
                            except Exception as e:
                                msg_erro = str(e)
                                st.error(f"❌ [ERRO] Falha no pedido {pedido_limpo}: {msg_erro}")
                                falhas.append({"pedido": pedido_limpo, "motivo": msg_erro})
                                
                            finally:
                                if os.path.exists(filepath):
                                    os.remove(filepath)
                                    
                        else:
                            msg_falha = "PDF não localizado no repositório carregado."
                            st.error(f"❌ [FALHA] Documento não encontrado para {nome_cliente} (Buscado: '{pedido_limpo}')")
                            falhas.append({"pedido": pedido_limpo, "motivo": msg_falha})
                            
                        progress_bar.progress((index + 1) / total)
                
                st.info(f"📊 Resumo do Lote: {len(sucessos)} processados com sucesso | {len(ignorados)} bloqueados (duplicados) | {len(falhas)} ocorrências.")
                
                linhas_relatorio.append(f"TOTAL PROCESSADOS: {len(sucessos) + len(falhas) + len(ignorados)}")
                linhas_relatorio.append(f"ENVIADOS COM SUCESSO: {len(sucessos)}")
                linhas_relatorio.append(f"FALHAS/IGNORADOS: {len(falhas) + len(ignorados)}\n")
                
                if sucessos:
                    linhas_relatorio.append("--- REGISTOS COM SUCESSO ---")
                    for item in sucessos:
                        linhas_relatorio.append(f"[OK] Pedido: {item['pedido']} | Cliente: {item['cliente']} | Email: {item['email']} | Ticket: #{item.get('ticket_id', 'Gerado')}")
                    linhas_relatorio.append("")
                    
                if falhas or ignorados:
                    linhas_relatorio.append("--- OCORRÊNCIAS E BLOQUEIOS ---")
                    for item in falhas + ignorados:
                        linhas_relatorio.append(f"[!] Pedido: {item['pedido']} | Motivo: {item['motivo']}")
                
                texto_final_txt = "\n".join(linhas_relatorio)
                
                nome_relatorio = f"relatorio_execucao_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
                st.download_button(
                    label="📥 Descarregar Relatório de Auditoria (.txt)",
                    data=texto_final_txt,
                    file_name=nome_relatorio,
                    mime="text/plain",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"Erro crítico na execução da transação: {e}")