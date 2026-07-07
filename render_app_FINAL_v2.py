#!/usr/bin/env python3
"""
Prompt Fundamentalista B3 - Flask App para Render
Multi-page: Home, Trial (7 dias), Compra (1 ano), Admin, Glossário
"""
import io
import os
import random
import secrets
import string
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_file, make_response, session

app = Flask(__name__)
# Necessário para usar sessão de admin (cookie assinado).
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(BASE_DIR, 'PROMPT_MESTRE_HIBRIDO_B3_v7.md')

# ADMIN_SENHA via variável de ambiente
ADMIN_SENHA = os.environ.get('ADMIN_SENHA', 'PromptB3@Admin2026')

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

# Blocos exclusivos do plano anual: cada entrada é (marcador_inicio, marcador_fim_exclusivo)
# O bloco vai do marcador_inicio até a próxima linha que comece com marcador_fim_exclusivo
# Se marcador_fim_exclusivo for None, remove apenas as linhas do bloco até a próxima linha vazia ou ---
_TRIAL_REMOVE_BLOCKS = [
    # Mapa de Dividendos Inteligente (Seção 5): bloco de ### até o próximo ---
    ("### Mapa de Dividendos Inteligente", "---"),
    # Frequência de Pagamento (Seção 7): linha única + linha seguinte de aviso
    ("**Modulo exclusivo do plano 1ANO", "---"),
    # Requisito de arquivo de download (Seção 8): bloco de ### até o próximo ---
    ("### REQUISITO DE ARQUIVO DE DOWNLOAD:", "---"),
]

def prompt_com_chave(chave, trial=False):
    """Lê o prompt original e substitui o placeholder da chave.
    Se trial=True, remove as seções exclusivas do plano anual.
    """
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    # Substitui o placeholder [CHAVE_DE_LICENCA] pelo valor real
    if '[CHAVE_DE_LICENCA]' in conteudo:
        conteudo = conteudo.replace('[CHAVE_DE_LICENCA]', chave, 1)

    if trial:
        linhas = conteudo.split('\n')
        resultado = []
        skip_until_terminator = None  # string que encerra o bloco premium atual

        for linha in linhas:
            # Se estamos dentro de um bloco premium, verificar se chegou ao fim
            if skip_until_terminator is not None:
                if linha.strip() == skip_until_terminator or linha.startswith('## '):
                    # Chegou ao fim do bloco premium — inclui a linha terminadora
                    skip_until_terminator = None
                    resultado.append(linha)
                # Enquanto dentro do bloco premium, pula as linhas
                continue

            # Verifica se esta linha inicia um bloco premium
            bloco_iniciado = False
            for (marcador_inicio, marcador_fim) in _TRIAL_REMOVE_BLOCKS:
                if marcador_inicio in linha:
                    # Inicia remoção do bloco
                    skip_until_terminator = marcador_fim
                    bloco_iniciado = True
                    # Substitui o bloco pelo título + aviso de recurso exclusivo
                    resultado.append(linha)  # mantém o título/primeira linha
                    resultado.append('')
                    resultado.append('> ⚠️ *[RECURSO EXCLUSIVO DO PLANO ANUAL — Adquira em https://prompt-b3.onrender.com/comprar]*')
                    resultado.append('')
                    break

            if not bloco_iniciado:
                resultado.append(linha)

        conteudo = '\n'.join(resultado)

    return conteudo

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
/* Tooltip Style */
.tooltip {
    position: relative;
    display: inline-block;
    border-bottom: 1px dashed #ffd700;
    color: #ffd700;
    cursor: help;
}
.tooltip .tooltiptext {
    visibility: hidden;
    width: 240px;
    background-color: #1a233a;
    color: #fff;
    text-align: left;
    border-radius: 6px;
    padding: 10px 14px;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    margin-left: -120px;
    opacity: 0;
    transition: opacity 0.3s;
    border: 1px solid #ffd700;
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    font-size: 0.85em;
    line-height: 1.4;
}
.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
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
        <a href="/glossario">Glossário</a>
        <a href="/relatorio">Relatório Visual</a>
        <a href="/trial">Teste 7 Dias</a>
        <a href="/comprar">Comprar 1 Ano</a>
    </div>
