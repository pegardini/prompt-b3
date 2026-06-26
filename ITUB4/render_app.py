#!/usr/bin/env python3
"""
Prompt Fundamentalista B3 - Flask App para Render
Multi-page: Home, Trial (7 dias), Compra (1 ano), Admin
"""
import os
import random
import string
import io
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_file, make_response

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(BASE_DIR, 'PROMPT_MESTRE_HIBRIDO_B3.md')
ADMIN_SENHA = os.environ.get('ADMIN_SENHA', 'Pe190759@')

# ─── Geração de Chave ────────────────────────────────────────────────────────

def gerar_chave(dias=7):
    """Gera chave com data de vencimento embutida.
    Formato: PROMPT-XXXXX-XXXXXXXX-AAAAMMDD-7DIAS ou 1ANO
    """
    p1 = ''.join(random.choices(string.digits, k=5))
    p2 = ''.join(random.choices(string.digits + string.ascii_uppercase, k=8))
    vencimento = (datetime.utcnow() + timedelta(days=dias)).strftime('%Y%m%d')
    sufixo = '7DIAS' if dias <= 7 else '1ANO'
    return f"PROMPT-{p1}-{p2}-{vencimento}-{sufixo}"

def prompt_com_chave(chave, duracao_label):
    """Lê o prompt original e insere a chave de licença no campo específico."""
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    bloco_chave = f"""
---
## 🔑 CHAVE DE LICENÇA ATIVA

| Campo | Valor |
|-------|-------|
| **Chave** | `{chave}` |
| **Validade** | {duracao_label} |
| **Status** | ✅ Licença Ativa |

> Cole esta chave no início de cada conversa com a IA para liberar o acesso completo.

---
"""
    # Insere o bloco logo após o cabeçalho de metadados (após a primeira linha ---)
    partes = conteudo.split('---', 2)
    if len(partes) >= 3:
        novo_conteudo = partes[0] + '---' + partes[1] + '---' + bloco_chave + partes[2]
    else:
        novo_conteudo = bloco_chave + conteudo

    return novo_conteudo

