import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import sqlite3
import os
import socket

# Configurações
url_base = 'http://localhost:5000'
data = '01/2025'
cnpj = '10.000.000/0001-00'
operadora = '10.000.000/0001-00'
COLUNAS_VALOR = ['TOTAL', 'VALOR', 'VALOR TOTAL', 'VALOR_TOTAL']
MAX_GRUPOS = int(os.environ.get('MAX_GRUPOS', '0'))
CHECKPOINT_FILE = 'checkpoint.txt'

# Ler dados do Excel
dados = pd.read_csv('dados_ficticios.csv', sep=';')

'''
def formatar_valor(valor):
    """Formata um valor para 2 casas decimais no padrão brasileiro (FUNÇÃO APENAS PARA O .xlsx ORIGINAL)"""
    try:
        if isinstance(valor, str):
            valor = valor.replace(',', '.')
        valor_float = float(valor)
        return f"{valor_float:.2f}".replace('.', ',')
    except (ValueError, TypeError):
        return '0,00'
'''

def limpar_dataframe(df):
    """Limpa o dataframe removendo linhas com valores nulos"""
    df_limpo = df.dropna(subset=['NOME', 'CPF', 'DEPENDENCIA'])
    df_limpo = df_limpo[
        (df_limpo['NOME'].astype(str).str.strip() != '') &
        (df_limpo['CPF'].astype(str).str.strip() != '') &
        (df_limpo['DEPENDENCIA'].astype(str).str.strip() != '')
    ]
    return df_limpo

