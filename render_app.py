import os
import secrets
import stripe
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
CUSTOMERS_FILE = os.path.join(BASE_DIR, 'customers.json')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = 'promptpegardini@gmail.com'

def log_debug(message):
    """Log debug messages"""
    print(f"[DEBUG] {message}")

def load_customers():
    """Load customers from JSON file"""
    if os.path.exists(CUSTOMERS_FILE):
        with open(CUSTOMERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_customers(customers):
    """Save customers to JSON file"""
    with open(CUSTOMERS_FILE, 'w') as f:
        json.dump(customers, f, indent=2)

def send_email(to_email, subject, html_content):
    """Send email using SendGrid"""
    if not SENDGRID_AVAILABLE or not SENDGRID_API_KEY:
        log_debug(f"SendGrid not available. Would send to {to_email}: {subject}")
        return
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        response = sg.send(message)
        log_debug(f"Email sent to {to_email}: {response.status_code}")
    except Exception as e:
        log_debug(f"Error sending email: {str(e)}")

def send_email_sequence_day1(email):
    """Send Day 1 email: Welcome + Teste"""
    subject = "🚀 Bem-vindo! Comece Seu Teste 7 Dias Grátis"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #ffd700; text-align: center;">🚀 Bem-vindo!</h2>
            
            <p style="color: #333; font-size: 16px;">Olá,</p>
            
            <p style="color: #333; font-size: 16px;">Obrigado por se interessar em nosso produto! Você tem <strong>7 dias grátis</strong> para testar toda a funcionalidade.</p>
            
            <div style="background-color: rgba(255,215,0,0.1); padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #ffd700; text-align: center;">
                <p style="color: #333; font-size: 18px; margin: 0;"><strong>🎁 Teste 7 Dias Grátis</strong></p>
                <p style="color: #666; font-size: 14px; margin: 10px 0 0 0;">Acesso completo a todas as funcionalidades</p>
                <a href="https://prompt-b3-ndes.onrender.com/trial" style="display: inline-block; background-color: #ffd700; color: #0a0f1e; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 15px;">Iniciar Teste Agora</a>
            </div>
            
            <p style="color: #333; font-size: 15px; margin-top: 20px;">Durante os 7 dias, você poderá:</p>
            <ul style="color: #333; font-size: 15px;">
                <li>✅ Acessar o prompt completo</li>
                <li>✅ Gerar relatórios visuais</li>
                <li>✅ Analisar quantas ações quiser</li>
                <li>✅ Exportar em PDF</li>
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
    """Send Day 3 email: Social proof + Preços"""
    subject = "💡 Veja Como Outros Estão Usando"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #ffd700; text-align: center;">💡 Histórias de Sucesso</h2>
            
            <p style="color: #333; font-size: 16px;">Olá,</p>
            
            <p style="color: #333; font-size: 16px;">Seus 7 dias de teste estão passando rápido! Veja como outros investidores estão usando nosso produto para tomar melhores decisões.</p>
            
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #ffd700; margin: 20px 0; border-radius: 8px;">
                <p style="color: #666; font-size: 14px; margin: 0;"><strong>📊 Análises Profissionais em Minutos</strong></p>
                <p style="color: #666; font-size: 14px; margin: 10px 0 0 0;">Usuários relatam que conseguem fazer análises que levavam horas em apenas 5 minutos.</p>
            </div>
            
            <h3 style="color: #333; margin-top: 30px;">💰 Planos Disponíveis</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #f0f0f0;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Teste</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>R$ 0</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">7 dias</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Mensal</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>R$ 25</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Renovável</td>
                </tr>
                <tr style="background-color: #f0f0f0;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Anual</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>R$ 180</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Melhor valor</td>
                </tr>
            </table>
            
            <a href="https://prompt-b3-ndes.onrender.com/comprar" style="display: inline-block; background-color: #ffd700; color: #0a0f1e; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 20px;">Ver Planos</a>
            
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
    subject = "🎁 Seu Ebook Gratuito: Análise Fundamentalista com IA"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #ffd700; text-align: center;">🎁 Seu Ebook Exclusivo</h2>
            
            <p style="color: #333; font-size: 16px;">Olá,</p>
            
            <p style="color: #333; font-size: 16px;">Obrigado por se interessar em nosso produto!</p>
            
            <p style="color: #333; font-size: 16px;">Em anexo, você encontra nosso guia introdutório com os fundamentos da <strong>Análise Fundamentalista com IA</strong> em 10 páginas práticas.</p>
            
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #ffd700; margin: 20px 0;">
                <p style="color: #666; font-size: 14px; margin: 0;"><strong>📚 O que você vai aprender:</strong></p>
                <ul style="color: #666; font-size: 14px; margin: 10px 0;">
                    <li>✅ Pilares da Análise Fundamentalista</li>
                    <li>✅ Indicadores-chave de qualidade</li>
                    <li>✅ Como a IA acelera sua análise</li>
                    <li>✅ Primeiros passos práticos</li>
                </ul>
            </div>
            
            <h3 style="color: #333; margin-top: 30px;">🚀 Próximos Passos:</h3>
            <p style="color: #333; font-size: 15px;">Após ler o ebook, você estará pronto para:</p>
            <ol style="color: #333; font-size: 15px; line-height: 1.8;">
                <li>Escolher uma ação para analisar</li>
                <li>Coletar dados financeiros</li>
                <li>Usar nossa ferramenta para análise completa</li>
                <li>Tomar decisões informadas</li>
            </ol>
            
            <div style="background-color: rgba(255,215,0,0.1); padding: 15px; border-radius: 8px; margin: 20px 0; border: 2px solid #ffd700;">
                <p style="color: #333; font-size: 14px; margin: 0;"><strong>💡 Quer aprofundar ainda mais?</strong></p>
                <p style="color: #333; font-size: 14px; margin: 10px 0 0 0;">Conheça nossos planos premium com acesso completo, atualizações constantes e suporte por email.</p>
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
                FileName('Guia_Introdutorio_Analise_Fundamentalista.pdf'),
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
            response = sg.send(message)
            log_debug(f"Lead magnet email sent to {email}: {response.status_code}")
        except Exception as e:
            log_debug(f"Error sending lead magnet email: {str(e)}")
    else:
        log_debug(f"SendGrid not available. Would send ebook to {email}")

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0f1e; color: #ffffff; min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
h1 { color: #ffd700; font-size: 2.5em; margin-bottom: 20px; text-align: center; }
h2 { color: #ffd700; font-size: 1.8em; margin: 40px 0 20px; }
h3 { color: #ffd700; margin: 20px 0 10px; }
p { line-height: 1.6; color: #ccc; margin-bottom: 15px; }
.card { background: #1a2332; border: 1px solid rgba(255,215,0,0.2); border-radius: 12px; padding: 25px; margin-bottom: 20px; }
.card-destaque { background: #1a2332; border: 2px solid #ffd700; }
.btn { display: inline-block; padding: 12px 25px; background: #ffd700; color: #0a0f1e; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; text-decoration: none; }
.btn:hover { background: #ffed4e; }
.btn-gold { background: #ffd700; color: #0a0f1e; }
.btn-green { background: #4ade80; color: #0a0f1e; }
@media (max-width: 768px) { h1 { font-size: 1.8em; } h2 { font-size: 1.3em; } .container { padding: 20px; } }
"""

NAV = """
<nav style="background: #1a2332; padding: 15px 20px; border-bottom: 1px solid rgba(255,215,0,0.2);">
    <div style="max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">
        <a href="/" style="color: #ffd700; text-decoration: none; font-weight: bold; font-size: 1.2em;">📈 Prompt B3</a>
        <div style="display: flex; gap: 20px;">
            <a href="/" style="color: #ccc; text-decoration: none;">Home</a>
            <a href="/trial" style="color: #ccc; text-decoration: none;">Teste</a>
            <a href="/comprar" style="color: #ccc; text-decoration: none;">Comprar</a>
            <a href="/admin?password=admin123" style="color: #ccc; text-decoration: none;">Admin</a>
        </div>
    </div>
</nav>
"""

FOOTER = """
<footer style="background: #1a2332; border-top: 1px solid rgba(255,215,0,0.2); padding: 30px 20px; margin-top: 60px;">
    <div style="max-width: 1200px; margin: 0 auto;">
        <p>&copy; 2026 Prompt Fundamentalista B3 | promptpegardini@gmail.com</p>
        <p style="font-size: 0.85em; margin-top: 10px;"><strong>⚠️ Aviso de Independência:</strong> Este produto é uma obra educacional independente. Não é oficial, afiliado, autorizado, patrocinado, licenciado, aprovado ou endossado por Luiz Barsi Filho, Finclass, B3 ou qualquer terceiro. Os critérios, filtros, pontuações e relatórios foram desenvolvidos de forma independente.</p>
        <p style="font-size: 0.85em; margin-top: 10px;"><strong>⚖️ Aviso Legal:</strong> Este produto é um prompt de IA para fins educacionais exclusivamente. Não constitui recomendação, aconselhamento ou sugestão de investimento. A IA pode cometer erros. Sempre verifique informações em fontes oficiais e consulte especialistas antes de tomar decisões financeiras.</p>
        <p style="font-size: 0.85em; margin-top: 10px;"><strong>🤖 Sobre IA:</strong> ChatGPT, Claude e Gemini são marcas de seus respectivos titulares. Este produto não possui afiliação, patrocínio ou endosso dessas plataformas.</p>
        <p style="font-size: 0.85em; margin-top: 10px;"><a href="/terms" style="color: #ffd700; text-decoration: none;">Termos de Uso Completos</a></p>
    </div>
</footer>
"""

@app.route('/')
def home():
    """Home page - Prompt B3 propaganda and features"""
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
                <strong style="color: #ff9800;">⚠️ Projeto Independente:</strong> Este produto é uma obra educacional independente. Não é oficial, afiliado, autorizado, patrocinado, licenciado, aprovado ou endossado por Luiz Barsi Filho, Finclass, B3 ou qualquer terceiro. Os critérios, filtros, pontuações e relatórios foram desenvolvidos de forma independente.
            </div>
            
            <div class="card card-destaque" style="text-align: center; padding: 50px 30px; margin-bottom: 40px;">
                <p style="font-size: 1.3em; margin-bottom: 15px; color: #ffd700; font-weight: bold;">Análise Inteligente de Ações B3 com IA</p>
                <p style="font-size: 1.1em; margin-bottom: 30px; color: #ccc;">Análise Fundamentalista Híbrida | Funciona com ChatGPT, Claude e Gemini</p>
                <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                    <a href="/trial" class="btn btn-gold" style="padding: 16px 40px; font-size: 1.1em; text-decoration: none;">📥 Teste 7 Dias Grátis</a>
                    <a href="/comprar" class="btn btn-green" style="padding: 16px 40px; font-size: 1.1em; text-decoration: none;">💳 Assinar Agora</a>
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
                    <p>Análise Fundamentalista + Veredito</p>
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
                    <img src="/static/ebook_cover.webp" style="max-width: 100%; border-radius: 8px; box-shadow: 0 8px 20px rgba(0,0,0,0.3);">
                </div>
                <div>
                    <h3>📖 Guia Introdutório Exclusivo</h3>
                    <p>Aprenda os fundamentos da Análise Fundamentalista com IA em 10 páginas práticas e diretas.</p>
                    <p style="margin-top: 20px; color: #ffd700; font-weight: bold;">Receba o ebook + atualizações exclusivas sobre novas versões do prompt.</p>
                    <a href="/lead-magnet" class="btn btn-gold" style="display: inline-block; padding: 14px 30px; margin-top: 20px; text-decoration: none;">🎁 Receber Ebook Grátis</a>
                </div>
            </div>
        </div>
        {FOOTER}
    </body>
    </html>
    """
    return html

@app.route('/terms')
def terms():
    """Terms of Use page"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Termos de Uso - Prompt B3</title>
        <style>{CSS}</style>
    </head>
    <body>
        {NAV}
        <div class="container">
            <h1>📋 Termos de Uso</h1>
            
            <div class="card">
                <h2>1. Independência e Não-Afiliação</h2>
                <p>Este produto é uma obra educacional independente. Não é oficial, afiliado, autorizado, patrocinado, licenciado, aprovado ou endossado por:</p>
                <ul style="color: #ccc; margin-left: 20px;">
                    <li>Luiz Barsi Filho</li>
                    <li>Finclass</li>
                    <li>B3 (Bolsa de Valores do Brasil)</li>
                    <li>ChatGPT, Claude, Gemini ou qualquer plataforma de IA</li>
                    <li>Qualquer terceiro mencionado</li>
                </ul>
                <p style="margin-top: 15px;">Os critérios, filtros, pontuações e relatórios foram desenvolvidos de forma independente.</p>
            </div>
            
            <div class="card">
                <h2>2. Isenção de Responsabilidade - Investimento</h2>
                <p><strong>Este produto NÃO constitui:</strong></p>
                <ul style="color: #ccc; margin-left: 20px;">
                    <li>Recomendação de investimento</li>
                    <li>Aconselhamento financeiro</li>
                    <li>Sugestão de compra ou venda de ações</li>
                    <li>Garantia de retorno financeiro</li>
                </ul>
                <p style="margin-top: 15px;">Sempre consulte especialistas e fontes oficiais antes de tomar qualquer decisão de investimento. Você é responsável por suas decisões financeiras.</p>
            </div>
            
            <div class="card">
                <h2>3. Limitações de Responsabilidade - IA</h2>
                <p>Inteligência artificial pode cometer erros, incluindo:</p>
                <ul style="color: #ccc; margin-left: 20px;">
                    <li>Cálculos incorretos</li>
                    <li>Interpretações equivocadas de dados</li>
                    <li>Alucinações ou informações fabricadas</li>
                    <li>Análises incompletas ou tendenciosas</li>
                </ul>
                <p style="margin-top: 15px;">Sempre verifique os resultados em fontes oficiais e não confie cegamente em análises geradas por IA.</p>
            </div>
            
            <div class="card">
                <h2>4. Uso Educacional</h2>
                <p>Este produto é destinado exclusivamente para fins educacionais. O usuário concorda em:</p>
                <ul style="color: #ccc; margin-left: 20px;">
                    <li>Usar o produto apenas para aprender conceitos de análise fundamentalista</li>
                    <li>Não usar para fins comerciais sem autorização</li>
                    <li>Não reproduzir ou distribuir o conteúdo sem permissão</li>
                    <li>Respeitar direitos autorais e propriedade intelectual</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>5. Dados Pessoais</h2>
                <p>Coletamos apenas:</p>
                <ul style="color: #ccc; margin-left: 20px;">
                    <li>Email (para envio de ebook e atualizações)</li>
                    <li>Informações de pagamento (processadas por Stripe)</li>
                    <li>Dados de uso (para melhorar o serviço)</li>
                </ul>
                <p style="margin-top: 15px;">Seus dados não serão vendidos a terceiros. Usamos apenas para fornecer o serviço e comunicações.</p>
            </div>
            
            <div class="card">
                <h2>6. Cancelamento de Assinatura</h2>
                <p>Você pode cancelar sua assinatura a qualquer momento. Após o cancelamento:</p>
                <ul style="color: #ccc; margin-left: 20px;">
                    <li>Você perderá acesso ao prompt e funcionalidades premium</li>
                    <li>Não há reembolso por dias não utilizados</li>
                    <li>Você pode reativar a assinatura a qualquer momento</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>7. Referências e Inspiração</h2>
                <p>Este produto faz referências educacionais a conceitos e estratégias de investimento. Essas referências são:</p>
                <ul style="color: #ccc; margin-left: 20px;">
                    <li>Exclusivamente para fins contextuais</li>
                    <li>Não representam afiliação ou endosso</li>
                    <li>Utilizadas como inspiração conceitual</li>
                    <li>Desenvolvidas de forma independente</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>8. Modificações dos Termos</h2>
                <p>Reservamos o direito de modificar estes termos a qualquer momento. Mudanças significativas serão comunicadas por email.</p>
            </div>
            
            <div class="card">
                <h2>9. Contato</h2>
                <p>Para dúvidas sobre estes termos, entre em contato:</p>
                <p style="margin-top: 10px;"><strong>Email:</strong> promptpegardini@gmail.com</p>
            </div>
            
            <div class="card" style="background: rgba(255,100,0,0.1); border: 1px solid rgba(255,100,0,0.3);">
                <p style="color: #ff9800;"><strong>⚠️ Última atualização:</strong> 13 de julho de 2026</p>
                <p style="color: #ff9800; margin-top: 10px;"><strong>Ao usar este produto, você concorda com todos os termos acima.</strong></p>
            </div>
        </div>
        {FOOTER}
    </body>
    </html>
    """
    return html

@app.route('/trial', methods=['GET', 'POST'])
