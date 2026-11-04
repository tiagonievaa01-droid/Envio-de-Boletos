import pandas as pd

def carregar_dados_clientes(caminho_csv):
    """
    Lê o ficheiro CSV de clientes e padroniza automaticamente:
    1. O cabeçalho (converte nomes das colunas para minúsculas e remove espaços extras).
    2. Nomes de colunas alternativos (mapeia 'num_pedido', 'cod_pedido', etc. para 'pedido').
    3. Os dados das células (remove espaços brancos antes e depois dos textos).
    """
    # 1. Lê o CSV detetando automaticamente o separador (vírgula ou ponto e vírgula)
    df = pd.read_csv(caminho_csv, encoding='utf-8-sig', sep=None, engine='python')
    
    # 2. Padronização dos NOMES DAS COLUNAS:
    # Remove espaços nas pontas e converte tudo para minúsculas
    # Exemplo: ' Pedido ' ou 'PEDIDO' passam a ser exatamente 'pedido'
    df.columns = df.columns.str.strip().str.lower()
    
    # 3. Mapeamento de sinonímia de colunas para garantir compatibilidade com o main.py
    mapeamento = {
        'cod_pedido': 'pedido',
        'num_pedido': 'pedido',
        'numero_pedido': 'pedido',
        'n_pedido': 'pedido',
        'nome_cliente': 'nome cliente',
        'cliente': 'nome cliente',
        'id_cliente': 'id cliente',
        'cod_cliente': 'id cliente'
    }
    df.rename(columns=mapeamento, inplace=True)
    
    # 4. Limpeza dos VALORES dentro das tabelas (remove espaços desnecessários nos dados)
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
        
    print(f"📋 Colunas prontas no CSV: {list(df.columns)}")
    
    return df