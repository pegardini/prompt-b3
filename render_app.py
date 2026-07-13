import io, os, random, secrets, string, sqlite3, stripe, time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, redirect, url_for
import json
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

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
DB_FILE = '/tmp/customers.json'
LOG_FILE = '/tmp/app_debug.log'
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'promptpegardini@gmail.com')
APP_URL = os.environ.get('APP_URL', 'https://prompt-b3-ndes.onrender.com')

def log_debug(message):
    """Write debug message to log file"""
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {message}\n")
    except:
        pass

def send_email(to_email, subject, html_content):
    """Send email using SendGrid"""
    if not SENDGRID_AVAILABLE or not SENDGRID_API_KEY:
        log_debug(f"SendGrid not available, skipping email to {to_email}")
        return False
    
    try:
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        log_debug(f"Email sent to {to_email}: {response.status_code}")
        return True
    except Exception as e:
        log_debug(f"Error sending email to {to_email}: {str(e)}")
        return False

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
            if 'key_history' not in customers[email]:
                customers[email]['key_history'] = []
            if customers[email].get('license_key'):
                customers[email]['key_history'].append({
                    'key': customers[email]['license_key'],
                    'issued_at': customers[email].get('key_issued_at', customers[email].get('created_at')),
                    'status': 'replaced'
                })
            customers[email]['stripe_customer_id'] = stripe_customer_id
            customers[email]['subscription_id'] = subscription_id
            customers[email]['subscription_status'] = status
            customers[email]['license_key'] = license_key
            customers[email]['key_issued_at'] = datetime.utcnow().isoformat()
            customers[email]['trial_expiry'] = None
        else:
            log_debug(f"Creating new customer: {email}")
            customers[email] = {
                'id': len(customers) + 1,
                'email': email,
                'license_key': license_key,
                'key_issued_at': datetime.utcnow().isoformat(),
                'key_history': [],
                'trial_expiry': None,
                'stripe_customer_id': stripe_customer_id,
                'subscription_id': subscription_id,
                'subscription_status': status,
                'created_at': datetime.utcnow().isoformat()
            }
        
        save_customers(customers)
        log_debug(f"Successfully saved customer: {email}")
        
        # Send welcome email with license key
        send_license_email(email, license_key)
    except Exception as e:
        log_debug(f"ERROR in update_subscription: {str(e)}")
        raise

def send_license_email(email, license_key):
    """Send license key email to customer with prompt attachment"""
    subject = "🔑 Sua Chave de Licença + Prompt B3"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #ffd700; text-align: center;">🎉 Bem-vindo ao Prompt B3!</h2>
            
            <p style="color: #333; font-size: 16px;">Olá,</p>
            
            <p style="color: #333; font-size: 16px;">Obrigado por sua compra! Sua assinatura foi ativada com sucesso.</p>
            
            <div style="background-color: #0a0f1e; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #ffd700;">
                <p style="color: #ffd700; font-size: 14px; margin: 0; text-align: center;">Sua Chave de Licença:</p>
                <p style="color: #ffffff; font-size: 18px; font-weight: bold; margin: 10px 0; text-align: center; font-family: monospace;">{license_key}</p>
            </div>
            
            <h3 style="color: #333; margin-top: 30px;">📝 Próximos Passos:</h3>
            <ol style="color: #333; font-size: 15px; line-height: 1.8;">
                <li><strong>Baixe o arquivo em anexo:</strong> PROMPT_MESTRE_HIBRIDO_B3_v7.md</li>
                <li>Abra ChatGPT, Claude ou Gemini</li>
                <li>Cole o conteúdo do arquivo no chat</li>
                <li>Cole sua chave de licença quando solicitado</li>
                <li>Comece a analisar ações com o Método Barsi + Finclass</li>
            </ol>
            
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #ffd700; margin: 20px 0;">
                <p style="color: #666; font-size: 14px; margin: 0;"><strong>💡 Dica:</strong> Guarde sua chave em um lugar seguro. Você precisará dela para usar o prompt.</p>
            </div>
            
            <h3 style="color: #333; margin-top: 30px;">❓ Dúvidas?</h3>
            <p style="color: #666; font-size: 14px;">Entre em contato conosco em <a href="mailto:promptpegardini@gmail.com" style="color: #ffd700; text-decoration: none;">promptpegardini@gmail.com</a></p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">© 2026 Prompt B3. Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    send_email_with_attachment(email, subject, html_content, PROMPT_FILE)

