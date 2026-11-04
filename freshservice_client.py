import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()
FS_DOMAIN = os.getenv("FRESHSERVICE_DOMAIN")
FS_API_KEY = os.getenv("FRESHSERVICE_API_KEY")

# Puxa o ID de forma segura do .env (com fallback para o ID padrão caso o .env não seja lido)
EMAIL_CONFIG_ID_DEFAULT = os.getenv("EMAIL_CONFIG_ID", 156000288508)

def validar_email(email):
    """Verifica se o formato do e-mail é válido antes do envio."""
    padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(padrao, str(email).strip()) is not None

def criar_ticket_enviar_boleto(filepath, dados_cliente, email_config_id=EMAIL_CONFIG_ID_DEFAULT):
    email_destinatario = str(dados_cliente['email']).strip()
    
    # Validação de formato de e-mail
    if not validar_email(email_destinatario):
        raise ValueError(f"E-mail inválido ou mal formatado: '{email_destinatario}'")

    url = f"https://{FS_DOMAIN}.freshdesk.com/api/v2/tickets/outbound_email"
    
    # Captura os dados básicos cruzando com as colunas minúsculas do CSV
    id_cliente = dados_cliente.get('id cliente', '')
    nome_cliente = dados_cliente.get('nome cliente', '')
    pedido_raw = str(dados_cliente.get('pedido', ''))
    
    # ==========================================
    # FORMATA OS PEDIDOS COM HÍFEN
    # ==========================================
    # Troca possíveis vírgulas por hífen e garante o espaçamento " - "
    pedido_com_hifen = pedido_raw.replace(',', '-')
    pedidos_lista = [p.strip() for p in pedido_com_hifen.split('-') if p.strip()]
    pedido_exibicao = " - ".join(pedidos_lista)
    
    # ==========================================
    # CAPTURA E FORMATA AS NOTAS FISCAIS
    # ==========================================
    notas = dados_cliente.get('nota fiscal', dados_cliente.get('nf', dados_cliente.get('nota', '')))
    notas_str = str(notas).strip().lower()
    
    # Ajusta o texto: quebra as notas por linha (substitui a vírgula por <br>)
    if notas and notas_str not in ('nan', 'none', ''):
        notas_lista = [n.strip() for n in str(notas).split(',') if n.strip()]
        notas_html = "<br>".join(notas_lista) # Adiciona a quebra de linha HTML entre as notas
        texto_notas = f"de acordo com as notas fiscais já faturadas e entregues. Nota:<br><b>{notas_html}</b>"
    else:
        texto_notas = "de acordo com as notas fiscais já faturadas e entregues."
    # ==========================================
    
    assunto = f"Envio de Boletos mistos aos clientes - {id_cliente}"
    
    texto_padrao = f"""
    Prezado cliente, {nome_cliente}<br>
    Segue anexo os boletos relacionados ao(s) pedido(s) <b>{pedido_exibicao}</b>, {texto_notas}<br><br>
    Se tiver alguma dúvida, estamos à disposição.<br>
    Entre em contato pelo WhatsApp (11) 95083-8179 ou, se preferir, ligue para 0800 770 8290.<br>
    #SorrisosQueGeramSorrisos<br>
    S.I.N. Implant System
    """
    
    data = {
        "email": email_destinatario,
        "cc_emails[]": "negociacao@sinimplantsystem.com",
        "subject": assunto,
        "description": texto_padrao,
        "status": 5,   # Fechado
        "priority": 1, # Baixa
        "source": 10,  # Outbound Email
        "type": "Envio de Boletos",
        "custom_fields[cf_categoria]": "Atendimento",
        "custom_fields[cf_subcategoria]": "Envio de Boletos",
        "email_config_id": int(email_config_id)
    }
    
    nome_arquivo_anexo = f"{nome_cliente}.pdf" 
    
    with open(filepath, 'rb') as f:
        files = [
            ('attachments[]', (nome_arquivo_anexo, f, 'application/pdf'))
        ]
        
        response = requests.post(url, auth=(FS_API_KEY, "X"), data=data, files=files)
        
        if response.status_code not in (200, 201):
            raise Exception(f"Falha na API ({response.status_code}): {response.text}")
            
        res_json = response.json()
        ticket_id = res_json.get("id", "Desconhecido")
        
        print(f"✅ Boleto enviado para {email_destinatario} | Ticket Freshdesk #{ticket_id}")
        return ticket_id