</nav>
"""

FOOTER = """
<footer>
    <p>© 2026 Prompt Fundamentalista B3 · <a href="mailto:promptpegardini@gmail.com" style="color:#ffd700;">promptpegardini@gmail.com</a></p>
    <p style="margin-top:8px; max-width:800px; margin-left:auto; margin-right:auto; line-height:1.6;">
        <strong style="color:#ff9800;">Aviso Legal:</strong> Este produto é exclusivamente um prompt de inteligência artificial para fins educacionais e informativos.
        Não constitui, em nenhuma hipótese, recomendação, consultoria ou aconselhamento de investimento.
        As análises geradas pela IA são baseadas em dados públicos e podem conter erros, imprecisões ou informações desatualizadas.
        O usuário é o único responsável pelas decisões de investimento tomadas. Rentabilidade passada não garante resultados futuros.
        Investir em renda variável envolve riscos, incluindo a perda total do capital investido.
    </p>
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
    
    /* Freemium Table */
    .compare-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        font-size: 0.95em;
    }}
    .compare-table th, .compare-table td {{
        padding: 14px 18px;
        text-align: left;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }}
    .compare-table th {{
        background: rgba(255,255,255,0.02);
        color: #ffd700;
        font-weight: bold;
    }}
    .compare-table tr:hover {{
        background: rgba(255,255,255,0.01);
    }}
    .check-yes {{ color: #00c853; font-weight: bold; }}
    .check-no {{ color: #d50000; font-weight: bold; }}
    .premium-row {{ background: rgba(255,215,0,0.03); }}
    </style>
</head>
<body>
{NAV}

<div class="hero">
    <h1>📈 Analise Ações B3<br>com Inteligência Artificial</h1>
    <p>O <strong style="color:#ffd700;">Prompt Fundamentalista B3</strong> combina a metodologia Barsi + Finclass em uma análise profunda. Funciona com ChatGPT, Claude e outras IAs.</p>
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
            <p>Une a filosofia de dividendos de <span class="tooltip">Luiz Barsi<span class="tooltiptext">Maior investidor pessoa física do Brasil, focado em renda passiva e dividendos de longo prazo.</span></span> com a análise de valor justo da <span class="tooltip">Finclass<span class="tooltiptext">Plataforma de educação financeira com foco em análise de empresas, crescimento e valuation.</span></span> em um único prompt poderoso.</p>
        </div>
        <div class="card">
            <div class="feature-icon">🤖</div>
            <h2>Funciona com Qualquer IA</h2>
            <p>Compatível com <strong style="color:#ffd700;">ChatGPT</strong>, <strong style="color:#ffd700;">Claude</strong>, <strong style="color:#ffd700;">Gemini</strong> e outras IAs. Basta colar o prompt e começar a analisar.</p>
        </div>
        <div class="card">
            <div class="feature-icon">🔐</div>
            <h2>Chave de Licença</h2>
            <p>Cada download vem com uma <strong style="color:#ffd700;">chave única</strong> inserida no prompt. A IA valida automaticamente antes de qualquer análise.</p>
        </div>
    </div>

    <div class="card">
        <h2>📊 Compare as Versões</h2>
        <p>Escolha o plano ideal para as suas análises fundamentalistas:</p>
        <table class="compare-table">
            <thead>
                <tr>
                    <th>Recurso</th>
                    <th>Teste 7 Dias (Grátis)</th>
                    <th style="color: #ffd700;">Plano Anual (R$ 60)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Análise <span class="tooltip">Barsi<span class="tooltiptext">Análise focada em dividendos, liquidez, endividamento e saúde financeira.</span></span> (Filtros Básicos)</td>
                    <td class="check-yes">✅ Sim</td>
                    <td class="check-yes">✅ Sim</td>
                </tr>
                <tr>
                    <td>Análise <span class="tooltip">Finclass<span class="tooltiptext">Análise focada em crescimento (CAGR), eficiência (ROIC) e reinvestimento.</span></span> (Filtros Básicos)</td>
                    <td class="check-yes">✅ Sim</td>
                    <td class="check-yes">✅ Sim</td>
                </tr>
                <tr>
                    <td>Valuation e Preço Justo</td>
                    <td class="check-yes">✅ Sim</td>
                    <td class="check-yes">✅ Sim</td>
                </tr>
                <tr>
                    <td>Simulador de Renda Passiva (Cenário A e B)</td>
                    <td class="check-yes">✅ Sim</td>
                    <td class="check-yes">✅ Sim</td>
                </tr>
                <tr class="premium-row">
                    <td><strong style="color:#ffd700;">Mapa de Dividendos Inteligente (Preço-Teto Barsi 6% e 5%)</strong></td>
                    <td class="check-no">❌ Não</td>
                    <td class="check-yes">✅ Sim</td>
                </tr>
                <tr class="premium-row">
                    <td><strong style="color:#ffd700;">Frequência Histórica de Dividendos (Meses de Pagamento)</strong></td>
                    <td class="check-no">❌ Não</td>
                    <td class="check-yes">✅ Sim</td>
                </tr>
                <tr class="premium-row">
                    <td><strong style="color:#ffd700;">Seção Alavancas e Pepinos (Gatilhos e Riscos)</strong></td>
                    <td class="check-no">❌ Não</td>
                    <td class="check-yes">✅ Sim</td>
                </tr>
                <tr class="premium-row">
                    <td><strong style="color:#ffd700;">Leitura e Citações do Estatuto Social e Release de Resultados</strong></td>
                    <td class="check-no">❌ Não</td>
                    <td class="check-yes">✅ Sim</td>
                </tr>
                <tr class="premium-row">
                    <td><strong style="color:#ffd700;">Instruções para Exportação Direta em PDF</strong></td>
                    <td class="check-no">❌ Não</td>
                    <td class="check-yes">✅ Sim</td>
                </tr>
                <tr class="premium-row">
                    <td><strong style="color:#ffd700;">Download como arquivo .md formatado</strong></td>
                    <td class="check-no">❌ Não (Copia da tela)</td>
                    <td class="check-yes">✅ Sim (Download automático)</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="card" style="background: rgba(255,215,0,0.04); border-color: rgba(255,215,0,0.25); margin-bottom: 30px;">
        <h2>🔄 Prompt em Constante Desenvolvimento</h2>
        <p>O <strong style="color:#ffd700;">Prompt Fundamentalista B3</strong> é atualizado regularmente com novas metodologias, melhorias de análise e correções. <strong style="color:#ffd700;">Quem assina o plano anual recebe todas as atualizações sem custo adicional</strong> durante o período de vigência da licença.</p>
        <p style="margin-bottom:0;">Ao adquirir hoje, você garante acesso a todas as versões futuras lançadas nos próximos 12 meses.</p>
    </div>

    <div class="card" style="background: rgba(255,100,0,0.04); border-color: rgba(255,100,0,0.2); margin-bottom: 30px;">
        <h2 style="color:#ff9800;">⚠️ Sobre os Limites da Inteligência Artificial</h2>
        <p>A IA que executa este prompt é uma ferramenta poderosa, mas <strong>não é infalível</strong>. Ela pode cometer erros, apresentar dados desatualizados ou fazer interpretações incorretas de indicadores financeiros.</p>
        <p style="margin-bottom:0;">Sempre confira os números em fontes oficiais (site de RI da empresa, CVM, B3) antes de tomar qualquer decisão. Use este prompt como ponto de partida para sua pesquisa, não como veredicto final.</p>
    </div>

    <div style="text-align:center; padding: 30px 0;">
        <h2 style="margin-bottom:20px;">Pronto para começar?</h2>
        <div style="display:flex; gap:15px; justify-content:center; flex-wrap:wrap;">
            <a href="/trial" class="btn btn-gold">🎁 Teste Grátis 7 Dias</a>
            <a href="/comprar" class="btn btn-green">💳 Comprar 1 Ano — R$ 60</a>
        </div>
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


# ─── Página Glossário ─────────────────────────────────────────────────────────

@app.route('/glossario')
def glossario():
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Glossário de Siglas — Prompt B3</title>
    <style>{CSS}
    .glossary-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }}
    .glossary-table th, .glossary-table td {{
        padding: 14px 18px;
        text-align: left;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }}
    .glossary-table th {{
        background: rgba(255,255,255,0.02);
        color: #ffd700;
        font-weight: bold;
    }}
    .glossary-table td strong {{
        color: #ffd700;
    }}
    </style>
</head>
<body>
{NAV}

<div class="container">
    <h1>📚 Glossário de Siglas Financeiras</h1>
    <p>Entenda os principais termos e indicadores fundamentalistas utilizados pelo nosso prompt:</p>

    <div class="card">
        <table class="glossary-table">
            <thead>
                <tr>
                    <th>Sigla</th>
                    <th>Nome Completo</th>
                    <th>O que significa</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>DY</strong></td>
                    <td>Dividend Yield</td>
                    <td>Rendimento de dividendos. É o valor dos proventos pagos nos últimos 12 meses dividido pelo preço atual da ação.</td>
                </tr>
                <tr>
                    <td><strong>ROIC</strong></td>
                    <td>Return on Invested Capital</td>
                    <td>Retorno sobre o capital investido. Mede a eficiência da empresa em gerar lucro com todo o dinheiro investido nela (capital próprio e de terceiros).</td>
                </tr>
                <tr>
                    <td><strong>ROE</strong></td>
                    <td>Return on Equity</td>
                    <td>Retorno sobre o patrimônio líquido. Mede a rentabilidade do dinheiro que os acionistas colocaram na empresa.</td>
                </tr>
                <tr>
                    <td><strong>CAGR</strong></td>
                    <td>Compound Annual Growth Rate</td>
                    <td>Taxa de crescimento anual composta. Mostra a velocidade média com que uma métrica (como lucro ou receita) cresceu ao longo dos anos.</td>
                </tr>
                <tr>
                    <td><strong>EBITDA</strong></td>
                    <td>Earnings Before Interest, Taxes, Depreciation, and Amortization</td>
                    <td>Lucro antes de juros, impostos, depreciação e amortização (LAJIDA). Mede a geração de caixa operacional da empresa.</td>
                </tr>
                <tr>
                    <td><strong>P/L</strong></td>
                    <td>Preço / Lucro</td>
                    <td>Múltiplo de valuation. Indica quantos anos levaria para recuperar o investimento na empresa caso ela mantivesse o lucro atual e distribuísse tudo.</td>
                </tr>
                <tr>
                    <td><strong>LPA</strong></td>
                    <td>Lucro por Ação</td>
                    <td>Lucro líquido da empresa dividido pelo número total de ações emitidas.</td>
                </tr>
                <tr>
                    <td><strong>Payout</strong></td>
                    <td>Payout Ratio</td>
                    <td>Percentual do lucro líquido que a empresa distribui aos acionistas na forma de proventos (dividendos e JCP).</td>
                </tr>
                <tr>
                    <td><strong>Capex</strong></td>
                    <td>Capital Expenditure</td>
                    <td>Investimentos em bens de capital. É o dinheiro que a empresa gasta para comprar, atualizar ou manter ativos físicos (fábricas, máquinas, etc.).</td>
                </tr>
                <tr>
                    <td><strong>ADTV</strong></td>
                    <td>Average Daily Trading Volume</td>
                    <td>Volume médio diário de negociação. Mede a liquidez da ação na bolsa para garantir que você consiga comprar ou vender sem dificuldade.</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
{FOOTER}
</body>
</html>"""
    return html


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
        margin: 15px 0 25px;
    }}
    .prompt-box {{
        text-align: left;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 20px;
        margin-top: 20px;
        max-height: 300px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 0.85em;
        white-space: pre-wrap;
    }}
    </style>
</head>
<body>
{NAV}

<div class="trial-hero">
    <h1>🎁 Teste Grátis por 7 Dias</h1>
    <p>Preencha os dados abaixo para gerar sua chave e acessar o prompt trial.</p>
</div>

<div class="container">
    <div class="card trial-form" id="form-container">
        <form id="trial-form">
            <div class="form-group">
                <label for="nome">Seu Nome</label>
                <input type="text" id="nome" required placeholder="Ex: Pedro Silva">
            </div>
            <div class="form-group">
                <label for="email">Seu Melhor E-mail</label>
                <input type="email" id="email" required placeholder="Ex: pedro@email.com">
            </div>
            <button type="submit" class="btn btn-gold" style="width:100%;">🚀 Gerar Minha Chave de Teste</button>
        </form>
    </div>

    <div class="success-box" id="success-box">
        <h2>Sua chave foi gerada com sucesso! 🎉</h2>
        <p>Esta chave é válida por 7 dias. Copie a chave abaixo:</p>
        <div class="chave-display" id="chave-val">PROMPT-XXXXX-XXXXXXXX-XXXXXXXX-7DIAS</div>
        
        <p style="margin-bottom: 15px;"><strong>Como usar:</strong> Copie o prompt abaixo, cole no seu ChatGPT ou Gemini e, quando ele solicitar, cole a chave acima.</p>
        
        <button class="btn btn-green" onclick="copyPrompt()">📋 Copiar Prompt Trial</button>
        
        <div class="prompt-box" id="prompt-content">Carregando prompt...</div>
    </div>
</div>

<script>
document.getElementById('trial-form').addEventListener('submit', function(e) {{
    e.preventDefault();
    const nome = document.getElementById('nome').value;
    const email = document.getElementById('email').value;

    fetch('/gerar-trial', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ nome, email }})
    }})
    .then(res => res.json())
    .then(data => {{
        if (data.success) {{
            document.getElementById('form-container').style.display = 'none';
            document.getElementById('success-box').style.display = 'block';
            document.getElementById('chave-val').innerText = data.chave;
            document.getElementById('prompt-content').innerText = data.prompt;
        }} else {{
            alert('Erro ao gerar chave.');
        }}
    }});
}});

function copyPrompt() {{
    const promptText = document.getElementById('prompt-content').innerText;
    navigator.clipboard.writeText(promptText).then(() => {{
        alert('Prompt copiado para a área de transferência! Cole no ChatGPT ou Gemini.');
    }});
}}
</script>

{FOOTER}
</body>
</html>"""
    return html

@app.route('/gerar-trial', methods=['POST'])
def gerar_trial():
    data = request.json or {}
    nome = data.get('nome')
    email = data.get('email')

    if not nome or not email:
        return jsonify({'success': False, 'message': 'Nome e email são obrigatórios.'})

    # Registra o lead de teste (salva em arquivo simples)
    leads_file = os.path.join(BASE_DIR, 'leads_trial.txt')
    with open(leads_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.utcnow().isoformat()} | {nome} | {email}\n")

    chave = gerar_chave(dias=7)
    # trial=True remove as seções exclusivas do plano anual
    prompt_trial = prompt_com_chave(chave, trial=True)

    return jsonify({
        'success': True,
        'chave': chave,
        'prompt': prompt_trial
    })


# ─── Página de Compra (1 Ano) ─────────────────────────────────────────────────

@app.route('/comprar')
def comprar_page():
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprar Plano Anual — Prompt B3</title>
    <style>{CSS}
    .purchase-hero {{
        text-align: center;
        padding: 60px 20px 40px;
        background: radial-gradient(ellipse at top, rgba(0,200,83,0.08) 0%, transparent 70%);
    }}
    .purchase-hero h1 {{ font-size: 2.4em; color: #00c853; }}
    .purchase-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 20px; }}
    .pix-box {{
        background: rgba(255,255,255,0.03);
        border: 2px dashed rgba(0,200,83,0.3);
        border-radius: 12px;
        padding: 30px;
        text-align: center;
    }}
    .pix-key {{
        background: rgba(0,0,0,0.4);
        border: 1px solid #00c853;
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        font-size: 1.1em;
        color: #00c853;
        margin: 15px 0;
        word-break: break-all;
    }}
    @media (max-width: 768px) {{
        .purchase-grid {{ grid-template-columns: 1fr; gap: 20px; }}
    }}
    </style>
</head>
<body>
{NAV}

<div class="purchase-hero">
    <h1>💳 Plano Anual Completo — R$ 60,00</h1>
    <p>Acesse o prompt definitivo com todos os recursos exclusivos por 365 dias.</p>
</div>

<div class="container">
    <div class="purchase-grid">
        <div class="card">
            <h2>1. Seus Dados</h2>
            <p style="margin-bottom: 20px;">Preencha o formulário para registrar sua solicitação de licença:</p>
            <form id="purchase-form">
                <div class="form-group">
                    <label for="p-nome">Seu Nome</label>
                    <input type="text" id="p-nome" required placeholder="Ex: Pedro Silva">
                </div>
                <div class="form-group">
                    <label for="p-email">Seu E-mail</label>
                    <input type="email" id="p-email" required placeholder="Ex: pedro@email.com">
                </div>
                <button type="submit" class="btn btn-green" style="width:100%;">🚀 Enviar Solicitação</button>
            </form>
            <div id="purchase-success" style="display:none; color:#00c853; font-weight:bold; margin-top:15px; text-align:center;">
                ✅ Solicitação enviada! Faça o PIX ao lado para liberação imediata.
            </div>
        </div>

        <div class="pix-box">
            <h2>2. Pagamento PIX</h2>
            <p style="margin-top: 10px;">Escaneie o QR Code abaixo com o app do seu banco para pagar <strong>R$ 60,00</strong> via PIX:</p>
            
            <div style="margin: 20px auto; max-width: 260px;">
                <img src="data:image/png;base64,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WMgKRJfYMKFTCtlYqbrM0vKoH8hFbXyShYcuaYx6VEMhGytVl1laHvUDuaiNT7Lw0CXOMKFTJbOxUuWoJ1XO+iNQO1PCmZhm3uNTLYsQsXCGCb1SMhsrVYksrZz1A7mpjU+y8NAlNkzoXIlsrFQls7Ry1A94URufZOGhK+E3TFvfwl1eXrb9+/fb/Py8zc/P2/79+215eXnb38v181w/1dZ/5V177bV29OhRO336tJ0+fdqOHj26mdN179876/Unk0nSz7R6vNszV/25frwNBoNtf7zH/7S/11up+T7tflPbP3V8evNeT7yprc9q9ciZnLCbNn72fOtlk9w/3sbj8eTkyZOTxcXFiZlt+7O4uDg5efLkZDwec/3M169Nbe057R67/PEe/7P8eNSjdr+z1OPdntGprSdq9aRy2cNs2SOFP/Rd8hAx169Pbe1Z8l/lah8C2M5E7JCy2oceOETfTG09UasnFYe+W5TMJuP69aE9u9PHbMFIWYqMZ39q64laPWrCv8O0d+9eu/XWW20wGExdHIbDoU0mE7viiivslltu4foZr1+b2tpT4dyH9/ifReo7IgrzPdUs9fAOUzO19UStnlTe7zCF3zApZZPVeP3a1NaeChumDX3IFlSa76l2Uw8bpmZq64laPal4JNfCO/uJbClsxXiIxbMPdpNNprRedYGst2asJ7GE3zBFp5CtRtYSlKmNT7V6vLH+1IP+asaGqTCFbDWylqBMbXyq1eON9ace9Fez8GeYvJ+Re1+frxWIpbYzGdG/ViBn/RE+Zq92v6w/zdTWk+j9xRmmniuZrUbWEpSpjU+1eryx/tSH/mrGhklAiWw1spagTG18qtXjjfWnXvTXdDySy3z9aebm5mzv3r12zTXXbOYbTe6VzbQTW//M8vKyHTp0aPO7MDyvv5uPN/exHrW30L15/ysytX1yjYdc9aRS+1d59PHpvR7mqqeLrwMocb9q+B6mFlE2TFstLi7addddZxdffPGu6j916pRdffXVtrKyUuT6qfpUDxumvHazYco9HmapJ5XaC1j08em9HnrU463L+1XDGaYeGQ6HNhqNbGVlxZaWlnadRr60tGQrKys2Go3OOnTnff1UfawHZeUcD4jPez3MWY831jd/rDYdipANp5ZFpVYPylLLhkNZatlnJccn65s/NkwFrK+v22AwsIMHDyb/2YMH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" alt="QR Code PIX R$ 60,00" style="width:100%; border-radius:10px; display:block;">
            </div>
            
            <p style="font-size: 0.85em; color: #aaa; margin-top: 5px;">📱 Abra o app do banco → PIX → Ler QR Code</p>
            
            <div style="margin-top: 25px; text-align: left; font-size: 0.9em; color: #aaa; line-height: 1.6;">
                <p><strong>Após o pagamento:</strong></p>
                <p>📧 Envie o comprovante para <strong style="color:#ffd700;">promptpegardini@gmail.com</strong></p>
                <p>⏱️ Sua licença anual será ativada e enviada para o seu e-mail em até 15 minutos após a confirmação!</p>
            </div>
        </div>
    </div>

    <div class="card" style="background: rgba(255,215,0,0.04); border-color: rgba(255,215,0,0.2); margin-top: 30px;">
        <h2>🔄 Assinantes Recebem Todas as Atualizações</h2>
        <p>O Prompt Fundamentalista B3 está em constante evolução. Ao assinar o plano anual, você recebe <strong style="color:#ffd700;">todas as novas versões lançadas durante os 12 meses de licença</strong>, sem nenhum custo adicional. Basta solicitar o arquivo atualizado pelo e-mail.</p>
    </div>

    <div class="disclaimer" style="margin-top: 20px; font-size: 0.85em; line-height: 1.7;">
        <strong>⚠️ Aviso Legal:</strong> Este produto é um prompt de inteligência artificial para fins exclusivamente educacionais e informativos.
        Não constitui recomendação, consultoria ou aconselhamento de investimento de qualquer natureza.
        As análises geradas pela IA podem conter erros, imprecisões ou dados desatualizados — sempre verifique as informações em fontes oficiais (site de RI, CVM, B3).
        O usuário é o único e exclusivo responsável por qualquer decisão de investimento tomada.
        Investir em renda variável envolve riscos, incluindo a perda total do capital investido.
    </div>
</div>

<script>
document.getElementById('purchase-form').addEventListener('submit', function(e) {{
    e.preventDefault();
    const nome = document.getElementById('p-nome').value;
    const email = document.getElementById('p-email').value;

    fetch('/registrar-compra', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ nome, email }})
    }})
    .then(res => res.json())
    .then(data => {{
        if (data.success) {{
            document.getElementById('purchase-success').style.display = 'block';
            document.getElementById('p-nome').disabled = true;
            document.getElementById('p-email').disabled = true;
        }} else {{
            alert('Erro ao registrar.');
        }}
    }});
}});