def verificar_servidor():
    """Verifica se o servidor Flask está rodando"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        return result == 0
    except:
        return False

def salvar_checkpoint(indice):
    """Salva o checkpoint"""
    try:
        with open(CHECKPOINT_FILE, 'w') as f:
            f.write(str(indice))
    except:
        pass

def carregar_checkpoint():
    """Carrega o checkpoint"""
    try:
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                return int(f.read().strip())
        return -1
    except:
        return -1

def processar_dataframe(df):
    """Processa o dataframe e agrupa por titular"""
    grupos = []
    grupo_atual = []
    
    for index, row in df.iterrows():
        if pd.isna(row['NOME']) or pd.isna(row['DEPENDENCIA']) or pd.isna(row['CPF']):
            continue
            
        dependencia = str(row['DEPENDENCIA']).strip().upper()
        
        if dependencia == 'TITULAR':
            if grupo_atual:
                grupos.append(grupo_atual)
            grupo_atual = [row]
        else:
            if grupo_atual:
                grupo_atual.append(row)
    
    if grupo_atual:
        grupos.append(grupo_atual)
    
    return grupos

def obter_valor(row):
    """Retorna o valor monetário da linha considerando múltiplas colunas."""
    for coluna in COLUNAS_VALOR:
        if coluna in row and pd.notna(row[coluna]):
            return row[coluna]
    return '0,00'

def mapear_dependencia(dependencia):
    """Mapeia dependência para opção do select"""
    mapeamento = {
        'TITULAR': 'Titular',
        'ESPOSA': 'Cônjuge',
        'ESPOSO': 'Cônjuge',
        'COMPANHEIRO(A)': 'Companheiro(a) com o(a) qual tenha filho ou viva há mais de 5 (cinco) anos ou possua declaração de união estável',
        'COMPANHEIRO': 'Companheiro(a) com o(a) qual tenha filho ou viva há mais de 5 (cinco) anos ou possua declaração de união estável',
        'COMPANHEIRA': 'Companheiro(a) com o(a) qual tenha filho ou viva há mais de 5 (cinco) anos ou possua declaração de união estável',
        'FILHA': 'Filho(a) ou enteado(a)',
        'FILHO': 'Filho(a) ou enteado(a)',
        'MAE': 'Pais, avós e bisavós',
        'MÃE': 'Pais, avós e bisavós',
        'PAI': 'Pais, avós e bisavós',
        'AGREGADO': 'Agregado/Outros',
        'OUTRA DEPENDENCIA': 'Agregado/Outros',
        'OUTRA DEPENDÊNCIA': 'Agregado/Outros',
        'SOGRO': 'Agregado/Outros',
        'SOGRA': 'Agregado/Outros'
    }
    
    dependencia_upper = str(dependencia).strip().upper()
    
    # Buscar mapeamento exato
    if dependencia_upper in mapeamento:
        return mapeamento[dependencia_upper]
    
    # Buscar mapeamento parcial (para variações)
    for key, value in mapeamento.items():
        if key in dependencia_upper or dependencia_upper in key:
            return value
    
    # Se não encontrar, usar "Agregado/Outros" como padrão
    return 'Agregado/Outros'

class EFDTestRunner:
    """Encapsula o fluxo de automação do formulário EFD-REINF via Selenium."""

    def __init__(self):
        """Inicializa o driver do Selenium."""
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Configura o driver do Chromium para uso em ambiente headless."""
        chrome_options = Options()
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def close_driver(self):
        """Encerra o driver caso ainda esteja aberto."""
        if self.driver:
            self.driver.quit()
    
    def navegar_para_formulario(self):
        """Abre a página inicial e navega até o formulário."""
        try:
            self.driver.get(url_base)
            formulario_link = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Acessar Formulário')]")
            formulario_link.click()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "data"))
            )
            return True
        except Exception as e:
            print(f"⚠️ Falha ao navegar para o formulário: {e}")
            return False
    
    def preencher_dados_iniciais(self, cpf_titular):
        """Preenche data, CNPJ e CPF do titular na primeira etapa."""
        try:
            data_field = self.driver.find_element(By.ID, "data")
            data_field.clear()
            data_field.send_keys(data)
            
            cnpj_field = self.driver.find_element(By.ID, "cnpj")
            cnpj_field.clear()
            cnpj_field.send_keys(cnpj)
            
            cpf_field = self.driver.find_element(By.ID, "cpf")
            cpf_field.clear()
            cpf_field.send_keys(cpf_titular)
            
            return True
        except Exception as e:
            print(f"⚠️ Erro ao preencher dados iniciais: {e}")
            return False
    
    def continuar_para_proxima_etapa(self):
        """Clica no botão de continuação e aguarda a etapa seguinte."""
        try:
            continuar_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continuar')]")
            continuar_btn.click()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Incluir Dependente')]"))
            )
            return True
        except Exception as e:
            print(f"⚠️ Erro ao avançar para a etapa 2: {e}")
            return False
    
    def adicionar_dependente(self, cpf_dependente, relacao, agregado_outros=None):
        """Abre o modal de dependente e insere CPF, relação e descrição opcional."""
        try:
            incluir_dependente_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Incluir Dependente')]")
            incluir_dependente_btn.click()
            
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "dependenteCpf"))
            )
            
            dependente_cpf = self.driver.find_element(By.ID, "dependenteCpf")
            dependente_cpf.send_keys(cpf_dependente)
            
            relacao_select = Select(self.driver.find_element(By.ID, "relacaoDependencia"))
            relacao_select.select_by_visible_text(relacao)
            
            # Se for "Agregado/Outros", preencher campo específico
            if relacao == "Agregado/Outros" and agregado_outros:
                # Verificar se agregado_outros é válido
                if not pd.isna(agregado_outros) and str(agregado_outros).strip() != '' and str(agregado_outros).strip().lower() != 'nan':
                    # Aguardar campo aparecer
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.ID, "agregadoOutros"))
                    )
                    agregado_field = self.driver.find_element(By.ID, "agregadoOutros")
                    agregado_field.send_keys(agregado_outros)
            
            adicionar_btn = self.driver.find_element(By.XPATH, "//div[@id='modalDependente']//button[contains(text(), 'Adicionar')]")
            adicionar_btn.click()
            
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located((By.ID, "modalDependente"))
            )
            return True
        except Exception as e:
            print(f"⚠️ Erro ao adicionar dependente: {e}")
            return False
    
    def adicionar_plano_saude(self, valor):
        """Registra o plano de saúde do titular via modal específico."""
        try:
            incluir_plano_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Incluir Plano de Saúde')]")
            incluir_plano_btn.click()
            
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "planoCnpj"))
            )
            
            plano_cnpj = self.driver.find_element(By.ID, "planoCnpj")
            plano_cnpj.send_keys(operadora)
            
            valor_pago = self.driver.find_element(By.ID, "valorPago")
            valor_pago.send_keys(valor)
            
            adicionar_btn = self.driver.find_element(By.XPATH, "//div[@id='modalPlanoSaude']//button[contains(text(), 'Adicionar')]")
            adicionar_btn.click()
            
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located((By.ID, "modalPlanoSaude"))
            )
            return True
        except Exception as e:
            print(f"⚠️ Erro ao adicionar plano de saúde: {e}")
            return False
    
    def adicionar_informacao_dependente(self, cpf_dependente, valor):
        """Adiciona os valores pagos para cada dependente informado."""
        try:
            adicionar_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Adicionar Informações dos Dependentes')]")
            adicionar_btn.click()
            
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "dependenteSelecionado"))
            )
            
            dependente_select = Select(self.driver.find_element(By.ID, "dependenteSelecionado"))
            dependente_select.select_by_visible_text(cpf_dependente)
            
            valor_field = self.driver.find_element(By.ID, "valorDependente")
            valor_field.send_keys(valor)
            
            adicionar_btn = self.driver.find_element(By.XPATH, "//div[@id='modalDependentePlano']//button[contains(text(), 'Adicionar')]")
            adicionar_btn.click()
            
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located((By.ID, "modalDependentePlano"))
            )
            return True
        except Exception as e:
            print(f"⚠️ Erro ao adicionar informações do dependente: {e}")
            return False
    
    def enviar_declaracao(self):
        """Submete o formulário final e aguarda o redirecionamento de sucesso."""
        try:
            enviar_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Enviar Declaração')]")
            enviar_btn.click()
            
            WebDriverWait(self.driver, 15).until(
                EC.url_contains("/sucesso_efd")
            )
            return True
        except Exception as e:
            print(f"⚠️ Erro ao enviar declaração: {e}")
            return False
    
    def processar_grupo(self, grupo):
        """Executa todas as etapas para um grupo (titular + dependentes)."""
        try:
            titular = grupo[0]
            dependentes = grupo[1:] if len(grupo) > 1 else []
            
            if not self.navegar_para_formulario():
                return False
            
            if not self.preencher_dados_iniciais(titular['CPF']):
                return False
            
            if not self.continuar_para_proxima_etapa():
                return False
            
            # Adicionar dependentes
            for dep in dependentes:
                if pd.notna(dep['CPF']):
                    dependencia_original = dep['DEPENDENCIA']
                    relacao = mapear_dependencia(dependencia_original)
                    
                    # Se for "Agregado/Outros", usar a dependência original como descrição
                    agregado_outros = dependencia_original if relacao == 'Agregado/Outros' else None
                    
                    self.adicionar_dependente(dep['CPF'], relacao, agregado_outros)
            
            # Adicionar plano de saúde
            valor_titular = obter_valor(titular)
            if not self.adicionar_plano_saude(valor_titular):
                return False
            
            # Adicionar informações dos dependentes
            for dep in dependentes:
                if pd.notna(dep['CPF']):
                    valor_dep = obter_valor(dep)
                    if valor_dep and str(valor_dep).strip() not in ('', '0', '0,00'):
                        self.adicionar_informacao_dependente(dep['CPF'], valor_dep)
            
            return self.enviar_declaracao()
        except Exception as e:
            print(f"⚠️ Erro geral ao processar grupo: {e}")
            return False

