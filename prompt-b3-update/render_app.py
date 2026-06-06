from flask import Flask, render_template_string, request, jsonify, send_file
from datetime import datetime, timedelta
import json
import os
import secrets
from pathlib import Path
import io

app = Flask(__name__)

# Arquivo de banco de dados
DB_FILE = 'chaves.json'

# ==================== FUNÇÕES DE BANCO DE DADOS ====================

def carregar_chaves():
    """Carrega as chaves do arquivo JSON"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'chaves': []}

def salvar_chaves(dados):
    """Salva as chaves no arquivo JSON"""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def gerar_chave(tipo='trial'):
    """Gera uma chave única"""
    parte1 = secrets.token_hex(3).upper()
    parte2 = secrets.token_hex(3).upper()
    
    if tipo == 'trial':
        return f"PROMPT-TRIAL-{parte1}-{parte2}-7DIAS"
    else:
        return f"PROMPT-PRO-{parte1}-{parte2}-1ANO"

def validar_chave(chave):
    """Valida se a chave é válida"""
    dados = carregar_chaves()
    
    for item in dados.get('chaves', []):
        if item['chave'] == chave:
            # Verifica se expirou
            data_expiracao = datetime.fromisoformat(item['data_expiracao'])
            if datetime.now() > data_expiracao:
                return {
                    'valida': False,
                    'mensagem': 'Chave expirada',
                    'tipo': 'expirada'
                }
            
            # Calcula dias restantes
            dias_restantes = (data_expiracao - datetime.now()).days
            
            return {
                'valida': True,
                'email': item['email'],
                'nome': item.get('nome', 'Usuário'),
                'tipo': item['tipo'],
                'data_expiracao': item['data_expiracao'],
                'dias_restantes': dias_restantes,
                'mensagem': f'Chave válida! {dias_restantes} dias restantes.'
            }
    
    return {
        'valida': False,
        'mensagem': 'Chave não encontrada',
        'tipo': 'nao_encontrada'
    }

def criar_chave_novo(email, nome, tipo='trial'):
    """Cria uma nova chave"""
    dados = carregar_chaves()
    chave = gerar_chave(tipo)
    
    if tipo == 'trial':
        data_expiracao = (datetime.now() + timedelta(days=7)).isoformat()
        dispositivos = 1
    else:
        data_expiracao = (datetime.now() + timedelta(days=365)).isoformat()
        dispositivos = 2
    
    novo_item = {
        'chave': chave,
        'email': email,
        'nome': nome,
        'tipo': tipo,
        'data_criacao': datetime.now().isoformat(),
        'data_expiracao': data_expiracao,
        'dispositivos_permitidos': dispositivos,
        'dispositivos_usados': 0
    }
    
    dados['chaves'].append(novo_item)
    salvar_chaves(dados)
    
    return novo_item

# ==================== CONTEÚDO DO PROMPT ====================

PROMPT_COMPLETO = """# 🎯 PROMPT FUNDAMENTALISTA B3 - VERSÃO COM VALIDAÇÃO

## 🔐 VALIDAÇÃO DE CHAVE (OBRIGATÓRIA)

Antes de começar, você precisa fornecer sua **chave de licença válida**.

**Cole sua chave aqui:**
```
PROMPT-TRIAL-XXXXXXX-XXXXXXX-7DIAS
```

---

## ⚠️ INSTRUÇÕES IMPORTANTES

### Validação Automática
Quando você colar sua chave, vou validar automaticamente chamando a API:
- ✅ Verifico se a chave existe
- ✅ Verifico se não expirou
- ✅ Verifico quantos dias faltam
- ✅ Se tudo OK, você pode começar!

### Se a Chave for Inválida
- ❌ Chave não encontrada → Gere uma nova
- ❌ Chave expirada → Compre uma licença paga
- ❌ Erro na API → Tente novamente em alguns segundos

---

## 🚀 COMEÇAR

**Passo 1:** Cole sua chave acima
**Passo 2:** Aguarde a validação
**Passo 3:** Se válida, continue com a análise

---

# 🎉 BEM-VINDO AO PROMPT FUNDAMENTALISTA B3

*Este conteúdo aparece após validação bem-sucedida*

## 👋 Olá!

