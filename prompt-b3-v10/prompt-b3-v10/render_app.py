#!/usr/bin/env python3
"""
Prompt Fundamentalista B3 - Web Server com Download Protegido por Chave
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from datetime import datetime, timedelta
import os
import base64
import io
import qrcode

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

# Conteúdo do prompt completo
PROMPT_CONTENT = """# 🔐 PROMPT FUNDAMENTALISTA B3 - COM VALIDAÇÃO DE CHAVE

## ⚠️ ATENÇÃO: VALIDAÇÃO DE LICENÇA OBRIGATÓRIA

Antes de começar, você precisa fornecer sua **chave de licença**. Este prompt requer autenticação.

---

## 🔑 PASSO 1: FORNEÇA SUA CHAVE

**Você tem uma chave?**

- ✅ **SIM** → Cole sua chave abaixo e continue
- ❌ **NÃO** → Compre uma licença em: https://prompt-b3.onrender.com

**Cole sua chave aqui:**
```
PROMPT-TRIAL-XXXXXXX-XXXXXXX-7DIAS
```

---

## 🔐 VALIDAÇÃO DE CHAVE

Sua chave será validada contra os seguintes critérios:

| Critério | Descrição | Status |
|---|---|---|
| **Formato** | Começa com "PROMPT-" | ✓ |
| **Comprimento** | Tem 34 caracteres | ✓ |
| **Validade** | Não expirou | ✓ |
| **Tipo** | Trial ou Profissional | ✓ |

---

## 🚨 IMPORTANTE

**Sem chave válida, o prompt não funcionará.**

Isso garante que:
- ✓ Apenas usuários autorizados usem o prompt
- ✓ Você controle o acesso
- ✓ Haja rastreamento de uso
- ✓ Seu trabalho seja protegido

---

## 🎯 PRÓXIMOS PASSOS

1. **Compre sua chave** em: https://prompt-b3.onrender.com
2. **Cole a chave acima**
3. **Aguarde validação**
4. **Comece a análise!**

---

## ❓ DÚVIDAS?

**P: Minha chave expirou?**  
R: Compre uma nova em: https://prompt-b3.onrender.com

**P: Perdi minha chave?**  
R: Entre em contato: pegardini@uol.com.br

**P: Posso usar em múltiplos computadores?**  
R: Sim, a mesma chave funciona em até 1 dispositivo (trial) ou ilimitado (profissional).

---

## ✅ VALIDAÇÃO AUTOMÁTICA

Quando você colar sua chave, o Claude validará automaticamente:

```
🔍 Validando chave...
✓ Formato correto
✓ Chave ativa
✓ Não expirada
✓ Acesso autorizado

✅ CHAVE VÁLIDA!
Bem-vindo!
Você tem 7 dias de acesso.
```

---

# 🎉 BEM-VINDO AO PROMPT FUNDAMENTALISTA B3

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
   - **Módulo 1**: Análise para DIVIDENDOS
   - **Módulo 2**: Análise para CRESCIMENTO
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

**Análise em progresso...** ⏳

Aguarde 15-30 minutos para resultado completo.

---

## 📞 SUPORTE

Email: pegardini@uol.com.br
Site: https://prompt-b3.onrender.com
"""

def gerar_qr_code_base64():
    """Gera QR Code como base64 dinamicamente"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(PIX_KEY)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    except Exception as e:
        print(f"Erro ao gerar QR Code: {e}")
        return None

def get_header_html():
    """Retorna o header HTML com navegação"""
    return '''
    <header style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 20px; color: white; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="font-size: 1.3em; font-weight: bold;">
            <a href="/" style="color: white; text-decoration: none;">📊 Prompt B3</a>
        </div>
        <nav style="display: flex; gap: 20px;">
            <a href="/" style="color: white; text-decoration: none; font-weight: 500;">Início</a>
            <a href="/documentacao" style="color: white; text-decoration: none; font-weight: 500;">Documentação</a>
            <a href="/validar" style="color: white; text-decoration: none; font-weight: 500;">Validar</a>
            <a href="/download" style="color: white; text-decoration: none; font-weight: 500;">Download</a>
        </nav>
    </header>
    '''

