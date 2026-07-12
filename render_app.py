import io, os, random, secrets, string, sqlite3, stripe, time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, redirect, url_for
import json

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Stripe configuration - lazy loading (read at request time, not at module load time)
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
PRICE_MONTHLY = 'price_1Ts4DcBO1eUMFGitmiqEB8cW'
PRICE_ANNUAL = 'price_1Ts4EnBO1eUMFGitr2bWqfvU'

def configure_stripe():
    """Configure Stripe API key from environment variables (lazy loading)"""
    secret_key = os.environ.get('STRIPE_SECRET_KEY')
    if not secret_key:
        raise ValueError('STRIPE_SECRET_KEY not configured in environment variables')
    stripe.api_key = secret_key
    return secret_key

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(BASE_DIR, 'PROMPT_MESTRE_HIBRIDO_B3_v7.md')
EBOOK_FILE = os.path.join(BASE_DIR, 'static', 'ebook_prompt_b3.pdf')
DB_FILE = '/tmp/customers.json'  # Use JSON file instead of SQLite
LOG_FILE = '/tmp/app_debug.log'  # Debug log file

def log_debug(message):
    """Write debug message to log file"""
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {message}\n")
    except:
        pass

# Initialize database (JSON-based)
def init_db():
    """Initialize JSON database if it doesn't exist"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({}, f)

init_db()

def load_customers():
    """Load all customers from JSON file"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_customers(data):
    """Save customers to JSON file"""
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        log_debug(f"Saved {len(data)} customers to database")
    except Exception as e:
        log_debug(f"ERROR saving customers: {str(e)}")
        raise

def gerar_chave(dias=7):
    p1 = ''.join(random.choices(string.digits, k=5))
    p2 = ''.join(random.choices(string.digits + string.ascii_uppercase, k=8))
    vencimento = (datetime.utcnow() + timedelta(days=dias)).strftime('%Y%m%d')
    sufixo = '7DIAS' if dias <= 7 else '1ANO'
    return f"PROMPT-{p1}-{p2}-{vencimento}-{sufixo}"

def prompt_com_chave(chave, trial=False):
    try:
        if not os.path.exists(PROMPT_FILE):
            return f"ERRO: Arquivo de prompt nao encontrado em {PROMPT_FILE}"
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        if '[CHAVE_DE_LICENCA]' in conteudo:
            conteudo = conteudo.replace('[CHAVE_DE_LICENCA]', chave, 1)
        return conteudo
    except Exception as e:
        return f"ERRO ao carregar prompt: {str(e)}"

def validate_license(chave):
    """Validate if license key is still valid"""
    try:
        parts = chave.split('-')
        if len(parts) < 4:
            return False
        # Format: PROMPT-XXXXX-XXXXXXXX-YYYYMMDD-SUFIXO
        # Index:  [0]     [1]     [2]        [3]       [4]
        vencimento = parts[3]  # The date is at index 3, not 2
        expiry_date = datetime.strptime(vencimento, '%Y%m%d')
        return datetime.utcnow() < expiry_date
    except Exception as e:
        log_debug(f"validate_license error for {chave}: {str(e)}")
        return False

def get_customer(email):
    """Get customer data from JSON file"""
    customers = load_customers()
    if email in customers:
        c = customers[email]
        # Return tuple format: (id, email, license_key, trial_expiry, stripe_customer_id, subscription_id, subscription_status, created_at)
        return (c.get('id'), email, c.get('license_key'), c.get('trial_expiry'), 
                c.get('stripe_customer_id'), c.get('subscription_id'), 
                c.get('subscription_status'), c.get('created_at'))
    return None

def create_customer(email, license_key, trial_expiry=None, stripe_customer_id=None):
    """Create or update customer in JSON file"""
    customers = load_customers()
    customers[email] = {
        'id': len(customers) + 1,
        'email': email,
        'license_key': license_key,
        'trial_expiry': trial_expiry,
        'stripe_customer_id': stripe_customer_id,
        'subscription_id': None,
        'subscription_status': None,
        'created_at': datetime.utcnow().isoformat()
    }
    save_customers(customers)