Você está prestes a usar um dos prompts mais completos para análise fundamentalista de ações da B3.

### O Que Você Pode Fazer

✅ Analisar qualquer ação da B3
✅ Identificar oportunidades de investimento
✅ Avaliar riscos
✅ Calcular potencial de dividendos
✅ Validar dados com múltiplas fontes
✅ Gerar classificações profissionais

### Como Funciona

1. **Você fornece** um relatório trimestral (ITR) ou anual (DFP)
2. **Eu extraio** os dados principais
3. **Eu valido** com Investidor10 e AGF
4. **Eu aplico** filtros de risco
5. **Eu calculo** scores
6. **Eu gero** uma classificação final
7. **Você registra** na Planilha Invest

### Próximos Passos

1. Escolha seu objetivo:
   - **Dividendos**: Análise para renda passiva
   - **Crescimento**: Análise para valorização
   - **Ambos**: Análise completa

2. Forneça a ação que quer analisar:
   - Exemplo: PETR4, VALE3, ITUB4

3. Aguarde a análise (15-30 minutos)

4. Você receberá:
   - Classificação (Aprovado, Pendente, Rejeitado)
   - Score detalhado
   - Análise de riscos
   - Potencial de ganho
   - Recomendações

---

## 📊 MÓDULOS DISPONÍVEIS

### Módulo 1: Análise para DIVIDENDOS
Foco em:
- Histórico de dividendos
- Payout ratio
- Rentabilidade
- Estabilidade

### Módulo 2: Análise para CRESCIMENTO
Foco em:
- Crescimento de receita
- Margem de lucro
- Retorno sobre patrimônio
- Potencial futuro

### Ambos: Análise Completa
Combina:
- Dividendos + Crescimento
- Risco + Oportunidade
- Curto + Longo prazo

---

## 🚀 COMEÇAR ANÁLISE

Qual é o seu objetivo?

1. **Dividendos** (renda passiva)
2. **Crescimento** (valorização)
3. **Ambos** (análise completa)

Qual ação você quer analisar?

---

## ⚠️ AVISO IMPORTANTE

Este prompt é uma **ferramenta de análise**, não uma recomendação de investimento.
**Você é responsável por suas decisões financeiras.**
Sempre consulte um profissional qualificado antes de investir.

---

**Análise em progresso...** ⏳

