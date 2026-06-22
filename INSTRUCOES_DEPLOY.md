# Instruções de Deploy — Prompt Fundamentalista B3

## O que fazer com estes arquivos

### Passo 1 — Copie os arquivos para sua pasta local

Copie **todos** estes arquivos para a pasta `C:\prompt-b3` no seu computador Windows:

```
render_app.py
requirements.txt
runtime.txt
PROMPT_MESTRE_HIBRIDO_B3.md
video_demo_final.mp4
.gitignore
```

> ⚠️ **Importante:** O arquivo `video_demo_final.mp4` tem 13MB. Pode demorar um pouco para fazer upload.

---

### Passo 2 — Abra o Terminal (Git Bash ou CMD) na pasta C:\prompt-b3

```bash
cd C:\prompt-b3
```

---

### Passo 3 — Faça o commit e push para o GitHub

```bash
git add .
git commit -m "feat: site multi-paginas com geracao de chaves e video"
git push origin main
```

---

### Passo 4 — O Render vai fazer o deploy automaticamente

Aguarde 2-3 minutos. O Render detecta o push e faz o deploy sozinho.

---

### Passo 5 — Verifique as configurações no Render

Acesse https://dashboard.render.com e confirme:

| Configuração | Valor |
|---|---|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python render_app.py` |
| Python Version | 3.11.0 |

---

### Passo 6 — Configure a variável de ambiente (opcional)

No Render, em **Environment**, adicione:

| Variável | Valor |
|---|---|
| `ADMIN_SENHA` | `Pe190759@` |

> Se não configurar, a senha padrão `Pe190759@` já está no código.

---

## Páginas do Site

Após o deploy, acesse:

| Página | URL |
|---|---|
| Home | `https://prompt-b3.onrender.com/` |
| Teste 7 Dias | `https://prompt-b3.onrender.com/trial` |
| Comprar 1 Ano | `https://prompt-b3.onrender.com/comprar` |
| Admin | `https://prompt-b3.onrender.com/admin?senha=Pe190759@` |

---

## Como funciona o Admin

1. Acesse `/admin?senha=Pe190759@`
2. Veja as compras pendentes (clientes que preencheram o formulário)
3. Após confirmar o PIX, clique em **"Gerar Link"**
4. Copie o link gerado e envie por e-mail para o cliente
5. O cliente clica no link e baixa o prompt com a chave de 1 ano

---

## Dúvidas?

Envie e-mail para: promptpegardini@gmail.com
