#!/usr/bin/env python3
"""
Prompt Fundamentalista B3 - Sistema Completo de Gerenciamento de Licenças
Com Painel Admin, Banco de Dados e Validação de Assinatura
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import sqlite3
import os
import uuid
import hashlib

app = Flask(__name__)
app.secret_key = 'sua-chave-secreta-super-segura-aqui'

# Caminho do banco de dados
DB_PATH = '/tmp/prompt_b3.db'

# Configurações
PIX_KEY = "055005108-27"
VALOR = 50.00
EMAIL = "pegardini@uol.com.br"

# =====================
# BANCO DE DADOS
# =====================

def init_db():
    """Inicializa o banco de dados"""
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Tabela de clientes
        c.execute('''
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                chave TEXT UNIQUE NOT NULL,
                data_compra TEXT NOT NULL,
                data_expiracao TEXT NOT NULL,
                ativo BOOLEAN DEFAULT 1,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de acessos
        c.execute('''
            CREATE TABLE acessos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                data_acesso TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        ''')
        
        conn.commit()
        conn.close()

def get_db():
    """Conecta ao banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def gerar_chave():
    """Gera uma chave única"""
    return f"PROMPT-{uuid.uuid4().hex[:12].upper()}"

# =====================
# ROTAS PÚBLICAS
# =====================