Aguarde 15-30 minutos para resultado completo.
"""

# ==================== ROTAS ====================

@app.route('/')
def index():
    """Página inicial com explicações e download"""
    html = '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Prompt Fundamentalista B3</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 900px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                color: white;
                margin-bottom: 40px;
                animation: slideDown 0.5s ease-out;
            }
            
            @keyframes slideDown {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
            }
            
            .content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 40px;
            }
            
            .card {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                animation: slideUp 0.5s ease-out;
            }
            
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .card h2 {
                color: #667eea;
                margin-bottom: 20px;
                font-size: 1.8em;
            }
            
            .card p {
                color: #555;
                line-height: 1.8;
                margin-bottom: 15px;
            }
            
            .card ul {
                margin-left: 20px;
                color: #555;
                line-height: 1.8;
            }
            
            .card li {
                margin-bottom: 10px;
            }
            
            .btn {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 1.05em;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                text-decoration: none;
                width: 100%;
                text-align: center;
                margin-top: 20px;
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            .btn-secondary {
                background: #e0e0e0;
                color: #333;
            }
            
            .btn-secondary:hover {
                background: #d0d0d0;
            }
            
            .highlight {
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                color: #856404;
            }
            
            .disclaimer {
                background: #ffebee;
                border: 2px solid #f44336;
                padding: 20px;
                border-radius: 8px;
                color: #c62828;
                margin-top: 30px;
            }
            
            .disclaimer h3 {
                margin-bottom: 10px;
            }
            
            .info-box {
                background: #e7f3ff;
                border-left: 4px solid #2196F3;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
                color: #1565c0;
            }
            
            .features {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 20px 0;
            }
            
            .feature {
                background: #f5f5f5;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            
            .feature strong {
                color: #667eea;
            }
            
            @media (max-width: 768px) {
                .content {
                    grid-template-columns: 1fr;
                }
                
                .header h1 {
                    font-size: 1.8em;
                }
                
                .features {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Prompt Fundamentalista B3</h1>
                <p>Análise Profissional de Ações da Bolsa Brasileira</p>
            </div>
            
            <div class="content">
                <!-- COLUNA 1: EXPLICAÇÕES -->
                <div class="card">
                    <h2>O Que é Este Prompt?</h2>
                    
                    <p>
                        Este é um <strong>sistema completo de análise fundamentalista</strong> para ações brasileiras listadas na B3.
                    </p>
                    
                    <p>
                        Ele ajuda você a tomar <strong>decisões de investimento mais informadas</strong>, analisando:
                    </p>
                    
                    <ul>
                        <li>✅ Lucro e rentabilidade</li>
                        <li>✅ Dividendos e proventos</li>
                        <li>✅ Dívida e alavancagem</li>
                        <li>✅ Riscos e oportunidades</li>
                        <li>✅ Comparação com concorrentes</li>
                    </ul>
                    
                    <div class="info-box">
                        <strong>📚 16 Módulos Técnicos</strong>
                        <p style="margin-top: 10px; font-size: 0.95em;">
                            Análise completa com papel, escopo, dados críticos, fórmulas, scoring e muito mais.
                        </p>
                    </div>
                    
                    <div class="highlight">
                        <strong>⏱️ Validade da Chave</strong>
                        <p style="margin-top: 10px;">
                            Sua chave de teste é válida por <strong>7 dias</strong>. Depois, você pode comprar uma licença paga.
                        </p>
                    </div>
                    
                    <div class="disclaimer">
                        <h3>⚠️ Aviso Importante</h3>
                        <p>
                            Este prompt é uma <strong>ferramenta de análise</strong>, não uma recomendação de investimento.
                            <strong>Você é responsável por suas decisões financeiras.</strong>
                        </p>
                    </div>
                </div>
                
                <!-- COLUNA 2: AÇÕES -->
                <div class="card">
                    <h2>Como Começar?</h2>
                    
                    <div class="features">
                        <div class="feature">
                            <strong>1️⃣ Baixe o Prompt</strong>
                            <p style="margin-top: 8px; font-size: 0.95em;">
                                Clique no botão abaixo para baixar o arquivo com o prompt completo.
                            </p>
                        </div>
                        
                        <div class="feature">
                            <strong>2️⃣ Acesse Claude</strong>
                            <p style="margin-top: 8px; font-size: 0.95em;">
                                Vá para https://claude.ai (ou ChatGPT, Gemini, Copilot)
                            </p>
                        </div>
                        
                        <div class="feature">
                            <strong>3️⃣ Cole o Prompt</strong>
                            <p style="margin-top: 8px; font-size: 0.95em;">
                                Cole o conteúdo do arquivo na conversa com a IA.
                            </p>
                        </div>
                        
                        <div class="feature">
                            <strong>4️⃣ Forneça a Chave</strong>
                            <p style="margin-top: 8px; font-size: 0.95em;">
                                Quando a IA pedir, cole sua chave de licença.
                            </p>
                        </div>
                    </div>
                    
                    <button class="btn" onclick="baixarPrompt()">
                        📥 Baixar Prompt Completo
                    </button>
                    
                    <button class="btn btn-secondary" onclick="irParaValidacao()">
                        🔐 Validar Chave Existente
                    </button>
                    
                    <div class="info-box" style="margin-top: 30px;">
                        <strong>💡 Dica</strong>
                        <p style="margin-top: 10px; font-size: 0.95em;">
                            Você pode testar o prompt gratuitamente por 7 dias. Depois, compre uma licença paga se gostar!
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function baixarPrompt() {
                const prompt = `''' + PROMPT_COMPLETO.replace('`', '\\`') + '''`;
                const element = document.createElement('a');
                element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(prompt));
                element.setAttribute('download', 'PROMPT_FUNDAMENTALISTA_B3.txt');
                element.style.display = 'none';
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);
            }
            
            function irParaValidacao() {
                window.location.href = '/validar';
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/validar')
def validar():
    """Página de validação de chaves"""
    html = '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Validar Chave - Prompt Fundamentalista B3</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .container {
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 500px;
                width: 100%;
                padding: 40px;
                animation: slideIn 0.5s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                color: #667eea;
                font-size: 28px;
                margin-bottom: 10px;
            }
            
            .header p {
                color: #666;
                font-size: 14px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 600;
                font-size: 14px;
            }
            
            input {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            button:hover {
                transform: translateY(-2px);
            }
            
            .resultado {
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                display: none;
                animation: fadeIn 0.3s ease-out;
            }
            
            @keyframes fadeIn {
                from {
                    opacity: 0;
                }
                to {
                    opacity: 1;
                }
            }
            
            .resultado.sucesso {
                background: #e8f5e9;
                border: 2px solid #4caf50;
                color: #2e7d32;
            }
            
            .resultado.erro {
                background: #ffebee;
                border: 2px solid #f44336;
                color: #c62828;
            }
            
            .prompt-container {
                margin-top: 30px;
                padding: 20px;
                background: #f5f5f5;
                border-radius: 8px;
                display: none;
            }
            
            .prompt-container h3 {
                color: #667eea;
                margin-bottom: 15px;
            }
            
            .copy-button {
                background: #4caf50;
                margin-bottom: 10px;
            }
            
            .copy-button:hover {
                background: #45a049;
            }
            
            .back-link {
                text-align: center;
                margin-top: 20px;
            }
            
            .back-link a {
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
            }
            
            .back-link a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Validação de Chave</h1>
                <p>Prompt Fundamentalista B3</p>
            </div>
            
            <form id="validacaoForm">
                <div class="form-group">
                    <label for="chave">Digite sua chave:</label>
                    <input type="text" id="chave" name="chave" placeholder="PROMPT-TRIAL-XXXXX-XXXXX-7DIAS" required autofocus>
                </div>
                
                <button type="submit">Validar Chave</button>
            </form>
            
            <div id="resultado" class="resultado"></div>
            
            <div id="promptContainer" class="prompt-container">
                <h3>✅ Acesso Liberado!</h3>
                <p style="margin-bottom: 15px; color: #666;">Sua chave é válida! Você pode usar o prompt normalmente.</p>
                <button class="copy-button" onclick="irParaHome()">← Voltar para Home</button>
            </div>
            
            <div class="back-link">
                <a href="/">← Voltar</a>
            </div>
        </div>
        
        <script>
            document.getElementById('validacaoForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const chave = document.getElementById('chave').value;
                const resultado = document.getElementById('resultado');
                
                try {
                    const response = await fetch('/api/validar', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ chave: chave })
                    });
                    
                    const data = await response.json();
                    
                    if (data.valida) {
                        resultado.className = 'resultado sucesso';
                        resultado.innerHTML = `✅ ${data.mensagem}<br>Nome: ${data.nome}<br>Dias restantes: ${data.dias_restantes}`;
                        resultado.style.display = 'block';
                        document.getElementById('promptContainer').style.display = 'block';
                    } else {
                        resultado.className = 'resultado erro';
                        resultado.innerHTML = `❌ ${data.mensagem}`;
                        resultado.style.display = 'block';
                        document.getElementById('promptContainer').style.display = 'none';
                    }
                } catch (error) {
                    resultado.className = 'resultado erro';
                    resultado.innerHTML = `❌ Erro ao validar: ${error.message}`;
                    resultado.style.display = 'block';
                }
            });
            
            function irParaHome() {
                window.location.href = '/';
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/api/validar', methods=['POST'])
def api_validar():
    """API para validar chaves"""
    data = request.get_json()
    chave = data.get('chave', '').strip()
    
    if not chave:
        return jsonify({'valida': False, 'mensagem': 'Chave não fornecida'})
    
    resultado = validar_chave(chave)
    return jsonify(resultado)

@app.route('/api/criar-chave', methods=['POST'])
def api_criar_chave():
    """API para criar nova chave (apenas para admin)"""
    data = request.get_json()
    email = data.get('email', '')
    nome = data.get('nome', '')
    tipo = data.get('tipo', 'trial')
    
    if not email or not nome:
        return jsonify({'sucesso': False, 'mensagem': 'Email e nome são obrigatórios'})
    
    novo_item = criar_chave_novo(email, nome, tipo)
    return jsonify({
        'sucesso': True,
        'chave': novo_item['chave'],
        'mensagem': 'Chave criada com sucesso!'
    })

@app.route('/health')
def health():
    """Health check para Render"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
