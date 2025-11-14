"""Servidor Flask para coleta e visualização das declarações EFD-REINF."""

from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import json

app = Flask(__name__)

def formatar_valor(valor):
    """Formata valores monetários para o padrão brasileiro com duas casas."""
    try:
        if isinstance(valor, str):
            valor = valor.replace(',', '.')
        valor_float = float(valor)
        return f"{valor_float:.2f}".replace('.', ',')
    except (ValueError, TypeError):
        return '0,00'

def init_db():
    """Cria a tabela principal do SQLite caso ainda não exista."""
    conn = sqlite3.connect('cadastros.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS efd_declaracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            cnpj TEXT NOT NULL,
            cpf TEXT NOT NULL,
            dependentes TEXT,
            planos_saude TEXT,
            dependentes_planos TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Renderiza o menu principal da aplicação."""
    return render_template('index.html')

@app.route('/formulario')
def formulario_efd():
    """Exibe o formulário para cadastro da declaração EFD-REINF."""
    return render_template('forms.html')

# Rota para processar o formulário EFD-REINF
@app.route('/submit_efd', methods=['POST'])
def submit_efd():
    """Recebe o formulário, persiste os dados e redireciona para a tela de sucesso."""
    data = request.form.get('data')
    cnpj = request.form.get('cnpj')
    cpf = request.form.get('cpf')
    
    # Pegar dados dos dependentes, planos e dependentes com planos
    dependentes = request.form.get('dependentes', '[]')
    planos_saude = request.form.get('planos_saude', '[]')
    dependentes_planos = request.form.get('dependentes_planos', '[]')
    
    # Salvar no banco de dados
    conn = sqlite3.connect('cadastros.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO efd_declaracoes (data, cnpj, cpf, dependentes, planos_saude, dependentes_planos)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data, cnpj, cpf, dependentes, planos_saude, dependentes_planos))
    conn.commit()
    conn.close()
    
    return redirect(url_for('sucesso_efd'))

@app.route('/sucesso_efd')
def sucesso_efd():
    """Confirma o envio da declaração para o usuário."""
    return render_template('success.html')

@app.route('/visualizar_efd')
def visualizar_efd():
    """Lista todas as declarações registradas para consulta."""
    conn = sqlite3.connect('cadastros.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM efd_declaracoes ORDER BY id DESC')
    declaracoes = cursor.fetchall()
    conn.close()
    return render_template('view.html', declaracoes=declaracoes)

# Rota para obter detalhes de uma declaração EFD-REINF
@app.route('/detalhes_efd/<int:declaracao_id>')
def detalhes_efd(declaracao_id):
    """Retorna os detalhes enriquecidos de uma declaração específica."""
    try:
        conn = sqlite3.connect('cadastros.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM efd_declaracoes WHERE id = ?', (declaracao_id,))
        declaracao = cursor.fetchone()
        conn.close()
        
        if not declaracao:
            return jsonify({'error': 'Declaração não encontrada'}), 404
        
        # Estrutura: id, data, cnpj, cpf, dependentes, planos_saude, dependentes_planos, data_cadastro
        dependentes = json.loads(declaracao[4]) if declaracao[4] else []
        planos_saude = json.loads(declaracao[5]) if declaracao[5] else []
        dependentes_planos = json.loads(declaracao[6]) if declaracao[6] else []
        
        # Valor do titular (primeiro plano de saúde)
        valor_titular = formatar_valor(planos_saude[0]['valor']) if planos_saude else '0,00'
        
        # Combinar dependentes com valores
        dependentes_completos = []
        for dep in dependentes:
            valor_dependente = '0,00'
            for dp in dependentes_planos:
                if dp['cpf'] == dep['cpf']:
                    valor_dependente = formatar_valor(dp['valor'])
                    break
            
            dependentes_completos.append({
                'cpf': dep['cpf'],
                'relacao': dep['relacao'],
                'valor': valor_dependente
            })
        
        return jsonify({
            'id': declaracao[0],
            'data': declaracao[1],
            'cnpj': declaracao[2],
            'cpf': declaracao[3],
            'data_cadastro': declaracao[7],
            'valor_titular': valor_titular,
            'dependentes': dependentes_completos
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

if __name__ == '__main__':
    init_db()
    print("🚀 Servidor rodando em: http://localhost:5000")
    print("📊 Visualizar dados em: http://localhost:5000/visualizar_efd")
    app.run(debug=True, port=5000)