@app.route('/')
def index():
    qr_base64 = gerar_qr_code_base64()
    
    qr_html = ""
    if qr_base64:
        qr_html = f'<img src="data:image/png;base64,{qr_base64}" alt="QR Code PIX" style="width: 250px; height: 250px; margin: 20px 0; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">'
    else:
        qr_html = '<div style="width: 250px; height: 250px; background: #f0f0f0; margin: 20px 0; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #999;">QR Code não disponível</div>'
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Prompt Fundamentalista B3</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; padding-top: 0; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header-title {{ text-align: center; color: white; margin: 40px 0 20px 0; }}
        .header-title h1 {{ font-size: 2.5em; margin-bottom: 10px; font-weight: 700; }}
        .header-title p {{ font-size: 1.1em; opacity: 0.9; }}
        .content {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
        .card {{ background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .card h2 {{ color: #667eea; margin-bottom: 20px; font-size: 1.5em; }}
        .card p {{ color: #555; line-height: 1.8; margin-bottom: 15px; }}
        .card ul {{ margin-left: 20px; color: #555; }}
        .card li {{ margin-bottom: 10px; }}
        .btn {{ display: block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px; border: none; border-radius: 8px; font-size: 1em; font-weight: bold; cursor: pointer; width: 100%; margin-top: 20px; text-align: center; text-decoration: none; transition: all 0.3s; }}
        .btn:hover {{ opacity: 0.9; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }}
        .btn-secondary {{ background: #e0e0e0; color: #333; }}
        .btn-secondary:hover {{ background: #d0d0d0; }}
        .btn-link {{ background: transparent; color: #667eea; border: 2px solid #667eea; padding: 10px; margin-top: 10px; }}
        .btn-link:hover {{ background: #667eea; color: white; }}
        .info {{ background: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin: 15px 0; border-radius: 5px; color: #1565c0; }}
        .warning {{ background: #ffebee; border: 2px solid #f44336; padding: 15px; margin: 15px 0; border-radius: 5px; color: #c62828; }}
        .price {{ background: #fff3cd; border: 2px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center; color: #856404; }}
        .price h3 {{ font-size: 1.8em; margin-bottom: 10px; font-weight: 700; }}
        .qr-container {{ text-align: center; background: #f5f5f5; padding: 30px; border-radius: 8px; margin: 20px 0; }}
        .qr-container p {{ color: #666; margin-top: 15px; font-size: 0.95em; }}
        .pix-key {{ background: white; border: 2px solid #667eea; padding: 12px; border-radius: 8px; margin: 10px 0; font-family: monospace; font-weight: bold; color: #667eea; word-break: break-all; }}
        .step {{ margin-bottom: 20px; }}
        .step-number {{ display: inline-block; background: #667eea; color: white; width: 30px; height: 30px; border-radius: 50%; text-align: center; line-height: 30px; margin-right: 10px; font-weight: bold; }}
        .step-text {{ display: inline-block; color: #333; }}
        @media (max-width: 768px) {{ 
            .content {{ grid-template-columns: 1fr; }} 
            .header-title h1 {{ font-size: 1.8em; }} 
        }}
    </style>
</head>
<body>
    {get_header_html()}
    
    <div class="container">
        <div class="header-title">
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
                
                <a href="/documentacao" class="btn btn-link">📖 Saiba Mais Sobre o Projeto</a>
            </div>
            
            <div class="card">
                <h2>Como Começar?</h2>
                
                <div class="price">
                    <h3>💰 R$ {VALOR:.2f}/ano</h3>
                    <p>Licença anual com suporte</p>
                </div>
                
                <div class="step">
                    <span class="step-number">1</span>
                    <span class="step-text"><strong>Escaneie o QR Code</strong></span>
                </div>
                
                <div class="qr-container">
                    {qr_html}
                    <p><strong>Ou copie a chave PIX:</strong></p>
                    <div class="pix-key">{PIX_KEY}</div>
                </div>
                
                <div class="step">
                    <span class="step-number">2</span>
                    <span class="step-text"><strong>Envie o Comprovante</strong></span>
                </div>
                
                <p style="margin-top: 15px; color: #555;">Clique no botão abaixo para enviar o comprovante:</p>
                
                <a href="mailto:{EMAIL}?subject=Comprovante%20de%20Pagamento%20-%20Prompt%20B3&body=Olá%2C%0A%0AEstou%20enviando%20o%20comprovante%20de%20pagamento%20do%20Prompt%20Fundamentalista%20B3.%0A%0AObrigado!" class="btn">📧 Enviar Comprovante</a>
                
                <div class="step" style="margin-top: 20px;">
                    <span class="step-number">3</span>
                    <span class="step-text"><strong>Receba a Chave</strong></span>
                </div>
                
                <p style="color: #555; margin-bottom: 15px;">Você receberá sua chave de licença por email em até 24 horas.</p>
                
                <a href="/download" class="btn">📥 Baixar Prompt</a>
                <button class="btn btn-secondary" onclick="window.location.href='/validar'">🔐 Validar Chave</button>
                
                <div class="info" style="margin-top: 30px;">
                    <strong>💡 Teste Grátis</strong>
                    <p style="margin-top: 10px;">7 dias de teste. Depois, compre a licença anual!</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
    return render_template_string(html)

@app.route('/download')
def download_page():
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Download - Prompt Fundamentalista B3</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); max-width: 600px; width: 100%; padding: 40px; }
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
        .info { background: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin: 15px 0; border-radius: 5px; color: #1565c0; font-size: 0.95em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📥 Download do Prompt</h1>
            <p>Validação de Chave Obrigatória</p>
        </div>
        
        <div class="info">
            <strong>🔐 Segurança</strong>
            <p>Para baixar o prompt, você precisa validar sua chave de licença.</p>
        </div>
        
        <form id="form">
            <div class="form-group">
                <label for="chave">Digite sua chave de licença:</label>
                <input type="text" id="chave" placeholder="PROMPT-TRIAL-XXXXXXX-XXXXXXX-7DIAS" required autofocus>
            </div>
            <button type="submit">🔓 Validar e Baixar</button>
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
                const response = await fetch('/api/validar-download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chave: chave })
                });
                
                const data = await response.json();
                
                if (data.valida) {
                    resultado.className = 'resultado sucesso';
                    resultado.innerHTML = `✅ ${data.mensagem}<br>Preparando download...`;
                    resultado.style.display = 'block';
                    
                    // Aguarda 1 segundo e faz o download
                    setTimeout(() => {
                        window.location.href = '/api/download-prompt?chave=' + encodeURIComponent(chave);
                    }, 1000);
                } else {
                    resultado.className = 'resultado erro';
                    resultado.innerHTML = `❌ ${data.mensagem}`;
                    resultado.style.display = 'block';
                }
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

@app.route('/api/validar-download', methods=['POST'])
def api_validar_download():
    data = request.get_json()
    chave = data.get('chave', '').strip()
    
    if chave in CHAVES:
        return jsonify({
            'valida': True,
            'mensagem': f'Chave válida! Baixando...'
        })
    
    return jsonify({
        'valida': False,
        'mensagem': 'Chave não encontrada. Verifique se digitou corretamente.'
    })

@app.route('/api/download-prompt')
def api_download_prompt():
    chave = request.args.get('chave', '').strip()
    
    # Valida chave
    if chave not in CHAVES:
        return jsonify({'erro': 'Chave inválida'}), 403
    
    # Cria arquivo em memória
    buffer = io.BytesIO()
    buffer.write(PROMPT_CONTENT.encode('utf-8'))
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='text/plain',
        as_attachment=True,
        download_name='PROMPT_FUNDAMENTALISTA_B3.txt'
    )

@app.route('/documentacao')
def documentacao():
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Documentação - Prompt Fundamentalista B3</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; padding-top: 0; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        .content {{ background: white; border-radius: 15px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-top: 20px; }}
        h1 {{ color: #667eea; font-size: 2em; margin-bottom: 30px; }}
        h2 {{ color: #667eea; font-size: 1.5em; margin-top: 30px; margin-bottom: 15px; }}
        p {{ color: #555; line-height: 1.8; margin-bottom: 15px; }}
        ul {{ margin-left: 20px; color: #555; margin-bottom: 15px; }}
        li {{ margin-bottom: 10px; }}
        .section {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
        .faq-item {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 8px; }}
        .faq-item strong {{ color: #667eea; }}
        .btn {{ display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 12px 30px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; text-decoration: none; margin-top: 20px; }}
        .btn:hover {{ opacity: 0.9; }}
    </style>
</head>
<body>
    {get_header_html()}
    
    <div class="container">
        <div class="content">
            <h1>📖 Documentação - Prompt Fundamentalista B3</h1>
            
            <h2>O Que é o Projeto?</h2>
            <p>O Prompt Fundamentalista B3 é uma ferramenta de análise profissional desenvolvida para investidores que desejam realizar análises fundamentalistas detalhadas de ações listadas na Bolsa de Valores do Brasil (B3).</p>
            
            <p>Este projeto nasceu da necessidade de ter um sistema estruturado, completo e acessível para análise de empresas brasileiras, utilizando inteligência artificial para processar e organizar dados financeiros.</p>
            
            <h2>Ideia Principal</h2>
            <div class="section">
                <p><strong>Democratizar a análise fundamentalista</strong> tornando-a acessível para investidores de todos os níveis, desde iniciantes até profissionais.</p>
                
                <p>Ao invés de gastar horas pesquisando e organizando dados, o usuário pode simplesmente fornecer o nome da ação e receber uma análise completa e estruturada.</p>
            </div>
            
            <h2>Como Funciona?</h2>
            <ol style="margin-left: 20px; color: #555; line-height: 1.8;">
                <li><strong>Você fornece o nome da ação</strong> (ex: VALE3, PETR4)</li>
                <li><strong>O prompt processa os dados</strong> usando inteligência artificial</li>
                <li><strong>Você recebe uma análise completa</strong> com 16 módulos técnicos</li>
                <li><strong>Você toma decisões informadas</strong> baseado em dados reais</li>
            </ol>
            
            <h2>16 Módulos Técnicos</h2>
            <div class="section">
                <ul>
                    <li>📊 Análise de Lucro e Rentabilidade</li>
                    <li>💰 Dividendos e Proventos</li>
                    <li>📈 Dívida e Alavancagem</li>
                    <li>⚠️ Riscos e Oportunidades</li>
                    <li>🏆 Comparação com Concorrentes</li>
                    <li>💹 Análise de Fluxo de Caixa</li>
                    <li>📉 Histórico de Preços</li>
                    <li>🎯 Projeções Futuras</li>
                    <li>📋 Dados Fundamentalistas</li>
                    <li>🔍 Análise SWOT</li>
                    <li>💼 Governança Corporativa</li>
                    <li>🌍 Contexto de Mercado</li>
                    <li>📊 Valuation</li>
                    <li>🎲 Análise de Risco</li>
                    <li>📈 Tendências do Setor</li>
                    <li>🎓 Recomendações Finais</li>
                </ul>
            </div>
            
            <h2>Por Que Usar?</h2>
            <ul>
                <li>✅ <strong>Economia de Tempo:</strong> Análise completa em minutos</li>
                <li>✅ <strong>Profissionalismo:</strong> Estrutura e rigor técnico</li>
                <li>✅ <strong>Acessibilidade:</strong> Preço justo (R$ 50/ano)</li>
                <li>✅ <strong>Confiabilidade:</strong> Baseado em dados reais</li>
                <li>✅ <strong>Suporte:</strong> Ajuda disponível quando precisar</li>
            </ul>
            
            <h2>Perguntas Frequentes</h2>
            
            <div class="faq-item">
                <strong>P: É recomendação de investimento?</strong>
                <p>R: Não. Este é uma ferramenta de análise. Sempre consulte um profissional antes de investir.</p>
            </div>
            
            <div class="faq-item">
                <strong>P: Posso usar em qualquer ação?</strong>
                <p>R: Sim! O prompt funciona com qualquer ação listada na B3.</p>
            </div>
            
            <div class="faq-item">
                <strong>P: Quanto tempo dura a licença?</strong>
                <p>R: A licença é anual. Você pode renovar a qualquer momento.</p>
            </div>
            
            <div class="faq-item">
                <strong>P: Posso compartilhar com amigos?</strong>
                <p>R: A licença é pessoal. Cada pessoa precisa de sua própria licença.</p>
            </div>
            
            <div class="faq-item">
                <strong>P: Como funciona o teste grátis?</strong>
                <p>R: Você tem 7 dias para testar. Depois, você pode comprar a licença anual.</p>
            </div>
            
            <h2>Contato e Suporte</h2>
            <p>Tem dúvidas? Entre em contato conosco:</p>
            <p><strong>Email:</strong> <a href="mailto:{EMAIL}">{EMAIL}</a></p>
            
            <a href="/" class="btn">← Voltar para Início</a>
        </div>
    </div>
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
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
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