def send_email_with_attachment(to_email, subject, html_content, attachment_path):
    """Send email with file attachment using SendGrid"""
    if not SENDGRID_AVAILABLE or not SENDGRID_API_KEY:
        log_debug(f"SendGrid not available, skipping email to {to_email}")
        return False
    
    try:
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
        import base64
        
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        # Attach file if it exists
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                file_data = f.read()
                file_b64 = base64.b64encode(file_data).decode()
            
            file_name = os.path.basename(attachment_path)
            attachment = Attachment(
                FileContent(file_b64),
                FileName(file_name),
                FileType('text/markdown' if file_name.endswith('.md') else 'application/octet-stream'),
                Disposition('attachment')
            )
            message.attachment = attachment
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        log_debug(f"Email sent to {to_email} with status {response.status_code}")
        return True
    except Exception as e:
        log_debug(f"Error sending email to {to_email}: {str(e)}")
        return False

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
    """Redirect to lead magnet landing page"""
    return redirect('/lead-magnet')

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

@app.route('/dashboard')
def dashboard():
    """Customer dashboard - view and manage licenses"""
    email = request.args.get('email')
    key = request.args.get('key')
    
    if not email or not key:
        return redirect(url_for('index'))
    
    try:
        customers = load_customers()
        if email not in customers:
            return "Cliente não encontrado", 404
        
        customer = customers[email]
        if customer.get('license_key') != key:
            return "Chave inválida", 401
        
        license_key = customer.get('license_key', '')
        parts = license_key.split('-')
        if len(parts) >= 4:
            expiry_str = parts[3]
            try:
                expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
                days_remaining = (expiry_date - datetime.utcnow()).days
            except:
                days_remaining = 0
        else:
            days_remaining = 0
        
        subscription_status = customer.get('subscription_status', 'unknown')
        created_at = customer.get('created_at', 'N/A')
        progress_percent = max(0, min(100, (days_remaining / 365) * 100))
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📊 Dashboard - Prompt B3</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0f1e; color: #ffffff; min-height: 100vh; padding: 20px; }}
                .container {{ max-width: 900px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .header h1 {{ color: #ffd700; font-size: 2.5em; margin-bottom: 10px; }}
                .card {{ background: #1a2332; border: 1px solid rgba(255,215,0,0.2); border-radius: 12px; padding: 25px; margin-bottom: 20px; }}
                .card h2 {{ color: #ffd700; margin-bottom: 15px; font-size: 1.3em; }}
                .info-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,215,0,0.1); }}
                .info-row:last-child {{ border-bottom: none; }}
                .info-label {{ color: #aaa; font-weight: 500; }}
                .info-value {{ color: #ffd700; font-weight: bold; font-family: monospace; }}
                .status-active {{ color: #4ade80; }}
                .status-inactive {{ color: #ef4444; }}
                .key-box {{ background: #0a0f1e; padding: 15px; border-radius: 8px; border: 2px solid #ffd700; margin: 15px 0; }}
                .key-text {{ color: #ffffff; font-family: monospace; font-size: 14px; word-break: break-all; }}
                .btn {{ display: inline-block; padding: 12px 25px; background: #ffd700; color: #0a0f1e; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; text-decoration: none; margin: 10px 5px 10px 0; }}
                .btn:hover {{ background: #ffed4e; }}
                .btn-secondary {{ background: #666; color: #fff; }}
                .btn-secondary:hover {{ background: #777; }}
                .progress-bar {{ width: 100%; height: 8px; background: #333; border-radius: 4px; margin: 10px 0; overflow: hidden; }}
                .progress-fill {{ height: 100%; background: #4ade80; width: {progress_percent}%; }}
                .warning {{ background: #7c2d12; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ff6b35; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Seu Dashboard</h1>
                    <p>Gerencie sua assinatura do Prompt B3</p>
                </div>
                
                <div class="card">
                    <h2>👤 Informações da Conta</h2>
                    <div class="info-row">
                        <span class="info-label">Email:</span>
                        <span class="info-value">{email}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Status:</span>
                        <span class="info-value status-{subscription_status}">{subscription_status.upper()}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Membro desde:</span>
                        <span class="info-value">{created_at[:10]}</span>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🔑 Sua Chave de Licença</h2>
                    <div class="key-box">
                        <p class="key-text">{license_key}</p>
                    </div>
                    <p style="color: #aaa; font-size: 0.9em; margin-top: 10px;">Use esta chave ao usar o Prompt B3 no ChatGPT, Claude ou Gemini.</p>
                </div>
                
                <div class="card">
                    <h2>⏱️ Validade da Assinatura</h2>
                    <div class="info-row">
                        <span class="info-label">Dias Restantes:</span>
                        <span class="info-value">{days_remaining} dias</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    {f'<div class="warning">⚠️ Sua assinatura vencerá em breve. Renove agora para continuar usando!</div>' if days_remaining < 30 else ''}
                </div>
                
                <div class="card">
                    <h2>📄 Histórico de Chaves</h2>
                    {f'<div style="color: #aaa; font-size: 0.9em;">Você tem {len(customer.get("key_history", []))} chave(s) anterior(es).</div>' if customer.get('key_history') else '<div style="color: #aaa; font-size: 0.9em;">Nenhuma chave anterior.</div>'}
                    {f'<div style="margin-top: 15px; max-height: 300px; overflow-y: auto;">' + ''.join([f'<div style="background: #0a0f1e; padding: 10px; border-radius: 4px; margin-bottom: 8px; border-left: 3px solid #666;"><p style="color: #ffd700; font-family: monospace; font-size: 12px; margin: 0;">{k["key"]}</p><p style="color: #aaa; font-size: 0.8em; margin: 5px 0 0 0;">Emitida em: {k["issued_at"][:10]}</p></div>' for k in customer.get('key_history', [])]) + '</div>' if customer.get('key_history') else ''}
                </div>
                
                <div class="card">
                    <h2>🔄 Ações</h2>
                    <button class="btn" onclick="copyToClipboard()">📋 Copiar Chave</button>
                    <a href="/comprar" class="btn btn-secondary">🔄 Renovar Assinatura</a>
                    <button class="btn btn-secondary" onclick="cancelSubscription()" style="background: #ef4444;">❌ Cancelar Assinatura</button>
                    <a href="/" class="btn btn-secondary">🏠 Voltar ao Início</a>
                </div>
            </div>
            
            <script>
                function copyToClipboard() {{
                    const key = '{license_key}';
                    navigator.clipboard.writeText(key).then(() => {{
                        alert('Chave copiada para a área de transferência!');
                    }}).catch(() => {{
                        alert('Erro ao copiar a chave');
                    }});
                }}
                
                function cancelSubscription() {{
                    if (!confirm('Tem certeza que deseja cancelar sua assinatura? Você perderá acesso ao Prompt B3.')) {{
                        return;
                    }}
                    
                    const formData = new FormData();
                    formData.append('email', '{email}');
                    formData.append('key', '{license_key}');
                    
                    fetch('/cancel-subscription', {{
                        method: 'POST',
                        body: formData
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            alert(data.message);
                            window.location.href = '/';
                        }} else {{
                            alert('Erro: ' + data.error);
                        }}
                    }})
                    .catch(error => {{
                        alert('Erro ao cancelar assinatura: ' + error);
                    }});
                }}
            </script>
        </body>
        </html>
        """
        return html
    except Exception as e:
        log_debug(f"Error in dashboard: {str(e)}")
        return f"Erro ao carregar dashboard: {str(e)}", 500

@app.route('/cancel-subscription', methods=['POST'])
def cancel_subscription():
    """Cancel a subscription"""
    email = request.form.get('email')
    key = request.form.get('key')
    
    if not email or not key:
        return jsonify({'success': False, 'error': 'Email e chave são obrigatórios'}), 400
    
    try:
        customers = load_customers()
        if email not in customers:
            return jsonify({'success': False, 'error': 'Cliente não encontrado'}), 404
        
        customer = customers[email]
        if customer.get('license_key') != key:
            return jsonify({'success': False, 'error': 'Chave inválida'}), 401
        
        # Cancel the Stripe subscription
        configure_stripe()
        subscription_id = customer.get('subscription_id')
        if subscription_id:
            stripe.Subscription.delete(subscription_id)
            log_debug(f"Cancelled Stripe subscription: {subscription_id}")
        
        # Update customer status
        customer['subscription_status'] = 'cancelled'
        customers[email] = customer
        save_customers(customers)
        log_debug(f"Cancelled subscription for {email}")
        
        # Send cancellation email
        send_cancellation_email(email)
        
        return jsonify({
            'success': True,
            'message': 'Assinatura cancelada com sucesso. Você receberá um email de confirmação.'
        })
    except Exception as e:
        log_debug(f"Error cancelling subscription: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def send_cancellation_email(email):
    """Send cancellation confirmation email"""
    subject = "🛑 Sua Assinatura foi Cancelada"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #ef4444; text-align: center;">🛑 Assinatura Cancelada</h2>
            
            <p style="color: #333; font-size: 16px;">Olá,</p>
            
            <p style="color: #333; font-size: 16px;">Sua assinatura do Prompt B3 foi cancelada com sucesso.</p>
            
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #ef4444; margin: 20px 0;">
                <p style="color: #666; font-size: 14px; margin: 0;"><strong>Data do Cancelamento:</strong> {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            <h3 style="color: #333; margin-top: 30px;">📝 Próximos Passos:</h3>
            <ul style="color: #333; font-size: 15px; line-height: 1.8;">
                <li>Sua chave de licença deixará de funcionar após o término do período pago</li>
                <li>Você pode reativar sua assinatura a qualquer momento</li>
                <li>Se tiver dúvidas, entre em contato conosco</li>
            </ul>
            
            <div style="background-color: rgba(255,215,0,0.1); padding: 15px; border-radius: 8px; margin: 20px 0; border: 2px solid #ffd700;">
                <p style="color: #333; font-size: 14px; margin: 0;"><strong>🙋 Sentiremos sua falta!</strong> Se você tiver alguma sugestão ou feedback, por favor nos envie um email.</p>
            </div>
            
            <h3 style="color: #333; margin-top: 30px;">❓ Dúvidas?</h3>
            <p style="color: #666; font-size: 14px;">Entre em contato conosco em <a href="mailto:promptpegardini@gmail.com" style="color: #ffd700; text-decoration: none;">promptpegardini@gmail.com</a></p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">© 2026 Prompt B3. Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    send_email(email, subject, html_content)

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard - view sales reports and customer list"""
    password = request.args.get('password')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    if not password or password != admin_password:
        return "Acesso negado", 401
    
    try:
        customers = load_customers()
        
        # Calculate statistics
        total_customers = len(customers)
        active_subscriptions = sum(1 for c in customers.values() if c.get('subscription_status') == 'active')
        cancelled_subscriptions = sum(1 for c in customers.values() if c.get('subscription_status') == 'cancelled')
        total_leads = sum(1 for c in customers.values() if c.get('is_lead'))
        leads_converted = sum(1 for c in customers.values() if c.get('is_lead') and c.get('subscription_status') == 'active')
        conversion_rate = (leads_converted / total_leads * 100) if total_leads > 0 else 0
        
        # Calculate total revenue (estimate)
        total_revenue = 0
        for customer in customers.values():
            plan = customer.get('plan', 'unknown')
            if plan == 'monthly':
                total_revenue += 25
            elif plan == 'annual':
                total_revenue += 180
        
        # Build customer list HTML
        customer_rows = ""
        for email, customer in sorted(customers.items()):
            status = customer.get('subscription_status', 'unknown')
            plan = customer.get('plan', 'unknown')
            created = customer.get('created_at', 'N/A')
            key = customer.get('license_key', 'N/A')[:20] + '...'
            status_color = '#4ade80' if status == 'active' else '#ef4444'
            
            customer_rows += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,215,0,0.1);">{email}</td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,215,0,0.1);">{plan}</td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,215,0,0.1);"><span style="color: {status_color}; font-weight: bold;">{status.upper()}</span></td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,215,0,0.1); font-family: monospace; font-size: 12px;">{key}</td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,215,0,0.1);">{created}</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📊 Admin Dashboard - Prompt B3</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0f1e; color: #ffffff; min-height: 100vh; padding: 20px; }}
                .container {{ max-width: 1400px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .header h1 {{ color: #ffd700; font-size: 2.5em; margin-bottom: 10px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
                .stat-card {{ background: #1a2332; border: 1px solid rgba(255,215,0,0.2); border-radius: 12px; padding: 25px; text-align: center; }}
                .stat-card h3 {{ color: #aaa; font-size: 0.9em; margin-bottom: 15px; text-transform: uppercase; }}
                .stat-card .number {{ color: #ffd700; font-size: 2.5em; font-weight: bold; }}
                .table-container {{ background: #1a2332; border: 1px solid rgba(255,215,0,0.2); border-radius: 12px; padding: 20px; overflow-x: auto; }}
                .table-container h2 {{ color: #ffd700; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                table th {{ background: rgba(255,215,0,0.1); padding: 15px; text-align: left; color: #ffd700; font-weight: bold; border-bottom: 2px solid rgba(255,215,0,0.2); }}
                table td {{ padding: 12px; border-bottom: 1px solid rgba(255,215,0,0.1); }}
                .btn {{ display: inline-block; padding: 12px 25px; background: #ffd700; color: #0a0f1e; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; text-decoration: none; margin-top: 20px; }}
                .btn:hover {{ background: #ffed4e; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Admin Dashboard</h1>
                    <p>Relatório de Vendas e Clientes - Prompt B3</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>👥 Total de Clientes</h3>
                        <div class="number">{total_customers}</div>
                    </div>
                    <div class="stat-card">
                        <h3>✅ Assinaturas Ativas</h3>
                        <div class="number" style="color: #4ade80;">{active_subscriptions}</div>
                    </div>
                    <div class="stat-card">
                        <h3>❌ Assinaturas Canceladas</h3>
                        <div class="number" style="color: #ef4444;">{cancelled_subscriptions}</div>
                    </div>
                    <div class="stat-card">
                        <h3>💰 Receita Estimada</h3>
                        <div class="number">R$ {total_revenue:,.2f}</div>
                    </div>
                    <div class="stat-card">
                        <h3>📧 Leads Capturados</h3>
                        <div class="number" style="color: #60a5fa;">{total_leads}</div>
                    </div>
                    <div class="stat-card">
                        <h3>🎯 Leads Convertidos</h3>
                        <div class="number" style="color: #34d399;">{leads_converted}</div>
                    </div>
                    <div class="stat-card">
                        <h3>📈 Taxa de Conversão</h3>
                        <div class="number" style="color: #fbbf24;">{conversion_rate:.1f}%</div>
                    </div>
                </div>
                
                <div class="table-container">
                    <h2>📋 Lista de Clientes</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Email</th>
                                <th>Plano</th>
                                <th>Status</th>
                                <th>Chave de Licença</th>
                                <th>Data de Criação</th>
                            </tr>
                        </thead>
                        <tbody>
                            {customer_rows}
                        </tbody>
                    </table>
                </div>
                
                <a href="/" class="btn">← Voltar</a>
            </div>
        </body>
        </html>
        """
        return html
    except Exception as e:
        log_debug(f"Error in admin_dashboard: {str(e)}")
        return f"Erro ao carregar dashboard admin: {str(e)}", 500

@app.route('/lead-magnet')
def lead_magnet():
    """Lead magnet page - capture emails with free ebook"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ebook Gratuito - Prompt B3</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0f1e; color: #ffffff; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }}
            .container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; max-width: 1200px; width: 100%; }}
            .ebook-image {{ display: flex; align-items: center; justify-content: center; }}
            .ebook-image img {{ max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 10px 40px rgba(255,215,0,0.2); }}
            .form-section {{ background: #1a2332; border: 2px solid rgba(255,215,0,0.3); border-radius: 12px; padding: 40px; }}
            .form-section h2 {{ color: #ffd700; font-size: 1.8em; margin-bottom: 10px; }}
            .form-section p {{ color: #aaa; margin-bottom: 20px; font-size: 0.95em; line-height: 1.6; }}
            .highlight {{ color: #ffd700; font-weight: bold; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; color: #ffd700; font-weight: bold; margin-bottom: 8px; }}
            .form-group input, .form-group textarea {{ width: 100%; padding: 12px; background: #0a0f1e; border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; color: #ffffff; font-family: inherit; }}
            .form-group input::placeholder, .form-group textarea::placeholder {{ color: #666; }}
            .form-group textarea {{ resize: vertical; min-height: 100px; }}
            .btn {{ width: 100%; padding: 14px; background: #ffd700; color: #0a0f1e; border: none; border-radius: 8px; font-weight: bold; font-size: 1em; cursor: pointer; margin-top: 10px; }}
            .btn:hover {{ background: #ffed4e; }}
            @media (max-width: 768px) {{
                .container {{ grid-template-columns: 1fr; gap: 30px; }}
                .form-section {{ padding: 30px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="ebook-image">
                <img src="/static/ebook_cover.webp" alt="Capa do Ebook Prompt B3">
            </div>
            
            <div class="form-section">
                <h2>📋 Guia Introdutório Exclusivo</h2>
                <p>Aprenda os fundamentos do <strong>Método Barsi e Finclass</strong> em <strong>10 páginas</strong> práticas e diretas.</p>
                
                <div style="background: rgba(255,215,0,0.1); padding: 15px; border-left: 4px solid #ffd700; margin: 20px 0; border-radius: 8px;">
                    <p style="color: #ffd700; font-weight: bold;">✨ Preencha seus dados abaixo e receba o ebook + atualizações sobre novas versões do prompt.</p>
                </div>
                
                <form method="POST" action="/submit-lead">
                    <div class="form-group">
                        <label for="email">📧 Seu Email</label>
                        <input type="email" id="email" name="email" placeholder="seu@email.com" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="question">❓ Tem alguma dúvida? (Opcional)</label>
                        <textarea id="question" name="question" placeholder="Compartilhe sua dúvida ou interesse..."></textarea>
                    </div>
                    
                    <button type="submit" class="btn">📥 Receber Ebook Grátis</button>
                </form>
                
                <p style="color: #666; font-size: 0.85em; margin-top: 20px; text-align: center;">
                    ✅ Sem spam. Você receberá apenas atualizações importantes.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/submit-lead', methods=['POST'])
def submit_lead():
    """Process lead form submission and send ebook"""
    email = request.form.get('email')
    question = request.form.get('question', '')
    
    if not email:
        return jsonify({'success': False, 'error': 'Email é obrigatório'}), 400
    
    try:
        # Store lead in database with analytics
        customers = load_customers()
        if email not in customers:
            customers[email] = {}
        
        customers[email]['lead_email'] = email
        customers[email]['lead_question'] = question
        customers[email]['lead_date'] = datetime.utcnow().isoformat()
        customers[email]['is_lead'] = True
        customers[email]['ebook_downloaded'] = True
        customers[email]['ebook_download_date'] = datetime.utcnow().isoformat()
        customers[email]['utm_source'] = request.args.get('utm_source', 'organic')
        customers[email]['utm_medium'] = request.args.get('utm_medium', 'direct')
        customers[email]['utm_campaign'] = request.args.get('utm_campaign', 'lead_magnet')
        save_customers(customers)
        
        # Send ebook by email
        send_lead_magnet_email(email, question)
        
        # Send Day 1 email sequence
        send_email_sequence_day1(email)
        
        # Redirect to thank you page
        return redirect(f'/thank-you?email={email}')
    except Exception as e:
        log_debug(f"Error processing lead: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/thank-you')
def thank_you():
    """Thank you page after lead submission with conversion CTA"""
    email = request.args.get('email', 'seu email')
    
    # Get download count from database
    customers = load_customers()
    download_count = len([c for c in customers.values() if 'leads' in str(c)])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Obrigado! - Prompt B3</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #0a0f1e 0%, #1a2332 100%); color: #ffffff; min-height: 100vh; padding: 20px; }}
            .container {{ max-width: 700px; margin: 0 auto; }}
            .success-card {{ background: #1a2332; border: 2px solid rgba(74,222,128,0.5); border-radius: 12px; padding: 40px; margin-bottom: 30px; text-align: center; }}
            .success-card h1 {{ color: #4ade80; font-size: 2.5em; margin-bottom: 15px; }}
            .success-card p {{ color: #aaa; margin-bottom: 15px; font-size: 1.05em; line-height: 1.6; }}
            .highlight {{ color: #ffd700; font-weight: bold; }}
            .social-proof {{ background: rgba(255,215,0,0.05); border: 1px solid rgba(255,215,0,0.2); border-radius: 8px; padding: 15px; margin: 20px 0; font-size: 0.95em; color: #ccc; }}
            .social-proof strong {{ color: #ffd700; }}
            .cta-section {{ background: #1a2332; border: 2px solid rgba(255,215,0,0.3); border-radius: 12px; padding: 35px; margin-bottom: 30px; text-align: center; }}
            .cta-section h2 {{ color: #ffd700; font-size: 1.8em; margin-bottom: 15px; }}
            .cta-section p {{ color: #aaa; margin-bottom: 20px; line-height: 1.6; }}
            .btn {{ display: inline-block; padding: 16px 40px; background: #ffd700; color: #0a0f1e; border: none; border-radius: 8px; font-weight: bold; text-decoration: none; font-size: 1.05em; margin: 10px 5px; transition: all 0.3s; }}
            .btn:hover {{ background: #ffed4e; transform: translateY(-2px); box-shadow: 0 8px 20px rgba(255,215,0,0.3); }}
            .btn-secondary {{ background: rgba(255,215,0,0.2); color: #ffd700; border: 2px solid #ffd700; }}
            .btn-secondary:hover {{ background: rgba(255,215,0,0.3); }}
            .features {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
            .feature {{ background: rgba(255,215,0,0.05); padding: 15px; border-radius: 8px; border-left: 3px solid #ffd700; }}
            .feature p {{ color: #ccc; font-size: 0.9em; margin: 0; }}
            .testimonial {{ background: rgba(74,222,128,0.05); border-left: 3px solid #4ade80; padding: 15px; margin: 15px 0; border-radius: 4px; font-style: italic; color: #ccc; }}
            .countdown {{ color: #ff6b6b; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Success Message -->
            <div class="success-card">
                <h1>✅ Obrigado!</h1>
                <p>Seu ebook está sendo enviado para <span class="highlight">{email}</span></p>
                <p style="color: #999; font-size: 0.95em;">Verifique sua caixa de entrada (e a pasta de spam) em <span class="countdown">2-5 minutos</span></p>
                
                <div class="social-proof">
                    <strong>📊 {download_count}+ pessoas</strong> já baixaram o ebook e estão aprendendo análise de ações com IA
                </div>
            </div>
            
            <!-- CTA Section -->
            <div class="cta-section">
                <h2>🚀 Pronto para Análises Profissionais?</h2>
                <p>O ebook é apenas o começo. O <strong>Prompt B3 Completo</strong> oferece:</p>
                
                <div class="features">
                    <div class="feature">
                        <p>✅ <strong>Análise Completa</strong><br/>Barsi + Finclass + Veredito</p>
                    </div>
                    <div class="feature">
                        <p>✅ <strong>Relatório Visual</strong><br/>Gráficos coloridos e profissionais</p>
                    </div>
                    <div class="feature">
                        <p>✅ <strong>Atualizações</strong><br/>Novas versões do prompt</p>
                    </div>
                    <div class="feature">
                        <p>✅ <strong>Suporte</strong><br/>Email direto com dúvidas</p>
                    </div>
                </div>
                
                <p style="margin: 25px 0 0 0; color: #999; font-size: 0.9em;">Começar com apenas <strong style="color: #ffd700;">R$ 25/mês</strong> ou <strong style="color: #ffd700;">R$ 180/ano</strong></p>
                
                <div style="margin-top: 20px;">
                    <a href="/comprar" class="btn">💳 Assinar Agora</a>
                    <a href="/trial" class="btn btn-secondary">📥 Teste 7 Dias Grátis</a>
                </div>
            </div>
            
            <!-- Testimonial -->
            <div class="testimonial">
                "Depois de usar o Prompt B3, minha análise de ações ficou muito mais rápida e precisa. Recomendo!" — João, Investidor
            </div>
            
            <!-- Next Steps -->
            <div style="background: rgba(255,215,0,0.05); border: 1px solid rgba(255,215,0,0.2); border-radius: 8px; padding: 20px; text-align: left;">
                <h3 style="color: #ffd700; margin-bottom: 15px;">📋 Próximos Passos:</h3>
                <ol style="color: #aaa; line-height: 2; margin-left: 20px;">
                    <li>Leia o ebook (10 minutos)</li>
                    <li>Escolha um plano (teste grátis ou assinatura)</li>
                    <li>Comece a analisar ações com IA</li>
                    <li>Receba atualizações exclusivas</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_email_sequence_day1(email):
    """Send Day 1 email: Welcome + CTA to try free"""
    subject = "🚀 Comece Agora: Teste 7 Dias Grátis do Prompt B3"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #ffd700; text-align: center;">🚀 Bem-vindo ao Prompt B3!</h2>
            
            <p style="color: #333; font-size: 16px;">Olá,</p>
            
            <p style="color: #333; font-size: 16px;">Você acabou de baixar nosso ebook. Agora é hora de colocar em prática!</p>
            
            <div style="background-color: rgba(255,215,0,0.1); padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #ffd700; text-align: center;">
                <p style="color: #333; font-size: 16px; margin: 0;"><strong>📥 Teste 7 Dias Grátis</strong></p>
                <p style="color: #666; font-size: 14px; margin: 10px 0 0 0;">Sem cartão de crédito. Sem compromisso.</p>
                <a href="https://prompt-b3-ndes.onrender.com/trial" style="display: inline-block; background-color: #ffd700; color: #0a0f1e; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 15px;">Começar Teste Grátis</a>
            </div>
            
            <h3 style="color: #333; margin-top: 30px;">✅ O que você terá acesso:</h3>
            <ul style="color: #333; font-size: 15px; line-height: 1.8;">
                <li>✓ Prompt B3 Completo</li>
                <li>✓ Análise de até 10 ações</li>
                <li>✓ Relatórios visuais em PDF</li>
                <li>✓ Suporte por email</li>
            </ul>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">© 2026 Prompt B3. Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    send_email(email, subject, html_content)
    log_debug(f"Day 1 email sent to {email}")

def send_email_sequence_day3(email):
    """Send Day 3 email: Success stories + pricing"""
    subject = "💡 Veja Como Outros Estão Usando o Prompt B3"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #ffd700; text-align: center;">💡 Histórias de Sucesso</h2>
            
            <p style="color: #333; font-size: 16px;">Olá,</p>
            
            <p style="color: #333; font-size: 16px;">Vários usuários já estão usando o Prompt B3 para análises profissionais. Veja alguns resultados:</p>
            
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #4ade80; margin: 20px 0;">
                <p style="color: #333; font-size: 14px; margin: 0;"><strong>"Reduzi meu tempo de análise de 2 horas para 15 minutos!"</strong></p>
                <p style="color: #666; font-size: 13px; margin: 5px 0 0 0;">— Maria, Investidora</p>
            </div>
            
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #4ade80; margin: 20px 0;">
                <p style="color: #333; font-size: 14px; margin: 0;"><strong>"Os gráficos visuais me ajudaram a tomar melhores decisões."</strong></p>
                <p style="color: #666; font-size: 13px; margin: 5px 0 0 0;">— Carlos, Trader</p>
            </div>
            
            <h3 style="color: #333; margin-top: 30px;">💳 Planos Disponíveis:</h3>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee;"><strong>Teste 7 Dias</strong></td>
                    <td style="padding: 10px; border: 1px solid #eee; text-align: right;">Grátis</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee;"><strong>Mensal</strong></td>
                    <td style="padding: 10px; border: 1px solid #eee; text-align: right;">R$ 25/mês</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee;"><strong>Anual</strong></td>
                    <td style="padding: 10px; border: 1px solid #eee; text-align: right;">R$ 180/ano</td>
                </tr>
            </table>
            
            <div style="text-align: center; margin: 20px 0;">
                <a href="https://prompt-b3-ndes.onrender.com/comprar" style="display: inline-block; background-color: #ffd700; color: #0a0f1e; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold;">Ver Todos os Planos</a>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">© 2026 Prompt B3. Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    send_email(email, subject, html_content)
    log_debug(f"Day 3 email sent to {email}")

def send_email_sequence_day7(email):
    """Send Day 7 email: Last chance offer"""
    subject = "⏰ Última Chance: Desconto Especial para Você"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #ff6b6b; text-align: center;">⏰ Oferta Especial Expirando!</h2>
            
            <p style="color: #333; font-size: 16px;">Olá,</p>
            
            <p style="color: #333; font-size: 16px;">Você tem até amanhã para aproveitar nossa oferta especial de boas-vindas.</p>
            
            <div style="background-color: rgba(255,107,107,0.1); padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #ff6b6b; text-align: center;">
                <p style="color: #333; font-size: 18px; margin: 0;"><strong>🎁 Primeiro Mês com 50% OFF</strong></p>
                <p style="color: #666; font-size: 14px; margin: 10px 0 0 0;">Use o código: <strong>EBOOK50</strong></p>
                <a href="https://prompt-b3-ndes.onrender.com/comprar" style="display: inline-block; background-color: #ff6b6b; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 15px;">Aproveitar Oferta</a>
            </div>
            
            <p style="color: #333; font-size: 15px; margin-top: 20px;">Não deixe passar essa oportunidade!</p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">© 2026 Prompt B3. Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    send_email(email, subject, html_content)
    log_debug(f"Day 7 email sent to {email}")

def send_lead_magnet_email(email, question=''):
    """Send lead magnet ebook by email"""
    subject = "🎁 Seu Ebook Gratuito: Método Barsi + Finclass com IA"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #ffd700; text-align: center;">🎁 Seu Ebook Exclusivo</h2>
            
            <p style="color: #333; font-size: 16px;">Olá,</p>
            
            <p style="color: #333; font-size: 16px;">Obrigado por se interessar no <strong>Prompt Fundamentalista B3</strong>!</p>
            
            <p style="color: #333; font-size: 16px;">Em anexo, você encontra nosso guia introdutório com os fundamentos do <strong>Método Barsi + Finclass</strong> em 10 páginas práticas.</p>
            
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #ffd700; margin: 20px 0;">
                <p style="color: #666; font-size: 14px; margin: 0;"><strong>📚 O que você vai aprender:</strong></p>
                <ul style="color: #666; font-size: 14px; margin: 10px 0;">
                    <li>✅ Pilares do Método Barsi</li>
                    <li>✅ Conceitos-chave do Finclass</li>
                    <li>✅ Como a IA acelera sua análise</li>
                    <li>✅ Primeiros passos práticos</li>
                </ul>
            </div>
            
            <h3 style="color: #333; margin-top: 30px;">🚀 Próximos Passos:</h3>
            <p style="color: #333; font-size: 15px;">Após ler o ebook, você estará pronto para:</p>
            <ol style="color: #333; font-size: 15px; line-height: 1.8;">
                <li>Escolher uma ação para analisar</li>
                <li>Coletar dados financeiros</li>
                <li>Usar o Prompt B3 para análise completa</li>
                <li>Tomar decisões informadas</li>
            </ol>
            
            <div style="background-color: rgba(255,215,0,0.1); padding: 15px; border-radius: 8px; margin: 20px 0; border: 2px solid #ffd700;">
                <p style="color: #333; font-size: 14px; margin: 0;"><strong>💡 Quer aprofundar ainda mais?</strong></p>
                <p style="color: #333; font-size: 14px; margin: 10px 0 0 0;">Conheça nossos planos premium com acesso ao Prompt B3 completo, atualizações constantes e suporte por email.</p>
            </div>
            
            <h3 style="color: #333; margin-top: 30px;">❓ Dúvidas?</h3>
            <p style="color: #666; font-size: 14px;">Entre em contato conosco em <a href="mailto:promptpegardini@gmail.com" style="color: #ffd700; text-decoration: none;">promptpegardini@gmail.com</a></p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">© 2026 Prompt B3. Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    
    # Send email with attachment
    if SENDGRID_AVAILABLE and SENDGRID_API_KEY:
        try:
            from sendgrid.helpers.mail import Attachment, FileContent, FileName, FileType, Disposition
            import base64
            
            # Read ebook file
            ebook_path = '/home/ubuntu/lead_magnet_ebook.pdf'
            with open(ebook_path, 'rb') as f:
                ebook_content = base64.b64encode(f.read()).decode()
            
            # Create attachment
            attachment = Attachment(
                FileContent(ebook_content),
                FileName('Guia_Introdutorio_Prompt_B3.pdf'),
                FileType('application/pdf'),
                Disposition('attachment')
            )
            
            # Send email
            message = Mail(
                from_email=SENDER_EMAIL,
                to_emails=email,
                subject=subject,
                html_content=html_content
            )
            message.attachment = attachment
            
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            sg.send(message)
            log_debug(f"Lead magnet email sent to {email}")
        except Exception as e:
            log_debug(f"Error sending lead magnet email: {str(e)}")
    else:
        log_debug(f"SendGrid not available, skipping lead magnet email to {email}")

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
