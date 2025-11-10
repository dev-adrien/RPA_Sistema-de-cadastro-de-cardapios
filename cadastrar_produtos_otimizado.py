import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- NOVAS IMPORTAÇÕES ---
import os # Para ler as variáveis de ambiente do sistema
from dotenv import load_dotenv # Para carregar o arquivo .env

# Carrega as variáveis do arquivo .env para o sistema
load_dotenv()
# -------------------------


# --- CONFIGURAÇÕES DE LOGIN (AGORA VINDAS DO .ENV) ---

# 1. Os dados de login agora são lidos do seu arquivo .env
#    Certifique-se de preencher seu .env!
SEU_USUARIO = os.getenv("USUARIO")
SUA_SENHA = os.getenv("SENHA")

# 2. Seletores (continuam aqui, pois não são sensíveis)
ID_CAMPO_USUARIO = "email"
ID_CAMPO_SENHA = "senha"
SELETOR_BTN_LOGIN = (By.ID, "botao_logar")

# -----------------------------------------------

# --- CONFIGURAÇÕES INICIAIS ---
URL_DE_LOGIN = os.getenv("LOGIN")
URL_DE_CADASTRO = os.getenv("CADASTRO")
NOME_ARQUIVO_EXCEL = os.getenv("ARQUIVO_EXCEL")
# ---------------------------------

print("Iniciando o script de automação OTIMIZADO...")

# 2. Configura as Opções para usar o BRAVE
try:
    options = Options()
    options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    driver = webdriver.Chrome(options=options)
    
except Exception as e:
    print(f"Erro ao iniciar o ChromeDriver: {e}")
    print("Verifique se o 'chromedriver.exe' está na mesma pasta do script.")
    print(r"Verifique se o caminho 'options.binary_location' está correto.")
    exit()

# 3. OTIMIZAÇÃO: Automatizando o Login
try:
    driver.get(URL_DE_LOGIN)
    driver.maximize_window() 
    
    # Cria um objeto de "Espera Inteligente"
    wait = WebDriverWait(driver, 10)

    print("="*30)
    print("Fazendo login automaticamente...")

    # Espera o campo de usuário aparecer e o preenche
    campo_usuario = wait.until(EC.visibility_of_element_located((By.ID, ID_CAMPO_USUARIO)))
    campo_usuario.send_keys(SEU_USUARIO)

    # Espera o campo de senha aparecer e o preenche
    campo_senha = wait.until(EC.visibility_of_element_located((By.ID, ID_CAMPO_SENHA)))
    campo_senha.send_keys(SUA_SENHA)

    # Espera o botão de login estar clicável e clica
    botao_login = wait.until(EC.element_to_be_clickable(SELETOR_BTN_LOGIN))
    botao_login.click()

    # Espera o login ser processado (esperamos a URL mudar da página de login)
    wait.until(EC.url_changes(URL_DE_LOGIN))
    print("Login realizado com sucesso!")
    print("="*30)

except Exception as e:
    print(f"!!! ERRO DURANTE O LOGIN AUTOMÁTICO: {e}")
    print("Verifique se os IDs dos campos de login e o seletor do botão estão corretos.")
    driver.quit()
    exit()

# Pausa para a sessão de login "assentar" no servidor
print("Aguardando 2 segundos para a sessão de login ser registrada...")
time.sleep(2) 

# 5. Navega para a página de cadastro
print(f"Navegando para a página de cadastro...")
driver.get(URL_DE_CADASTRO)

# 6. Carrega a planilha (sem mudança aqui)
try:
    if NOME_ARQUIVO_EXCEL.endswith('.xlsx'):
        planilha = pd.read_excel(NOME_ARQUIVO_EXCEL)
    elif NOME_ARQUIVO_EXCEL.endswith('.csv'):
        planilha = pd.read_csv(NOME_ARQUIVO_EXCEL)
    else:
        raise ValueError("Formato de arquivo não suportado.")
    print(f"Sucesso! Planilha '{NOME_ARQUIVO_EXCEL}' carregada.")
    print(f"Encontrados {len(planilha)} produtos para cadastrar.")
except Exception as e:
    print(f"Erro ao ler a planilha: {e}")
    driver.quit()
    exit()

# --- OTIMIZAÇÃO: Bloco de Espera Principal ---
# (Este bloco espera o botão "Cadastrar" aparecer antes de iniciar o loop)
try:
    print("Aguardando a página de cadastro carregar...")
    SELETOR_BTN_NOVO = (By.CSS_SELECTOR, ".btn.btn-info.fw-bold.br-5")
    # Aumentando o tempo de espera aqui para 15s por segurança
    wait_longo = WebDriverWait(driver, 15) 
    wait_longo.until(EC.element_to_be_clickable(SELETOR_BTN_NOVO))
    print("Página pronta. Iniciando cadastros...")
except Exception as e:
    print(f"Erro ao carregar a página de cadastro: {e}")
    print("Não foi possível encontrar o botão 'Cadastrar novo produto'.")
    driver.quit()
    exit()
# ---------------------------------------------

# Define o wait padrão de volta para 10s para o loop
wait = WebDriverWait(driver, 10)