</script>

{FOOTER}
</body>
</html>"""
    return html

@app.route('/registrar-compra', methods=['POST'])
def registrar_compra():
    data = request.json or {}
    nome = data.get('nome')
    email = data.get('email')

    if not nome or not email:
        return jsonify({'success': False, 'message': 'Nome e email são obrigatórios.'})

    # Registra a intenção de compra
    compras_file = os.path.join(BASE_DIR, 'compras_pendentes.txt')
    with open(compras_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.utcnow().isoformat()} | PENDENTE | {nome} | {email}\n")

    return jsonify({'success': True})


# ─── Painel Admin (Gerenciamento) ─────────────────────────────────────────────

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Login via formulário POST
    if request.method == 'POST':
        senha = request.form.get('senha')
        if senha == ADMIN_SENHA:
            session['admin_logged_in'] = True
        else:
            return render_login_page(error="Senha incorreta!")

    # Verifica se está logado
    if not session.get('admin_logged_in'):
        # Também aceita login direto via parâmetro ?senha= na URL para conveniência
        url_senha = request.args.get('senha')
        if url_senha == ADMIN_SENHA:
            session['admin_logged_in'] = True
        else:
            return render_login_page()

    # Se logado, renderiza o painel
    return render_admin_panel()

def render_login_page(error=None):
    error_msg = f'<div style="color:#ff3d00; margin-bottom:15px; text-align:center; font-weight:bold;">❌ {error}</div>' if error else ''
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Admin — Prompt B3</title>
    <style>{CSS}
    .login-box {{
        max-width: 450px;
        margin: 100px auto 0;
        border: 2px solid #ffd700;
        box-shadow: 0 10px 30px rgba(255,215,0,0.1);
    }}
    </style>
</head>
<body>
<div class="container">
    <div class="card login-box">
        <h2 style="text-align:center; margin-bottom:20px; color:#ffd700;">🔐 Acesso Administrador</h2>
        {error_msg}
        <form method="POST" action="/admin">
            <div class="form-group">
                <label for="senha">Senha do Admin</label>
                <input type="password" name="senha" id="senha" required placeholder="Digite a senha secreta" autofocus>
            </div>
            <button type="submit" class="btn btn-gold" style="width:100%; font-size:1.1em; padding:14px;">🚀 Entrar no Painel</button>
        </form>
    </div>
</div>
</body>
</html>"""
    return html

