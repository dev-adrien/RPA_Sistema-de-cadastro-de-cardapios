# Projeto de Automação de Cardápios (RPA)

Este projeto contém três robôs Python para automatizar completamente o fluxo de trabalho de cadastro de produtos, desde a imagem do cardápio até o cadastro no sistema.

* **Robô 1: `processar_cardapios.py`** (Processador de IA)
    * Lê imagens de cardápios (`.jpg`, `.png`) da pasta `menus_para_processar`.
    * Usa a IA do Google (Gemini) para extrair, formatar e classificar os produtos.
    * Salva cada cardápio como uma planilha `.xlsx` formatada na pasta `planilhas_prontas`.
    * Move as imagens processadas para `menus_arquivados`.
    * Chama automaticamente o Robô 2.

* **Robô 2: `juntar_planilhas.py`** (Unificador)
    * Arquiva a planilha unificada antiga (se existir) para a pasta `planilhas_arquivadas`.
    * Lê todas as planilhas da pasta `planilhas_prontas`.
    * Junta todas num único ficheiro: `cardapio_unificado_para_rpa.xlsx`.
    * Remove duplicados e limpa os dados, deixando-o pronto para o Robô 3.

* **Robô 3: `cadastrar_produtos_otimizado.py`** (Cadastrador RPA)
    * Lê o ficheiro `cardapio_unificado_para_rpa.xlsx`.
    * Faz login automático no seu sistema web.
    * Navega até a página de cadastro.
    * Preenche o formulário (incluindo campos complexos) para cada produto da planilha.

---

## 1. Instalação (Comando Único)

Todo o projeto foi configurado para ser instalado com um único comando.
Na pasta do projeto , execute:
```bash
py -m pip install -r requirements.txt
```

---

## 2. Configuração (3 Ficheiros)

Antes de executar, você precisa configurar 3 ficheiros:

### A. `.env` (Arquivo de variáveis)

Crie um ficheiro chamado `.env` e preencha com os seus dados:

```
# Credenciais do Robô 3 (RPA)
USUARIO="seu-email@dominio.com"
SENHA="SuaSenhaSuperSecreta"
LOGIN="[https://url-do-seu-login.com](https://url-do-seu-login.com)"
CADASTRO="[https://url-do-painel-de-produtos.com](https://url-do-painel-de-produtos.com)"
ARQUIVO_EXCEL="cardapio_unificado_para_rpa.xlsx"

# Chave de API do Robô 1 (IA)
GEMINI_API_KEY="COLE_SUA_CHAVE_DE_API_AQUI" 
```
*(Para obter a sua `GEMINI_API_KEY`, vá ao [Google AI Studio](https://aistudio.google.com/) e clique em "Get API Key".)*

### B. `categorias.json` (Suas Categorias)

Edite este ficheiro para incluir *exatamente* as categorias que o seu sistema aceita. A IA será forçada a usar apenas estas.

### C. `cadastrar_produtos_otimizado.py` (O Navegador)

O script está configurado para usar o **Brave** por padrão. Se quiser usar outro navegador, edite esta secção de acordo com as opções abaixo e apague o arquivo chromedriver.exe antes de executar o programa para que ele instale o novo driver:

```python
# --- OPÇÃO 1: BRAVE (Padrão) ---
options = Options()
options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
driver = webdriver.Chrome(options=options)

# --- OPÇÃO 2: GOOGLE CHROME (Normal) ---
# (Apague ou comente as 3 linhas do Brave e descomente a linha abaixo)
# driver = webdriver.Chrome()

# --- OPÇÃO 3: FIREFOX ---
# (Apague ou comente as 3 linhas do Brave e descomente a linha abaixo)
# driver = webdriver.Firefox()
```
*(O Selenium 4 irá baixar automaticamente o driver para Chrome e Firefox.)*

---

## 3. Como Usar o Fluxo Completo

O seu fluxo de trabalho agora é muito simples:

1.  **Etapa 1:** Jogue quantas imagens de cardápio (`.png`, `.jpg`) quiser na pasta `menus_para_processar`.
2.  **Etapa 2:** Rode o primeiro robô:
    ```bash
    py processar_cardapios.py
    ```
    * Isto irá processar as imagens, criar as planilhas individuais e, no final, chamar o Robô 2 para criar o `planilha_cardapio_RPA.xlsx`.
3.  **Etapa 3:** Rode o terceiro robô:
    ```bash
    py cadastrar_produtos_otimizado.py
    ```
    * Este robô fará o login e cadastrará todos os produtos da planilha unificada.

---

## Anexo: Tutorial de Drivers de Navegador (Raro)

O Selenium 4 quase sempre baixa os drivers para si. Se, por algum motivo, ele falhar (especialmente com o Brave), aqui está como instalar manualmente:

**Para Brave / Chrome:**

1.  **Descubra a sua Versão:**
    * No Brave, vá para: `brave://version/`
    * Procure a linha **Chromium** (ex: `119.0.6045.163`). A versão que importa é a `119`.
2.  **Baixe o Driver:**
    * Vá para: [https://googlechromelabs.github.io/chrome-for-testing/](https://googlechromelabs.github.io/chrome-for-testing/)
    * Encontre a secção "Stable" que corresponde à sua versão (ex: `119.0...`).
    * Clique em `chromedriver-win64.zip` para baixar.
3.  **Instale:**
    * Extraia o `chromedriver.exe` do .zip e coloque-o na **mesma pasta** do seu script `.py`.

**Para Firefox (GeckoDriver):**

1.  **Baixe o Driver:**
    * Vá para: [https://github.com/mozilla/geckodriver/releases](https://github.com/mozilla/geckodriver/releases)
    * Clique no link `geckodriver-vX.X.X-win64.zip`.
2.  **Instale:**
    * Extraia o `geckodriver.exe` do .zip e coloque-o na **mesma pasta** do seu script `.py`.