# 7. Loop Principal
for indice, linha in planilha.iterrows():
    try:
        nome = linha['Nome']
        preco = linha['Valor']
        categoria = linha['Categoria']
        descricao = linha['Descrição']

        if pd.isna(descricao):
            descricao = ""

        print(f"\n--- Cadastrando Produto {indice + 1}/{len(planilha)}: {nome} ---")

        # 8.1. Clica no botão "Cadastrar novo produto"
        print("1. Abrindo modal de cadastro...")
        # (Usamos a espera que já definimos, não precisa do time.sleep)
        btn_novo_produto = wait.until(EC.element_to_be_clickable(SELETOR_BTN_NOVO))
        btn_novo_produto.click()

        # 8.2. Clica no botão de rádio "produto sem estoque"
        print("2. Marcando 'sem estoque'...")
        radio_sem_estoque = wait.until(EC.element_to_be_clickable((By.ID, "produto_sem_estoque")))
        radio_sem_estoque.click()

        # 8.3. Preenche o Nome do produto
        print(f"3. Preenchendo Nome: {nome}")
        campo_nome = wait.until(EC.visibility_of_element_located((By.ID, "nome")))
        campo_nome.clear() 
        campo_nome.send_keys(nome) 

        # 8.4. Preenche o Valor do produto (LÓGICA INALTERADA - JÁ ESTÁ OTIMIZADA)
        print(f"4. Preenchendo Preço: {preco}")
        try:
            preco_limpo = str(preco)
            preco_limpo = "".join(filter(lambda c: c.isdigit() or c == ',', preco_limpo))
            preco_limpo = preco_limpo.replace(',', '.')
            if not preco_limpo:
                preco_limpo = "0"
            preco_float = float(preco_limpo)
            preco_centavos = preco_float * 100
            preco_final_para_enviar = str(int(preco_centavos))
            
            campo_valor = wait.until(EC.visibility_of_element_located((By.ID, "valor")))
            campo_valor.clear()
            
            print(f"    (Digitando {preco_final_para_enviar} humanamente...)")
            for digito in preco_final_para_enviar:
                campo_valor.send_keys(digito)
                time.sleep(0.1) # MANTIDO DE PROPÓSITO para a máscara

        except Exception as e:
            print(f"!!! ERRO ao limpar ou preencher o PREÇO: {e}")
            raise e

        # 8.5. Preenche a Categoria (LÓGICA INALTERADA - JÁ ESTÁ OTIMIZADA)
        print(f"5. Preenchendo Categoria: {categoria}...")
        try:
            container_categoria = wait.until(EC.element_to_be_clickable((By.ID, "select2-id_categoria-container")))
            container_categoria.click()

            seletor_campo_busca = (By.XPATH, "//span[contains(@class, 'select2-dropdown')]//input[contains(@class, 'select2-search__field')]")
            campo_busca_categoria = wait.until(EC.visibility_of_element_located(seletor_campo_busca))
            
            driver.execute_script("arguments[0].value = arguments[1];", campo_busca_categoria, categoria)
            driver.execute_script(
                "var event = new Event('keyup', { 'bubbles': true, 'cancelable': true });"
                "arguments[0].dispatchEvent(event);", 
                campo_busca_categoria
            )
            time.sleep(1) # MANTIDO DE PROPÓSITO para o filtro
            
            seletor_resultado = (By.XPATH, f"//ul[contains(@class, 'select2-results__options')]//li[text()='{categoria}']")
            resultado_categoria = wait.until(EC.element_to_be_clickable(seletor_resultado))
            resultado_categoria.click()
            time.sleep(1) # MANTIDO DE PROPÓSITO para fechar
            
        except Exception as e:
            print(f"!!! ERRO ao tentar preencher a categoria (Select2): {e}")
            raise e

        # 8.6. Preenche a Descrição
        print(f"6. Preenchendo Descrição...")
        seletor_iframe = (By.CSS_SELECTOR, ".cke_wysiwyg_frame.cke_reset")
        iframe_descricao = wait.until(EC.visibility_of_element_located(seletor_iframe))
        driver.switch_to.frame(iframe_descricao)
        
        editor_body = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        editor_body.clear()
        editor_body.send_keys(descricao)
        driver.switch_to.default_content()

        # 8.7. Clica no link "Próximo" (LÓGICA INALTERADA - JÁ ESTÁ OTIMIZADA)
        print("7. Clicando em 'Próximo'...")
        try:
            proximo_link = wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Próximo")))
            driver.execute_script("arguments[0].click();", proximo_link)
            
        except Exception as e:
            print(f"!!! ERRO ao clicar em 'Próximo': {e}")
            raise e

        # 8.8. Clica no link "Finalizar" (LÓGICA OTIMIZADA COM SWEETALERT)
        print("8. Clicando em 'Finalizar'...")
        try:
            finalizar_link = wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Finalizar")))
            driver.execute_script("arguments[0].click();", finalizar_link)
            
            print("Aguardando salvamento (esperando modal fechar)...")
            wait.until(EC.staleness_of(finalizar_link)) # Espera o modal antigo sumir

            # --- Tratamento do Pop-up "SweetAlert" ---
            print("Aguardando pop-up de sucesso...")
            SELETOR_SWAL = (By.CSS_SELECTOR, ".swal2-container.swal2-shown")
            
            # Espera o pop-up APARECER
            wait_longo.until(EC.visibility_of_element_located(SELETOR_SWAL))
            
            print("Pop-up encontrado. Aguardando pop-up DESAPARECER...")
            # Espera o pop-up DESAPARECER
            wait_longo.until(EC.invisibility_of_element_located(SELETOR_SWAL))
            # --- Fim do tratamento ---

            print(f"SUCESSO! Produto '{nome}' cadastrado.")
            
        except Exception as e:
            print(f"!!! ERRO ao clicar em 'Finalizar' ou aguardar salvamento: {e}")
            raise e

    except Exception as e:
        print(f"\n!!!!!! ERRO GERAL AO CADASTRAR: {nome} !!!!!!")
        print(f"Erro: {e}")
        print("O script será INTERROMPIDO.")
        print("Limpando foco do iframe (por segurança)...")
        driver.switch_to.default_content() 
        break 

# 10. Finalização
print("\n="*30)
print("Automação otimizada concluída!")
driver.quit()