def render_admin_panel():
    # Lê as compras pendentes
    compras_file = os.path.join(BASE_DIR, 'compras_pendentes.txt')
    compras_list = []
    if os.path.exists(compras_file):
        with open(compras_file, 'r', encoding='utf-8') as f:
            compras_list = f.readlines()

    # Lê os leads de trial
    leads_file = os.path.join(BASE_DIR, 'leads_trial.txt')
    leads_list = []
    if os.path.exists(leads_file):
        with open(leads_file, 'r', encoding='utf-8') as f:
            leads_list = f.readlines()

    # Renderiza as tabelas no painel
    compras_html = ""
    for c in reversed(compras_list):
        partes = c.strip().split(' | ')
        if len(partes) >= 4:
            data, status, nome, email = partes[0], partes[1], partes[2], partes[3]
            compras_html += f"""<tr>
                <td>{data[:16]}</td>
                <td><span style="color:#ff9800; font-weight:bold;">{status}</span></td>
                <td>{nome}</td>
                <td>{email}</td>
                <td>
                    <button class="btn btn-green" style="padding:6px 12px; font-size:0.85em;" onclick="gerarLinkAnual('{nome}', '{email}')">Gerar Link 1 Ano</button>
                </td>
            </tr>"""

    leads_html = ""
    for l in reversed(leads_list):
        partes = l.strip().split(' | ')
        if len(partes) >= 3:
            data, nome, email = partes[0], partes[1], partes[2]
            leads_html += f"""<tr>
                <td>{data[:16]}</td>
                <td>{nome}</td>
                <td>{email}</td>
            </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Admin — Prompt B3</title>
    <style>{CSS}
    table {{ width:100%; border-collapse:collapse; margin-top:15px; font-size:0.9em; }}
    th, td {{ padding:12px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.05); }}
    th {{ color:#ffd700; background:rgba(255,255,255,0.02); }}
    .admin-grid {{ display:grid; grid-template-columns: 2fr 1fr; gap:30px; margin-top:20px; }}
    .modal {{
        display:none; position:fixed; top:0; left:0; width:100%; height:100%;
        background:rgba(0,0,0,0.8); z-index:1000; justify-content:center; align-items:center;
    }}
    .modal-content {{ background:#121829; border:2px solid #ffd700; border-radius:12px; padding:30px; max-width:600px; width:90%; }}
    </style>
</head>
<body>
{NAV}

<div class="container">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:30px;">
        <h1>🔑 Painel de Controle</h1>
        <a href="/admin/logout" class="btn btn-blue" style="padding:8px 16px; font-size:0.9em;">Sair</a>
    </div>

    <div class="card">
        <h2>💳 Solicitações de Compra Pendentes</h2>
        <table>
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Status</th>
                    <th>Nome</th>
                    <th>E-mail</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                {compras_html if compras_html else '<tr><td colspan="5" style="text-align:center; color:#555;">Nenhuma solicitação pendente.</td></tr>'}
            </tbody>
        </table>
    </div>

    <div class="admin-grid">
        <div class="card">
            <h2>🎁 Leads de Teste (7 Dias)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Nome</th>
                        <th>E-mail</th>
                    </tr>
                </thead>
                <tbody>
                    {leads_html if leads_html else '<tr><td colspan="3" style="text-align:center; color:#555;">Nenhum lead de teste ainda.</td></tr>'}
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>🛠️ Gerador Manual</h2>
            <p>Gerar licença de 1 ano diretamente:</p>
            <div class="form-group" style="margin-top:15px;">
                <label>Nome do Cliente</label>
                <input type="text" id="m-nome" placeholder="Ex: Pedro Silva">
            </div>
            <div class="form-group">
                <label>E-mail do Cliente</label>
                <input type="email" id="m-email" placeholder="Ex: pedro@email.com">
            </div>
            <button class="btn btn-gold" style="width:100%;" onclick="gerarLinkAnualManual()">Gerar Licença 1 Ano</button>
        </div>
    </div>
</div>

<div class="modal" id="link-modal">
    <div class="modal-content">
        <h2 style="color:#00c853; margin-bottom:15px;">Chave Anual Gerada! 🎉</h2>
        <p>Envie o link de download abaixo para o cliente. Ele fará o download do prompt de 1 ano já com a chave dele inserida.</p>
        
        <div class="form-group" style="margin-top:20px;">
            <label>Link Único de Download</label>
            <input type="text" id="link-display" readonly style="background:rgba(0,0,0,0.3); color:#ffd700; border-color:#00c853;">
        </div>
        
        <div style="display:flex; gap:10px; margin-top:20px;">
            <button class="btn btn-green" onclick="copyLink()">📋 Copiar Link</button>
            <button class="btn btn-blue" onclick="fecharModal()">Fechar</button>
        </div>
    </div>
</div>

<script>
function gerarLinkAnual(nome, email) {{
    fetch('/admin/gerar-link-anual', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ nome, email }})
    }})
    .then(res => res.json())
    .then(data => {{
        if (data.success) {{
            document.getElementById('link-display').value = window.location.origin + '/download/' + data.token;
            document.getElementById('link-modal').style.display = 'flex';
        }} else {{
            alert('Erro ao gerar link.');
        }}
    }});
}}

function gerarLinkAnualManual() {{
    const nome = document.getElementById('m-nome').value;
    const email = document.getElementById('m-email').value;
    if (!nome || !email) {{
        alert('Preencha nome e email!');
        return;
    }}
    gerarLinkAnual(nome, email);
}}

function copyLink() {{
    const linkVal = document.getElementById('link-display');
    linkVal.select();
    document.execCommand('copy');
    alert('Link copiado!');
}}

function fecharModal() {{
    document.getElementById('link-modal').style.display = 'none';
    window.location.reload();
}}
</script>

{FOOTER}
</body>
</html>"""
    return html

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return make_response("Deslogado com sucesso. <a href='/admin'>Voltar ao login</a>", 200)

