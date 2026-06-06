#!/usr/bin/env python3
"""
Prompt Fundamentalista B3 - Web Server com PIX
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from datetime import datetime, timedelta
import os
import base64

app = Flask(__name__)

# Chaves válidas (em memória)
CHAVES = {
    'PROMPT-TRIAL-65C033-7339A6-7DIAS': {
        'nome': 'Teste',
        'dias': 7
    }
}

# Configurações
PIX_KEY = "055005108-27"
VALOR = 50.00
EMAIL = "pegardini@uol.com.br"

# QR Code em base64 (será carregado do arquivo)
QR_CODE_BASE64 = None

def carregar_qr_code():
    """Carrega o QR Code como base64"""
    global QR_CODE_BASE64
    try:
        with open('/home/ubuntu/qrcode_pix.png', 'rb') as f:
            QR_CODE_BASE64 = base64.b64encode(f.read()).decode()
    except:
        QR_CODE_BASE64 = None

carregar_qr_code()

@app.route('/')
def index():
    qr_html = ""
    if QR_CODE_BASE64:
        qr_html = f'<img src="data:image/png;base64,{QR_CODE_BASE64}" alt="QR Code PIX" style="width: 200px; height: 200px; margin: 20px 0;">'
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Prompt Fundamentalista B3</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{ text-align: center; color: white; margin-bottom: 40px; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .content {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
        .card {{ background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .card h2 {{ color: #667eea; margin-bottom: 20px; }}
        .card p {{ color: #555; line-height: 1.8; margin-bottom: 15px; }}
        .card ul {{ margin-left: 20px; color: #555; }}
        .card li {{ margin-bottom: 10px; }}
        .btn {{ display: block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px; border: none; border-radius: 8px; font-size: 1em; font-weight: bold; cursor: pointer; width: 100%; margin-top: 20px; text-align: center; text-decoration: none; }}
        .btn:hover {{ opacity: 0.9; }}
        .info {{ background: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin: 15px 0; border-radius: 5px; color: #1565c0; }}
        .warning {{ background: #ffebee; border: 2px solid #f44336; padding: 15px; margin: 15px 0; border-radius: 5px; color: #c62828; }}
        .price {{ background: #fff3cd; border: 2px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center; color: #856404; }}
        .price h3 {{ font-size: 1.5em; margin-bottom: 10px; }}
        .qr-container {{ text-align: center; background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .contact {{ background: #e8f5e9; border: 2px solid #4caf50; padding: 15px; margin: 15px 0; border-radius: 5px; color: #2e7d32; }}
        .contact a {{ color: #2e7d32; font-weight: bold; text-decoration: none; }}
        @media (max-width: 768px) {{ .content {{ grid-template-columns: 1fr; }} .header h1 {{ font-size: 1.8em; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Prompt Fundamentalista B3</h1>
            <p>Análise Profissional de Ações da B3</p>
        </div>
        
        <div class="content">
            <div class="card">
                <h2>O Que é Este Prompt?</h2>
                
                <p>Um sistema completo de análise fundamentalista para ações brasileiras.</p>
                
                <ul>
                    <li>✅ Análise de lucro e rentabilidade</li>
                    <li>✅ Dividendos e proventos</li>
                    <li>✅ Dívida e alavancagem</li>
                    <li>✅ Riscos e oportunidades</li>
                    <li>✅ Comparação com concorrentes</li>
                </ul>
                
                <div class="info">
                    <strong>📚 16 Módulos Técnicos</strong>
                    <p style="margin-top: 10px; font-size: 0.95em;">Análise completa com papel, escopo, dados críticos e muito mais.</p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Aviso Importante</strong>
                    <p>Este é uma ferramenta de análise, não recomendação de investimento.</p>
                </div>
            </div>
            
            <div class="card">
                <h2>Como Começar?</h2>
                
                <div class="price">
                    <h3>💰 R$ {VALOR:.2f}/ano</h3>
                    <p>Licença anual com suporte</p>
                </div>
                
                <p><strong>1. Pague via PIX</strong></p>
                <div class="qr-container">
                    {qr_html}
                    <p style="margin-top: 15px; color: #666;"><strong>Chave PIX:</strong> {PIX_KEY}</p>
                </div>
                
                <p><strong>2. Envie Comprovante</strong></p>
                <div class="contact">
                    <p>Envie o comprovante para: <a href="mailto:{EMAIL}">{EMAIL}</a></p>
                </div>
                
                <p><strong>3. Receba a Chave</strong></p>
                <p style="color: #555; margin-bottom: 15px;">Você receberá sua chave de licença por email</p>
                
                <button class="btn" onclick="baixarPrompt()">📥 Baixar Prompt (Teste Grátis)</button>
                <button class="btn" onclick="window.location.href='/validar'" style="background: #e0e0e0; color: #333;">🔐 Validar Chave</button>
                
                <div class="info" style="margin-top: 30px;">
                    <strong>💡 Teste Grátis</strong>
                    <p style="margin-top: 10px;">7 dias de teste. Depois, compre a licença anual!</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function baixarPrompt() {{
            const prompt = "# PROMPT FUNDAMENTALISTA B3\\n\\n## Validação de Chave\\nCole sua chave aqui: PROMPT-TRIAL-XXXXXXX-XXXXXXX-7DIAS\\n\\n## Bem-vindo!\\nEste é um sistema de análise fundamentalista para ações da B3.\\n\\nVocê pode analisar:\\n- Lucro e rentabilidade\\n- Dividendos\\n- Dívida\\n- Riscos\\n- Oportunidades\\n\\n## Aviso\\nEste é uma ferramenta de análise, não recomendação de investimento.";
            const element = document.createElement('a');
            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(prompt));
            element.setAttribute('download', 'PROMPT_FUNDAMENTALISTA_B3.txt');
            element.style.display = 'none';
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
        }}
    </script>
</body>
</html>'''
    return render_template_string(html)

@app.route('/validar')
def validar():
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Validar Chave</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); max-width: 500px; width: 100%; padding: 40px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #667eea; font-size: 28px; margin-bottom: 10px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: bold; }
        input { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        input:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }
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
            <p>Prompt Fundamentalista B3</p>
        </div>
        
        <form id="form">
            <div class="form-group">
                <label for="chave">Digite sua chave:</label>
                <input type="text" id="chave" placeholder="PROMPT-TRIAL-XXXXX-XXXXX-7DIAS" required autofocus>
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
                const response = await fetch('/api/validar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chave: chave })
                });
                
                const data = await response.json();
                
                if (data.valida) {
                    resultado.className = 'resultado sucesso';
                    resultado.innerHTML = `✅ ${data.mensagem}<br>Dias: ${data.dias}`;
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

@app.route('/api/validar', methods=['POST'])
def api_validar():
    data = request.get_json()
    chave = data.get('chave', '').strip()
    
    if chave in CHAVES:
        return jsonify({
            'valida': True,
            'mensagem': f'Chave válida!',
            'dias': CHAVES[chave]['dias']
        })
    
    return jsonify({
        'valida': False,
        'mensagem': 'Chave não encontrada'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
