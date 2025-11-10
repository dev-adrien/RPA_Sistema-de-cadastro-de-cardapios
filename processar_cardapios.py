import os
import glob
import base64
import json
import time
import requests 
import pandas as pd
import xlsxwriter 
from dotenv import load_dotenv
from PIL import Image 
import juntar_planilhas
import sys # Nova importação para sair do script em caso de erro

# Carrega as variáveis de ambiente (do seu .env)
load_dotenv()

# --- CONFIGURAÇÕES ---
API_KEY = os.getenv("GEMINI_API_KEY")
PASTA_DE_ENTRADA = "menus_para_processar"
PASTA_DE_SAIDA = "planilhas_prontas"
PASTA_PROCESSADOS = "menus_arquivados"
FICHEIRO_CATEGORIAS = "categorias.json" # Nova configuração
# ---------------------

# O modelo Gemini que entende imagens
MODELO_API = "gemini-2.5-flash-preview-09-2025"
URL_API = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_API}:generateContent?key={API_KEY}"

# O "molde" que vamos forçar a IA a usar
SCHEMA_JSON = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "Nome": {"type": "STRING"},
            "Valor": {"type": "STRING"},
            "Categoria": {"type": "STRING"},
            "Descrição": {"type": "STRING"} 
        },
        "required": ["Nome", "Valor", "Categoria", "Descrição"]
    }
}


# --- NOVA FUNÇÃO ---
def carregar_categorias():
    """Lê o ficheiro .json de categorias e retorna uma lista."""
    try:
        with open(FICHEIRO_CATEGORIAS, 'r', encoding='utf-8') as f:
            categorias = json.load(f)
        if not isinstance(categorias, list) or not all(isinstance(c, str) for c in categorias):
            raise ValueError("Ficheiro de categorias deve ser uma lista de strings.")
        print(f"Sucesso: {len(categorias)} categorias carregadas de '{FICHEIRO_CATEGORIAS}'.")
        return categorias
    except FileNotFoundError:
        print(f"!!! ERRO FATAL: Ficheiro '{FICHEIRO_CATEGORIAS}' não encontrado.")
        print("    Por favor, crie o ficheiro com a sua lista de categorias.")
        sys.exit(1) # Para o script
    except json.JSONDecodeError:
        print(f"!!! ERRO FATAL: Ficheiro '{FICHEIRO_CATEGORIAS}' contém um JSON inválido.")
        sys.exit(1)
    except ValueError as e:
        print(f"!!! ERRO FATAL: {e}")
        sys.exit(1)
# --- FIM DA NOVA FUNÇÃO ---


# Carrega as categorias UMA VEZ no início
CATEGORIAS_PERMITIDAS = carregar_categorias()


