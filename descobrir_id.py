import os
import requests
from dotenv import load_dotenv

load_dotenv()
FS_DOMAIN = os.getenv("FRESHSERVICE_DOMAIN")
FS_API_KEY = os.getenv("FRESHSERVICE_API_KEY")

url = f"https://{FS_DOMAIN}.freshdesk.com/api/v2/email_configs"

print("🔍 A procurar IDs de e-mail na sua conta Freshdesk...")
response = requests.get(url, auth=(FS_API_KEY, "X"))

if response.status_code == 200:
    emails = response.json()
    print("\n✅ E-mails encontrados:")
    for email in emails:
        endereco = email.get('reply_email', 'E-mail desconhecido')
        id_email = email.get('id', 'Sem ID')
        print(f"E-mail: {endereco} ---> email_config_id: {id_email}")
else:
    print(f"\n❌ Acesso negado pela API (Erro {response.status_code}).")
    print("A sua chave API também não tem permissão para ler os e-mails.")