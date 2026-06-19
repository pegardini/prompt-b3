import os
import sqlite3
import secrets
import string
import qrcode
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_file
from functools import wraps
import markdown
from weasyprint import HTML, CSS
import tempfile

app = Flask(__name__)
DB_PATH = 'database.db'

# Configurações de email
EMAIL_REMETENTE = "promptpegardini@gmail.com"
EMAIL_SENHA = "iacdonjyvifkqfna"  # Senha de app do Google (sem espaços)
EMAIL_ADMIN = "pegardini@protonmail.com"
EMAIL_DEBUG = "pegardini@gmail.com"  # Email para debug

def enviar_email_debug(assunto, corpo):
    """Envia email de debug para pegardini@gmail.com com o percurso da mensagem"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = EMAIL_DEBUG
        msg['Subject'] = assunto
        
        corpo_html = f"<pre style='font-family: monospace; white-space: pre-wrap;'>{corpo}</pre>"
        msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))
        
        servidor = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, EMAIL_SENHA)
        servidor.sendmail(EMAIL_REMETENTE, EMAIL_DEBUG, msg.as_string())
        servidor.quit()
        
        print(f"✅ Email de debug enviado para {EMAIL_DEBUG}")
    except Exception as e:
        print(f"❌ Erro ao enviar email de debug: {str(e)}")
        import traceback
        traceback.print_exc()

def enviar_email(destinatario, assunto, corpo):
    """Envia email via Gmail com debug detalhado"""
    debug_log = []
    
    try:
        debug_log.append(f"[1] Iniciando envio para: {destinatario}")
        print(f"[1] Iniciando envio para: {destinatario}")
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario
        msg['Subject'] = assunto
        debug_log.append(f"[2] Email headers criados")
        print(f"[2] Email headers criados")
        
        msg.attach(MIMEText(corpo, 'html', 'utf-8'))
        debug_log.append(f"[3] Corpo do email anexado ({len(corpo)} caracteres)")
        print(f"[3] Corpo do email anexado ({len(corpo)} caracteres)")
        
        debug_log.append(f"[4] Conectando ao SMTP: smtp.gmail.com:587")
        print(f"[4] Conectando ao SMTP: smtp.gmail.com:587")
        servidor = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        debug_log.append(f"[5] Conexão SMTP estabelecida")
        print(f"[5] Conexão SMTP estabelecida")
        
        debug_log.append(f"[6] Iniciando TLS")
        print(f"[6] Iniciando TLS")
        servidor.starttls()
        debug_log.append(f"[7] TLS ativado")
        print(f"[7] TLS ativado")
        
        debug_log.append(f"[8] Fazendo login com: {EMAIL_REMETENTE}")
        print(f"[8] Fazendo login com: {EMAIL_REMETENTE}")
        servidor.login(EMAIL_REMETENTE, EMAIL_SENHA)
        debug_log.append(f"[9] Login bem-sucedido")
        print(f"[9] Login bem-sucedido")
        
        debug_log.append(f"[10] Enviando email para {destinatario}...")
        print(f"[10] Enviando email para {destinatario}...")
        servidor.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())
        debug_log.append(f"[11] Email enviado com sucesso!")
        print(f"[11] Email enviado com sucesso!")
        
        debug_log.append(f"[12] Fechando conexão")
        print(f"[12] Fechando conexão")
        servidor.quit()
        debug_log.append(f"[13] ✅ SUCESSO - Email entregue ao servidor SMTP")
        print(f"[13] ✅ SUCESSO - Email entregue ao servidor SMTP")
        
        # Envia log de debug para o usuário
        log_msg = "\n".join(debug_log)
        enviar_email_debug(f"[DEBUG] Sucesso - {assunto}", log_msg)
        
        return True
    except Exception as e:
        debug_log.append(f"[❌] ERRO: {str(e)}")
        print(f"[❌] ERRO: {str(e)}")
        import traceback
        tb = traceback.format_exc()
        debug_log.append(tb)
        print(tb)
        
        # Envia log de erro para o usuário
        log_msg = "\n".join(debug_log)
        enviar_email_debug(f"[DEBUG] ERRO - {assunto}", log_msg)
        
        return False

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Tabela de chaves de licença
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chaves_licenca (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_expiracao TIMESTAMP NOT NULL,
                ativa BOOLEAN DEFAULT 1,
                tipo TEXT DEFAULT 'trial'
            )
        ''')
        
        # Tabela de requisições de teste
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requisicoes_teste (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                telefone TEXT,
                data_requisicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aprovada BOOLEAN DEFAULT 0,
                chave_gerada TEXT,
                email_enviado BOOLEAN DEFAULT 0
            )
        ''')
        
        # Tabela de configurações do admin
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave TEXT UNIQUE NOT NULL,
                valor TEXT NOT NULL,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insere a senha padrão do admin
        cursor.execute('''
            INSERT INTO admin_settings (chave, valor)
            VALUES ('admin_password', 'Pe190759@')
        ''')
        
        conn.commit()
        conn.close()

def obter_senha_admin():
    """Obtém a senha do admin do banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT valor FROM admin_settings WHERE chave = ?', ('admin_password',))
    resultado = cursor.fetchone()
    conn.close()
    
    return resultado[0] if resultado else 'Pe190759@'