# 1. Função para converter imagem em base64 (sem alterações)
def image_to_base64(filepath):
    """Converte um arquivo de imagem em uma string base64."""
    try:
        img = Image.open(filepath)
        img.verify() 
        with open(filepath, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except (IOError, SyntaxError) as e:
        print(f"  Erro: O ficheiro {filepath} está corrompido ou não é uma imagem: {e}")
        return None
    except Exception as e:
        print(f"  Erro ao ler o ficheiro {filepath}: {e}")
        return None

# 2. Função para chamar a API Gemini (com o prompt mais recente)
def extrair_dados_do_cardapio(base64_image, mime_type):
    """
    Envia a imagem para a API Gemini e pede para ela extrair os dados
    usando o nosso molde (SCHEMA_JSON).
    """
    headers = {"Content-Type": "application/json"}
    
    # --- PROMPT REFINADO (GENERALISTA, PRECISO E COM AUTO-CORREÇÃO) ---
    
    # Formata a lista de categorias vinda do ficheiro .json
    lista_categorias_formatada = ", ".join([f"'{c}'" for c in CATEGORIAS_PERMITIDAS])
    
    prompt = (
        "Você é um assistente especialista em extração de dados de imagens. "
        "Sua tarefa é analisar a imagem (que pode ser um cardápio, uma tabela de preços de salão, uma lista de produtos de loja, ou um screenshot de WhatsApp) "
        "e extrair TODOS os itens, serviços e seus respetivos preços, formatando o texto com precisão cirúrgica."

        "--- REGRAS DE ANÁLISE VISUAL E CONTEXTUAL ---"
        "1. [OBJETIVO]: O objetivo é extrair uma lista de 'Itens' (que podem ser produtos ou serviços) com seus 'Nomes', 'Valores', 'Categorias' e 'Descrições'."
        "2. [ASSOCIAÇÃO DE PREÇO]: Preste muita atenção ao layout visual. O preço pode estar à direita do nome, abaixo da descrição, ou em colunas (P, M, G). Associe o preço correto ao item/serviço correto."
        
        "--- REGRA CRÍTICA DE EXPANSÃO (A MAIS IMPORTANTE) ---"
        "Se um item tiver múltiplas variações de tamanho ou tipo (ex: P, M, G; 'Corte', 'Corte + Barba') "
        "com preços diferentes, você DEVE criar uma LINHA SEPARADA para cada variação."
        "EXEMPLO 1: 'Pizza Calabresa | P: R$ 20,00 | M: R$ 30,00' "
        "DEVE SER GERADO COMO: "
        "1. {'Nome': 'Pizza Calabresa P', 'Valor': 'R$ 20,00', ...} "
        "2. {'Nome': 'Pizza Calabresa M', 'Valor': 'R$ 30,00', ...} "
        "EXEMPLO 2: 'Corte | Cabelo: R$ 30 | Cabelo+Barba: R$ 50'"
        "DEVE SER GERADO COMO:"
        "1. {'Nome': 'Corte Cabelo', 'Valor': 'R$ 30', ...}"
        "2. {'Nome': 'Corte Cabelo+Barba', 'Valor': 'R$ 50', ...}"

        "--- REGRAS CRÍTICAS DE FORMATAÇÃO DE TEXTO ---"
        "1. [Nome]: Formate como um título (Title Case). "
        "   - Ex: 'Açaí com Morango e Leite Ninho' (conectivos 'de', 'com', 'e' em minúsculo)."
        
        "2. [Descrição]: Formate como uma frase (Sentence Case)."
        "   - Ex: 'Molho de tomate, queijo e orégano. Acompanha borda.'"
        "   - Se não houver descrição, retorne uma string vazia ('')."

        "--- REGRAS CRÍTICAS DE CLASSIFICAÇÃO E PRECISÃO (AUTO-CORREÇÃO) ---"
        "1. [CLASSIFICAÇÃO DE CATEGORIA]: A sua tarefa é classificar cada item numa das seguintes categorias pré-definidas: "
        f"   {lista_categorias_formatada}. "
        "   Use o título da seção na imagem (ex: 'SANDUÍCHES', 'SERVIÇOS DE MANICURE') para decidir a categoria correta da lista. "
        "   Se a imagem for de um salão e a seção for 'Manicure', e a lista de categorias tiver 'Unhas', classifique como 'Unhas'. "
        "   Se um item não se encaixar em nenhuma, use a categoria 'Outros'."

        "2. [METODOLOGIA DE REVISÃO DE PRECISÃO (O MAIS IMPORTANTE)]: O OCR do texto pode conter erros. "
        "   Antes de finalizar, você DEVE agir como um revisor."
        "   - Se uma palavra extraída parecer um erro de digitação ou não for uma palavra real em Português (ex: 'Arobe', 'Calabreza', 'Sobrancela'), você DEVE corrigi-la."
        "   - Use o contexto da imagem (como a descrição ou outros itens) para deduzir e corrigir a palavra (ex: 'Árabe', 'Calabresa', 'Sobrancelha')."
        "   - Verifique a plausibilidade. O seu conhecimento da língua portuguesa é crucial para corrigir erros de OCR."

        "--- SAÍDA ---"
        "Retorne TODOS os itens encontrados, seguindo TODAS as regras acima (visuais, de expansão, "
        "formatação, classificação e precisão), no formato JSON solicitado."
    )
    # --- FIM DO PROMPT REFINADO ---
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": base64_image
                    }
                }
            ]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA_JSON
        }
    }

    # Implementa retry com exponential backoff (sem alterações)
    for i in range(5): 
        try:
            response = requests.post(URL_API, headers=headers, data=json.dumps(payload), timeout=30)
            
            if response.status_code == 200:
                response_json = response.json()
                
                if 'candidates' not in response_json or not response_json['candidates']:
                    print("  Erro na API: Resposta recebida, mas sem 'candidates'.")
                    continue
                    
                json_text = response_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(json_text)
                
            else:
                print(f"  Erro na API (Tentativa {i+1}): Status {response.status_code}")
        
        except requests.exceptions.ReadTimeout:
            print(f"  Erro: A API demorou muito para responder (Timeout na Tentativa {i+1}).")
        except requests.exceptions.RequestException as e:
            print(f"  Erro de conexão (Tentativa {i+1}): {e}")
        except json.JSONDecodeError:
            print(f"  Erro: A API retornou um JSON inválido. Resposta: {response.text}")
            
        time.sleep(2 ** i) 

    print("  Falha ao extrair dados após várias tentativas.")
    return None