@app.route('/admin/gerar-link-anual', methods=['POST'])
def admin_gerar_link_anual():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Não autorizado.'}), 403

    data = request.json or {}
    nome = data.get('nome')
    email = data.get('email')

    if not nome or not email:
        return jsonify({'success': False, 'message': 'Nome e email são obrigatórios.'})

    # Gera token único de download
    token = secrets.token_urlsafe(16)
    chave = gerar_chave(dias=365)

    # Registra o token no arquivo de tokens válidos
    tokens_file = os.path.join(BASE_DIR, 'tokens_ativos.txt')
    with open(tokens_file, 'a', encoding='utf-8') as f:
        f.write(f"{token} | {chave} | {nome} | {email} | {datetime.utcnow().isoformat()}\n")

    # Remove da lista de pendentes (marca como APROVADO)
    compras_file = os.path.join(BASE_DIR, 'compras_pendentes.txt')
    if os.path.exists(compras_file):
        with open(compras_file, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
        with open(compras_file, 'w', encoding='utf-8') as f:
            for l in linhas:
                if email in l and "PENDENTE" in l:
                    l = l.replace("PENDENTE", "APROVADO")
                f.write(l)

    return jsonify({'success': True, 'token': token})


# ─── Download do Prompt Anual (Link Único) ───────────────────────────────────

@app.route('/download/<token>')
def download_prompt(token):
    tokens_file = os.path.join(BASE_DIR, 'tokens_ativos.txt')
    if not os.path.exists(tokens_file):
        return "Link inválido ou expirado.", 404

    with open(tokens_file, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    chave_encontrada = None
    nome_cliente = "Cliente"
    for l in linhas:
        partes = l.strip().split(' | ')
        if len(partes) >= 4 and partes[0] == token:
            chave_encontrada = partes[1]
            nome_cliente = partes[2]
            break

    if not chave_encontrada:
        return "Link de download inválido ou já utilizado.", 404

    # Gera o prompt customizado com a chave de 1 ano
    prompt_final = prompt_com_chave(chave_encontrada)

    # Prepara o arquivo para download
    memoria_arquivo = io.BytesIO()
    memoria_arquivo.write(prompt_final.encode('utf-8'))
    memoria_arquivo.seek(0)

    # Nome limpo para o arquivo
    nome_arquivo_limpo = f"Prompt_Fundamentalista_B3_1ano.md"

    return send_file(
        memoria_arquivo,
        as_attachment=True,
        download_name=nome_arquivo_limpo,
        mimetype='text/markdown'
    )



# ─── Página /relatorio ────────────────────────────────────────────────────────

RELATORIO_CSS_EXTRA = """
/* ── Layout geral ── */
.rel-instrucoes {
    background: linear-gradient(135deg, rgba(255,215,0,0.08), rgba(255,215,0,0.03));
    border: 1px solid rgba(255,215,0,0.3);
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 30px;
}
.rel-instrucoes h2 { margin-bottom: 16px; }
.rel-steps { display: flex; flex-direction: column; gap: 14px; margin-top: 16px; }
.rel-step {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    background: rgba(255,255,255,0.04);
    border-radius: 10px;
    padding: 14px 18px;
}
.rel-step-num {
    background: #ffd700;
    color: #000;
    font-weight: bold;
    font-size: 1em;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.rel-step-text { color: #ccc; line-height: 1.6; }
.rel-step-text strong { color: #fff; }
.rel-step-text code {
    background: rgba(255,255,255,0.1);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.9em;
    color: #ffd700;
}
.rel-textarea-wrap { margin-bottom: 20px; }
.rel-textarea-wrap label { display: block; color: #ffd700; font-weight: bold; margin-bottom: 10px; font-size: 1em; }
#rel-input {
    width: 100%;
    min-height: 220px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,215,0,0.3);
    border-radius: 10px;
    color: #ddd;
    font-family: monospace;
    font-size: 0.88em;
    padding: 16px;
    resize: vertical;
    line-height: 1.5;
}
#rel-input:focus { outline: none; border-color: #ffd700; }
.rel-btn-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
.rel-hint { font-size: 0.82em; color: #666; margin-top: 6px; }

/* ── Relatório visual ── */
#rel-output { display: none; margin-top: 40px; }
.rel-header {
    background: linear-gradient(135deg, #0d1526, #1a2540);
    border: 2px solid rgba(255,215,0,0.4);
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 28px;
}
.rel-header-ticker { font-size: 2.4em; font-weight: bold; color: #ffd700; }
.rel-header-empresa { font-size: 1.1em; color: #aaa; margin-top: 4px; }
.rel-header-meta {
    display: flex; flex-wrap: wrap; gap: 20px; margin-top: 18px;
}
.rel-meta-item { text-align: center; }
.rel-meta-label { font-size: 0.75em; color: #888; text-transform: uppercase; letter-spacing: 1px; }
.rel-meta-value { font-size: 1.2em; font-weight: bold; color: #fff; margin-top: 2px; }
.rel-meta-value.preco { color: #ffd700; }

/* Seções */
.rel-section {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 22px;
}
.rel-section-title {
    font-size: 1.15em;
    font-weight: bold;
    color: #ffd700;
    margin-bottom: 18px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255,215,0,0.15);
    display: flex;
    align-items: center;
    gap: 10px;
}

/* Tabelas */
.rel-table { width: 100%; border-collapse: collapse; font-size: 0.92em; margin-top: 8px; }
.rel-table th {
    background: rgba(255,255,255,0.04);
    color: #ffd700;
    padding: 10px 14px;
    text-align: left;
    font-weight: bold;
    border-bottom: 1px solid rgba(255,215,0,0.2);
}
.rel-table td { padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,0.04); color: #ccc; }
.rel-table tr:last-child td { border-bottom: none; }
.rel-table tr:hover td { background: rgba(255,255,255,0.02); }
.status-ok { color: #00c853; font-weight: bold; }
.status-fail { color: #ff3d00; font-weight: bold; }
.status-na { color: #888; }

/* Score + Pizza */
.rel-score-wrap {
    display: flex;
    align-items: center;
    gap: 28px;
    margin-top: 18px;
    flex-wrap: wrap;
}
.rel-score-chart { width: 130px; height: 130px; flex-shrink: 0; }
.rel-score-info { flex: 1; min-width: 180px; }
.rel-score-num { font-size: 2.4em; font-weight: bold; }
.rel-score-label { font-size: 0.85em; color: #888; margin-top: 2px; }
.rel-veredito {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.95em;
    margin-top: 10px;
    letter-spacing: 0.5px;
}
.veredito-aprovada { background: rgba(0,200,83,0.15); color: #00c853; border: 1px solid #00c853; }
.veredito-reprovada { background: rgba(255,61,0,0.15); color: #ff3d00; border: 1px solid #ff3d00; }
.veredito-pendente { background: rgba(255,152,0,0.15); color: #ff9800; border: 1px solid #ff9800; }
.veredito-inconclusivo { background: rgba(150,150,150,0.15); color: #aaa; border: 1px solid #aaa; }

/* Semáforo / Mapa de Dividendos */
.rel-semaforo {
    display: flex;
    align-items: center;
    gap: 14px;
    background: rgba(0,0,0,0.25);
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 14px;
}
.rel-semaforo-dot {
    width: 22px; height: 22px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-verde { background: #00c853; box-shadow: 0 0 10px #00c853; }
.dot-amarelo { background: #ffd700; box-shadow: 0 0 10px #ffd700; }
.dot-vermelho { background: #ff3d00; box-shadow: 0 0 10px #ff3d00; }
.rel-semaforo-text { font-size: 1em; color: #ddd; line-height: 1.5; }
.rel-semaforo-text strong { color: #fff; }

/* Veredito final */
.rel-veredito-final {
    border-radius: 14px;
    padding: 28px 32px;
    text-align: center;
    margin-bottom: 22px;
}
.vf-comprar { background: linear-gradient(135deg, rgba(0,200,83,0.12), rgba(0,200,83,0.04)); border: 2px solid #00c853; }
.vf-acompanhar { background: linear-gradient(135deg, rgba(255,215,0,0.12), rgba(255,215,0,0.04)); border: 2px solid #ffd700; }
.vf-evitar { background: linear-gradient(135deg, rgba(255,61,0,0.12), rgba(255,61,0,0.04)); border: 2px solid #ff3d00; }
.vf-inconclusivo { background: linear-gradient(135deg, rgba(150,150,150,0.12), rgba(150,150,150,0.04)); border: 2px solid #888; }
.vf-emoji { font-size: 3em; margin-bottom: 10px; }
.vf-classificacao { font-size: 1.8em; font-weight: bold; margin-bottom: 8px; }
.vf-precos { display: flex; gap: 30px; justify-content: center; flex-wrap: wrap; margin-top: 16px; }
.vf-preco-item { text-align: center; }
.vf-preco-label { font-size: 0.78em; color: #888; text-transform: uppercase; letter-spacing: 1px; }
.vf-preco-val { font-size: 1.3em; font-weight: bold; color: #ffd700; margin-top: 3px; }

/* Citações de documentos */
.rel-citacao {
    background: rgba(255,215,0,0.05);
    border-left: 3px solid #ffd700;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 10px 0;
    font-style: italic;
    color: #ccc;
    font-size: 0.9em;
    line-height: 1.6;
}
.rel-citacao-fonte { font-style: normal; color: #888; font-size: 0.82em; margin-top: 5px; }

/* Alavancas e Pepinos */
.rel-alavancas { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 8px; }
.rel-alavanca-box { border-radius: 10px; padding: 16px 18px; }
.box-verde { background: rgba(0,200,83,0.07); border: 1px solid rgba(0,200,83,0.25); }
.box-vermelho { background: rgba(255,61,0,0.07); border: 1px solid rgba(255,61,0,0.25); }
.rel-alavanca-titulo { font-weight: bold; margin-bottom: 10px; font-size: 0.95em; }
.box-verde .rel-alavanca-titulo { color: #00c853; }
.box-vermelho .rel-alavanca-titulo { color: #ff6b35; }
.rel-alavanca-item { color: #bbb; font-size: 0.88em; line-height: 1.6; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.rel-alavanca-item:last-child { border-bottom: none; }

/* Simulador */
.rel-sim-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 8px; }
.rel-sim-box { background: rgba(255,255,255,0.03); border-radius: 10px; padding: 16px 18px; border: 1px solid rgba(255,255,255,0.07); }
.rel-sim-titulo { font-weight: bold; color: #ffd700; margin-bottom: 12px; font-size: 0.95em; }
.rel-sim-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 0.88em; }
.rel-sim-row:last-child { border-bottom: none; }
.rel-sim-key { color: #888; }
.rel-sim-val { color: #ddd; font-weight: bold; }
.rel-sim-val.destaque { color: #00c853; font-size: 1.05em; }

/* Frequência */
.rel-freq-badge {
    display: inline-block;
    background: rgba(255,215,0,0.12);
    border: 1px solid rgba(255,215,0,0.3);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.88em;
    color: #ffd700;
    margin: 4px 4px 4px 0;
}

/* Disclaimer */
.rel-disclaimer {
    background: rgba(255,100,0,0.07);
    border: 1px solid rgba(255,100,0,0.2);
    border-radius: 10px;
    padding: 16px 20px;
    font-size: 0.82em;
    color: #aaa;
    line-height: 1.7;
    margin-top: 10px;
}

/* Botões de ação */
.rel-action-bar {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 28px;
    padding: 16px 20px;
    background: rgba(255,255,255,0.03);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.06);
    align-items: center;
}
.rel-action-bar span { color: #888; font-size: 0.88em; flex: 1; min-width: 200px; }

/* Aviso de dado indisponível */
.dado-indisponivel { color: #ff9800; font-style: italic; font-size: 0.88em; }
.dado-desatualizado { color: #ff9800; font-style: italic; font-size: 0.88em; }

/* Print */
@media print {
    nav, .rel-instrucoes, .rel-textarea-wrap, .rel-btn-row, .rel-hint, .rel-action-bar,
    footer, #form-area { display: none !important; }
    #rel-output { display: block !important; }
    body { background: #fff !important; color: #000 !important; }
    .rel-header, .rel-section, .rel-veredito-final {
        background: #fff !important;
        border-color: #ccc !important;
        color: #000 !important;
        break-inside: avoid;
    }
    .rel-header-ticker, .rel-section-title, h1, h2 { color: #000 !important; }
    .rel-table th { background: #f0f0f0 !important; color: #000 !important; }
    .rel-table td { color: #333 !important; }
    .rel-score-num, .vf-classificacao { color: #000 !important; }
    .rel-citacao { border-left-color: #999 !important; color: #333 !important; }
    canvas { max-width: 120px !important; max-height: 120px !important; }
}

@media (max-width: 768px) {
    .rel-alavancas, .rel-sim-grid { grid-template-columns: 1fr; }
    .rel-score-wrap { flex-direction: column; align-items: flex-start; }
    .vf-precos { gap: 16px; }
}
"""

RELATORIO_PAGE_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gerador de Relatório Visual — Prompt B3</title>
    <style>{css}{css_extra}</style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
{nav}

<div class="container">
    <h1>📊 Gerador de Relatório Visual</h1>
    <p>Cole abaixo o texto gerado pela IA e transforme em um relatório colorido, com gráficos e pronto para imprimir.</p>

    <div id="form-area">
        <!-- ── Instruções passo a passo ── -->
        <div class="rel-instrucoes">
            <h2>📋 Como usar esta página</h2>
            <div class="rel-steps">
                <div class="rel-step">
                    <div class="rel-step-num">1</div>
                    <div class="rel-step-text">
                        <strong>Abra o ChatGPT, Claude ou Gemini</strong> com o seu prompt ativo.
                        Se ainda não tem o prompt, <a href="/trial" style="color:#ffd700;">solicite o teste grátis de 7 dias</a>.
                    </div>
                </div>
                <div class="rel-step">
                    <div class="rel-step-num">2</div>
                    <div class="rel-step-text">
                        <strong>Peça a análise da ação</strong> que deseja (ex: "Analise TAEE11") e aguarde a IA gerar o relatório completo.
                    </div>
                </div>
                <div class="rel-step">
                    <div class="rel-step-num">3</div>
                    <div class="rel-step-text">
                        <strong>Selecione todo o texto</strong> da resposta da IA
                        (<code>Ctrl+A</code> dentro da resposta ou clique e arraste),
                        depois copie (<code>Ctrl+C</code>).
                    </div>
                </div>
                <div class="rel-step">
                    <div class="rel-step-num">4</div>
                    <div class="rel-step-text">
                        <strong>Cole aqui abaixo</strong> (<code>Ctrl+V</code>) e clique em
                        <strong style="color:#ffd700;">Gerar Relatório Visual</strong>.
                    </div>
                </div>
                <div class="rel-step">
                    <div class="rel-step-num">5</div>
                    <div class="rel-step-text">
                        <strong>Para salvar em PDF:</strong> clique em
                        <strong style="color:#ffd700;">🖨️ Imprimir / Salvar PDF</strong>,
                        escolha a impressora <code>Salvar como PDF</code> e marque
                        <code>Gráficos de fundo</code> para manter as cores.
                    </div>
                </div>
                <div class="rel-step">
                    <div class="rel-step-num">6</div>
                    <div class="rel-step-text">
                        <strong>Tem documentos (Estatuto Social ou Release de Resultados)?</strong>
                        Faça uma segunda análise na IA com os documentos anexados, cole o novo texto
                        no campo abaixo e clique em <strong style="color:#ffd700;">➕ Mesclar com Análise Anterior</strong>
                        — o relatório será atualizado com as citações dos documentos sem perder os dados anteriores.
                    </div>
                </div>
            </div>
        </div>

        <!-- ── Campo de entrada ── -->
        <div class="rel-textarea-wrap">
            <label for="rel-input">📥 Cole aqui o texto gerado pela IA:</label>
            <textarea id="rel-input" placeholder="Cole aqui o texto completo da análise gerada pela IA...&#10;&#10;Exemplo: # 📊 Relatório Fundamentalista Híbrido: VALE3&#10;**Data**: 07/07/2026 | **Empresa**: Vale S.A. | ..."></textarea>
        </div>
        <div class="rel-btn-row">
            <button class="btn btn-gold" onclick="gerarRelatorio(false)">📊 Gerar Relatório Visual</button>
            <button class="btn btn-blue" onclick="gerarRelatorio(true)" id="btn-mesclar" style="display:none;">➕ Mesclar com Análise Anterior</button>
            <button class="btn" style="background:rgba(255,255,255,0.08); color:#aaa;" onclick="limparTudo()">🗑️ Limpar</button>
        </div>
        <p class="rel-hint">⚠️ Os dados são processados localmente no seu navegador — nenhuma informação é enviada para nossos servidores.</p>
    </div>

    <!-- ── Saída do relatório ── -->
    <div id="rel-output">
        <div class="rel-action-bar">
            <span>✅ Relatório gerado com sucesso! Role a página para ver o conteúdo completo.</span>
            <button class="btn btn-gold" onclick="window.print()" style="padding:10px 22px;">🖨️ Imprimir / Salvar PDF</button>
            <button class="btn" style="background:rgba(255,255,255,0.08); color:#aaa; padding:10px 18px;" onclick="voltarFormulario()">✏️ Nova Análise</button>
        </div>
        <div id="rel-conteudo"></div>
    </div>
</div>

{footer}

<script>
// ─── Estado global ────────────────────────────────────────────────────────────
let estadoAnterior = null;
let chartBarsi = null;
let chartFinclass = null;

// ─── Utilitários ─────────────────────────────────────────────────────────────

function extrairValor(texto, ...padroes) {{
    for (const p of padroes) {{
        const m = texto.match(p);
        if (m) return m[1].trim();
    }}
    return null;
}}

function extrairScore(texto, secao) {{
    const padroes = [
        new RegExp(secao + '[\\\\s\\\\S]*?Score[:\\\\s]+([0-9]+)\\\\s*/\\\\s*100', 'i'),
        new RegExp('Score[:\\\\s]+([0-9]+)\\\\s*/\\\\s*100[\\\\s\\\\S]*?' + secao, 'i'),
        /Score[:\s]+([0-9]+)\s*\/\s*100/i,
    ];
    for (const p of padroes) {{
        const m = texto.match(p);
        if (m) return parseInt(m[1]);
    }}
    return null;
}}

function extrairVeredito(texto, secao) {{
    const bloco = extrairBloco(texto, secao, ['## ']);
    if (!bloco) return null;
    if (/APROVADA/i.test(bloco)) return 'APROVADA';
    if (/REPROVADA/i.test(bloco)) return 'REPROVADA';
    if (/INCONCLUSIVO/i.test(bloco)) return 'INCONCLUSIVO';
    if (/PENDENTE/i.test(bloco)) return 'PENDENTE';
    return null;
}}

function extrairBloco(texto, marcadorInicio, marcadoresFim) {{
    const idx = texto.indexOf(marcadorInicio);
    if (idx < 0) return null;
    let fim = texto.length;
    for (const mf of marcadoresFim) {{
        const i = texto.indexOf(mf, idx + marcadorInicio.length);
        if (i > 0 && i < fim) fim = i;
    }}
    return texto.slice(idx + marcadorInicio.length, fim).trim();
}}

function classeVeredito(v) {{
    if (!v) return 'veredito-pendente';
    const u = v.toUpperCase();
    if (u.includes('APROVADA')) return 'veredito-aprovada';
    if (u.includes('REPROVADA')) return 'veredito-reprovada';
    if (u.includes('INCONCLUSIVO')) return 'veredito-inconclusivo';
    return 'veredito-pendente';
}}

function corScore(score) {{
    if (score === null) return '#888';
    if (score >= 70) return '#00c853';
    if (score >= 45) return '#ffd700';
    return '#ff3d00';
}}

function parsearTabela(bloco) {{
    const linhas = bloco.split('\\n').filter(l => l.includes('|'));
    if (linhas.length < 2) return null;
    const rows = linhas.map(l =>
        l.split('|').map(c => c.trim()).filter((c, i, a) => i > 0 && i < a.length - 1)
    ).filter(r => r.length > 0 && !r.every(c => /^[-:]+$/.test(c)));
    if (rows.length < 2) return null;
    return {{ header: rows[0], body: rows.slice(1) }};
}}

function renderTabela(tabela) {{
    if (!tabela) return '<p class="dado-indisponivel">Tabela não encontrada.</p>';
    let html = '<table class="rel-table"><thead><tr>';
    tabela.header.forEach(h => {{ html += `<th>${{h}}</th>`; }});
    html += '</tr></thead><tbody>';
    tabela.body.forEach(row => {{
        html += '<tr>';
        row.forEach((cell, i) => {{
            let cls = '';
            if (i === row.length - 1) {{
                if (/✅/.test(cell)) cls = 'status-ok';
                else if (/❌/.test(cell)) cls = 'status-fail';
            }}
            // Destaca dados indisponíveis
            const cellHtml = cell
                .replace(/\[Dado não disponível[^\]]*\]/gi, m => `<span class="dado-indisponivel">${{m}}</span>`)
                .replace(/\[Dado desatualizado[^\]]*\]/gi, m => `<span class="dado-desatualizado">${{m}}</span>`);
            html += `<td class="${{cls}}">${{cellHtml}}</td>`;
        }});
        html += '</tr>';
    }});
    html += '</tbody></table>';
    return html;
}}