def processar_todos_os_grupos():
    """Executa o processamento sequencial de todos os grupos do Excel."""
    if not verificar_servidor():
        print("❌ Servidor Flask não está rodando em localhost:5000")
        print("Execute: python app.py")
        return
    
    dados_limpos = limpar_dataframe(dados)
    grupos = processar_dataframe(dados_limpos)
    
    checkpoint = carregar_checkpoint()
    inicio = checkpoint + 1 if checkpoint >= 0 else 0
    
    if inicio >= len(grupos):
        print("✅ Todos os grupos já foram processados.")
        print("🔁 Apague o arquivo checkpoint.txt para reprocessar desde o início.")
        return
    
    print(f"📊 Total de grupos: {len(grupos)}")
    print(f"▶️ Iniciando do grupo: {inicio + 1}")
    
    try:
        processados = 0
        for i in range(inicio, len(grupos)):
            print(f"\n🔄 Processando grupo {i + 1}/{len(grupos)}")
            
            runner = EFDTestRunner()
            try:
                resultado = runner.processar_grupo(grupos[i])
                status = "✅ Sucesso" if resultado else "❌ Falha"
                print(f"Resultado: {status}")
                salvar_checkpoint(i)
            finally:
                runner.close_driver()
            
            processados += 1
            if MAX_GRUPOS and processados >= MAX_GRUPOS:
                print(f"⏹️ Limite de {MAX_GRUPOS} grupo(s) atingido (MAX_GRUPOS).")
                break
                
    except KeyboardInterrupt:
        print(f"\n⏸️ Pausado no grupo {i + 1}")
        print("Execute novamente para continuar")

if __name__ == "__main__":
    processar_todos_os_grupos()