# 3. Função para salvar os dados em um Excel formatado (sem alterações)
def salvar_excel_formatado(dados_json, output_filepath):
    """Salva a lista de dados em um .xlsx formatado."""
    
    if not dados_json:
        print("  Nenhum dado para salvar.")
        return

    df = pd.DataFrame(dados_json)
    
    colunas_esperadas = ['Categoria', 'Nome', 'Valor', 'Descrição']
    for col in colunas_esperadas:
        if col not in df.columns:
            df[col] = "" 

    df = df[colunas_esperadas]
    
    writer = pd.ExcelWriter(output_filepath, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Cardapio', index=False)
    
    workbook = writer.book
    worksheet = writer.sheets['Cardapio']
    
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC', 
        'border': 1
    })

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
    
    worksheet.set_column('A:A', 20) # Categoria
    worksheet.set_column('B:B', 35) # Nome
    worksheet.set_column('C:C', 10) # Valor
    worksheet.set_column('D:D', 50) # Descrição
    
    writer.close()
    print(f"  Sucesso! Planilha formatada salva em: {output_filepath}")

# 4. Função Principal (com a chamada do 'juntar_planilhas')
def main():
    print("Iniciando Robô Processador de Cardápios (Etapa 1)...")
    
    os.makedirs(PASTA_DE_ENTRADA, exist_ok=True)
    os.makedirs(PASTA_DE_SAIDA, exist_ok=True)
    os.makedirs(PASTA_PROCESSADOS, exist_ok=True)
    
    arquivos = glob.glob(os.path.join(PASTA_DE_ENTRADA, "*.png"))
    arquivos.extend(glob.glob(os.path.join(PASTA_DE_ENTRADA, "*.jpg")))
    arquivos.extend(glob.glob(os.path.join(PASTA_DE_ENTRADA, "*.jpeg"))) 
    
    if not arquivos:
        print(f"Nenhum ficheiro .png, .jpg ou .jpeg encontrado em '{PASTA_DE_ENTRADA}'.")
        print("Adicione imagens de cardápio nesta pasta e rode o script novamente.")
        return # Termina o script se não houver nada para processar

    print(f"Encontrados {len(arquivos)} cardápios para processar...")
    
    arquivos_processados_com_sucesso = 0
    
    for filepath in arquivos:
        filename = os.path.basename(filepath)
        print(f"\nProcessando: {filename}...")
        
        mime_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
        
        b64_image = image_to_base64(filepath)
        if not b64_image:
            try:
                os.rename(filepath, os.path.join(PASTA_PROCESSADOS, f"CORROMPIDO_{filename}"))
                print(f"  Ficheiro corrompido movido para '{PASTA_PROCESSADOS}'.")
            except Exception as e:
                print(f"  Erro ao mover ficheiro corrompido: {e}")
            continue
            
        dados = extrair_dados_do_cardapio(b64_image, mime_type)
        if not dados:
            print("  Não foi possível extrair dados.")
            continue
            
        output_filename = os.path.splitext(filename)[0] + ".xlsx"
        output_filepath = os.path.join(PASTA_DE_SAIDA, output_filename)
        salvar_excel_formatado(dados, output_filepath)
        
        try:
            os.rename(filepath, os.path.join(PASTA_PROCESSADOS, filename))
            print(f"  Ficheiro original movido para '{PASTA_PROCESSADOS}'.")
            arquivos_processados_com_sucesso += 1
        except Exception as e:
            print(f"  Erro ao mover ficheiro original: {e}")

    print("\nProcessamento (Etapa 1) concluído!")
    
    # --- NOVIDADE AQUI ---
    # Se algum ficheiro foi processado, chama o robô unificador
    if arquivos_processados_com_sucesso > 0:
        print("\n-------------------------------------------")
        print("Iniciando Robô Unificador de Planilhas (Etapa 2)...")
        try:
            juntar_planilhas.main()
            print("Robô Unificador finalizado.")
        except Exception as e:
            print(f"!!! ERRO ao executar o script 'juntar_planilhas': {e}")
    else:
        print("Nenhum ficheiro novo foi processado, pulando a unificação.")
    # --- FIM DA ADIÇÃO ---


# Roda a função principal
if __name__ == "__main__":
    main()