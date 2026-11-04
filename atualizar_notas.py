import pandas as pd
import os
import re

def limpar_numero_pedido(pedido_str):
    """Remove a palavra 'PED' caso exista e tira espaços vazios, deixando só a numeração."""
    return re.sub(r'(?i)PED', '', str(pedido_str)).strip()

def cruzar_dados_notas(caminho_csv, caminho_excel):
    print("🔄 Iniciando o cruzamento inteligente de dados...")
    
    try:
        # 1. Lê a base CSV com utf-8-sig para remover caracteres ocultos (BOM)
        df_csv = pd.read_csv(caminho_csv, sep=';', encoding='utf-8-sig')
        
        print(f"📄 Lendo o arquivo Excel: {caminho_excel}")
        df_excel = pd.read_excel(caminho_excel, engine='openpyxl')
        
        # Padroniza colunas (remove espaços nas pontas)
        df_csv.columns = df_csv.columns.astype(str).str.strip()
        df_excel.columns = df_excel.columns.astype(str).str.strip()

        # Localiza a coluna de pedido no CSV
        col_pedido_csv = None
        for col in df_csv.columns:
            if 'pedido' in col.lower():
                col_pedido_csv = col
                break
        
        if not col_pedido_csv:
            print(f"❌ Erro: Coluna de pedido não encontrada no CSV. Colunas encontradas: {list(df_csv.columns)}")
            return

        # Localiza a coluna de pedido no Excel ('Nº Pedido', 'N° Pedido', 'Pedido', etc.)
        col_pedido_excel = None
        for col in df_excel.columns:
            col_lower = col.lower().replace('°', 'º')
            if 'nº pedido' in col_lower or 'pedido' in col_lower:
                col_pedido_excel = col
                break
                
        if not col_pedido_excel:
            print(f"❌ Erro: Coluna de pedido não encontrada no Excel. Colunas encontradas: {list(df_excel.columns)}")
            return

        # Localiza a coluna de referência/nota fiscal no Excel ('Referência', 'Referencia', etc.)
        col_ref_excel = None
        for col in df_excel.columns:
            if 'referê' in col.lower() or 'referen' in col.lower() or 'refer' in col.lower() or 'nota' in col.lower():
                col_ref_excel = col
                break

        if not col_ref_excel:
            print(f"❌ Erro: Coluna de nota/referência não encontrada no Excel. Colunas encontradas: {list(df_excel.columns)}")
            return

        print(f"ℹ️ Mapeamento confirmado -> Pedido: '{col_pedido_excel}' | Nota: '{col_ref_excel}'")

        # 2. Prepara o Excel: Limpa o número do pedido e agrupa as notas
        df_excel['pedido_limpo'] = df_excel[col_pedido_excel].apply(limpar_numero_pedido)
        
        notas_por_pedido = df_excel.groupby('pedido_limpo')[col_ref_excel].apply(
            lambda x: ', '.join(x.dropna().astype(str).str.strip())
        ).to_dict()

        # Listas para o relatório final
        pedidos_com_nota = []
        pedidos_sem_nota = []

        # 3. Função para buscar notas e contabilizar sucessos/falhas
        def buscar_notas_para_pedidos(pedidos_str):
            if pd.isna(pedidos_str) or str(pedidos_str).strip() == '':
                return ""
            
            pedidos_lista = str(pedidos_str).split('-')
            notas_encontradas = []
            
            for p in pedidos_lista:
                p_limpo = limpar_numero_pedido(p)
                if not p_limpo:
                    continue
                    
                if p_limpo in notas_por_pedido and str(notas_por_pedido[p_limpo]).strip():
                    nota_val = str(notas_por_pedido[p_limpo]).strip()
                    notas_encontradas.append(nota_val)
                    pedidos_com_nota.append((p_limpo, nota_val))
                else:
                    pedidos_sem_nota.append(p_limpo)
            
            if notas_encontradas:
                todas_notas = ", ".join(notas_encontradas)
                lista_final = [n.strip() for n in todas_notas.split(',') if n.strip()]
                return ", ".join(lista_final)
            return ""

        # Identifica ou define a coluna 'nota fiscal' no CSV
        col_nota_csv = None
        for col in df_csv.columns:
            if 'nota' in col.lower() or 'fiscal' in col.lower():
                col_nota_csv = col
                break
        if not col_nota_csv:
            col_nota_csv = 'nota fiscal'

        # 4. Aplica a busca no CSV
        df_csv[col_nota_csv] = df_csv[col_pedido_csv].apply(buscar_notas_para_pedidos)

        # 5. Salva mantendo o padrão de ponto e vírgula (;) e codificação segura
        df_csv.to_csv(caminho_csv, sep=';', index=False, encoding='utf-8-sig')
        
        # 6. Exibe o resumo no terminal
        print("\n==================================================")
        print("📋 RESUMO DA ATUALIZAÇÃO DE NOTAS FISCAIS")
        print("==================================================")
        
        if pedidos_com_nota:
            print("\n✅ NOTAS LOCALIZADAS E INJETADAS:")
            for ped, nota in pedidos_com_nota:
                print(f"   • Pedido {ped} ➔ Nota(s): {nota}")
        
        if pedidos_sem_nota:
            print("\n⚠️ NOTAS NÃO ENCONTRADAS NO EXCEL (Preencher manualmente no CSV):")
            for ped in pedidos_sem_nota:
                print(f"   ❌ Pedido {ped} ➔ Nota não localizada em '{os.path.basename(caminho_excel)}'")
        else:
            print("\n🎉 Todos os pedidos do CSV tiveram suas notas encontradas!")
            
        print("==================================================\n")
        print("✅ Arquivo 'base_clientes.csv' atualizado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante o cruzamento: {e}")

if __name__ == "__main__":
    ARQUIVO_CSV = "Dados/base_clientes.csv"
    ARQUIVO_EXCEL = "Dados/Base.xlsx" if os.path.exists("Dados/Base.xlsx") else "Dados/base.xlsx"
    
    if not os.path.exists(ARQUIVO_CSV):
        print(f"⚠️ Arquivo CSV não encontrado: {ARQUIVO_CSV}")
    elif not os.path.exists(ARQUIVO_EXCEL):
        print(f"⚠️ Arquivo Excel não encontrado: {ARQUIVO_EXCEL}")
    else:
        cruzar_dados_notas(ARQUIVO_CSV, ARQUIVO_EXCEL)