import pandas as pd
import os
import glob

# --- CONFIGURAÇÕES ---
PASTA_PLANILHAS_PRONTAS = "planilhas_prontas"
PASTA_ARQUIVADAS = "planilhas_arquivadas"
# O nome do ficheiro é lido do .env pelo script principal, mas definimos um nome aqui
# para que este script possa arquivá-lo corretamente.
NOME_ARQUIVO_UNIFICADO = "planilha_cardapio_RPA.xlsx"
# ---------------------

def arquivar_planilha_antiga(caminho_unificado):
    """
    Verifica se a planilha unificada já existe. Se sim, move para a pasta
    de arquivadas com um ID sequencial.
    """
    if not os.path.exists(caminho_unificado):
        return # Não há nada para arquivar

    print(f"Encontrado ficheiro antigo: '{NOME_ARQUIVO_UNIFICADO}'. Arquivando...")
    
    # (A pasta já terá sido criada pela função 'main')
    
    # Encontra o próximo ID sequencial disponível
    id_seq = 1
    while True:
        nome_base_sem_ext = os.path.splitext(NOME_ARQUIVO_UNIFICADO)[0]
        nome_arquivado = f"{nome_base_sem_ext}_{id_seq}.xlsx"
        
        caminho_arquivado = os.path.join(PASTA_ARQUIVADAS, nome_arquivado)
        
        if not os.path.exists(caminho_arquivado):
            os.rename(caminho_unificado, caminho_arquivado)
            print(f"  Ficheiro antigo movido para: '{caminho_arquivado}'")
            break
        
        id_seq += 1 

def juntar_planilhas():
    """
    Junta todas as planilhas da pasta 'planilhas_prontas' em um único
    ficheiro Excel, limpando os dados e depois apagando os ficheiros originais.
    """
    
    # 1. Procura todos os ficheiros .xlsx na pasta de planilhas prontas
    arquivos_excel = glob.glob(os.path.join(PASTA_PLANILHAS_PRONTAS, "*.xlsx"))
    
    if not arquivos_excel:
        print(f"Nenhum ficheiro .xlsx encontrado em '{PASTA_PLANILHAS_PRONTAS}'.")
        return False 

    print(f"Encontrados {len(arquivos_excel)} ficheiros para unificar...")
    
    # 2. Lê cada Excel e guarda num "balde" (lista de DataFrames)
    lista_dataframes = []
    for f in arquivos_excel:
        try:
            df = pd.read_excel(f)
            lista_dataframes.append(df)
        except Exception as e:
            print(f"  Erro ao ler o ficheiro {f}: {e}. Pulando...")
            
    if not lista_dataframes:
        print("Nenhuma planilha pôde ser lida.")
        return False 
        
    # 3. Junta todos os DataFrames em um só
    df_unificado = pd.concat(lista_dataframes, ignore_index=True)
    
    # 4. Limpeza de Dados (Muito Importante!)
    df_unificado = df_unificado.dropna(subset=['Nome', 'Valor'])
    df_unificado['Descrição'] = df_unificado['Descrição'].fillna('')
    df_unificado = df_unificado.drop_duplicates(subset=['Nome'], keep='first')
    df_unificado = df_unificado[['Categoria', 'Nome', 'Valor', 'Descrição']]
    
    # 5. Salva a nova planilha unificada
    caminho_unificado = os.path.join(".", NOME_ARQUIVO_UNIFICADO)
    df_unificado.to_excel(caminho_unificado, index=False)
    
    print("\n--- Sucesso! ---")
    print(f"Total de {len(df_unificado)} itens únicos salvos em:")
    print(f"{caminho_unificado}")
    
    # 6. Apaga os ficheiros individuais que acabaram de ser juntados.
    print(f"\nLimpando {len(arquivos_excel)} planilhas individuais de '{PASTA_PLANILHAS_PRONTAS}'...")
    arquivos_removidos = 0
    for f in arquivos_excel:
        try:
            os.remove(f)
            arquivos_removidos += 1
        except Exception as e:
            print(f"  Aviso: Não foi possível remover o ficheiro {f}: {e}")
    
    print(f"  {arquivos_removidos} ficheiros removidos.")  
    
    return True # Retorna Verdadeiro para indicar que uma nova planilha foi criada

def main():
    print("Iniciando Robô Unificador de Planilhas...")
    
    # Garante que TODAS as pastas de trabalho do unificador existam
    print(f"Verificando pasta de planilhas prontas: '{PASTA_PLANILHAS_PRONTAS}'")
    os.makedirs(PASTA_PLANILHAS_PRONTAS, exist_ok=True)
    print(f"Verificando pasta de arquivadas: '{PASTA_ARQUIVADAS}'")
    os.makedirs(PASTA_ARQUIVADAS, exist_ok=True)
    
    caminho_unificado = os.path.join(".", NOME_ARQUIVO_UNIFICADO)
    
    # 1. Arquiva a planilha antiga, se existir
    arquivar_planilha_antiga(caminho_unificado)
    
    # 2. Cria a nova planilha unificada
    sucesso = juntar_planilhas()
    
    if sucesso:
        print("Processo de unificação concluído.")
    else:
        print("Processo de unificação concluído (nenhuma planilha nova para juntar).")


if __name__ == "__main__":
    main()