# ─── CSS Compartilhado ────────────────────────────────────────────────────────

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #0a0f1e;
    color: #e0e0e0;
    min-height: 100vh;
}
nav {
    background: rgba(255,255,255,0.05);
    border-bottom: 1px solid rgba(255,215,0,0.2);
    padding: 15px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(10px);
}
nav .logo {
    color: #ffd700;
    font-size: 1.2em;
    font-weight: bold;
    text-decoration: none;
}
nav .nav-links a {
    color: #ccc;
    text-decoration: none;
    margin-left: 25px;
    font-size: 0.95em;
    transition: color 0.3s;
}
nav .nav-links a:hover { color: #ffd700; }
.container { max-width: 1100px; margin: 0 auto; padding: 40px 20px; }
h1 { font-size: 2.4em; color: #ffd700; margin-bottom: 15px; }
h2 { font-size: 1.6em; color: #ffd700; margin-bottom: 15px; }
p { color: #bbb; line-height: 1.7; margin-bottom: 15px; }
.btn {
    display: inline-block;
    padding: 14px 32px;
    border-radius: 8px;
    font-size: 1em;
    font-weight: bold;
    cursor: pointer;
    border: none;
    text-decoration: none;
    transition: transform 0.2s, box-shadow 0.2s;
}
.btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
.btn-gold {
    background: linear-gradient(135deg, #ffd700, #ff8c00);
    color: #000;
}
.btn-green {
    background: linear-gradient(135deg, #00c853, #00897b);
    color: #fff;
}
.btn-blue {
    background: linear-gradient(135deg, #1565c0, #0288d1);
    color: #fff;
}
.card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,215,0,0.15);
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 25px;
}
.form-group { margin-bottom: 20px; }
.form-group label { display: block; color: #ffd700; margin-bottom: 8px; font-weight: bold; }
.form-group input {
    width: 100%;
    padding: 12px 16px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,215,0,0.3);
    border-radius: 8px;
    color: #fff;
    font-size: 1em;
}
.form-group input:focus {
    outline: none;
    border-color: #ffd700;
    background: rgba(255,255,255,0.12);
}
.disclaimer {
    background: rgba(255,100,0,0.1);
    border: 1px solid rgba(255,100,0,0.3);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85em;
    color: #ff9800;
    margin-top: 20px;
}
footer {
    text-align: center;
    padding: 30px;
    color: #555;
    font-size: 0.85em;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin-top: 60px;
}
@media (max-width: 768px) {
    h1 { font-size: 1.7em; }
    nav { padding: 12px 20px; }
    nav .nav-links a { margin-left: 12px; font-size: 0.85em; }
}
"""

NAV = """
<nav>
    <a class="logo" href="/">📈 Prompt B3</a>
    <div class="nav-links">
        <a href="/">Home</a>
        <a href="/trial">Teste 7 Dias</a>
        <a href="/comprar">Comprar 1 Ano</a>
    </div>
</nav>
"""

FOOTER = """
<footer>
    <p>© 2026 Prompt Fundamentalista B3 · <a href="mailto:promptpegardini@gmail.com" style="color:#ffd700;">promptpegardini@gmail.com</a></p>
    <p style="margin-top:8px;">Este produto é um prompt de IA. Não constitui recomendação de investimento.</p>
</footer>
"""

# ─── Página Home ─────────────────────────────────────────────────────────────

@app.route('/')
def home():
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prompt Fundamentalista B3 — Análise de Ações com IA</title>
    <style>{CSS}
    .hero {{
        text-align: center;
        padding: 80px 20px 60px;
        background: radial-gradient(ellipse at top, rgba(255,215,0,0.08) 0%, transparent 70%);
    }}
    .hero h1 {{ font-size: 2.8em; line-height: 1.2; margin-bottom: 20px; }}
    .hero p {{ font-size: 1.15em; max-width: 680px; margin: 0 auto 35px; }}
    .hero-btns {{ display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; }}
    .video-wrap {{
        max-width: 820px;
        margin: 0 auto 60px;
        border-radius: 14px;
        overflow: hidden;
        border: 2px solid rgba(255,215,0,0.25);
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }}
    .video-wrap video {{ width: 100%; display: block; }}
    .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 50px; }}
    .feature-icon {{ font-size: 2em; margin-bottom: 12px; }}
    .modules-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; margin-top: 15px; }}
    .module-item {{
        background: rgba(255,215,0,0.06);
        border: 1px solid rgba(255,215,0,0.15);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 0.88em;
        color: #ccc;
    }}
    .module-item span {{ color: #ffd700; font-weight: bold; }}
    .how-open {{
        background: rgba(0,200,83,0.07);
        border: 1px solid rgba(0,200,83,0.25);
        border-radius: 12px;
        padding: 25px 30px;
        margin-bottom: 40px;
    }}
    .how-open h2 {{ color: #00c853; }}
    .how-open ol {{ margin-left: 20px; color: #bbb; line-height: 2; }}
    .how-open a {{ color: #00c853; }}
    </style>
</head>
<body>
{NAV}

<div class="hero">
    <h1>📈 Analise Ações B3<br>com Inteligência Artificial</h1>
    <p>O <strong style="color:#ffd700;">Prompt Fundamentalista B3</strong> combina a metodologia Barsi + Finclass em 16 módulos de análise profunda. Funciona com ChatGPT, Claude e outras IAs.</p>
    <div class="hero-btns">
        <a href="/trial" class="btn btn-gold">🎁 Teste Grátis 7 Dias</a>
        <a href="/comprar" class="btn btn-green">💳 Comprar 1 Ano — R$ 60</a>
    </div>
</div>

<div class="container">

    <div class="video-wrap">
        <video controls autoplay muted loop playsinline>
            <source src="/video" type="video/mp4">
            Seu navegador não suporta vídeo HTML5.
        </video>
    </div>

    <div class="features">
        <div class="card">
            <div class="feature-icon">🎯</div>
            <h2>Metodologia Híbrida</h2>
            <p>Une a filosofia de dividendos de <strong style="color:#ffd700;">Luiz Barsi</strong> com a análise de valor justo da <strong style="color:#ffd700;">Finclass</strong> em um único prompt poderoso.</p>
        </div>
        <div class="card">
            <div class="feature-icon">🤖</div>
            <h2>Funciona com Qualquer IA</h2>
            <p>Compatible com <strong style="color:#ffd700;">ChatGPT</strong>, <strong style="color:#ffd700;">Claude</strong>, <strong style="color:#ffd700;">Gemini</strong> e outras IAs. Basta colar o prompt e começar a analisar.</p>
        </div>
        <div class="card">
            <div class="feature-icon">🔐</div>
            <h2>Chave de Licença</h2>
            <p>Cada download vem com uma <strong style="color:#ffd700;">chave única</strong> inserida no prompt. A IA valida automaticamente antes de qualquer análise.</p>
        </div>
    </div>

    <div class="card">
        <h2>📚 16 Módulos de Análise</h2>
        <p>O prompt cobre todos os aspectos fundamentalistas de uma ação B3:</p>
        <div class="modules-grid">
            <div class="module-item"><span>01</span> Papel e Escopo</div>
            <div class="module-item"><span>02</span> Regras Absolutas</div>
            <div class="module-item"><span>03</span> Dados Críticos</div>
            <div class="module-item"><span>04</span> Modos de Análise</div>
            <div class="module-item"><span>05</span> Uso de PDFs e Docs</div>
            <div class="module-item"><span>06</span> Fórmulas e Anti-Erro</div>
            <div class="module-item"><span>07</span> Recorrência Contábil</div>
            <div class="module-item"><span>08</span> Filtros Barsi</div>
            <div class="module-item"><span>09</span> Filtros Finclass</div>
            <div class="module-item"><span>10</span> Score Ponderado</div>
            <div class="module-item"><span>11</span> Relatório Final</div>
            <div class="module-item"><span>12</span> Análise de Riscos</div>
            <div class="module-item"><span>13</span> Análise Setorial</div>
            <div class="module-item"><span>14</span> Valuation</div>
            <div class="module-item"><span>15</span> Dividendos</div>
            <div class="module-item"><span>16</span> Recomendação Final</div>
        </div>
    </div>

    <div class="how-open">
        <h2>📂 Como Abrir Arquivos .md (Gratuito)</h2>
        <p>O prompt é entregue no formato <strong>.md (Markdown)</strong>. É um arquivo de texto simples — fácil de abrir:</p>
        <ol>
            <li><strong>Online (mais fácil):</strong> Acesse <a href="https://dillinger.io" target="_blank">dillinger.io</a> e cole o conteúdo do arquivo</li>
            <li><strong>VS Code (gratuito):</strong> Baixe o <a href="https://code.visualstudio.com" target="_blank">VS Code</a> e abra o arquivo normalmente</li>
            <li><strong>Bloco de Notas:</strong> Clique com botão direito no arquivo → "Abrir com" → Bloco de Notas</li>
            <li><strong>Obsidian (gratuito):</strong> Excelente para ler e organizar arquivos .md</li>
        </ol>
    </div>

    <div style="text-align:center; padding: 40px 0;">
        <h2 style="margin-bottom:20px;">Pronto para começar?</h2>
        <div style="display:flex; gap:15px; justify-content:center; flex-wrap:wrap;">
            <a href="/trial" class="btn btn-gold">🎁 Teste Grátis 7 Dias</a>
            <a href="/comprar" class="btn btn-green">💳 Comprar 1 Ano — R$ 60</a>
        </div>
        <div class="disclaimer">⚠️ Este produto é um prompt de inteligência artificial. Não constitui recomendação de investimento. Use com responsabilidade.</div>
    </div>

</div>
{FOOTER}
</body>
</html>"""
    return html


# ─── Servir Vídeo ─────────────────────────────────────────────────────────────

@app.route('/video')
def video():
    video_path = os.path.join(BASE_DIR, 'video_demo_final.mp4')
    if os.path.exists(video_path):
        return send_file(video_path, mimetype='video/mp4')
    return "Vídeo não encontrado", 404


# ─── Página Trial (7 Dias) ────────────────────────────────────────────────────

@app.route('/trial')
def trial_page():
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Teste Grátis 7 Dias — Prompt B3</title>
    <style>{CSS}
    .trial-hero {{
        text-align: center;
        padding: 60px 20px 40px;
        background: radial-gradient(ellipse at top, rgba(255,215,0,0.08) 0%, transparent 70%);
    }}
    .trial-hero h1 {{ font-size: 2.4em; }}
    .trial-form {{ max-width: 500px; margin: 0 auto; }}
    .success-box {{
        display: none;
        background: rgba(0,200,83,0.1);
        border: 2px solid #00c853;
        border-radius: 12px;
        padding: 30px;
        text-align: center;
        margin-top: 20px;
    }}
    .success-box h2 {{ color: #00c853; margin-bottom: 15px; }}
    .chave-display {{
        background: rgba(0,0,0,0.4);
        border: 1px solid #ffd700;
        border-radius: 8px;
        padding: 14px;
        font-family: monospace;
        font-size: 1.1em;
        color: #ffd700;
        word-break: break-all;
        margin: 15px 0;
    }}
    </style>
</head>
<body>
{NAV}

<div class="trial-hero">
    <h1>🎁 Teste Grátis por 7 Dias</h1>
    <p style="max-width:560px; margin:15px auto 0;">Preencha seus dados abaixo e o prompt será baixado automaticamente com sua chave de licença já inserida.</p>
</div>

<div class="container">
    <div class="trial-form">
        <div class="card">
            <h2>Seus Dados</h2>
            <form id="trialForm">
                <div class="form-group">
                    <label for="nome">Nome completo</label>
                    <input type="text" id="nome" name="nome" placeholder="Seu nome" required>
                </div>
                <div class="form-group">
                    <label for="email">E-mail</label>
                    <input type="email" id="email" name="email" placeholder="seu@email.com" required>
                </div>
                <button type="submit" class="btn btn-gold" style="width:100%; font-size:1.1em; padding:16px;">
                    ⬇️ Gerar Chave e Baixar Prompt
                </button>
            </form>

            <div class="success-box" id="successBox">
                <h2>✅ Chave Gerada!</h2>
                <p>Sua chave de 7 dias foi inserida no prompt:</p>
                <div class="chave-display" id="chaveDisplay">—</div>
                <p style="color:#aaa; font-size:0.9em;">O download deve iniciar automaticamente.<br>Se não iniciou, <a href="#" id="downloadLink" style="color:#ffd700;">clique aqui</a>.</p>
                <div style="margin-top:20px; padding:15px; background:rgba(255,215,0,0.07); border-radius:8px; font-size:0.9em; color:#ccc;">
                    💡 <strong style="color:#ffd700;">Gostou do teste?</strong> Após os 7 dias, adquira o acesso anual por apenas R$ 60,00.<br>
                    Envie um e-mail para <a href="mailto:promptpegardini@gmail.com" style="color:#ffd700;">promptpegardini@gmail.com</a> solicitando sua chave de 1 ano.
                </div>
            </div>

            <div class="disclaimer">⚠️ Não constitui recomendação de investimento. Uso educacional.</div>
        </div>
    </div>
</div>

{FOOTER}

<script>
document.getElementById('trialForm').addEventListener('submit', async function(e) {{
    e.preventDefault();
    const nome = document.getElementById('nome').value.trim();
    const email = document.getElementById('email').value.trim();
    if (!nome || !email) return;

    const btn = this.querySelector('button[type=submit]');
    btn.textContent = '⏳ Gerando...';
    btn.disabled = true;

    try {{
        const resp = await fetch('/gerar-trial', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{nome, email}})
        }});
        const data = await resp.json();

        document.getElementById('chaveDisplay').textContent = data.chave;
        document.getElementById('successBox').style.display = 'block';

        // Download automático
        const link = document.createElement('a');
        link.href = '/download-trial?chave=' + encodeURIComponent(data.chave);
        link.download = 'Prompt_Fundamentalista_B3_7dias.md';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        document.getElementById('downloadLink').href = '/download-trial?chave=' + encodeURIComponent(data.chave);

        this.style.display = 'none';
    }} catch(err) {{
        btn.textContent = '⬇️ Gerar Chave e Baixar Prompt';
        btn.disabled = false;
        alert('Erro ao gerar chave. Tente novamente.');
    }}
}});
</script>
</body>
</html>"""
    return html


# ─── API: Gerar Chave Trial ───────────────────────────────────────────────────

@app.route('/gerar-trial', methods=['POST'])
def gerar_trial():
    dados = request.get_json()
    nome = dados.get('nome', '').strip()
    email = dados.get('email', '').strip()
    if not nome or not email:
        return jsonify({'erro': 'Nome e email são obrigatórios'}), 400
    chave = gerar_chave(dias=7)
    return jsonify({'chave': chave, 'nome': nome, 'email': email})


# ─── Download do Prompt com Chave ─────────────────────────────────────────────

@app.route('/download-trial')
def download_trial():
    chave = request.args.get('chave', '').strip()
    if not chave or not chave.startswith('PROMPT-') or '7DIAS' not in chave:
        return "Chave inválida", 400
    conteudo = prompt_com_chave(chave, '7 dias (teste gratuito)')
    buf = io.BytesIO(conteudo.encode('utf-8'))
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name='Prompt_Fundamentalista_B3_7dias.md',
        mimetype='text/markdown'
    )


# ─── Download Anual via Link Único ────────────────────────────────────────────

@app.route('/download-anual/<token>')
def download_anual(token):
    """Link único gerado pelo admin para clientes que pagaram."""
    # Token = chave 1ANO codificada em base64 simples
    import base64
    try:
        chave = base64.urlsafe_b64decode(token.encode()).decode('utf-8')
    except Exception:
        return "Link inválido", 400
    if not chave.startswith('PROMPT-') or '1ANO' not in chave:
        return "Link inválido", 400
    conteudo = prompt_com_chave(chave, '1 ano')
    buf = io.BytesIO(conteudo.encode('utf-8'))
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name='Prompt_Fundamentalista_B3_1ano.md',
        mimetype='text/markdown'
    )


# ─── Página Comprar ───────────────────────────────────────────────────────────

@app.route('/comprar')
def comprar_page():
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprar 1 Ano — Prompt B3</title>
    <style>{CSS}
    .comprar-hero {{
        text-align: center;
        padding: 60px 20px 40px;
        background: radial-gradient(ellipse at top, rgba(0,200,83,0.08) 0%, transparent 70%);
    }}
    .pix-box {{
        background: rgba(0,200,83,0.07);
        border: 2px solid rgba(0,200,83,0.3);
        border-radius: 12px;
        padding: 25px;
        text-align: center;
        margin: 20px 0;
    }}
    .pix-chave {{
        font-size: 1.8em;
        font-weight: bold;
        color: #00c853;
        letter-spacing: 2px;
        margin: 10px 0;
    }}
    .steps-list {{ list-style: none; counter-reset: steps; }}
    .steps-list li {{
        counter-increment: steps;
        display: flex;
        align-items: flex-start;
        gap: 15px;
        margin-bottom: 18px;
        color: #bbb;
        line-height: 1.6;
    }}
    .steps-list li::before {{
        content: counter(steps);
        background: #ffd700;
        color: #000;
        font-weight: bold;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 0.9em;
    }}
    .comprar-form {{ max-width: 500px; margin: 0 auto; }}
    .success-compra {{
        display: none;
        background: rgba(0,200,83,0.1);
        border: 2px solid #00c853;
        border-radius: 12px;
        padding: 25px;
        text-align: center;
        margin-top: 20px;
    }}
    </style>
</head>
<body>
{NAV}

<div class="comprar-hero">
    <h1>💳 Acesso Anual — R$ 60,00</h1>
    <p style="max-width:560px; margin:15px auto 0;">Acesso completo por 1 ano. Após confirmar seu pagamento, você receberá um link exclusivo para baixar o prompt com sua chave de 1 ano.</p>
</div>

<div class="container">
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:25px;">

        <div class="card">
            <h2>💰 Pagamento via PIX</h2>
            <div class="pix-box">
                <p style="color:#aaa; margin-bottom:5px;">Chave PIX (CPF):</p>
                <div class="pix-chave">055.005.108-27</div>
                <p style="color:#aaa; margin-top:10px;">Titular: <strong style="color:#fff;">Pedro de Celso Gardini</strong></p>
                <p style="color:#aaa;">Valor: <strong style="color:#00c853; font-size:1.3em;">R$ 60,00</strong></p>
            </div>
            <h2 style="margin-top:20px;">Como funciona:</h2>
            <ul class="steps-list">
                <li>Faça o PIX de R$ 60,00 para a chave acima</li>
                <li>Preencha o formulário ao lado com seus dados</li>
                <li>Aguarde a confirmação em até 24 horas</li>
                <li>Você receberá um link exclusivo por e-mail</li>
                <li>Clique no link e baixe o prompt com sua chave de 1 ano</li>
            </ul>
        </div>

        <div class="comprar-form">
            <div class="card">
                <h2>📋 Seus Dados</h2>
                <form id="comprarForm">
                    <div class="form-group">
                        <label for="nome_c">Nome completo</label>
                        <input type="text" id="nome_c" name="nome" placeholder="Seu nome" required>
                    </div>
                    <div class="form-group">
                        <label for="email_c">E-mail</label>
                        <input type="email" id="email_c" name="email" placeholder="seu@email.com" required>
                    </div>
                    <button type="submit" class="btn btn-green" style="width:100%; font-size:1.05em; padding:15px;">
                        ✅ Enviar Dados e Aguardar Confirmação
                    </button>
                </form>

                <div class="success-compra" id="successCompra">
                    <h2>✅ Dados Recebidos!</h2>
                    <p>Obrigado, <strong id="nomeConfirm" style="color:#ffd700;"></strong>!</p>
                    <p style="margin-top:10px; color:#aaa;">Após confirmarmos seu pagamento PIX, enviaremos o link de download para <strong id="emailConfirm" style="color:#ffd700;"></strong>.</p>
                    <p style="margin-top:10px; color:#aaa;">Prazo: até 24 horas.</p>
                </div>

                <div class="disclaimer">⚠️ Não constitui recomendação de investimento.</div>
            </div>
        </div>

    </div>
</div>

{FOOTER}

<script>
document.getElementById('comprarForm').addEventListener('submit', async function(e) {{
    e.preventDefault();
    const nome = document.getElementById('nome_c').value.trim();
    const email = document.getElementById('email_c').value.trim();
    if (!nome || !email) return;

    const btn = this.querySelector('button[type=submit]');
    btn.textContent = '⏳ Enviando...';
    btn.disabled = true;

    try {{
        const resp = await fetch('/registrar-compra', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{nome, email}})
        }});
        const data = await resp.json();

        document.getElementById('nomeConfirm').textContent = nome;
        document.getElementById('emailConfirm').textContent = email;
        document.getElementById('successCompra').style.display = 'block';
        this.style.display = 'none';
    }} catch(err) {{
        btn.textContent = '✅ Enviar Dados e Aguardar Confirmação';
        btn.disabled = false;
        alert('Erro ao enviar. Tente novamente.');
    }}
}});
</script>
</body>
</html>"""
    return html


# ─── API: Registrar Interesse de Compra ───────────────────────────────────────

@app.route('/registrar-compra', methods=['POST'])
def registrar_compra():
    dados = request.get_json()
    nome = dados.get('nome', '').strip()
    email = dados.get('email', '').strip()
    if not nome or not email:
        return jsonify({'erro': 'Nome e email são obrigatórios'}), 400
    # Salva em arquivo de texto simples para o admin consultar
    log_path = os.path.join(BASE_DIR, 'compras_pendentes.txt')
    from datetime import datetime
    linha = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} | {nome} | {email}\n"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(linha)
    return jsonify({'status': 'ok'})


# ─── Página Admin ─────────────────────────────────────────────────────────────

@app.route('/admin')
def admin_page():
    senha = request.args.get('senha', '')
    if senha != ADMIN_SENHA:
        return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin</title>
        <style>body{{background:#0a0f1e;color:#fff;font-family:sans-serif;display:flex;
        align-items:center;justify-content:center;min-height:100vh;}}
        form{{background:rgba(255,255,255,0.05);padding:30px;border-radius:12px;text-align:center;}}
        input{{padding:10px;margin:10px 0;width:250px;background:rgba(255,255,255,0.1);
        border:1px solid #ffd700;border-radius:6px;color:#fff;}}
        button{{padding:10px 25px;background:#ffd700;color:#000;border:none;border-radius:6px;
        font-weight:bold;cursor:pointer;margin-top:10px;}}
        </style></head><body>
        <form method="get" action="/admin">
        <h2 style="color:#ffd700;margin-bottom:20px;">🔐 Admin</h2>
        <input type="password" name="senha" placeholder="Senha do admin"><br>
        <button type="submit">Entrar</button>
        </form></body></html>""", 401

    # Lê compras pendentes
    log_path = os.path.join(BASE_DIR, 'compras_pendentes.txt')
    pendentes = []
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            pendentes = [l.strip() for l in f.readlines() if l.strip()]

    linhas_html = ''
    for p in pendentes:
        partes = p.split(' | ')
        if len(partes) == 3:
            data, nome, email = partes
            linhas_html += f"""
            <tr>
                <td>{data}</td>
                <td>{nome}</td>
                <td>{email}</td>
                <td>
                    <button onclick="gerarLink('{nome}','{email}')" 
                        style="background:#ffd700;color:#000;border:none;padding:6px 14px;
                        border-radius:6px;cursor:pointer;font-weight:bold;">
                        🔑 Gerar Link
                    </button>
                </td>
            </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin — Prompt B3</title>
    <style>{CSS}
    table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
    th {{ background:rgba(255,215,0,0.15); color:#ffd700; padding:12px; text-align:left; }}
    td {{ padding:12px; border-bottom:1px solid rgba(255,255,255,0.08); color:#ccc; }}
    tr:hover td {{ background:rgba(255,255,255,0.03); }}
    .link-box {{
        background:rgba(0,200,83,0.1);
        border:1px solid #00c853;
        border-radius:8px;
        padding:15px;
        margin-top:15px;
        display:none;
    }}
    .link-url {{
        font-family:monospace;
        font-size:0.9em;
        color:#00c853;
        word-break:break-all;
    }}
    </style>
</head>
<body>
{NAV}
<div class="container">
    <h1>🔧 Painel Admin</h1>

    <div class="card" style="margin-bottom:30px;">
        <h2>🔑 Gerar Link de Download (1 Ano)</h2>
        <p>Gere um link único para enviar ao cliente após confirmar o pagamento PIX.</p>
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:15px;">
            <input type="text" id="nomeManual" placeholder="Nome do cliente"
                style="flex:1;padding:10px;background:rgba(255,255,255,0.08);
                border:1px solid rgba(255,215,0,0.3);border-radius:8px;color:#fff;">
            <input type="email" id="emailManual" placeholder="Email do cliente"
                style="flex:1;padding:10px;background:rgba(255,255,255,0.08);
                border:1px solid rgba(255,215,0,0.3);border-radius:8px;color:#fff;">
            <button onclick="gerarLinkManual()" class="btn btn-gold">🔑 Gerar Link</button>
        </div>
        <div class="link-box" id="linkBox">
            <p style="color:#00c853;font-weight:bold;margin-bottom:8px;">✅ Link gerado! Envie para o cliente:</p>
            <div class="link-url" id="linkUrl"></div>
            <button onclick="copiarLink()" class="btn btn-green" style="margin-top:12px;padding:8px 20px;">
                📋 Copiar Link
            </button>
        </div>
    </div>

    <div class="card">
        <h2>📋 Compras Pendentes ({len(pendentes)})</h2>
        {"<p style='color:#aaa;'>Nenhuma compra pendente.</p>" if not pendentes else f"<table><thead><tr><th>Data</th><th>Nome</th><th>E-mail</th><th>Ação</th></tr></thead><tbody>{linhas_html}</tbody></table>"}
    </div>
</div>

<script>
const BASE = window.location.origin;

async function gerarLinkManual() {{
    const nome = document.getElementById('nomeManual').value.trim();
    const email = document.getElementById('emailManual').value.trim();
    if (!nome || !email) {{ alert('Preencha nome e email'); return; }}
    gerarLink(nome, email);
}}

async function gerarLink(nome, email) {{
    const resp = await fetch('/admin/gerar-link-anual', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{nome, email, senha: '{ADMIN_SENHA}'}})
    }});
    const data = await resp.json();
    if (data.link) {{
        document.getElementById('linkUrl').textContent = data.link;
        document.getElementById('linkBox').style.display = 'block';
        document.getElementById('linkBox').scrollIntoView({{behavior:'smooth'}});
    }}
}}

function copiarLink() {{
    const texto = document.getElementById('linkUrl').textContent;
    navigator.clipboard.writeText(texto).then(() => alert('Link copiado!'));
}}
</script>
</body>
</html>"""
    return html


# ─── API Admin: Gerar Link Anual ──────────────────────────────────────────────

@app.route('/admin/gerar-link-anual', methods=['POST'])
def admin_gerar_link():
    import base64
    dados = request.get_json()
    if dados.get('senha') != ADMIN_SENHA:
        return jsonify({'erro': 'Não autorizado'}), 403
    nome = dados.get('nome', '').strip()
    email = dados.get('email', '').strip()
    if not nome or not email:
        return jsonify({'erro': 'Nome e email são obrigatórios'}), 400
    chave = gerar_chave(dias=365)
    token = base64.urlsafe_b64encode(chave.encode()).decode()
    base_url = request.host_url.rstrip('/')
    link = f"{base_url}/download-anual/{token}"
    return jsonify({'chave': chave, 'link': link, 'nome': nome, 'email': email})


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'prompt-b3'})


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