function renderPizza(canvasId, score, cor) {{
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    const s = score !== null ? score : 0;
    const chart = new Chart(ctx, {{
        type: 'doughnut',
        data: {{
            datasets: [{{
                data: [s, 100 - s],
                backgroundColor: [cor, 'rgba(255,255,255,0.06)'],
                borderWidth: 0,
                hoverOffset: 0,
            }}]
        }},
        options: {{
            cutout: '72%',
            plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: false }} }},
            animation: {{ duration: 800 }},
        }}
    }});
    return chart;
}}

function semaforo(zona) {{
    const z = (zona || '').toUpperCase();
    if (z.includes('COMPRA') || z.includes('🟢')) return {{ cls: 'dot-verde', label: '🟢 ZONA DE COMPRA' }};
    if (z.includes('ATENCAO') || z.includes('ATENÇÃO') || z.includes('🟡')) return {{ cls: 'dot-amarelo', label: '🟡 ZONA DE ATENÇÃO' }};
    if (z.includes('EVITAR') || z.includes('🔴')) return {{ cls: 'dot-vermelho', label: '🔴 ZONA DE EVITAR' }};
    return null;
}}

function classificacaoFinal(texto) {{
    if (/COMPRAR|🟢\s*COMPRAR/i.test(texto)) return {{ emoji: '🟢', label: 'COMPRAR', cls: 'vf-comprar', cor: '#00c853' }};
    if (/ACOMPANHAR|🟡\s*ACOMPANHAR/i.test(texto)) return {{ emoji: '🟡', label: 'ACOMPANHAR', cls: 'vf-acompanhar', cor: '#ffd700' }};
    if (/EVITAR|🔴\s*EVITAR/i.test(texto)) return {{ emoji: '🔴', label: 'EVITAR', cls: 'vf-evitar', cor: '#ff3d00' }};
    if (/INCONCLUSIVO/i.test(texto)) return {{ emoji: '⚪', label: 'INCONCLUSIVO', cls: 'vf-inconclusivo', cor: '#888' }};
    return null;
}}

// ─── Parser principal ─────────────────────────────────────────────────────────