@app.route('/')
def index():
    """Página inicial com apresentação completa"""
    html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prompt Fundamentalista B3</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px 30px; text-align: center; }
        .header h1 { font-size: 2.8em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .content { padding: 40px 30px; }
        .section { margin-bottom: 40px; }
        .section h2 { color: #667eea; margin-bottom: 20px; font-size: 1.8em; border-bottom: 3px solid #667eea; padding-bottom: 15px; }
        .section h3 { color: #333; margin-top: 20px; margin-bottom: 10px; font-size: 1.2em; }
        .section p { color: #555; line-height: 1.8; margin-bottom: 15px; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .feature { background: #f5f5f5; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
        .feature h4 { color: #667eea; margin-bottom: 10px; }
        .feature p { color: #666; font-size: 0.95em; }
        .modules { background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .modules h4 { color: #667eea; margin-bottom: 15px; }
        .modules ul { list-style: none; columns: 2; }
        .modules li { padding: 8px 0; color: #555; }
        .modules li:before { content: "✓ "; color: #4caf50; font-weight: bold; margin-right: 8px; }
        .steps { counter-reset: step-counter; }
        .step { counter-increment: step-counter; display: flex; margin-bottom: 20px; }
        .step-number { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 20px; flex-shrink: 0; }
        .step-content { flex: 1; }
        .step-content h4 { color: #333; margin-bottom: 5px; }
        .step-content p { color: #666; }
        .button-container { display: flex; gap: 15px; margin: 30px 0; flex-wrap: wrap; justify-content: center; }
        .btn { padding: 15px 40px; border: none; border-radius: 8px; font-size: 1.1em; cursor: pointer; font-weight: bold; transition: all 0.3s ease; text-decoration: none; display: inline-block; text-align: center; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-primary:hover { transform: translateY(-3px); box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4); }
        .btn-secondary { background: #f0f0f0; color: #333; border: 2px solid #667eea; }
        .btn-secondary:hover { background: #667eea; color: white; }
        .btn-admin { background: #fff; color: #667eea; border: 2px solid #667eea; }
        .btn-admin:hover { background: #667eea; color: white; }
        .highlight { background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; border-radius: 4px; margin: 20px 0; }
        .highlight h4 { color: #856404; margin-bottom: 10px; }
        .highlight p { color: #856404; }
        .footer { background: #f8f9fa; padding: 30px; text-align: center; color: #666; border-top: 1px solid #ddd; }
        .footer p { margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Prompt Fundamentalista B3</h1>
            <p>Análise Profissional de Ações da B3 com IA</p>
        </div>
        
        <div class="content">
            <!-- Seção: O que é -->
            <div class="section">
                <h2>🎯 O Que é o Prompt Fundamentalista B3?</h2>
                <p>Um prompt avançado de IA que realiza análise fundamentalista completa de ações da B3 (Bolsa de Valores do Brasil). Usando dados de relatórios financeiros (DFP/ITR), o prompt identifica oportunidades de investimento, avalia riscos e fornece classificações profissionais.</p>
            </div>
            
            <!-- Seção: Benefícios -->
            <div class="section">
                <h2>✨ Benefícios</h2>
                <div class="features">
                    <div class="feature">
                        <h4>⚡ Análise Rápida</h4>
                        <p>Resultados em 15-30 minutos, não em horas</p>
                    </div>
                    <div class="feature">
                        <h4>🎯 Preciso</h4>
                        <p>Validação cruzada com múltiplas fontes</p>
                    </div>
                    <div class="feature">
                        <h4>📊 Profissional</h4>
                        <p>Classificações e scores detalhados</p>
                    </div>
                    <div class="feature">
                        <h4>🔒 Seguro</h4>
                        <p>Acesso controlado com chave de licença</p>
                    </div>
                </div>
            </div>
            
            <!-- Seção: Módulos -->
            <div class="section">
                <h2>📚 Módulos de Análise</h2>
                <p>O prompt inclui 16 módulos especializados:</p>
                <div class="modules">
                    <h4>Análise Fundamentalista Completa:</h4>
                    <ul>
                        <li>Papel e Escopo</li>
                        <li>Regras Absolutas</li>
                        <li>Dados Críticos</li>
                        <li>Modos de Análise</li>
                        <li>Uso de PDFs</li>
                        <li>Fórmulas Financeiras</li>
                        <li>Definições Técnicas</li>
                        <li>Filtros de Risco</li>
                        <li>Sistema de Scoring</li>
                        <li>Tratamentos Especiais</li>
                        <li>Validação Humana</li>
                        <li>Disclaimers Legais</li>
                        <li>Fontes Secundárias</li>
                        <li>Análise de Oportunidades</li>
                        <li>Avaliação com IA</li>
                        <li>Roadmap para 10/10</li>
                    </ul>
                </div>
            </div>
            
            <!-- Seção: Como Funciona -->
            <div class="section">
                <h2>🚀 Como Funciona</h2>
                <div class="steps">
                    <div class="step">
                        <div class="step-number">1</div>
                        <div class="step-content">
                            <h4>Compre uma Licença</h4>
                            <p>Escolha entre Trial (7 dias) ou Profissional (1 ano)</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">2</div>
                        <div class="step-content">
                            <h4>Receba sua Chave</h4>
                            <p>Você receberá uma chave única de acesso por email</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">3</div>
                        <div class="step-content">
                            <h4>Cole o Prompt em Claude/ChatGPT</h4>
                            <p>Copie o prompt com sua chave pré-preenchida</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">4</div>
                        <div class="step-content">
                            <h4>Forneça os Dados</h4>
                            <p>Cole um relatório financeiro (DFP/ITR) ou ticker da ação</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">5</div>
                        <div class="step-content">
                            <h4>Receba a Análise</h4>
                            <p>Classificação, scores e recomendações profissionais</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Seção: Comprar -->
            <div class="section">
                <h2>💳 Comprar Licença</h2>
                <p>Escolha entre Trial (7 dias) ou Profissional (1 ano) e comece a usar agora!</p>
                <div style="display: flex; justify-content: center; margin: 30px 0;">
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 12px; text-align: center; max-width: 400px;">
                        <h3 style="color: #667eea; margin-bottom: 20px;">💰 Licença Profissional</h3>
                        <p style="font-size: 2em; color: #333; font-weight: bold; margin-bottom: 20px;">R$ 50,00</p>
                        <p style="color: #666; margin-bottom: 30px;">1 ano de acesso completo</p>
                        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <img src="data:image/png;base64,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
            
            <!-- Seção: Próximos Passos -->
            <div class="section">
                <h2>📋 Próximos Passos</h2>
                <h3>Se você JÁ tem uma chave:</h3>
                <p>Clique em "Validar Chave e Começar" acima. Você será redirecionado para a página de validação onde poderá inserir sua chave.</p>
                
                <h3>Se você NÃO tem uma chave:</h3>
                <p>Entre em contato conosco para comprar uma licença. Você receberá uma chave única que funcionará em Claude, ChatGPT ou qualquer IA compatível.</p>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Prompt Fundamentalista B3 v3.0</strong></p>
            <p>Análise Profissional de Ações da B3</p>
            <p>© 2026 — Todos os direitos reservados</p>
        </div>
    </div>
</body>
</html>'''
    return render_template_string(html)

@app.route('/validar')
def validar():
    """Página de validação de chave"""
    html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validar Chave</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { background: white; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 600px; width: 100%; padding: 40px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #667eea; font-size: 28px; margin-bottom: 10px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: bold; }
        input { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        input:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }
        button:hover { opacity: 0.9; }
        .resultado { margin-top: 20px; padding: 15px; border-radius: 8px; display: none; }
        .sucesso { background: #e8f5e9; border: 2px solid #4caf50; color: #2e7d32; }
        .erro { background: #ffebee; border: 2px solid #f44336; color: #c62828; }
        .back { text-align: center; margin-top: 20px; }
        .back a { color: #667eea; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Validar Chave</h1>
        </div>
        
        <form id="form">
            <div class="form-group">
                <label for="chave">Digite sua chave:</label>
                <input type="text" id="chave" placeholder="PROMPT-XXXXXXXXXXXXXXXX" required autofocus>
            </div>
            <button type="submit">Validar</button>
        </form>
        
        <div id="resultado" class="resultado"></div>
        
        <div class="back">
            <a href="/">← Voltar</a>
        </div>
    </div>
    
    <script>
        document.getElementById('form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const chave = document.getElementById('chave').value;
            const resultado = document.getElementById('resultado');
            
            try {
                const response = await fetch('/api/validar-assinatura', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chave: chave })
                });
                
                const data = await response.json();
                
                if (data.valida) {
                    resultado.className = 'resultado sucesso';
                    resultado.innerHTML = `✅ Chave válida!<br>Válida até: ${data.data_expiracao}`;
                } else {
                    resultado.className = 'resultado erro';
                    resultado.innerHTML = `❌ ${data.mensagem}`;
                }
                resultado.style.display = 'block';
            } catch (error) {
                resultado.className = 'resultado erro';
                resultado.innerHTML = `❌ Erro: ${error.message}`;
                resultado.style.display = 'block';
            }
        });
    </script>
</body>
</html>'''
    return render_template_string(html)

# =====================
# API DE VALIDAÇÃO
# =====================

@app.route('/api/validar-assinatura', methods=['POST'])
def api_validar_assinatura():
    """API para validar assinatura"""
    data = request.get_json()
    chave = data.get('chave', '').strip()
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM clientes WHERE chave = ? AND ativo = 1', (chave,))
    cliente = c.fetchone()
    
    if not cliente:
        conn.close()
        return jsonify({
            'valida': False,
            'mensagem': 'Chave não encontrada'
        })
    
    # Verificar expiração
    data_expiracao = datetime.strptime(cliente['data_expiracao'], '%Y-%m-%d')
    agora = datetime.now()
    
    if agora > data_expiracao:
        conn.close()
        return jsonify({
            'valida': False,
            'mensagem': f'Sua assinatura expirou em {cliente["data_expiracao"]}'
        })
    
    # Registrar acesso
    c.execute('INSERT INTO acessos (cliente_id) VALUES (?)', (cliente['id'],))
    conn.commit()
    conn.close()
    
    return jsonify({
        'valida': True,
        'mensagem': 'Chave válida',
        'data_expiracao': cliente['data_expiracao'],
        'nome': cliente['nome']
    })

# =====================
# PAINEL ADMIN
# =====================

@app.route('/admin')
def admin():
    """Painel admin - listar clientes"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM clientes ORDER BY criado_em DESC')
    clientes = c.fetchall()
    conn.close()
    
    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Admin</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 2em; }}
        .btn {{ padding: 10px 20px; background: white; color: #667eea; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; text-decoration: none; display: inline-block; }}
        .btn:hover {{ opacity: 0.9; }}
        .content {{ padding: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; font-weight: bold; color: #667eea; }}
        tr:hover {{ background: #f9f9f9; }}
        .btn-delete {{ background: #f44336; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em; }}
        .btn-delete:hover {{ opacity: 0.9; }}
        .btn-novo {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; margin-bottom: 20px; }}
        .footer {{ background: #f8f9fa; padding: 20px 30px; text-align: center; color: #666; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>👨‍💼 Painel Admin</h1>
            <a href="/" class="btn">← Voltar</a>
        </div>
        
        <div class="content">
            <a href="/admin/novo-cliente" class="btn btn-novo">➕ Novo Cliente</a>
            
            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Chave</th>
                        <th>Compra</th>
                        <th>Expiração</th>
                        <th>Status</th>
                        <th>Ação</th>
                    </tr>
                </thead>
                <tbody>
'''
    
    for cliente in clientes:
        status = "✅ Ativo" if cliente['ativo'] else "❌ Inativo"
        html += f'''
                    <tr>
                        <td>{cliente['nome']}</td>
                        <td>{cliente['email']}</td>
                        <td><code>{cliente['chave']}</code></td>
                        <td>{cliente['data_compra']}</td>
                        <td>{cliente['data_expiracao']}</td>
                        <td>{status}</td>
                        <td>
                            <button class="btn-delete" onclick="deletarCliente({cliente['id']})">Deletar</button>
                        </td>
                    </tr>
'''
    
    html += '''
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p><strong>Prompt Fundamentalista B3 - Admin</strong></p>
            <p>© 2026 — Todos os direitos reservados</p>
        </div>
    </div>
    
    <script>
        function deletarCliente(id) {
            if (confirm('Tem certeza que quer deletar este cliente?')) {
                fetch(`/admin/deletar/${id}`, { method: 'DELETE' })
                    .then(() => location.reload());
            }
        }
    </script>
</body>
</html>'''
    
    return render_template_string(html)

@app.route('/admin/novo-cliente', methods=['GET', 'POST'])
def novo_cliente():
    """Criar novo cliente"""
    if request.method == 'POST':
        data = request.get_json()
        nome = data.get('nome')
        email = data.get('email')
        data_compra = data.get('data_compra')
        dias = int(data.get('dias', 365))
        
        chave = gerar_chave()
        data_expiracao = (datetime.strptime(data_compra, '%Y-%m-%d') + timedelta(days=dias)).strftime('%Y-%m-%d')
        
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('''
                INSERT INTO clientes (nome, email, chave, data_compra, data_expiracao)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, email, chave, data_compra, data_expiracao))
            conn.commit()
            conn.close()
            
            return jsonify({
                'sucesso': True,
                'chave': chave,
                'data_expiracao': data_expiracao
            })
        except Exception as e:
            return jsonify({'sucesso': False, 'erro': str(e)})
    
    html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novo Cliente</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { background: white; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 600px; width: 100%; padding: 40px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #667eea; font-size: 28px; margin-bottom: 10px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: bold; }
        input { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        input:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }
        button:hover { opacity: 0.9; }
        .resultado { margin-top: 20px; padding: 15px; border-radius: 8px; display: none; }
        .sucesso { background: #e8f5e9; border: 2px solid #4caf50; color: #2e7d32; }
        .back { text-align: center; margin-top: 20px; }
        .back a { color: #667eea; text-decoration: none; font-weight: bold; }
        code { background: #f5f5f5; padding: 5px 10px; border-radius: 4px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>➕ Novo Cliente</h1>
        </div>
        
        <form id="form">
            <div class="form-group">
                <label for="nome">Nome:</label>
                <input type="text" id="nome" required>
            </div>
            
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" required>
            </div>
            
            <div class="form-group">
                <label for="data_compra">Data de Compra:</label>
                <input type="date" id="data_compra" required>
            </div>
            
            <div class="form-group">
                <label for="dias">Dias de Acesso:</label>
                <input type="number" id="dias" value="365" required>
            </div>
            
            <button type="submit">Criar Cliente</button>
        </form>
        
        <div id="resultado" class="resultado"></div>
        
        <div class="back">
            <a href="/admin">← Voltar</a>
        </div>
    </div>
    
    <script>
        document.getElementById('form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                nome: document.getElementById('nome').value,
                email: document.getElementById('email').value,
                data_compra: document.getElementById('data_compra').value,
                dias: document.getElementById('dias').value
            };
            
            const response = await fetch('/admin/novo-cliente', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const resultado = await response.json();
            const resultDiv = document.getElementById('resultado');
            
            if (resultado.sucesso) {
                resultDiv.className = 'resultado sucesso';
                resultDiv.innerHTML = `
                    ✅ Cliente criado com sucesso!<br><br>
                    <strong>Chave:</strong> <code>${resultado.chave}</code><br>
                    <strong>Expira em:</strong> ${resultado.data_expiracao}<br><br>
                    <a href="/admin" style="color: #2e7d32; text-decoration: none; font-weight: bold;">← Voltar ao Admin</a>
                `;
            } else {
                resultDiv.className = 'resultado erro';
                resultDiv.innerHTML = `❌ Erro: ${resultado.erro}`;
            }
            resultDiv.style.display = 'block';
        });
    </script>
</body>
</html>'''
    
    return render_template_string(html)

@app.route('/admin/deletar/<int:cliente_id>', methods=['DELETE'])
def deletar_cliente(cliente_id):
    """Deletar cliente"""
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'sucesso': True})

# =====================
# INICIALIZAÇÃO
# =====================

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