def atualizar_senha_admin(nova_senha):
    """Atualiza a senha do admin no banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE admin_settings SET valor = ?, data_atualizacao = CURRENT_TIMESTAMP
        WHERE chave = ?
    ''', (nova_senha, 'admin_password'))
    
    conn.commit()
    conn.close()

def gerar_chave_licenca(tipo='trial'):
    """Gera uma chave de licença no formato PROMPT-XXXXX-XXXXXXXX-XXXXXXXX-XANO/XDIAS"""
    caracteres = string.ascii_uppercase + string.digits
    parte1 = ''.join(secrets.choice(caracteres) for _ in range(5))
    parte2 = ''.join(secrets.choice(caracteres) for _ in range(8))
    parte3 = ''.join(secrets.choice(caracteres) for _ in range(8))
    
    if tipo == 'trial':
        sufixo = '7DIAS'
    else:
        sufixo = '1ANO'
    
    chave = f"PROMPT-{parte1}-{parte2}-{parte3}-{sufixo}"
    return chave

def gerar_qr_code_pix():
    """Gera QR code para PIX"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data('00020126580014br.gov.bcb.pix0136055005108-27520400005303986540510.005802BR5913PEDRO CELSO6009ARARAQUARA62410503***63041D3D')
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    img_base64 = base64.b64encode(img_io.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

def validar_chave(chave):
    """Valida se a chave existe e está ativa"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM chaves_licenca 
        WHERE chave = ? AND ativa = 1 AND data_expiracao > datetime('now')
    ''', (chave,))
    
    resultado = cursor.fetchone()
    conn.close()
    
    return resultado is not None

def markdown_para_pdf(markdown_text, nome_arquivo="relatorio.pdf"):
    """Converte Markdown para PDF usando WeasyPrint"""
    try:
        # Converte Markdown para HTML
        html_content = markdown.markdown(markdown_text, extensions=['tables', 'fenced_code'])
        
        # Adiciona CSS para formatação
        css_template = '''
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 40px;
                }
                h1 { color: #1e3c72; border-bottom: 3px solid #2a5298; padding-bottom: 10px; }
                h2 { color: #2a5298; margin-top: 20px; }
                h3 { color: #555; }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                th {
                    background-color: #1e3c72;
                    color: white;
                    font-weight: bold;
                }
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                code {
                    background-color: #f4f4f4;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }
                pre {
                    background-color: #f4f4f4;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                }
                .page-break {
                    page-break-after: always;
                }
                hr {
                    border: none;
                    border-top: 2px solid #2a5298;
                    margin: 30px 0;
                }
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        '''
        
        html_final = css_template.format(html_content=html_content)
        
        # Cria PDF com WeasyPrint
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            HTML(string=html_final).write_pdf(tmp_file.name)
            return tmp_file.name
    except Exception as e:
        print(f"Erro ao converter Markdown para PDF: {str(e)}")
        return None

@app.route('/')
def index():
    qr_code = gerar_qr_code_pix()
    return render_template_string('''
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
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
            padding: 40px 20px;
        }
        
        h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .cta-banner {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .cta-banner h2 {
            font-size: 2em;
            margin-bottom: 15px;
        }
        
        .cta-banner p {
            font-size: 1.1em;
            margin-bottom: 20px;
        }
        
        .btn-trial {
            background: white;
            color: #28a745;
            padding: 15px 30px;
            font-size: 1em;
            font-weight: bold;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn-trial:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #1e3c72;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .card p {
            color: #555;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        
        .modules {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .modules h3 {
            color: #1e3c72;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .module-list {
            list-style: none;
        }
        
        .module-list li {
            padding: 8px 0;
            border-bottom: 1px solid #ddd;
            color: #666;
        }
        
        .module-list li:last-child {
            border-bottom: none;
        }
        
        .qr-container {
            text-align: center;
        }
        
        .qr-container img {
            max-width: 300px;
            margin: 20px 0;
        }
        
        .price {
            font-size: 2.5em;
            color: #28a745;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }
        
        .tools-section {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }
        
        .tools-section h2 {
            color: #1e3c72;
            margin-bottom: 15px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            font-size: 1em;
            transition: transform 0.2s;
            margin: 10px 5px;
        }
        
        .btn:hover {
            transform: scale(1.05);
        }
        
        .btn-secondary {
            background: #6c757d;
        }
        
        .payment-section {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .payment-section h2 {
            color: #1e3c72;
            margin-bottom: 20px;
        }
        
        .payment-steps {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .payment-steps h3 {
            color: #1e3c72;
            margin-bottom: 15px;
        }
        
        .payment-steps ol {
            margin-left: 20px;
            color: #555;
            line-height: 1.8;
        }
        
        .payment-steps li {
            margin-bottom: 10px;
        }
        
        @media (max-width: 768px) {
            .content {
                grid-template-columns: 1fr;
            }
            h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📈 Prompt Fundamentalista B3</h1>
            <p class="subtitle">Análise Inteligente do Mercado de Ações Brasileiro</p>
        </header>
        
        <!-- BANNER CTA DESTACADO -->
        <div class="cta-banner">
            <h2>🎁 Teste Grátis por 7 Dias!</h2>
            <p>Comece a analisar ações da B3 com o Prompt Fundamentalista agora mesmo.</p>
            <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                <button class="btn-trial" onclick="abrirModalTeste()">Solicitar Acesso Grátis →</button>
            </div>
        </div>
        
        <!-- SEÇÃO DE FERRAMENTAS -->
        <div class="tools-section">
            <h2>🛠️ Ferramentas Úteis</h2>
            <p>Converta seus relatórios Markdown em PDF profissional</p>
            <button class="btn btn-secondary" onclick="window.location.href='/converter-pdf'">📄 Converter Markdown → PDF</button>
        </div>
        
        <div class="content">
            <div class="card">
                <h2>🎯 O Que É?</h2>
                <p>Um prompt especializado para Claude e ChatGPT que analisa ações da B3 com base em fundamentos sólidos.</p>
                
                <div class="modules">
                    <h3>📚 16 Módulos de Análise:</h3>
                    <ul class="module-list">
                        <li>1. Papel e Escopo</li>
                        <li>2. Regras Absolutas</li>
                        <li>3. Dados Críticos</li>
                        <li>4. Modos de Análise</li>
                        <li>5. Uso de PDFs</li>
                        <li>6. Fórmulas Principais</li>
                        <li>7. Definições Fundamentais</li>
                        <li>8. Filtros Barsi (Dividendos)</li>
                        <li>9. Filtros Finclass (Crescimento)</li>
                        <li>10. Sistema de Scoring</li>
                        <li>11. Instituições Financeiras</li>
                        <li>12. Setores Especiais</li>
                        <li>13. Ajustes Contábeis</li>
                        <li>14. Sensibilidade</li>
                        <li>15. Validação Humana</li>
                        <li>16. Disclaimer</li>
                    </ul>
                </div>
            </div>
            
            <div class="card">
                <h2>💳 Adquirir Acesso Anual</h2>
                
                <div class="price">R$ 50,00</div>
                <p>Acesso por 1 ano com renovação manual</p>
                
                <div class="qr-container">
                    <p><strong>Escaneie para pagar via PIX:</strong></p>
                    <img src="{{ qr_code }}" alt="QR Code PIX">
                    <p style="font-size: 0.9em; color: #666; margin-top: 10px;">
                        <strong>CPF:</strong> 055.005.108-27<br>
                        <strong>Titular:</strong> Pedro de Celso Gardini<br>
                        <strong>Valor:</strong> R$ 50,00
                    </p>
                </div>
                
                <p style="margin-top: 20px; text-align: center; color: #666; font-size: 0.9em;">
                    Após o pagamento, envie comprovante para receber sua chave de licença.
                </p>
            </div>
        </div>
        
        <!-- SEÇÃO DE INSTRUÇÕES DE PAGAMENTO -->
        <div class="payment-section">
            <h2>📱 Como Comprar (Após Teste de 7 Dias)</h2>
            <div class="payment-steps">
                <h3>Passo a Passo:</h3>
                <ol>
                    <li><strong>Escaneie o QR Code</strong> ou use a chave PIX acima</li>
                    <li><strong>Faça a transferência</strong> de R$ 50,00 via PIX</li>
                    <li><strong>Tire um screenshot</strong> do comprovante de pagamento</li>
                    <li><strong>Envie o comprovante</strong> para: <strong>promptpegardini@gmail.com</strong></li>
                    <li><strong>Assunto do email:</strong> "Compra - Prompt Fundamentalista B3"</li>
                    <li><strong>Aguarde confirmação</strong> em até 24 horas</li>
                    <li><strong>Receba seu prompt</strong> com chave de 1 ano!</li>
                </ol>
            </div>
        </div>
    </div>
    
    <!-- Modal Teste Grátis -->
    <div id="modalTeste" class="modal">
        <div class="modal-content">
            <span class="close" onclick="fecharModalTeste()">&times;</span>
            <h2>🎁 Solicitar Teste Grátis</h2>
            <form onsubmit="enviarFormularioTeste(event)">
                <div class="form-group">
                    <label for="nome">Nome Completo:</label>
                    <input type="text" id="nome" name="nome" required>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="telefone">Telefone (opcional):</label>
                    <input type="tel" id="telefone" name="telefone">
                </div>
                <div class="form-group">
                    <label for="mensagem">Mensagem (opcional):</label>
                    <textarea id="mensagem" name="mensagem"></textarea>
                </div>
                <button type="submit" class="btn">Enviar Solicitação</button>
            </form>
        </div>
    </div>
    
    <style>
        .modal {
            display: none;
            position: fixed;
            z-index: 1;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.4);
        }
        
        .modal-content {
            background-color: #fefefe;
            margin: 10% auto;
            padding: 20px;
            border: 1px solid #888;
            border-radius: 10px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: black;
        }
        
        .modal-content h2 {
            color: #1e3c72;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: bold;
        }
        
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: Arial, sans-serif;
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 100px;
        }
    </style>
    
    <script>
        function abrirModalTeste() {
            document.getElementById("modalTeste").style.display = "block";
        }
        
        function fecharModalTeste() {
            document.getElementById("modalTeste").style.display = "none";
        }
        
        window.onclick = function(event) {
            var modal = document.getElementById("modalTeste");
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }
        
        function enviarFormularioTeste(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            
            fetch('/api/requisitar-teste', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.sucesso) {
                    alert('✅ Solicitação enviada! Você receberá um email em breve.');
                    fecharModalTeste();
                    event.target.reset();
                } else {
                    alert('❌ Erro: ' + data.erro);
                }
            })
            .catch(error => {
                alert('❌ Erro ao enviar: ' + error);
            });
        }
    </script>
</body>
</html>
    ''', qr_code=qr_code)

@app.route('/download-prompt')
def download_prompt():
    # Lê o prompt do arquivo
    with open('/home/ubuntu/PROMPT_MESTRE_HIBRIDO_B3.md', 'r', encoding='utf-8') as f:
        conteudo_prompt = f.read()
    
    # Cria arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(conteudo_prompt)
        temp_path = f.name
    
    return send_file(temp_path, as_attachment=True, download_name='PROMPT_FUNDAMENTALISTA_B3.md', mimetype='text/markdown')

@app.route('/converter-pdf')
def converter_pdf():
    return render_template_string('''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converter Markdown → PDF</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        h1 {
            color: #1e3c72;
            margin-bottom: 20px;
            text-align: center;
        }
        
        p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
            text-align: center;
        }
        
        form {
            margin-top: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 10px;
            color: #333;
            font-weight: bold;
        }
        
        textarea {
            width: 100%;
            min-height: 400px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            resize: vertical;
        }
        
        textarea:focus {
            outline: none;
            border-color: #2a5298;
        }
        
        .button-group {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }
        
        .btn-converter {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn-converter:hover {
            transform: scale(1.05);
        }
        
        .btn-voltar {
            background: #6c757d;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn-voltar:hover {
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📄 Converter Markdown → PDF</h1>
        <p>Cole seu Markdown abaixo e converta para PDF profissional</p>
        
        <form onsubmit="converterParaPDF(event)">
            <div class="form-group">
                <label for="markdown">Cole seu Markdown aqui:</label>
                <textarea id="markdown" name="markdown" placeholder="Cole seu conteúdo Markdown aqui..." required></textarea>
            </div>
            
            <div class="button-group">
                <button type="submit" class="btn-converter">📥 Converter para PDF</button>
                <button type="button" class="btn-voltar" onclick="window.location.href='/'">← Voltar</button>
            </div>
        </form>
    </div>
    
    <script>
        function converterParaPDF(event) {
            event.preventDefault();
            
            const markdown = document.getElementById('markdown').value;
            
            if (!markdown.trim()) {
                alert('❌ Por favor, cole o Markdown antes de converter!');
                return;
            }
            
            fetch('/api/converter-pdf', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({markdown: markdown})
            })
            .then(response => {
                if (response.ok) {
                    return response.blob();
                }
                throw new Error('Erro ao converter');
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'relatorio_b3.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
                alert('✅ PDF gerado com sucesso!');
            })
            .catch(error => {
                alert('❌ Erro ao converter: ' + error);
            });
        }
    </script>
</body>
</html>
    ''')

@app.route('/api/converter-pdf', methods=['POST'])
def api_converter_pdf():
    data = request.get_json()
    markdown_text = data.get('markdown', '')
    
    if not markdown_text:
        return jsonify({'erro': 'Markdown vazio'}), 400
    
    pdf_path = markdown_para_pdf(markdown_text)
    
    if not pdf_path:
        return jsonify({'erro': 'Erro ao converter'}), 500
    
    return send_file(pdf_path, mimetype='application/pdf', as_attachment=True, download_name='relatorio_b3.pdf')

@app.route('/api/requisitar-teste', methods=['POST'])
def requisitar_teste():
    nome = request.form.get('nome')
    email = request.form.get('email')
    telefone = request.form.get('telefone', '')
    mensagem = request.form.get('mensagem', '')
    
    if not nome or not email:
        return jsonify({'sucesso': False, 'erro': 'Nome e email são obrigatórios'})
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO requisicoes_teste (nome, email, telefone)
        VALUES (?, ?, ?)
    ''', (nome, email, telefone))
    
    conn.commit()
    requisicao_id = cursor.lastrowid
    conn.close()
    
    # Envia email de notificação ao admin
    corpo_admin = f'''
    <h2>Nova Solicitação de Teste Grátis</h2>
    <p><strong>ID:</strong> {requisicao_id}</p>
    <p><strong>Nome:</strong> {nome}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Telefone:</strong> {telefone or 'Não informado'}</p>
    <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    <p><a href="https://prompt-b3.onrender.com/admin?senha=Pe190759@">Aprovar no Admin</a></p>
    '''
    
    enviar_email(EMAIL_ADMIN, f'Nova Solicitação de Teste - {nome}', corpo_admin)
    
    # Envia email de confirmação ao cliente
    corpo_cliente = '''
    <h2>✅ Solicitação Recebida!</h2>
    <p>Obrigado por se interessar no Prompt Fundamentalista B3!</p>
    <p>Sua solicitação foi recebida e será analisada em breve.</p>
    <p>Você receberá um email com sua chave de acesso em até 24 horas.</p>
    <p>Atenciosamente,<br>Equipe Prompt Fundamentalista B3</p>
    '''
    
    enviar_email(email, 'Solicitação de Teste Recebida', corpo_cliente)
    
    return jsonify({'sucesso': True})

@app.route('/admin')
def admin():
    senha = request.args.get('senha')
    senha_admin = obter_senha_admin()
    
    if senha != senha_admin:
        return '''
        <html>
        <head><title>Admin</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>Acesso Restrito</h1>
            <form method="get">
                <input type="password" name="senha" placeholder="Senha" required>
                <button type="submit">Entrar</button>
            </form>
        </body>
        </html>
        '''
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM requisicoes_teste WHERE aprovada = 0 ORDER BY data_requisicao DESC')
    requisicoes = cursor.fetchall()
    
    cursor.execute('SELECT * FROM chaves_licenca ORDER BY data_criacao DESC')
    chaves = cursor.fetchall()
    
    conn.close()
    
    html = f'''
    <html>
    <head>
        <title>Admin - Prompt B3</title>
        <style>
            body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
            h1 {{ color: #1e3c72; }}
            h2 {{ color: #1e3c72; margin-top: 30px; }}
            table {{ width: 100%; border-collapse: collapse; background: white; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #1e3c72; color: white; }}
            button {{ padding: 8px 15px; background: #2a5298; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }}
            button:hover {{ background: #1e3c72; }}
            .sucesso {{ color: green; }}
            .erro {{ color: red; }}
            .settings-section {{ background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .settings-section input {{ padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>📊 Admin Panel - Prompt Fundamentalista B3</h1>
        
        <div class="settings-section">
            <h2>🔐 Configurações de Segurança</h2>
            <p><strong>Mudar Senha do Admin:</strong></p>
            <form onsubmit="mudarSenha(event, '{senha_admin}')">
                <input type="password" id="senhaAtual" placeholder="Senha Atual" required>
                <input type="password" id="novaSenha" placeholder="Nova Senha" required>
                <input type="password" id="confirmarSenha" placeholder="Confirmar Senha" required>
                <button type="submit">Atualizar Senha</button>
            </form>
        </div>
        
        <h2>Solicitações de Teste Pendentes</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Nome</th>
                <th>Email</th>
                <th>Telefone</th>
                <th>Data</th>
                <th>Ação</th>
            </tr>
    '''
    
    for req in requisicoes:
        html += f'''
            <tr>
                <td>{req[0]}</td>
                <td>{req[1]}</td>
                <td>{req[2]}</td>
                <td>{req[3] or '-'}</td>
                <td>{req[4]}</td>
                <td>
                    <button onclick="aprovarTeste({req[0]}, '{req[2]}', '{req[1]}', '{senha_admin}')">Aprovar</button>
                </td>
            </tr>
        '''
    
    html += '''
        </table>
        
        <h2>Chaves de Licença Geradas</h2>
        <table>
            <tr>
                <th>Chave</th>
                <th>Email</th>
                <th>Criada em</th>
                <th>Expira em</th>
                <th>Status</th>
                <th>Tipo</th>
            </tr>
    '''
    
    for chave in chaves:
        status = '✅ Ativa' if chave[5] else '❌ Inativa'
        html += f'''
            <tr>
                <td>{chave[1]}</td>
                <td>{chave[2]}</td>
                <td>{chave[3]}</td>
                <td>{chave[4]}</td>
                <td>{status}</td>
                <td>{chave[6]}</td>
            </tr>
        '''
    
    html += '''
        </table>
        
        <script>
            function mudarSenha(event, senhaAtual) {
                event.preventDefault();
                
                const senhaAtualInput = document.getElementById('senhaAtual').value;
                const novaSenha = document.getElementById('novaSenha').value;
                const confirmarSenha = document.getElementById('confirmarSenha').value;
                
                if (senhaAtualInput !== senhaAtual) {
                    alert('❌ Senha atual incorreta!');
                    return;
                }
                
                if (novaSenha !== confirmarSenha) {
                    alert('❌ As senhas não conferem!');
                    return;
                }
                
                if (novaSenha.length < 6) {
                    alert('❌ A nova senha deve ter pelo menos 6 caracteres!');
                    return;
                }
                
                fetch('/api/mudar-senha-admin', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({senha_atual: senhaAtualInput, nova_senha: novaSenha})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.sucesso) {
                        alert('✅ Senha alterada com sucesso!');
                        location.reload();
                    } else {
                        alert('❌ Erro: ' + data.erro);
                    }
                });
            }
            
            function aprovarTeste(id, email, nome, senha) {
                if (confirm('Gerar chave e enviar para ' + email + '?')) {
                    fetch('/api/aprovar-teste', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({id: id, email: email, nome: nome, senha: senha})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.sucesso) {
                            alert('✅ Chave gerada e enviada!');
                            location.reload();
                        } else {
                            alert('❌ Erro: ' + data.erro);
                        }
                    });
                }
            }
        </script>
    </body>
    </html>
    '''
    
    return html

@app.route('/api/mudar-senha-admin', methods=['POST'])
def mudar_senha_admin():
    data = request.get_json()
    senha_atual = data.get('senha_atual')
    nova_senha = data.get('nova_senha')
    
    senha_admin = obter_senha_admin()
    
    if senha_atual != senha_admin:
        return jsonify({'sucesso': False, 'erro': 'Senha atual incorreta'})
    
    if len(nova_senha) < 6:
        return jsonify({'sucesso': False, 'erro': 'A nova senha deve ter pelo menos 6 caracteres'})
    
    atualizar_senha_admin(nova_senha)
    
    return jsonify({'sucesso': True, 'mensagem': 'Senha alterada com sucesso'})

@app.route('/api/aprovar-teste', methods=['POST'])
def aprovar_teste():
    data = request.get_json()
    requisicao_id = data.get('id')
    email = data.get('email')
    nome = data.get('nome')
    senha = data.get('senha')
    
    senha_admin = obter_senha_admin()
    
    if senha != senha_admin:
        return jsonify({'sucesso': False, 'erro': 'Não autorizado'})
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Gera chave
    chave = gerar_chave_licenca(tipo='trial')
    data_expiracao = (datetime.now() + timedelta(days=7)).isoformat()
    
    cursor.execute('''
        INSERT INTO chaves_licenca (chave, email, data_expiracao, tipo)
        VALUES (?, ?, ?, ?)
    ''', (chave, email, data_expiracao, 'trial'))
    
    # Marca requisição como aprovada
    cursor.execute('''
        UPDATE requisicoes_teste SET aprovada = 1, chave_gerada = ?, email_enviado = 1
        WHERE id = ?
    ''', (chave, requisicao_id))
    
    conn.commit()
    conn.close()
    
    # EMAIL 1: Aprovação do Teste (7 Dias) - MELHORADO
    data_expiracao_formatada = (datetime.now() + timedelta(days=7)).strftime('%d/%m/%Y')
    
    corpo = f'''
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #f5f5f5; padding: 20px; border-radius: 10px; }}
            .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }}
            .content {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .chave {{ background: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 1.1em; margin: 15px 0; word-break: break-all; }}
            .passo {{ background: #f9f9f9; padding: 15px; margin: 15px 0; border-left: 4px solid #2a5298; border-radius: 5px; }}
            .passo-numero {{ background: #2a5298; color: white; padding: 5px 10px; border-radius: 50%; display: inline-block; margin-right: 10px; font-weight: bold; }}
            .importante {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; border-radius: 5px; margin: 15px 0; }}
            .footer {{ text-align: center; color: #666; font-size: 0.9em; padding-top: 20px; border-top: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Bem-vindo ao Prompt Fundamentalista B3!</h1>
                <p>Sua solicitação foi APROVADA!</p>
            </div>
            
            <div class="content">
                <h2>Olá {nome},</h2>
                
                <p>Parabéns! Sua solicitação de teste grátis foi <strong>APROVADA</strong>!</p>
                
                <p>Você agora tem acesso a <strong>7 dias de teste GRÁTIS</strong> do Prompt Fundamentalista B3.</p>
                
                <h3>🔑 SUA CHAVE DE TESTE</h3>
                <div class="chave">{chave}</div>
                
                <p><strong>⏰ Válida até:</strong> {data_expiracao_formatada}</p>
                
                <h3>📋 PASSO A PASSO PARA USAR:</h3>
                
                <div class="passo">
                    <span class="passo-numero">1️⃣</span>
                    <strong>Baixar o Arquivo</strong><br>
                    Acesse <a href="https://prompt-b3.onrender.com/download-prompt">https://prompt-b3.onrender.com/download-prompt</a> e baixe o arquivo PROMPT_FUNDAMENTALISTA_B3.md
                </div>
                
                <div class="passo">
                    <span class="passo-numero">2️⃣</span>
                    <strong>Abrir o Arquivo</strong><br>
                    Abra com um editor de texto simples (Notepad, Word, etc). Você verá a chave no início do arquivo.
                </div>
                
                <div class="passo">
                    <span class="passo-numero">3️⃣</span>
                    <strong>Copiar Tudo</strong><br>
                    Selecione todo o conteúdo: <strong>Ctrl+A</strong> e copie: <strong>Ctrl+C</strong>
                </div>
                
                <div class="passo">
                    <span class="passo-numero">4️⃣</span>
                    <strong>Abrir Claude ou ChatGPT</strong><br>
                    Acesse <a href="https://claude.ai">https://claude.ai</a> (Claude) ou <a href="https://chat.openai.com">https://chat.openai.com</a> (ChatGPT)
                </div>
                
                <div class="passo">
                    <span class="passo-numero">5️⃣</span>
                    <strong>Colar o Prompt</strong><br>
                    Clique na caixa de mensagem e cole: <strong>Ctrl+V</strong>, depois pressione <strong>Enter</strong>
                </div>
                
                <div class="passo">
                    <span class="passo-numero">6️⃣</span>
                    <strong>Pronto!</strong><br>
                    O modelo lerá a chave automaticamente e você poderá começar a analisar ações!
                </div>
                
                <h3>💡 DICAS IMPORTANTES</h3>
                <ul>
                    <li>✅ Você pode usar o mesmo arquivo QUANTAS VEZES QUISER durante os 7 dias</li>
                    <li>✅ Cada conversa é independente</li>
                    <li>✅ Você pode fazer múltiplas análises</li>
                    <li>✅ Não há limite de uso</li>
                </ul>
                
                <h3>⏰ PRÓXIMOS PASSOS (APÓS 7 DIAS)</h3>
                
                <p>Se você gostar do Prompt Fundamentalista B3, você pode adquirir uma licença de <strong>1 ANO</strong> por apenas:</p>
                
                <div class="importante">
                    <strong>💰 R$ 50,00 (via PIX)</strong>
                </div>
                
                <p><strong>COMO COMPRAR:</strong></p>
                <ol>
                    <li>Acesse <a href="https://prompt-b3.onrender.com/">https://prompt-b3.onrender.com/</a></li>
                    <li>Escaneie o QR Code PIX ou use a chave PIX</li>
                    <li>Faça a transferência de R$ 50,00</li>
                    <li>Tire um PRINT/SCREENSHOT do comprovante</li>
                    <li>Envie o comprovante para: <strong>promptpegardini@gmail.com</strong></li>
                    <li>Assunto: <strong>"Compra - Prompt Fundamentalista B3"</strong></li>
                    <li>Você receberá o prompt de 1 ANO em até 24 horas</li>
                </ol>
                
                <h3>❓ DÚVIDAS?</h3>
                <p>Se tiver qualquer dúvida ou problema:</p>
                <p>📧 Envie um email para: <strong>promptpegardini@gmail.com</strong><br>
                ⏱️ Responderemos em até 24 horas</p>
                
                <p style="margin-top: 20px; font-weight: bold;">Aproveite o teste! 🚀</p>
            </div>
            
            <div class="footer">
                <p>Atenciosamente,<br>Equipe Prompt Fundamentalista B3</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    enviar_email(email, '✅ Sua Chave de Teste - Prompt Fundamentalista B3', corpo)
    
    return jsonify({'sucesso': True})

@app.route('/api/validar-assinatura', methods=['POST'])
def validar_assinatura():
    data = request.get_json()
    chave = data.get('chave')
    
    if validar_chave(chave):
        return jsonify({'valida': True, 'mensagem': 'Chave válida'})
    else:
        return jsonify({'valida': False, 'mensagem': 'Chave inválida ou expirada'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
