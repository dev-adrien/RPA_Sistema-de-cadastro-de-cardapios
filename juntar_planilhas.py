import pandas as pd
import os
import glob

# --- CONFIGURAÇÕES ---
PASTA_PLANILHAS_PRONTAS = "planilhas_prontas"
PASTA_ARQUIVADAS = "planilhas_arquivadas"
NOME_ARQUIVO_UNIFICADO = "planilha_cardapio_RPA.xlsx"
# ---------------------

def arquivar_planilha_antiga(caminho_unificado):
    """
    Verifica se a planilha unificada já existe. Se sim, move para a pasta
    de arquivadas com um ID sequencial.
    """
    if not os.path.exists(caminho_unificado):
        return # Não há nada para arquivar

    print(f"Encontrado arquivo antigo: '{NOME_ARQUIVO_UNIFICADO}'. Arquivando...")
    
    # (A pasta já terá sido criada pela função 'main')
    
    # Encontra o próximo ID sequencial disponível
    id_seq = 1
    while True:
        # Tenta nomes como "cardapio_unificado_1.xlsx", "cardapio_unificado_2.xlsx", ...
        nome_base_sem_ext = os.path.splitext(NOME_ARQUIVO_UNIFICADO)[0]
        nome_arquivado = f"{nome_base_sem_ext}_{id_seq}.xlsx"
        
        caminho_arquivado = os.path.join(PASTA_ARQUIVADAS, nome_arquivado)
        
        if not os.path.exists(caminho_arquivado):
            # Encontrou um nome livre, move o arquivo
            os.rename(caminho_unificado, caminho_arquivado)
            print(f"  Arquivo antigo movido para: '{caminho_arquivado}'")
            break
        
        id_seq += 1 # Tenta o próximo número

def juntar_planilhas():
    """
    Junta todas as planilhas da pasta 'planilhas_prontas' em um único
    arquivo Excel, limpando os dados no processo.
    """
    
    # 1. Procura todos os arquivos .xlsx na pasta de planilhas prontas
    arquivos_excel = glob.glob(os.path.join(PASTA_PLANILHAS_PRONTAS, "*.xlsx"))
    
    if not arquivos_excel:
        print(f"Nenhum arquivo .xlsx encontrado em '{PASTA_PLANILHAS_PRONTAS}'.")
        return False # Retorna Falso para indicar que nada foi feito

    print(f"Encontrados {len(arquivos_excel)} arquivos para unificar...")
    
    # 2. Lê cada Excel e guarda num "balde" (lista de DataFrames)
    lista_dataframes = []
    for f in arquivos_excel:
        try:
            df = pd.read_excel(f)
            lista_dataframes.append(df)
        except Exception as e:
            print(f"  Erro ao ler o arquivo {f}: {e}. Pulando...")
            
    if not lista_dataframes:
        print("Nenhuma planilha pôde ser lida.")
        return False # Retorna Falso
        
    # 3. Junta todos os DataFrames em um só
    df_unificado = pd.concat(lista_dataframes, ignore_index=True)
    
    # 4. Limpeza de Dados (Muito Importante!)
    
    # Remove linhas onde o 'Nome' ou 'Valor' são nulos (lixo da IA)
    df_unificado = df_unificado.dropna(subset=['Nome', 'Valor'])
    
    # Garante que descrições nulas (NaN) virem strings vazias ('')
    df_unificado['Descrição'] = df_unificado['Descrição'].fillna('')
    
    # Remove produtos duplicados (baseado no Nome)
    # 'keep='first'' mantém o primeiro que apareceu
    df_unificado = df_unificado.drop_duplicates(subset=['Nome'], keep='first')
    
    # Garante a ordem correta das colunas
    df_unificado = df_unificado[['Categoria', 'Nome', 'Valor', 'Descrição']]
    
    # 5. Salva a nova planilha unificada
    caminho_unificado = os.path.join(".", NOME_ARQUIVO_UNIFICADO)
    
    df_unificado.to_excel(caminho_unificado, index=False)
    
    print("\n--- Sucesso! ---")
    print(f"Total de {len(df_unificado)} itens únicos salvos em:")
    print(f"{caminho_unificado}")
    
    return True # Retorna Verdadeiro para indicar que uma nova planilha foi criada

def main():
    print("Iniciando Robô Unificador de Planilhas...")
    
    # --- CORREÇÃO APLICADA AQUI ---
    # Garante que TODAS as pastas de trabalho do unificador existam
    # antes de começar.
    print(f"Verificando pasta de planilhas prontas: '{PASTA_PLANILHAS_PRONTAS}'")
    os.makedirs(PASTA_PLANILHAS_PRONTAS, exist_ok=True)
    print(f"Verificando pasta de arquivadas: '{PASTA_ARQUIVADAS}'")
    os.makedirs(PASTA_ARQUIVADAS, exist_ok=True)
    # --- FIM DA CORREÇÃO ---
    
    caminho_unificado = os.path.join(".", NOME_ARQUIVO_UNIFICADO)
    
    # 1. Arquiva a planilha antiga, se existir
    arquivar_planilha_antiga(caminho_unificado)
    
    # 2. Cria a nova planilha unificada
    #    A função agora retorna True/False
    sucesso = juntar_planilhas()
    
    if sucesso:
        print("Processo de unificação concluído.")
    else:
        print("Processo de unificação concluído (nenhuma planilha nova para juntar).")


if __name__ == "__main__":
    main()