function parsearAnalise(texto) {{
    const dados = {{}};

    // Cabeçalho
    dados.ticker = extrairValor(texto,
        /Relatório Fundamentalista[^:]*:\s*([A-Z0-9]+)/i,
        /Relatorio Fundamentalista[^:]*:\s*([A-Z0-9]+)/i,
        /##\s*([A-Z0-9]{{4,6}})\b/
    ) || '—';
    dados.empresa = extrairValor(texto, /\*\*Empresa\*\*[:\s]+([^\|\\n]+)/i) || '';
    dados.setor = extrairValor(texto, /\*\*Setor\*\*[:\s]+([^\|\\n]+)/i) || '';
    dados.data = extrairValor(texto, /\*\*Data\*\*[:\s]+([^\|\\n]+)/i) || '';
    dados.preco = extrairValor(texto,
        /\*\*Preço Atual\*\*[:\s]+R\$\s*([\d,.]+)/i,
        /\*\*Preco Atual\*\*[:\s]+R\$\s*([\d,.]+)/i,
        /Preço Atual[:\s]+R\$\s*([\d,.]+)/i
    ) || '';

    // Scores
    const blocoBarsi = extrairBloco(texto, '## 2.', ['## 3.', '## 4.', '## 5.', '## 6.']);
    const blocoFinclass = extrairBloco(texto, '## 3.', ['## 4.', '## 5.', '## 6.']);
    dados.scoreBarsi = extrairScore(blocoBarsi || texto, 'Barsi');
    dados.scoreFinclass = extrairScore(blocoFinclass || texto, 'Finclass');
    dados.vereBarsi = extrairVeredito(blocoBarsi || texto, 'Barsi') || extrairVeredito(texto, '## 2');
    dados.vereFinclass = extrairVeredito(blocoFinclass || texto, 'Finclass') || extrairVeredito(texto, '## 3');

    // Tabelas
    dados.tabelaBarsi = blocoBarsi ? parsearTabela(blocoBarsi) : null;
    dados.tabelaFinclass = blocoFinclass ? parsearTabela(blocoFinclass) : null;

    // Mapa de Dividendos
    const blocoMapa = extrairBloco(texto, 'MAPA DE DIVIDENDOS', ['## ', '---']);
    dados.mapaTexto = blocoMapa;
    if (blocoMapa) {{
        dados.precoTeto6 = extrairValor(blocoMapa,
            /Preço-Teto Barsi[^:]*:\s*R\$\s*([\d,.]+)/i,
            /Preco-Teto Barsi[^:]*:\s*R\$\s*([\d,.]+)/i,
            /6%[^=]*=\s*R\$\s*([\d,.]+)/i
        );
        dados.precoTeto5 = extrairValor(blocoMapa,
            /Preço-Teto Conservador[^:]*:\s*R\$\s*([\d,.]+)/i,
            /Preco-Teto Conservador[^:]*:\s*R\$\s*([\d,.]+)/i,
            /5%[^=]*=\s*R\$\s*([\d,.]+)/i
        );
        dados.zonaBarsi = extrairValor(blocoMapa, /Zona[:\s]+([^\n]+)/i) ||
            (blocoMapa.includes('🟢') ? '🟢 COMPRA' :
             blocoMapa.includes('🟡') ? '🟡 ATENÇÃO' :
             blocoMapa.includes('🔴') ? '🔴 EVITAR' : null);
    }}

    // Valuation Finclass
    const blocoVal = extrairBloco(texto, 'VALUATION E PRECO JUSTO', ['## ', '---']);
    dados.precoJusto = extrairValor(blocoVal || texto,
        /Preço Justo[^:]*:\s*R\$\s*([\d,.]+)/i,
        /Preco Justo[^:]*:\s*R\$\s*([\d,.]+)/i
    );
    dados.precoCompra = extrairValor(blocoVal || texto,
        /Preço de Compra[^:]*:\s*R\$\s*([\d,.]+)/i,
        /Preco de Compra[^:]*:\s*R\$\s*([\d,.]+)/i,
        /margem[^:]*:\s*R\$\s*([\d,.]+)/i
    );
    dados.blocoValText = blocoVal;

    // Fontes / Documentos
    const blocoFontes = extrairBloco(texto, '## 1.', ['## 2.']);
    dados.fontes = blocoFontes;
    // Citações
    const citRegex = /citação[:\s]+"([^"]+)"\s*\(([^)]+)\)/gi;
    dados.citacoes = [];
    let m;
    const textoBusca = blocoFontes || texto;
    while ((m = citRegex.exec(textoBusca)) !== null) {{
        dados.citacoes.push({{ texto: m[1], fonte: m[2] }});
    }}

    // Alavancas e Pepinos
    const blocoAlav = extrairBloco(texto, '## 4.', ['## 5.', '## 6.']);
    if (blocoAlav) {{
        dados.alavancas = extrairValor(blocoAlav,
            /Alavancas[^:]*:\*\*[:\s]*([^\n]+(?:\n(?![-*]|\*\*Pepinos)[^\n]+)*)/i,
            /Alavancas[^:]*:\s*([^\n]+)/i
        );
        dados.pepinos = extrairValor(blocoAlav,
            /Pepinos[^:]*:\*\*[:\s]*([^\n]+(?:\n(?![-*]|\*\*Alav)[^\n]+)*)/i,
            /Pepinos[^:]*:\s*([^\n]+)/i
        );
        dados.blocoAlavTexto = blocoAlav;
    }}

    // Simulador de Renda Passiva
    const blocoSim = extrairBloco(texto, '## 5.', ['## 6.']);
    dados.blocoSimTexto = blocoSim;
    if (blocoSim) {{
        dados.simTabelaA = parsearTabela(
            extrairBloco(blocoSim, 'Cenário A', ['Cenário B', 'Cenario B', '---']) ||
            extrairBloco(blocoSim, 'Cenario A', ['Cenario B', '---']) || ''
        );
        dados.simTabelaB = parsearTabela(
            extrairBloco(blocoSim, 'Cenário B', ['---', 'Período', 'Periodo']) ||
            extrairBloco(blocoSim, 'Cenario B', ['---', 'Periodo']) || ''
        );
        dados.simTabelaPeriodos = parsearTabela(
            extrairBloco(blocoSim, 'Período', ['---']) ||
            extrairBloco(blocoSim, 'Periodo', ['---']) || ''
        );
        dados.yieldOnCost = extrairValor(blocoSim, /Yield on Cost[:\s]+([0-9,.]+%)/i);
        dados.dyAtual = extrairValor(blocoSim, /Dividend Yield sobre preço atual[:\s]+([0-9,.]+%)/i);
        dados.tempoRecuperar = extrairValor(blocoSim, /Tempo estimado[^:]*:\s*([0-9,.]+ anos)/i);
    }}

    // Frequência de Pagamento
    const freqM = texto.match(/Frequência de Pagamento[^:]*:([^\n]+(?:\n(?!##)[^\n]+){{0,3}})/i) ||
                  texto.match(/Frequencia de Pagamento[^:]*:([^\n]+(?:\n(?!##)[^\n]+){{0,3}})/i);
    dados.frequencia = freqM ? freqM[1].trim() : null;

    // Veredito Final
    const blocoVerd = extrairBloco(texto, 'PAINEL DE DECISÃO', ['---', '## ⚠️', '## Disclaimer']) ||
                      extrairBloco(texto, 'PAINEL DE DECISAO', ['---', '## ⚠️', '## Disclaimer']);
    dados.blocoVerdTexto = blocoVerd;
    dados.precoTetoFinal = extrairValor(blocoVerd || texto,
        /Preço-Teto Previdenciário[^:]*:\s*R\$\s*([\d,.]+)/i,
        /Preco-Teto Previdenciario[^:]*:\s*R\$\s*([\d,.]+)/i
    ) || dados.precoTeto6;
    dados.precoJustoFinal = extrairValor(blocoVerd || texto,
        /Preço Justo de Crescimento[^:]*:\s*R\$\s*([\d,.]+)/i,
        /Preco Justo de Crescimento[^:]*:\s*R\$\s*([\d,.]+)/i
    ) || dados.precoJusto;
    dados.classificacaoFinal = blocoVerd || texto;

    // Disclaimer
    const blocoDisc = extrairBloco(texto, '## ⚠️ Disclaimer', ['---']) ||
                      extrairBloco(texto, '## Disclaimer', ['---']);
    dados.disclaimer = blocoDisc;

    return dados;
}}

// ─── Mesclagem de análises ────────────────────────────────────────────────────

function mesclarDados(anterior, novo) {{
    const merged = Object.assign({{}}, anterior);
    // Campos que o novo pode complementar (documentos, citações, alavancas)
    const camposNovo = ['citacoes', 'fontes', 'blocoAlavTexto', 'alavancas', 'pepinos',
                        'precoTeto6', 'precoTeto5', 'zonaBarsi', 'precoJusto', 'precoCompra',
                        'precoTetoFinal', 'precoJustoFinal', 'frequencia', 'disclaimer'];
    camposNovo.forEach(c => {{
        if (novo[c] && (!anterior[c] || anterior[c] === '—' || anterior[c] === '')) {{
            merged[c] = novo[c];
        }}
    }});
    // Citações: concatena sem duplicar
    if (novo.citacoes && novo.citacoes.length > 0) {{
        const textosCit = (anterior.citacoes || []).map(c => c.texto);
        novo.citacoes.forEach(c => {{
            if (!textosCit.includes(c.texto)) merged.citacoes.push(c);
        }});
    }}
    // Scores e tabelas: usa o que tiver valor
    ['scoreBarsi','scoreFinclass','vereBarsi','vereFinclass',
     'tabelaBarsi','tabelaFinclass','simTabelaA','simTabelaB','simTabelaPeriodos'].forEach(c => {{
        if (novo[c] !== null && novo[c] !== undefined && !anterior[c]) merged[c] = novo[c];
    }});
    return merged;
}}

// ─── Renderização do relatório ────────────────────────────────────────────────

function renderRelatorio(dados) {{
    let html = '';

    // ── Cabeçalho ──
    html += `<div class="rel-header">
        <div class="rel-header-ticker">📈 ${{dados.ticker}}</div>
        <div class="rel-header-empresa">${{dados.empresa || ''}}</div>
        <div class="rel-header-meta">
            ${{dados.setor ? `<div class="rel-meta-item"><div class="rel-meta-label">Setor</div><div class="rel-meta-value">${{dados.setor}}</div></div>` : ''}}
            ${{dados.preco ? `<div class="rel-meta-item"><div class="rel-meta-label">Preço Atual</div><div class="rel-meta-value preco">R$ ${{dados.preco}}</div></div>` : ''}}
            ${{dados.data ? `<div class="rel-meta-item"><div class="rel-meta-label">Data</div><div class="rel-meta-value">${{dados.data}}</div></div>` : ''}}
            ${{dados.precoTeto6 ? `<div class="rel-meta-item"><div class="rel-meta-label">Preço-Teto Barsi (6%)</div><div class="rel-meta-value" style="color:#00c853;">R$ ${{dados.precoTeto6}}</div></div>` : ''}}
            ${{dados.precoJusto ? `<div class="rel-meta-item"><div class="rel-meta-label">Preço Justo Finclass</div><div class="rel-meta-value" style="color:#4fc3f7;">R$ ${{dados.precoJusto}}</div></div>` : ''}}
        </div>
    </div>`;

    // ── Fontes / Documentos ──
    if (dados.fontes || (dados.citacoes && dados.citacoes.length > 0)) {{
        html += `<div class="rel-section">
            <div class="rel-section-title">📄 Fontes Analisadas</div>`;
        if (dados.citacoes && dados.citacoes.length > 0) {{
            dados.citacoes.forEach(c => {{
                html += `<div class="rel-citacao">"${{c.texto}}"<div class="rel-citacao-fonte">📌 ${{c.fonte}}</div></div>`;
            }});
        }} else if (dados.fontes) {{
            const linhas = dados.fontes.split('\\n').filter(l => l.trim().startsWith('-'));
            linhas.forEach(l => {{
                html += `<p style="color:#bbb; font-size:0.9em; margin:6px 0;">${{l.replace(/^-\s*/, '• ')}}</p>`;
            }});
        }}
        html += `</div>`;
    }}

    // ── Análise Barsi ──
    const corB = corScore(dados.scoreBarsi);
    html += `<div class="rel-section">
        <div class="rel-section-title">🏦 Análise Barsi — Dividendos</div>
        ${{renderTabela(dados.tabelaBarsi)}}
        <div class="rel-score-wrap">
            <canvas id="chart-barsi" class="rel-score-chart"></canvas>
            <div class="rel-score-info">
                <div class="rel-score-num" style="color:${{corB}};">${{dados.scoreBarsi !== null ? dados.scoreBarsi : '—'}}<span style="font-size:0.5em; color:#888;">/100</span></div>
                <div class="rel-score-label">Score Barsi</div>
                ${{dados.vereBarsi ? `<div class="rel-veredito ${{classeVeredito(dados.vereBarsi)}}">${{dados.vereBarsi}}</div>` : ''}}
            </div>
        </div>`;

    // Mapa de Dividendos
    if (dados.precoTeto6 || dados.mapaTexto) {{
        const sem = semaforo(dados.zonaBarsi || '');
        html += `<div style="margin-top:18px;">
            <div style="font-weight:bold; color:#ffd700; margin-bottom:10px;">🗺️ Mapa de Dividendos Inteligente</div>`;
        if (dados.precoTeto6) {{
            html += `<div style="display:flex; gap:16px; flex-wrap:wrap; margin-bottom:12px;">
                <div style="background:rgba(0,200,83,0.08); border:1px solid rgba(0,200,83,0.3); border-radius:8px; padding:12px 18px; text-align:center;">
                    <div style="font-size:0.75em; color:#888; text-transform:uppercase;">Preço-Teto Barsi (6%)</div>
                    <div style="font-size:1.4em; font-weight:bold; color:#00c853; margin-top:4px;">R$ ${{dados.precoTeto6}}</div>
                </div>
                ${{dados.precoTeto5 ? `<div style="background:rgba(255,152,0,0.08); border:1px solid rgba(255,152,0,0.3); border-radius:8px; padding:12px 18px; text-align:center;">
                    <div style="font-size:0.75em; color:#888; text-transform:uppercase;">Preço-Teto Conservador (5%)</div>
                    <div style="font-size:1.4em; font-weight:bold; color:#ff9800; margin-top:4px;">R$ ${{dados.precoTeto5}}</div>
                </div>` : ''}}
            </div>`;
        }}
        if (sem) {{
            html += `<div class="rel-semaforo">
                <div class="rel-semaforo-dot ${{sem.cls}}"></div>
                <div class="rel-semaforo-text"><strong>${{sem.label}}</strong></div>
            </div>`;
        }}
        html += `</div>`;
    }}
    html += `</div>`;

    // ── Análise Finclass ──
    const corF = corScore(dados.scoreFinclass);
    html += `<div class="rel-section">
        <div class="rel-section-title">📈 Análise Finclass — Crescimento (GARP)</div>
        ${{renderTabela(dados.tabelaFinclass)}}
        <div class="rel-score-wrap">
            <canvas id="chart-finclass" class="rel-score-chart"></canvas>
            <div class="rel-score-info">
                <div class="rel-score-num" style="color:${{corF}};">${{dados.scoreFinclass !== null ? dados.scoreFinclass : '—'}}<span style="font-size:0.5em; color:#888;">/100</span></div>
                <div class="rel-score-label">Score Finclass</div>
                ${{dados.vereFinclass ? `<div class="rel-veredito ${{classeVeredito(dados.vereFinclass)}}">${{dados.vereFinclass}}</div>` : ''}}
            </div>
        </div>`;

    // Valuation
    if (dados.precoJusto || dados.precoCompra) {{
        html += `<div style="margin-top:18px;">
            <div style="font-weight:bold; color:#ffd700; margin-bottom:10px;">🎯 Valuation e Preço Justo</div>
            <div style="display:flex; gap:16px; flex-wrap:wrap;">
                ${{dados.precoJusto ? `<div style="background:rgba(79,195,247,0.08); border:1px solid rgba(79,195,247,0.3); border-radius:8px; padding:12px 18px; text-align:center;">
                    <div style="font-size:0.75em; color:#888; text-transform:uppercase;">Preço Justo</div>
                    <div style="font-size:1.4em; font-weight:bold; color:#4fc3f7; margin-top:4px;">R$ ${{dados.precoJusto}}</div>
                </div>` : ''}}
                ${{dados.precoCompra ? `<div style="background:rgba(0,200,83,0.08); border:1px solid rgba(0,200,83,0.3); border-radius:8px; padding:12px 18px; text-align:center;">
                    <div style="font-size:0.75em; color:#888; text-transform:uppercase;">Preço de Compra (margem 20%)</div>
                    <div style="font-size:1.4em; font-weight:bold; color:#00c853; margin-top:4px;">R$ ${{dados.precoCompra}}</div>
                </div>` : ''}}
            </div>
        </div>`;
    }}
    html += `</div>`;

    // ── Alavancas e Pepinos ──
    if (dados.blocoAlavTexto) {{
        const linhasAlav = (dados.blocoAlavTexto || '').split('\\n')
            .filter(l => /Alavancas/i.test(l) || /Pepinos/i.test(l) || l.trim().startsWith('-'));
        let alavancasList = [], pepinosList = [];
        let modo = null;
        (dados.blocoAlavTexto || '').split('\\n').forEach(l => {{
            if (/Alavancas/i.test(l)) {{ modo = 'a'; return; }}
            if (/Pepinos/i.test(l)) {{ modo = 'p'; return; }}
            const item = l.replace(/^[-*•]\s*/, '').trim();
            if (item && item.length > 3) {{
                if (modo === 'a') alavancasList.push(item);
                else if (modo === 'p') pepinosList.push(item);
            }}
        }});
        // Fallback: tenta extrair da linha única
        if (alavancasList.length === 0 && dados.alavancas) {{
            alavancasList = dados.alavancas.split(';').map(s => s.trim()).filter(Boolean);
        }}
        if (pepinosList.length === 0 && dados.pepinos) {{
            pepinosList = dados.pepinos.split(';').map(s => s.trim()).filter(Boolean);
        }}

        html += `<div class="rel-section">
            <div class="rel-section-title">⚡ Alavancas e Pepinos</div>
            <div class="rel-alavancas">
                <div class="rel-alavanca-box box-verde">
                    <div class="rel-alavanca-titulo">🚀 Alavancas (Gatilhos Positivos)</div>
                    ${{alavancasList.length > 0
                        ? alavancasList.map(i => `<div class="rel-alavanca-item">✔ ${{i}}</div>`).join('')
                        : '<div class="dado-indisponivel">Não identificadas na análise.</div>'}}
                </div>
                <div class="rel-alavanca-box box-vermelho">
                    <div class="rel-alavanca-titulo">⚠️ Pepinos (Riscos)</div>
                    ${{pepinosList.length > 0
                        ? pepinosList.map(i => `<div class="rel-alavanca-item">✖ ${{i}}</div>`).join('')
                        : '<div class="dado-indisponivel">Não identificados na análise.</div>'}}
                </div>
            </div>
        </div>`;
    }}

    // ── Simulador de Renda Passiva ──
    if (dados.blocoSimTexto) {{
        html += `<div class="rel-section">
            <div class="rel-section-title">💰 Simulador de Renda Passiva</div>
            <div class="rel-sim-grid">`;

        if (dados.simTabelaA) {{
            html += `<div class="rel-sim-box">
                <div class="rel-sim-titulo">📊 Cenário A — Posição Existente</div>
                ${{dados.simTabelaA.body.map(row => `
                    <div class="rel-sim-row">
                        <span class="rel-sim-key">${{row[0] || ''}}</span>
                        <span class="rel-sim-val ${{/Renda anual/i.test(row[0]||'') ? 'destaque' : ''}}">${{row[1] || ''}}</span>
                    </div>`).join('')}}
            </div>`;
        }}
        if (dados.simTabelaB) {{
            html += `<div class="rel-sim-box">
                <div class="rel-sim-titulo">📊 Cenário B — Compra Hipotética</div>
                ${{dados.simTabelaB.body.map(row => `
                    <div class="rel-sim-row">
                        <span class="rel-sim-key">${{row[0] || ''}}</span>
                        <span class="rel-sim-val ${{/Renda anual/i.test(row[0]||'') ? 'destaque' : ''}}">${{row[1] || ''}}</span>
                    </div>`).join('')}}
            </div>`;
        }}
        html += `</div>`;

        // Tabela de períodos
        if (dados.simTabelaPeriodos) {{
            html += `<div style="margin-top:16px;">
                <div style="font-weight:bold; color:#ffd700; margin-bottom:10px; font-size:0.9em;">📅 Projeção por Período</div>
                ${{renderTabela(dados.simTabelaPeriodos)}}
            </div>`;
        }}

        // Frequência
        if (dados.frequencia) {{
            html += `<div style="margin-top:14px;">
                <div style="font-weight:bold; color:#ffd700; margin-bottom:8px; font-size:0.9em;">📆 Frequência de Pagamento</div>
                <div>${{dados.frequencia.split(/[,;.]/).filter(s => s.trim().length > 3)
                    .map(s => `<span class="rel-freq-badge">${{s.trim()}}</span>`).join('')}}
                </div>
            </div>`;
        }}
        html += `</div>`;
    }}

    // ── Veredito Final ──
    const cf = classificacaoFinal(dados.classificacaoFinal || '');
    if (cf) {{
        html += `<div class="rel-veredito-final ${{cf.cls}}">
            <div class="vf-emoji">${{cf.emoji}}</div>
            <div class="vf-classificacao" style="color:${{cf.cor}};">${{cf.label}}</div>
            <div class="vf-precos">
                ${{dados.precoTetoFinal ? `<div class="vf-preco-item">
                    <div class="vf-preco-label">Preço-Teto Barsi</div>
                    <div class="vf-preco-val">R$ ${{dados.precoTetoFinal}}</div>
                </div>` : ''}}
                ${{dados.preco ? `<div class="vf-preco-item">
                    <div class="vf-preco-label">Preço Atual</div>
                    <div class="vf-preco-val" style="color:#fff;">R$ ${{dados.preco}}</div>
                </div>` : ''}}
                ${{dados.precoJustoFinal ? `<div class="vf-preco-item">
                    <div class="vf-preco-label">Preço Justo Finclass</div>
                    <div class="vf-preco-val" style="color:#4fc3f7;">R$ ${{dados.precoJustoFinal}}</div>
                </div>` : ''}}
                ${{dados.precoCompra ? `<div class="vf-preco-item">
                    <div class="vf-preco-label">Preço de Compra (−20%)</div>
                    <div class="vf-preco-val" style="color:#00c853;">R$ ${{dados.precoCompra}}</div>
                </div>` : ''}}
            </div>
        </div>`;
    }}

    // ── Disclaimer ──
    html += `<div class="rel-disclaimer">
        <strong>⚠️ Aviso Legal:</strong> ${{dados.disclaimer || 'Relatório gerado por IA, para fins educacionais. Não constitui recomendação de compra ou venda de ativos. Investir em renda variável envolve riscos, incluindo a perda total do capital. Rentabilidade passada não garante resultados futuros. O usuário é o único responsável por suas decisões de investimento.'}}
    </div>`;

    return html;
}}

// ─── Ações da página ──────────────────────────────────────────────────────────

function gerarRelatorio(mesclar) {{
    const texto = document.getElementById('rel-input').value.trim();
    if (!texto || texto.length < 100) {{
        alert('Cole o texto completo da análise gerada pela IA antes de continuar.');
        return;
    }}

    const novosDados = parsearAnalise(texto);

    if (mesclar && estadoAnterior) {{
        estadoAnterior = mesclarDados(estadoAnterior, novosDados);
    }} else {{
        estadoAnterior = novosDados;
    }}

    // Destrói gráficos anteriores
    if (chartBarsi) {{ chartBarsi.destroy(); chartBarsi = null; }}
    if (chartFinclass) {{ chartFinclass.destroy(); chartFinclass = null; }}

    const conteudo = document.getElementById('rel-conteudo');
    conteudo.innerHTML = renderRelatorio(estadoAnterior);

    // Renderiza gráficos de pizza após inserir o HTML
    setTimeout(() => {{
        chartBarsi = renderPizza('chart-barsi', estadoAnterior.scoreBarsi, corScore(estadoAnterior.scoreBarsi));
        chartFinclass = renderPizza('chart-finclass', estadoAnterior.scoreFinclass, corScore(estadoAnterior.scoreFinclass));
    }}, 50);

    // Mostra o relatório e o botão de mesclar
    document.getElementById('rel-output').style.display = 'block';
    document.getElementById('btn-mesclar').style.display = 'inline-block';
    document.getElementById('rel-input').value = '';

    // Scroll suave para o relatório
    document.getElementById('rel-output').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
}}

function voltarFormulario() {{
    document.getElementById('rel-output').style.display = 'none';
    document.getElementById('rel-input').value = '';
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}

function limparTudo() {{
    estadoAnterior = null;
    document.getElementById('rel-input').value = '';
    document.getElementById('rel-output').style.display = 'none';
    document.getElementById('btn-mesclar').style.display = 'none';
    if (chartBarsi) {{ chartBarsi.destroy(); chartBarsi = null; }}
    if (chartFinclass) {{ chartFinclass.destroy(); chartFinclass = null; }}
}}
</script>
</body>
</html>
"""

@app.route('/relatorio')
def relatorio_page():
    html = RELATORIO_PAGE_HTML.format(
        css=CSS,
        css_extra=RELATORIO_CSS_EXTRA,
        nav=NAV,
        footer=FOOTER
    )
    return html

if __name__ == '__main__':
    # Porta 5000 para rodar localmente ou no Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