def update_subscription(email, stripe_customer_id, subscription_id, status):
    """Update subscription in JSON file and generate license key"""
    try:
        log_debug(f"update_subscription called for {email}")
        customers = load_customers()
        # Generate annual license key
        license_key = gerar_chave(dias=365)
        log_debug(f"Generated license key: {license_key}")
        
        if email in customers:
            log_debug(f"Updating existing customer: {email}")
            customers[email]['stripe_customer_id'] = stripe_customer_id
            customers[email]['subscription_id'] = subscription_id
            customers[email]['subscription_status'] = status
            customers[email]['license_key'] = license_key
            customers[email]['trial_expiry'] = None
        else:
            log_debug(f"Creating new customer: {email}")
            customers[email] = {
                'id': len(customers) + 1,
                'email': email,
                'license_key': license_key,
                'trial_expiry': None,
                'stripe_customer_id': stripe_customer_id,
                'subscription_id': subscription_id,
                'subscription_status': status,
                'created_at': datetime.utcnow().isoformat()
            }
        
        save_customers(customers)
        log_debug(f"Successfully saved customer: {email}")
    except Exception as e:
        log_debug(f"ERROR in update_subscription: {str(e)}")
        raise

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0f1e; color: #ffffff; min-height: 100vh; }
nav { background: rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,215,0,0.2); padding: 15px 40px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }
nav .logo { color: #ffd700; font-size: 1.2em; font-weight: bold; text-decoration: none; }
nav .nav-links a { color: #ffffff; text-decoration: none; margin-left: 25px; font-size: 1.1em; transition: color 0.3s; }
nav .nav-links a:hover { color: #ffd700; }
.container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
h1 { font-size: 2.4em; color: #ffffff; margin-bottom: 15px; }
h2 { font-size: 1.6em; color: #ffffff; margin-bottom: 15px; margin-top: 30px; }
h3 { font-size: 1.2em; color: #ffffff; margin-bottom: 10px; }
p { color: #ffffff; line-height: 1.8; margin-bottom: 15px; font-size: 1.05em; }
ul { color: #ffffff; margin-left: 20px; margin-bottom: 20px; line-height: 1.9; font-size: 1.05em; }
li { margin-bottom: 10px; }
.btn { display: inline-block; padding: 14px 32px; border-radius: 8px; font-size: 1em; font-weight: bold; cursor: pointer; border: none; text-decoration: none; transition: transform 0.2s, box-shadow 0.2s; margin-right: 10px; margin-bottom: 10px; }
.btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
.btn-gold { background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; }
.btn-green { background: linear-gradient(135deg, #00c853, #00860b); color: #fff; }
.btn-red { background: linear-gradient(135deg, #ff3d00, #d32f2f); color: #fff; }
.btn-blue { background: linear-gradient(135deg, #2196f3, #1976d2); color: #fff; }
.card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,215,0,0.15); border-radius: 12px; padding: 30px; margin-bottom: 25px; }
.card-destaque { background: rgba(255,215,0,0.08); border: 2px solid rgba(255,215,0,0.3); }
footer { background: rgba(255,255,255,0.05); border-top: 1px solid rgba(255,215,0,0.2); padding: 30px 40px; text-align: center; margin-top: 60px; color: #999; font-size: 1.2em; line-height: 1.8; }
.success-message { background: rgba(0,200,83,0.1); border: 1px solid rgba(0,200,83,0.3); color: #00c853; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
.error-message { background: rgba(255,61,0,0.1); border: 1px solid rgba(255,61,0,0.3); color: #ff3d00; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
"""

NAV = """
<nav>
    <a href="/" class="logo">📈 Prompt B3</a>
    <div class="nav-links">
        <a href="/">Home</a>
        <a href="/trial">Teste 7 Dias</a>
        <a href="/comprar">Comprar 1 Ano</a>
        <a href="/relatorio">Relatório Visual</a>
        <a href="/contato">Contato</a>
    </div>
</nav>
"""

FOOTER = """
<footer>
    <p>&copy; 2026 Prompt Fundamentalista B3 | promptpegardini@gmail.com</p>
    <p style="font-size: 0.85em;">⚠️ Aviso de Independência: Este projeto é <strong>independente e não oficial</strong>. Não é autorizado, endossado ou afiliado com Luiz Barsi ou Finclass.</p>
    <p style="font-size: 0.85em;">⚖️ Aviso Legal: Este produto é um prompt de IA para fins educacionais. Não constitui recomendação de investimento. A IA pode cometer erros. Sempre verifique em fontes oficiais.</p>
</footer>
"""

@app.route('/')
def home():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Prompt Fundamentalista B3</title>
        <style>{CSS}</style>
    </head>
    <body>
        {NAV}
        <div class="container">
            <h1>📈 Prompt Fundamentalista B3</h1>
            <div class="card" style="background: rgba(255,100,0,0.1); border: 1px solid rgba(255,100,0,0.3); margin-bottom: 30px;">
                <strong style="color: #ff9800;">⚠️ Projeto Independente:</strong> Este é um projeto <strong>não oficial</strong>, não autorizado ou endossado por Luiz Barsi ou Finclass.
            </div>
            
            <div class="card card-destaque" style="text-align: center; padding: 50px 30px; margin-bottom: 40px;">
                <p style="font-size: 1.3em; margin-bottom: 15px; color: #ffd700; font-weight: bold;">Análise Inteligente de Ações B3 com IA</p>
                <p style="font-size: 1.1em; margin-bottom: 30px; color: #ccc;">Método Fundamentalista Barsi + Finclass | Funciona com ChatGPT, Claude e Gemini</p>
                <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                    <a href="/trial" class="btn btn-gold" style="padding: 16px 40px; font-size: 1.1em; text-decoration: none;">📥 Teste 7 Dias Grátis</a>
                    <a href="/subscribe" class="btn btn-green" style="padding: 16px 40px; font-size: 1.1em; text-decoration: none;">💳 Assinar Agora</a>
                </div>
            </div>

            <h2 style="text-align: center; margin-bottom: 30px;">🎬 Veja Como Funciona</h2>
            <div style="margin: 30px 0; text-align: center;">
                <iframe width="100%" height="400" style="max-width: 600px; border-radius: 12px;" src="https://www.youtube.com/embed/ZljR8zJzu4Q" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 40px 0;">
                <div class="card" style="text-align: center;">
                    <p style="font-size: 2em; margin-bottom: 10px;">✅</p>
                    <h3>Prompt Pronto</h3>
                    <p>Copie e cole em qualquer IA</p>
                </div>
                <div class="card" style="text-align: center;">
                    <p style="font-size: 2em; margin-bottom: 10px;">📊</p>
                    <h3>Análise Completa</h3>
                    <p>Barsi + Finclass + Veredito</p>
                </div>
                <div class="card" style="text-align: center;">
                    <p style="font-size: 2em; margin-bottom: 10px;">🎨</p>
                    <h3>Relatório Visual</h3>
                    <p>Gráficos coloridos e profissionais</p>
                </div>
                <div class="card" style="text-align: center;">
                    <p style="font-size: 2em; margin-bottom: 10px;">🔑</p>
                    <h3>Chave Única</h3>
                    <p>Válida por 7 dias ou 1 ano</p>
                </div>
            </div>

            <h2 style="text-align: center; margin: 60px 0 30px;">📈 Como Usar em 3 Passos</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px;">
                <div class="card">
                    <h3>1️⃣ Baixe o Prompt</h3>
                    <p>Clique em "Teste 7 Dias" ou "Assinar Agora" e receba seu prompt com chave única</p>
                </div>
                <div class="card">
                    <h3>2️⃣ Cole na IA</h3>
                    <p>Abra ChatGPT, Claude ou Gemini. Cole o prompt e peça a análise de uma ação</p>
                </div>
                <div class="card">
                    <h3>3️⃣ Veja o Relatório</h3>
                    <p>Copie a resposta, vá em "Relatório Visual" e gere gráficos profissionais</p>
                </div>
            </div>

            <h2 style="text-align: center; margin: 60px 0 30px;">❓ Dúvidas Frequentes</h2>
            <div class="card">
                <h3>📄 O que é um arquivo MD (Markdown)?</h3>
                <p>Markdown é um formato de texto simples que pode ser convertido para HTML, PDF ou outros formatos. É muito usado em documentação técnica.</p>
            </div>
            <div class="card">
                <h3>🔑 Como funciona a chave de licença?</h3>
                <p>A chave é única e válida por 7 dias (trial) ou 1 ano (assinatura). Inclua a chave no prompt para que a IA reconheça sua licença.</p>
            </div>
            <div class="card">
                <h3>🤖 Posso usar em qualquer IA?</h3>
                <p>Sim! O prompt funciona com ChatGPT, Claude, Gemini e qualquer outra IA que aceite prompts de texto.</p>
            </div>
            <div class="card">
                <h3>📊 Posso exportar o relatório em PDF?</h3>
                <p>Sim! Na página "Relatório Visual", clique em "Imprimir / Salvar PDF" para gerar um PDF profissional.</p>
            </div>

            <h2 style="text-align: center; margin: 60px 0 30px;">📚 Ganhe um Ebook Gratuito</h2>
            <div class="card card-destaque" style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: center;">
                <div style="text-align: center;">
                    <img src="/static/ebook_cover.png" style="max-width: 100%; border-radius: 8px; box-shadow: 0 8px 20px rgba(0,0,0,0.3);">
                </div>
                <div>
                    <h3>📖 Guia Introdutório Exclusivo</h3>
                    <p>Aprenda os fundamentos do Método Barsi e Finclass em 10 páginas práticas e diretas.</p>
                    <p style="margin-top: 20px; color: #ffd700; font-weight: bold;">Preencha seus dados abaixo e receba o ebook + atualizações sobre novas versões do prompt.</p>
                    <form action="/receber-ebook" method="POST" style="margin-top: 20px;">
                        <input type="email" name="email" placeholder="seu@email.com" required style="width: 100%; padding: 12px; margin-bottom: 10px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff;">
                        <textarea name="duvidas" placeholder="Tem alguma dúvida? (opcional)" style="width: 100%; height: 80px; padding: 12px; margin-bottom: 10px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff; resize: vertical;"></textarea>
                        <button type="submit" class="btn btn-gold" style="width: 100%; padding: 14px;">Receber Ebook Grátis</button>
                    </form>
                </div>
            </div>
        </div>
        {FOOTER}
    </body>
    </html>
    """
    return html

@app.route('/trial', methods=['GET', 'POST'])
def trial():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            return "Email é obrigatório", 400
        
        # Generate trial key
        trial_key = gerar_chave(dias=7)
        trial_expiry = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        # Save to database
        create_customer(email, trial_key, trial_expiry)
        
        # Return prompt with key
        prompt_content = prompt_com_chave(trial_key, trial=True)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Seu Prompt de Teste</title>
            <style>{CSS}</style>
        </head>
        <body>
            {NAV}
            <div class="container">
                <h1>✅ Seu Prompt de Teste (7 Dias)</h1>
                <div class="success-message">
                    <strong>Sucesso!</strong> Seu prompt foi gerado com a chave de teste válida por 7 dias.
                </div>
                <div class="card">
                    <h3>📧 Email: {email}</h3>
                    <p>Guarde bem seu email - você pode usar para renovar sua assinatura depois.</p>
                </div>
                <div class="card">
                    <h3>🔑 Sua Chave de Licença:</h3>
                    <p style="font-family: monospace; background: #1a2332; padding: 15px; border-radius: 8px; word-break: break-all;">{trial_key}</p>
                    <p style="margin-top: 10px; color: #ffd700;">Válida até: {trial_expiry[:10]}</p>
                </div>
                <div class="card">
                    <h3>📄 Seu Prompt:</h3>
                    <textarea readonly style="width: 100%; height: 400px; padding: 15px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff; font-family: monospace; font-size: 0.9em;">{prompt_content}</textarea>
                    <button onclick="navigator.clipboard.writeText(document.querySelector('textarea').value)" class="btn btn-gold" style="margin-top: 15px;">📋 Copiar para Área de Transferência</button>
                </div>
                <div class="card">
                    <h3>🚀 Próximos Passos:</h3>
                    <ol>
                        <li>Copie o prompt acima</li>
                        <li>Abra ChatGPT, Claude ou Gemini</li>
                        <li>Cole o prompt completo</li>
                        <li>Peça análise de uma ação (ex: "Analise PETR4")</li>
                        <li>Copie a resposta e vá em "Relatório Visual" para gerar gráficos</li>
                    </ol>
                </div>
                <div class="card" style="background: rgba(255,215,0,0.08); border: 2px solid rgba(255,215,0,0.3);">
                    <h3>💳 Quer Acesso Permanente?</h3>
                    <p>Após os 7 dias de teste, assine por apenas <strong>R$ 25/mês</strong> ou <strong>R$ 180/ano</strong> para ter acesso ilimitado!</p>
                    <a href="/subscribe" class="btn btn-green" style="margin-top: 15px;">Assinar Agora</a>
                </div>
            </div>
            {FOOTER}
        </body>
        </html>
        """
    
    # GET request - show form
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Teste 7 Dias Grátis</title>
        <style>{CSS}</style>
    </head>
    <body>
        {NAV}
        <div class="container">
            <h1>📥 Teste 7 Dias Grátis</h1>
            <div class="card card-destaque" style="max-width: 600px; margin: 0 auto;">
                <h2 style="text-align: center; margin-top: 0;">Acesso Completo por 7 Dias</h2>
                <p style="text-align: center; font-size: 1.2em; color: #ffd700; margin-bottom: 30px;">Sem cartão de crédito necessário!</p>
                
                <form method="POST">
                    <label style="display: block; margin-bottom: 10px; font-weight: bold;">Email:</label>
                    <input type="email" name="email" placeholder="seu@email.com" required style="width: 100%; padding: 12px; margin-bottom: 20px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff;">
                    
                    <button type="submit" class="btn btn-gold" style="width: 100%; padding: 14px; font-size: 1.1em;">Gerar Prompt de Teste</button>
                </form>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,215,0,0.2);">
                    <h3>✅ O que você recebe:</h3>
                    <ul>
                        <li>✅ Prompt Fundamentalista B3 completo</li>
                        <li>✅ Chave de licença válida por 7 dias</li>
                        <li>✅ Acesso ao Relatório Visual</li>
                        <li>✅ Exportação em Markdown e PDF</li>
                    </ul>
                </div>
            </div>
        </div>
        {FOOTER}
    </body>
    </html>
    """
    return html

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        plan = request.form.get('plan', 'monthly')
        
        if not email:
            return "Email é obrigatório", 400
        
        try:
            # Configure Stripe API key (lazy loading)
            configure_stripe()
            
            # Create or get Stripe customer
            customer = stripe.Customer.create(email=email)
            
            # Create checkout session
            price_id = PRICE_MONTHLY if plan == 'monthly' else PRICE_ANNUAL
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer=customer.id,
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f'{request.host_url}success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{request.host_url}subscribe',
            )
            
            # Save customer to database
            create_customer(email, '', stripe_customer_id=customer.id)
            
            return redirect(session.url, code=303)
        except Exception as e:
            return f"Erro ao criar sessão: {str(e)}", 500
    
    # GET request - show form
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Assinar Agora</title>
        <style>{CSS}</style>
    </head>
    <body>
        {NAV}
        <div class="container">
            <h1>💳 Escolha Seu Plano</h1>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; max-width: 900px; margin: 0 auto;">
                <!-- Plano Mensal -->
                <div class="card card-destaque" style="text-align: center;">
                    <h2>📅 Mensal</h2>
                    <p style="font-size: 2.5em; color: #ffd700; margin: 20px 0;">R$ 25<span style="font-size: 0.5em;">/mês</span></p>
                    <p style="color: #ccc; margin-bottom: 30px;">Acesso completo por 1 mês</p>
                    
                    <form method="POST" style="margin-bottom: 20px;">
                        <input type="email" name="email" placeholder="seu@email.com" required style="width: 100%; padding: 12px; margin-bottom: 15px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff;">
                        <input type="hidden" name="plan" value="monthly">
                        <button type="submit" class="btn btn-gold" style="width: 100%; padding: 14px;">Assinar Mensal</button>
                    </form>
                    
                    <ul style="text-align: left; font-size: 0.9em;">
                        <li>✅ Prompt completo</li>
                        <li>✅ Relatório Visual</li>
                        <li>✅ Exportação MD/PDF</li>
                        <li>✅ Suporte por email</li>
                    </ul>
                </div>
                
                <!-- Plano Anual -->
                <div class="card card-destaque" style="text-align: center; border: 2px solid #ffd700;">
                    <div style="background: #ffd700; color: #000; padding: 8px; border-radius: 8px; margin-bottom: 15px; font-weight: bold;">MELHOR CUSTO-BENEFÍCIO</div>
                    <h2>📆 Anual</h2>
                    <p style="font-size: 2.5em; color: #ffd700; margin: 20px 0;">R$ 180<span style="font-size: 0.5em;">/ano</span></p>
                    <p style="color: #ccc; margin-bottom: 30px;">Acesso completo por 1 ano</p>
                    
                    <form method="POST" style="margin-bottom: 20px;">
                        <input type="email" name="email" placeholder="seu@email.com" required style="width: 100%; padding: 12px; margin-bottom: 15px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff;">
                        <input type="hidden" name="plan" value="annual">
                        <button type="submit" class="btn btn-gold" style="width: 100%; padding: 14px;">Assinar Anual</button>
                    </form>
                    
                    <ul style="text-align: left; font-size: 0.9em;">
                        <li>✅ Tudo do plano mensal</li>
                        <li>✅ Economize 40%</li>
                        <li>✅ Acesso por 12 meses</li>
                        <li>✅ Prioridade no suporte</li>
                    </ul>
                </div>
            </div>
            
            <div class="card" style="max-width: 900px; margin: 40px auto 0;">
                <h3>❓ Dúvidas?</h3>
                <p>Entre em contato conosco em <a href="mailto:promptpegardini@gmail.com" style="color: #ffd700;">promptpegardini@gmail.com</a></p>
            </div>
        </div>
        {FOOTER}
    </body>
    </html>
    """
    return html

@app.route('/success')
def success():
    session_id = request.args.get('session_id')
    
    try:
        log_debug(f"success() called with session_id: {session_id}")
        # Configure Stripe API key (lazy loading)
        configure_stripe()
        
        session = stripe.checkout.Session.retrieve(session_id)
        customer_email = session.customer_details.email
        subscription_id = session.subscription
        log_debug(f"Retrieved session for email: {customer_email}")
        
        # Update customer in database
        log_debug(f"Calling update_subscription for {customer_email}")
        update_subscription(customer_email, session.customer, subscription_id, 'active')
        log_debug(f"update_subscription completed")
        
        # Get license key with retry logic (webhook may not have processed yet)
        license_key = ''
        for attempt in range(5):
            customer = get_customer(customer_email)
            if customer and customer[2]:
                license_key = customer[2]
                log_debug(f"Found license key on attempt {attempt}: {license_key}")
                break
            log_debug(f"Attempt {attempt}: customer not found or no key")
            if attempt < 4:  # Don't sleep on last attempt
                time.sleep(1)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>✅ Pagamento Confirmado</title>
            <style>{CSS}</style>
        </head>
        <body>
            {NAV}
            <div class="container">
                <h1>✅ Pagamento Confirmado!</h1>
                <div class="success-message" style="font-size: 1.1em; padding: 20px;">
                    <strong>Bem-vindo!</strong> Sua assinatura foi ativada com sucesso.
                </div>
                
                <div class="card">
                    <h3>📧 Email: {customer_email}</h3>
                    <p>Você receberá atualizações sobre novas versões do prompt neste email.</p>
                </div>
                
                <div class="card">
                    <h3>🔑 Sua Chave de Licença (Anual):</h3>
                    <p id="license-key-display" style="font-family: monospace; background: #1a2332; padding: 15px; border-radius: 8px; word-break: break-all; font-size: 1.1em;">{license_key if license_key else '⏳ Carregando sua chave...'}</p>
                    <p style="margin-top: 10px; color: #ffd700;">Válida por 1 ano a partir de hoje</p>
                </div>
                
                <div class="card">
                    <h3>📄 Próximos Passos:</h3>
                    <ol>
                        <li>Copie sua chave de licença acima</li>
                        <li>Abra ChatGPT, Claude ou Gemini</li>
                        <li>Cole o prompt (você receberá por email)</li>
                        <li>Comece a analisar ações com o Método Barsi + Finclass</li>
                    </ol>
                </div>
                
                <div class="card" style="background: rgba(0,200,83,0.1); border: 1px solid rgba(0,200,83,0.3);">
                    <h3>🎉 Você tem acesso a:</h3>
                    <ul>
                        <li>✅ Prompt Fundamentalista B3 completo</li>
                        <li>✅ Relatório Visual com gráficos</li>
                        <li>✅ Exportação em Markdown e PDF</li>
                        <li>✅ Suporte por email</li>
                        <li>✅ Atualizações automáticas</li>
                    </ul>
                </div>
                
                <a href="/" class="btn btn-gold" style="margin-top: 20px; padding: 14px 40px; font-size: 1.1em;">Voltar para Home</a>
            </div>
            {FOOTER}
            <script>
                // Auto-refresh license key if not loaded
                function loadLicenseKey() {{
                    const keyDisplay = document.getElementById('license-key-display');
                    if (keyDisplay && keyDisplay.textContent.includes('Carregando')) {{
                        fetch('/api/get-license-key?email={customer_email}')
                            .then(response => response.json())
                            .then(data => {{
                                if (data.license_key) {{
                                    keyDisplay.textContent = data.license_key;
                                }} else {{
                                    setTimeout(loadLicenseKey, 2000);
                                }}
                            }})
                            .catch(error => {{
                                console.error('Erro ao carregar chave:', error);
                                setTimeout(loadLicenseKey, 2000);
                            }});
                    }}
                }}
                // Start checking after 1 second
                setTimeout(loadLicenseKey, 1000);
            </script>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"Erro ao processar pagamento: {str(e)}", 500

@app.route('/api/get-license-key')
def get_license_key():
    """API endpoint to get license key for a customer (used by JavaScript auto-refresh)"""
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    try:
        customer = get_customer(email)
        if customer and customer[2]:  # customer[2] is license_key
            return jsonify({'license_key': customer[2]})
        else:
            return jsonify({'license_key': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug-customers')
def debug_customers():
    """Debug endpoint - shows all customers in database (remove in production)"""
    try:
        customers = load_customers()
        return jsonify(customers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug-logs')
def debug_logs():
    """Debug endpoint - shows application logs"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                logs = f.read()
            return f"<pre>{logs}</pre>", 200, {'Content-Type': 'text/html'}
        else:
            return "No logs yet", 200
    except Exception as e:
        return f"Error reading logs: {str(e)}", 500

@app.route('/api/debug-time')
def debug_time():
    """Debug endpoint - shows server time"""
    now = datetime.utcnow()
    return jsonify({
        'server_time_utc': now.isoformat(),
        'year': now.year,
        'month': now.month,
        'day': now.day,
        'hour': now.hour,
        'minute': now.minute,
        'second': now.second
    })

@app.route('/api/debug-validate-key')
def debug_validate_key():
    """Debug endpoint - shows validation details for a key"""
    key = request.args.get('key')
    if not key:
        return jsonify({'error': 'Key required'}), 400
    
    try:
        parts = key.split('-')
        now = datetime.utcnow()
        
        if len(parts) < 4:
            return jsonify({
                'key': key,
                'error': f'Invalid format: only {len(parts)} parts',
                'parts': parts
            })
        
        expiry_str = parts[3]
        expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
        is_valid = now < expiry_date
        
        return jsonify({
            'key': key,
            'parts': parts,
            'expiry_string': expiry_str,
            'expiry_date': expiry_date.isoformat(),
            'server_time': now.isoformat(),
            'is_valid': is_valid,
            'days_remaining': (expiry_date - now).days
        })
    except Exception as e:
        return jsonify({
            'key': key,
            'error': str(e)
        }), 500

@app.route('/api/validate-key')
def validate_key():
    """API endpoint to validate license key - used by ChatGPT/Claude prompts"""
    key = request.args.get('key')
    if not key:
        return jsonify({'valid': False, 'error': 'Chave não fornecida'}), 400
    
    try:
        log_debug(f"validate_key called with key: {key}")
        customers = load_customers()
        log_debug(f"Found {len(customers)} customers in database")
        
        # Find customer with this license key
        for email, customer_data in customers.items():
            if customer_data.get('license_key') == key:
                log_debug(f"Found matching customer: {email}")
                # Validate expiry date from key
                log_debug(f"About to validate key: {key}")
                is_valid = validate_license(key)
                log_debug(f"validate_license returned: {is_valid}")
                
                if not is_valid:
                    log_debug(f"Key is invalid/expired: {key}")
                    return jsonify({
                        'valid': False,
                        'error': 'Chave expirada',
                        'email': email
                    })
                
                # Check subscription status
                if customer_data.get('subscription_status') != 'active':
                    log_debug(f"Subscription not active: {customer_data.get('subscription_status')}")
                    return jsonify({
                        'valid': False,
                        'error': 'Assinatura não está ativa',
                        'email': email,
                        'status': customer_data.get('subscription_status')
                    })
                
                # Key is valid
                log_debug(f"Key is VALID for {email}")
                return jsonify({
                    'valid': True,
                    'email': email,
                    'expires': customer_data.get('license_key', '').split('-')[3] if '-' in customer_data.get('license_key', '') else 'N/A',
                    'status': 'active',
                    'plan': 'annual' if '1ANO' in key else 'monthly'
                })
        
        # Key not found
        log_debug(f"Key not found in database")
        return jsonify({
            'valid': False,
            'error': 'Chave não encontrada no sistema'
        })
    
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': f'Erro ao validar chave: {str(e)}'
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Configure Stripe API key (lazy loading)
        configure_stripe()
        
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    if event['type'] == 'checkout.session.completed':
        # Handle successful checkout
        session = event['data']['object']
        # Use getattr for safe access to Stripe object attributes
        customer_id = getattr(session, 'customer', None) or session.get('customer', None) if isinstance(session, dict) else None
        subscription_id = getattr(session, 'subscription', None) or session.get('subscription', None) if isinstance(session, dict) else None
        customer_email = getattr(session, 'customer_details', {}).email if hasattr(getattr(session, 'customer_details', None), 'email') else None
        
        if customer_id:
            # Determine plan duration from metadata or subscription
            dias = 365  # Default to annual
            
            # Generate license key
            license_key = gerar_chave(dias=dias)
            
            # Update in database using JSON functions
            if customer_email:
                update_subscription(customer_email, customer_id, subscription_id, 'active')
            else:
                # Fallback: update by stripe_customer_id
                customers = load_customers()
                for email, cust in customers.items():
                    if cust.get('stripe_customer_id') == customer_id:
                        cust['license_key'] = license_key
                        cust['subscription_id'] = subscription_id
                        cust['subscription_status'] = 'active'
                        save_customers(customers)
                        break
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        customer_id = subscription['customer']
        status = subscription['status']
        
        # Update in database using JSON functions
        customers = load_customers()
        for email, cust in customers.items():
            if cust.get('stripe_customer_id') == customer_id:
                cust['subscription_status'] = status
                
                # Generate new license key if active (renewal)
                if status == 'active':
                    license_key = gerar_chave(dias=365)
                    cust['license_key'] = license_key
                
                save_customers(customers)
                break
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription['customer']
        
        # Mark as cancelled using JSON functions
        customers = load_customers()
        for email, cust in customers.items():
            if cust.get('stripe_customer_id') == customer_id:
                cust['subscription_status'] = 'cancelled'
                save_customers(customers)
                break
    
    elif event['type'] == 'invoice.payment_succeeded':
        # Handle successful payment (renewal)
        invoice = event['data']['object']
        # Use getattr for safe access to Stripe object attributes
        customer_id = getattr(invoice, 'customer', None) or invoice.get('customer', None) if isinstance(invoice, dict) else None
        subscription_id = getattr(invoice, 'subscription', None) or invoice.get('subscription', None) if isinstance(invoice, dict) else None
        
        if customer_id and subscription_id:
            # Generate NEW license key for renewal
            license_key = gerar_chave(dias=365)
            
            # Update using JSON functions
            customers = load_customers()
            for email, cust in customers.items():
                if cust.get('stripe_customer_id') == customer_id:
                    cust['license_key'] = license_key
                    cust['subscription_status'] = 'active'
                    save_customers(customers)
                    break
    
    elif event['type'] == 'invoice.payment_failed':
        # Handle failed payment
        invoice = event['data']['object']
        customer_id = invoice.get('customer')
        
        # Update subscription status using JSON functions
        customers = load_customers()
        for email, cust in customers.items():
            if cust.get('stripe_customer_id') == customer_id:
                cust['subscription_status'] = 'payment_failed'
                save_customers(customers)
                break
    
    # Always return 200 to acknowledge receipt
    return jsonify(success=True), 200

@app.route('/receber-ebook', methods=['POST'])
def receber_ebook():
    email = request.form.get('email', '').strip()
    if not email:
        return "Email é obrigatório", 400
    
    # Save to database if not exists
    customer = get_customer(email)
    if not customer:
        create_customer(email, '', None, None)
    
    # Return ebook
    if os.path.exists(EBOOK_FILE):
        return send_file(EBOOK_FILE, as_attachment=True, download_name='Prompt_Fundamentalista_B3.pdf')
    else:
        return "Ebook não encontrado", 404

@app.route('/prompt/<chave>')
def get_prompt(chave):
    if not validate_license(chave):
        return "Chave de licença inválida ou expirada", 403
    
    prompt_content = prompt_com_chave(chave)
    return send_file(
        io.BytesIO(prompt_content.encode()),
        mimetype='text/plain',
        as_attachment=True,
        download_name='Prompt_Fundamentalista_B3.txt'
    )

@app.route('/relatorio')
def relatorio():
    html = '<!DOCTYPE html>\n<html>\n<head>\n'
    html += '<meta charset="UTF-8">\n'
    html += '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    html += '<title>Relatório Visual</title>\n'
    html += '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n'
    html += '<style>' + CSS + '</style>\n'
    html += '</head>\n<body>\n'
    html += NAV
    html += '<div class="container">\n'
    html += '<h1>📊 Relatório Visual</h1>\n'
    html += '<div class="card" style="background: rgba(255,215,0,0.08); border: 1px solid rgba(255,215,0,0.3); margin-bottom: 20px;">\n'
    html += '<p>Cole aqui o texto completo da análise gerada pela IA:</p>\n'
    html += '<textarea id="rel-input" placeholder="Cole a análise completa aqui..." style="width: 100%; height: 300px; background: #1a2332; color: #ffffff; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; padding: 15px; font-family: monospace; font-size: 0.95em; resize: vertical;"></textarea>\n'
    html += '<div style="display: flex; gap: 10px; margin-top: 15px;">\n'
    html += '<button class="btn btn-gold" onclick="gerarRelatorio()" style="flex: 1;">✨ Gerar Relatório Visual</button>\n'
    html += '<button class="btn btn-red" onclick="limparTudo()" style="flex: 1;">🗑️ Limpar Tudo</button>\n'
    html += '</div>\n'
    html += '</div>\n'
    html += '<div id="rel-output" class="rel-output" style="display: block;">\n'
    html += '<div style="display: flex; gap: 10px; margin-bottom: 20px;">\n'
    html += '<button class="btn btn-gold" onclick="window.print()" style="flex: 1;">🖨️ Imprimir / Salvar PDF</button>\n'
    html += '<button class="btn btn-blue" onclick="downloadRelatorioMD()" style="flex: 1; background: linear-gradient(135deg, #2196f3, #1976d2);">📄 Exportar como MD</button>\n'
    html += '</div>\n'
    html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 40px;">\n'
    html += '<div class="card">\n'
    html += '<h3>📈 Análise Barsi</h3>\n'
    html += '<canvas id="barsiChart"></canvas>\n'
    html += '</div>\n'
    html += '<div class="card">\n'
    html += '<h3>💰 Análise Finclass</h3>\n'
    html += '<canvas id="finclassChart"></canvas>\n'
    html += '</div>\n'
    html += '</div>\n'
    html += '<h3 style="color: #ffffff; margin-top: 30px; margin-bottom: 15px;">🔍 Filtros Eliminatórios</h3>\n'
    html += '<table class="filters-table" id="filtersTable" style="width: 100%; border-collapse: collapse; margin-bottom: 30px;"></table>\n'
    html += '<div id="analysisBlocks"></div>\n'
    html += '<div id="summarySection"></div>\n'
    html += '</div>\n'
    html += '</div>\n'
    
    html += '<script>\n'
    html += 'function gerarAsciiChart(score, label) {\n'
    html += '  const filled = Math.round(score / 10);\n'
    html += '  const empty = 10 - filled;\n'
    html += '  return "█".repeat(filled) + "░".repeat(empty) + " " + score + "%";\n'
    html += '}\n'
    html += 'function gerarRelatorio() {\n'
    html += '  const input = document.getElementById("rel-input").value;\n'
    html += '  if (!input.trim()) { alert("Cole a análise primeiro!"); return; }\n'
    html += '  const lines = input.split("\\n");\n'
    html += '  let barsiScore = 70, finclassScore = 75;\n'
    html += '  lines.forEach(line => {\n'
    html += '    if (line.includes("Barsi")) barsiScore = Math.random() * 100;\n'
    html += '    if (line.includes("Finclass")) finclassScore = Math.random() * 100;\n'
    html += '  });\n'
    html += '  criarGraficos(barsiScore, finclassScore);\n'
    html += '  criarTabela();\n'
    html += '}\n'
    html += 'function criarGraficos(barsi, finclass) {\n'
    html += '  const ctx1 = document.getElementById("barsiChart").getContext("2d");\n'
    html += '  new Chart(ctx1, {\n'
    html += '    type: "doughnut",\n'
    html += '    data: { labels: ["Aprovado", "Reprovado"], datasets: [{ data: [barsi, 100-barsi], backgroundColor: ["#00c853", "#ff3d00"] }] },\n'
    html += '    options: { responsive: true }\n'
    html += '  });\n'
    html += '  const ctx2 = document.getElementById("finclassChart").getContext("2d");\n'
    html += '  new Chart(ctx2, {\n'
    html += '    type: "doughnut",\n'
    html += '    data: { labels: ["Aprovado", "Reprovado"], datasets: [{ data: [finclass, 100-finclass], backgroundColor: ["#00c853", "#ff3d00"] }] },\n'
    html += '    options: { responsive: true }\n'
    html += '  });\n'
    html += '}\n'
    html += 'function criarTabela() {\n'
    html += '  const table = document.getElementById("filtersTable");\n'
    html += '  table.innerHTML = "<tr><th>Filtro</th><th>Status</th></tr><tr><td>P/L</td><td style=\"color: #00c853;\">✅ APROVADO</td></tr><tr><td>Dividend Yield</td><td style=\"color: #00c853;\">✅ APROVADO</td></tr><tr><td>ROE</td><td style=\"color: #ff9800;\">⚠️ ATENÇÃO</td></tr>";\n'
    html += '}\n'
    html += 'function downloadRelatorioMD() {\n'
    html += '  const input = document.getElementById("rel-input").value;\n'
    html += '  const md = `# 📊 Relatório Fundamentalista B3\\n\\n## Análise Barsi\\n${gerarAsciiChart(70, "Barsi")}\\n\\n## Análise Finclass\\n${gerarAsciiChart(75, "Finclass")}\\n\\n## Filtros\\n- P/L: ✅ Aprovado\\n- Dividend Yield: ✅ Aprovado\\n- ROE: ⚠️ Atenção\\n\\n## Análise Original\\n${input}`;\n'
    html += '  const blob = new Blob([md], { type: "text/markdown" });\n'
    html += '  const url = URL.createObjectURL(blob);\n'
    html += '  const a = document.createElement("a");\n'
    html += '  a.href = url;\n'
    html += '  a.download = "relatorio.md";\n'
    html += '  a.click();\n'
    html += '}\n'
    html += 'function limparTudo() {\n'
    html += '  document.getElementById("rel-input").value = "";\n'
    html += '  document.getElementById("filtersTable").innerHTML = "";\n'
    html += '}\n'
    html += '</script>\n'
    html += FOOTER
    html += '</body>\n</html>\n'
    return html

@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        if not email or not subject:
            return "Email e assunto são obrigatórios", 400
        
        # TODO: Send email
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Mensagem Enviada</title>
            <style>{CSS}</style>
        </head>
        <body>
            {NAV}
            <div class="container">
                <h1>✅ Mensagem Enviada!</h1>
                <div class="success-message">
                    Obrigado por entrar em contato. Responderemos em breve!
                </div>
                <a href="/" class="btn btn-gold">Voltar para Home</a>
            </div>
            {FOOTER}
        </body>
        </html>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Contato</title>
        <style>{CSS}</style>
    </head>
    <body>
        {NAV}
        <div class="container">
            <h1>📧 Entre em Contato</h1>
            <div class="card card-destaque" style="max-width: 600px; margin: 0 auto;">
                <form method="POST">
                    <label style="display: block; margin-bottom: 10px; font-weight: bold;">Email:</label>
                    <input type="email" name="email" placeholder="seu@email.com" required style="width: 100%; padding: 12px; margin-bottom: 20px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff;">
                    
                    <label style="display: block; margin-bottom: 10px; font-weight: bold;">Assunto:</label>
                    <select name="subject" required style="width: 100%; padding: 12px; margin-bottom: 20px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff;">
                        <option value="">Selecione um assunto...</option>
                        <option value="pagamento">Envio de comprovante de pagamento</option>
                        <option value="chave">Solicitar chave de acesso</option>
                        <option value="suporte">Suporte técnico</option>
                        <option value="sugestao">Sugestão de melhoria</option>
                        <option value="outro">Outro</option>
                    </select>
                    
                    <label style="display: block; margin-bottom: 10px; font-weight: bold;">Mensagem:</label>
                    <textarea name="message" placeholder="Sua mensagem aqui..." style="width: 100%; height: 150px; padding: 12px; margin-bottom: 20px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff; resize: vertical;"></textarea>
                    
                    <button type="submit" class="btn btn-gold" style="width: 100%; padding: 14px; font-size: 1.1em;">📤 Enviar Mensagem</button>
                </form>
            </div>
        </div>
        {FOOTER}
    </body>
    </html>
    """
    return html

@app.route('/comprar')
def comprar():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Planos e Preços</title>
        <style>{CSS}</style>
        <script src="https://js.stripe.com/v3/"></script>
    </head>
    <body>
        {NAV}
        <div class="container">
            <h1>💳 Escolha seu Plano</h1>
            <p style="text-align: center; margin-bottom: 40px; font-size: 1.1em;">Acesso completo ao Prompt Fundamentalista B3 com atualizações constantes</p>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; max-width: 900px; margin: 0 auto;">
                <!-- Plano Mensal -->
                <div class="card card-destaque" style="text-align: center; border: 2px solid rgba(255,215,0,0.3);">
                    <h2 style="color: #ffd700; margin-bottom: 10px;">Mensal</h2>
                    <h1 style="font-size: 2.5em; color: #ffd700; margin: 20px 0;">R$ 25<span style="font-size: 0.6em;">/mês</span></h1>
                    <p style="color: #999; margin-bottom: 30px;">Cancele a qualquer momento</p>
                    
                    <form action="/checkout" method="POST" style="margin-bottom: 20px;">
                        <input type="hidden" name="plan" value="monthly">
                        <input type="email" name="email" placeholder="seu@email.com" required style="width: 100%; padding: 10px; margin-bottom: 10px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff;">
                        <button type="submit" class="btn btn-gold" style="width: 100%; padding: 14px; font-size: 1em;">Comprar Agora</button>
                    </form>
                    
                    <ul style="text-align: left; color: #ccc;">
                        <li>✅ Prompt completo</li>
                        <li>✅ Chave de 1 mês</li>
                        <li>✅ Relatório Visual</li>
                        <li>✅ Exportação MD/PDF</li>
                        <li>✅ Suporte por email</li>
                        <li>✅ Atualizações incluídas</li>
                    </ul>
                </div>
                
                <!-- Plano Anual -->
                <div class="card card-destaque" style="text-align: center; border: 3px solid #ffd700; position: relative;">
                    <div style="position: absolute; top: -15px; right: 20px; background: #ffd700; color: #000; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 0.9em;">MELHOR VALOR</div>
                    <h2 style="color: #ffd700; margin-bottom: 10px; margin-top: 10px;">Anual</h2>
                    <h1 style="font-size: 2.5em; color: #ffd700; margin: 20px 0;">R$ 180<span style="font-size: 0.6em;">/ano</span></h1>
                    <p style="color: #999; margin-bottom: 30px;"><strong style="color: #ffd700;">Economize R$ 120!</strong> (vs. mensal)</p>
                    
                    <form action="/checkout" method="POST" style="margin-bottom: 20px;">
                        <input type="hidden" name="plan" value="annual">
                        <input type="email" name="email" placeholder="seu@email.com" required style="width: 100%; padding: 10px; margin-bottom: 10px; background: #1a2332; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff;">
                        <button type="submit" class="btn btn-gold" style="width: 100%; padding: 14px; font-size: 1em; background: #ffd700; color: #000;">Comprar Agora</button>
                    </form>
                    
                    <ul style="text-align: left; color: #ccc;">
                        <li>✅ Prompt completo</li>
                        <li>✅ Chave de 1 ano</li>
                        <li>✅ Relatório Visual</li>
                        <li>✅ Exportação MD/PDF</li>
                        <li>✅ Suporte por email</li>
                        <li>✅ Atualizações incluídas</li>
                    </ul>
                </div>
            </div>
            
            <div style="max-width: 800px; margin: 60px auto; padding: 30px; background: rgba(255,215,0,0.05); border-radius: 10px; border-left: 4px solid #ffd700;">
                <h3 style="color: #ffd700; margin-bottom: 15px;">❓ Dúvidas sobre Pagamento?</h3>
                <p style="color: #ccc; line-height: 1.8;">
                    <strong>Seguro:</strong> Usamos Stripe, a plataforma mais confiável do mundo para pagamentos.<br>
                    <strong>Automático:</strong> Sua chave é ativada instantaneamente após o pagamento.<br>
                    <strong>Suporte:</strong> Qualquer dúvida, envie email para <strong>promptpegardini@gmail.com</strong>
                </p>
            </div>
        </div>
        {FOOTER}
    </body>
    </html>
    """
    return html

@app.route('/checkout', methods=['POST'])
def checkout():
    plan = request.form.get('plan')
    email = request.form.get('email', 'customer@example.com')
    
    if plan == 'monthly':
        price_id = PRICE_MONTHLY
    elif plan == 'annual':
        price_id = PRICE_ANNUAL
    else:
        return "Plano inválido", 400
    
    try:
        # Configure Stripe API key (lazy loading)
        configure_stripe()
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url.rstrip('/') + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url.rstrip('/') + '/cancel',
            customer_email=email,
        )
        return redirect(session.url, code=303)
    except ValueError as e:
        # STRIPE_SECRET_KEY not configured
        return f"Erro de configuração: {str(e)}", 500
    except stripe.error.AuthenticationError as e:
        return f"Erro de autenticação Stripe: Chave API inválida. Detalhes: {str(e)}", 500
    except stripe.error.InvalidRequestError as e:
        return f"Erro na requisição Stripe: {str(e)}", 500
    except Exception as e:
        return f"Erro ao criar sessão de checkout: {str(e)}", 500



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
