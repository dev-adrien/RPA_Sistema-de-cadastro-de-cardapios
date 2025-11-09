import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import subprocess
import threading
import os
import shutil

# --- Configuração das Pastas ---
# (Certifique-se que estas pastas existem)
PASTA_DE_ENTRADA = "menus_para_processar"
# --------------------------------

class InterfaceApp:
    def __init__(self, root):
        self.root = root
        root.title("Assistente de Automação de Cardápios")
        root.geometry("700x550")

        # --- Frame Principal ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Frame de Botões ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)

        # Botão 1: Adicionar Imagens
        self.btn_add = ttk.Button(button_frame, text="1. Adicionar Imagens...", command=self.adicionar_imagens)
        self.btn_add.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Botão 2: Processar Cardápios (Robô 1 e 2)
        self.btn_process = ttk.Button(button_frame, text="2. Processar Cardápios (IA)", command=lambda: self.run_script("processar_cardapios.py"))
        self.btn_process.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Botão 3: Cadastrar Produtos (Robô 3)
        self.btn_upload = ttk.Button(button_frame, text="3. Cadastrar Produtos (RPA)", command=lambda: self.run_script("cadastrar_produtos_otimizado.py"))
        self.btn_upload.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # --- Caixa de Log (Saída do Terminal) ---
        log_label = ttk.Label(main_frame, text="Log de Atividade:")
        log_label.pack(anchor=tk.W)

        self.log_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=25, state=tk.DISABLED)
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Tag para logs de sucesso
        self.log_area.tag_config('success', foreground='green')
        # Tag para logs de erro
        self.log_area.tag_config('error', foreground='red', font=('Helvetica', '9', 'bold'))
        # Tag para cabeçalhos
        self.log_area.tag_config('header', foreground='blue', font=('Helvetica', '10', 'bold'))
        
        # Garante que as pastas existem ao iniciar
        os.makedirs(PASTA_DE_ENTRADA, exist_ok=True)

    def adicionar_imagens(self):
        """Abre uma janela para o usuário selecionar as imagens."""
        filetypes = [("Ficheiros de Imagem", "*.jpg *.jpeg *.png"), ("Todos os ficheiros", "*.*")]
        files = filedialog.askopenfilenames(title="Selecione as imagens dos cardápios", filetypes=filetypes)
        
        if not files:
            self.log("Nenhuma imagem selecionada.", "error")
            return
            
        self.log(f"Copiando {len(files)} imagens para a pasta '{PASTA_DE_ENTRADA}'...", "header")
        
        count = 0
        for f_path in files:
            try:
                filename = os.path.basename(f_path)
                dest_path = os.path.join(PASTA_DE_ENTRADA, filename)
                shutil.copy(f_path, dest_path)
                self.log(f"  + {filename}")
                count += 1
            except Exception as e:
                self.log(f"  Erro ao copiar {filename}: {e}", "error")
                
        self.log(f"\n{count} imagens copiadas com sucesso.", "success")

    def run_script(self, script_name):
        """Inicia a execução de um script num 'thread' separado para não bloquear a interface."""
        
        # Desativa os botões para evitar cliques duplos
        self.btn_add.config(state=tk.DISABLED)
        self.btn_process.config(state=tk.DISABLED)
        self.btn_upload.config(state=tk.DISABLED)
        
        self.log(f"--- Iniciando script: {script_name} ---", "header")
        
        # Cria e inicia o 'thread'
        thread = threading.Thread(target=self.execute_subprocess, args=(script_name,), daemon=True)
        thread.start()

    def execute_subprocess(self, script_name):
        """O processo que corre "por trás dos panos"."""
        
        # Este é o comando que você digitaria no terminal
        command = ["py", script_name]
        
        try:
            # Inicia o processo
            # stdout=subprocess.PIPE: Captura a saída padrão (os 'print')
            # stderr=subprocess.STDOUT: Captura os erros e os envia para o mesmo sítio que a saída padrão
            # text=True: Retorna a saída como texto (string)
            # encoding='utf-8': Garante a leitura correta de acentos
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW # (Apenas Windows) Esconde a janela do terminal
            )

            # Lê a saída linha por linha, em tempo real
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                self.log(line)
            
            # Espera o processo terminar
            process.wait()
            
            if process.returncode == 0:
                self.log(f"--- Script {script_name} concluído com SUCESSO. ---", "success")
            else:
                self.log(f"--- Script {script_name} falhou (Código: {process.returncode}). ---", "error")

        except FileNotFoundError:
            self.log(f"ERRO: Script '{script_name}' não encontrado.", "error")
        except Exception as e:
            self.log(f"ERRO ao executar o script: {e}", "error")
        
        # Reativa os botões quando o script termina
        self.reactivate_buttons()

    def log(self, message, tag=None):
        """Adiciona uma mensagem à caixa de log na interface."""
        # A interface não pode ser atualizada por outro 'thread'
        # root.after() agenda a atualização para ser feita pelo 'thread' principal
        self.root.after(0, self._insert_log, message.strip(), tag)

    def _insert_log(self, message, tag):
        """Função interna para inserir o log."""
        self.log_area.config(state=tk.NORMAL) # Permite edição
        self.log_area.insert(tk.END, message + "\n", tag)
        self.log_area.config(state=tk.DISABLED) # Bloqueia edição
        self.log_area.see(tk.END) # Rola para o final

    def reactivate_buttons(self):
        """Reativa os botões (chamado pelo root.after)."""
        self.root.after(0, self._set_button_state, tk.NORMAL)

    def _set_button_state(self, state):
        self.btn_add.config(state=state)
        self.btn_process.config(state=state)
        self.btn_upload.config(state=state)


if __name__ == "__main__":
    # Verifica se as dependências do terminal estão instaladas
    try:
        import pandas
        import selenium
        import dotenv
        import requests
        import PIL
        import xlsxwriter
    except ImportError as e:
        messagebox.showerror(
            "Dependências em Falta",
            f"Erro: A biblioteca '{e.name}' não está instalada.\n\n"
            "Por favor, feche esta janela e execute o seguinte comando no seu terminal:\n\n"
            "py -m pip install -r requirements.txt"
        )
        sys.exit(1)
        
    root = tk.Tk()
    app = InterfaceApp(root)
    root.mainloop()