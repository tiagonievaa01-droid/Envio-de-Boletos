import os
from datetime import datetime

def registrar_log(status, pedido, email="N/A", detalhes=""):
    """
    Escreve uma linha de registo no ficheiro relatorio_envios.txt.
    status: 'SUCESSO' ou 'FALHA'
    """
    ficheiro_log = "relatorio_envios.txt"
    
    # Obtém a data e hora exatas no formato DD/MM/AAAA HH:MM:SS
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Monta a linha que será escrita no ficheiro
    linha_log = f"[{agora}] {status} | Pedido: {pedido} | E-mail: {email} | Detalhes: {detalhes}\n"
    
    # Abre o ficheiro em modo 'a' (append) para adicionar no final sem apagar o que já existe
    with open(ficheiro_log, "a", encoding="utf-8") as f:
        f.write(linha_log)