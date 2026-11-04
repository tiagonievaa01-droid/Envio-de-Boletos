import os
import glob
import shutil
import re
from datetime import datetime
from csv_handler import carregar_dados_clientes
from freshservice_client import criar_ticket_enviar_boleto

# Tenta importar a integracao do SharePoint
try:
    from sharepoint_handler import (
        sincronizar_boletos_e_csv_do_sharepoint,
        mover_boleto_no_sharepoint,
        CLIENT_ID
    )
    SHAREPOINT_HABILITADO = bool(CLIENT_ID)
except Exception:
    SHAREPOINT_HABILITADO = False

# Configuracoes
EMAIL_CONFIG_ID = 156000288508 
DIR_ENTRADA = "boletos_sap"
DIR_PROCESSADOS = "boletos_processados"
ARQUIVO_CSV = "Base de Dados/base_clientes.csv"

def limpar_numero_pedido(pedido_str):
    """Remove 'PED', 'PED.', 'PED ' e espaços vazios, deixando apenas a numeração."""
    return re.sub(r'(?i)PED[\.\s]*', '', str(pedido_str)).strip()

def gerar_relatorio_execucao(sucessos, falhas):
    """Gera um arquivo de texto com o resumo dos envios."""
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_relatorio = f"relatorio_envios_{data_hora}.txt"
    
    with open(nome_relatorio, "w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write(f"RELATÓRIO DE ENVIO DE BOLETOS - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("==================================================\n\n")
        
        f.write(f"TOTAL PROCESSADOS: {len(sucessos) + len(falhas)}\n")
        f.write(f"ENVIADOS COM SUCESSO: {len(sucessos)}\n")
        f.write(f"FALHAS/IGNORADOS: {len(falhas)}\n\n")
        
        if sucessos:
            f.write("--- SUCESSOS ---\n")
            for item in sucessos:
                f.write(f"[OK] Pedido: {item['pedido']} | Cliente: {item['cliente']} | Email: {item['email']} | Ticket: #{item['ticket_id']}\n")
            f.write("\n")
            
        if falhas:
            f.write("--- FALHAS E IGNORADOS ---\n")
            for item in falhas:
                f.write(f"[!] Pedido: {item['pedido']} | Motivo: {item['motivo']}\n")
                
    print(f"\n📄 Relatório detalhado gerado: {nome_relatorio}")

def processar_boletos():
    os.makedirs(DIR_PROCESSADOS, exist_ok=True)
    
    # 1. Sincroniza dados com o SharePoint se as credenciais existirem
    if SHAREPOINT_HABILITADO:
        try:
            print("☁️ Conectando ao SharePoint para sincronizar arquivos...")
            sincronizar_boletos_e_csv_do_sharepoint()
        except Exception as e:
            print(f"⚠️ Aviso SharePoint: {e}. Prosseguindo com arquivos locais.")
    else:
        print("💻 Modo Local: Processando arquivos das pastas internas.")

    # 2. Carrega a base CSV
    print("📖 Carregando base de clientes...")
    df_clientes = carregar_dados_clientes(ARQUIVO_CSV)
    
    # Cria uma coluna com o pedido limpo para comparação segura
    df_clientes['pedido_limpo'] = df_clientes['pedido'].astype(str).apply(limpar_numero_pedido)
    
    arquivos_pdf = glob.glob(os.path.join(DIR_ENTRADA, "*.pdf"))
    if not arquivos_pdf:
        print("ℹ️ Nenhum boleto encontrado para processar.")
        return

    print(f"🚀 Encontrados {len(arquivos_pdf)} boletos. Iniciando processamento...\n")
    
    sucessos = []
    falhas = []

    for filepath in arquivos_pdf:
        nome_arquivo = os.path.basename(filepath)
        pedido_arquivo = os.path.splitext(nome_arquivo)[0]
        pedido_limpo = limpar_numero_pedido(pedido_arquivo)
        
        # ==========================================
        # TRAVA DE SEGURANÇA CONTRA DUPLICIDADE
        # ==========================================
        caminho_destino = os.path.join(DIR_PROCESSADOS, nome_arquivo)
        if os.path.exists(caminho_destino):
            msg_duplicado = "Boleto já processado anteriormente (encontrado na pasta de processados)."
            print(f"⏩ Ignorado: {nome_arquivo} já foi enviado.")
            falhas.append({"pedido": pedido_arquivo, "motivo": msg_duplicado})
            
            # Remove o arquivo duplicado da pasta de entrada
            os.remove(filepath)
            continue
        # ==========================================
        
        # Busca flexível no CSV (compara ambos limpos sem 'PED' ou 'PED.')
        cliente_info = df_clientes[df_clientes['pedido_limpo'] == pedido_limpo]
        
        if cliente_info.empty:
            msg = f"Pedido '{pedido_arquivo}' não encontrado na base CSV."
            print(f"⚠️ {msg}")
            falhas.append({"pedido": pedido_arquivo, "motivo": msg})
            continue
            
        dados_cliente = cliente_info.iloc[0].to_dict()
        
        try:
            # Envia o ticket pelo Freshservice
            ticket_id = criar_ticket_enviar_boleto(filepath, dados_cliente, EMAIL_CONFIG_ID)
            
            # Move o arquivo localmente
            shutil.move(filepath, caminho_destino)
            
            # Se o SharePoint estiver ativo, move a copia remota tambem
            if SHAREPOINT_HABILITADO:
                try:
                    mover_boleto_no_sharepoint(nome_arquivo)
                except Exception as sp_err:
                    print(f"⚠️ Erro ao mover no SharePoint ({nome_arquivo}): {sp_err}")

            sucessos.append({
                "pedido": dados_cliente['pedido'],
                "cliente": dados_cliente['nome cliente'],
                "email": dados_cliente['email'],
                "ticket_id": ticket_id
            })
        except Exception as e:
            msg_erro = str(e)
            print(f"❌ Erro ao enviar pedido {pedido_arquivo}: {msg_erro}")
            falhas.append({"pedido": pedido_arquivo, "motivo": msg_erro})

    # Gera o relatório final de execução
    gerar_relatorio_execucao(sucessos, falhas)

if __name__ == "__main__":
    processar_boletos()