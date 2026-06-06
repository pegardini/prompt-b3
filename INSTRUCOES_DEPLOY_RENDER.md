# 🚀 Instruções de Deploy no Render

Guia passo a passo para colocar sua aplicação online no Render (grátis!)

---

## 📋 Pré-requisitos

Você precisa ter:
- ✅ Conta no GitHub (grátis em github.com)
- ✅ Conta no Render (grátis em render.com) — **Você já tem!**
- ✅ Os arquivos prontos (você tem!)

---

## 🎯 Passo 1: Criar Repositório no GitHub

### 1.1 Acesse GitHub
```
https://github.com/new
```

### 1.2 Preencha os dados
- **Repository name**: `prompt-fundamentalista-b3`
- **Description**: `Prompt Fundamentalista B3 com validação de chaves`
- **Public** (deixe público)
- Clique: **Create repository**

### 1.3 Você vai ver instruções
Copie os comandos que aparecem (você vai usar em breve)

---

## 📁 Passo 2: Preparar Arquivos Locais

### 2.1 Crie uma pasta no seu PC
```
Exemplo: C:\Users\Seu Nome\prompt-b3
```

### 2.2 Coloque os arquivos nessa pasta
```
prompt-b3/
├── render_app.py          (servidor Python)
├── requirements.txt       (dependências)
├── render.yaml           (configuração)
└── .gitignore            (arquivo especial)
```

### 2.3 Crie arquivo .gitignore
Crie um arquivo chamado `.gitignore` (com ponto no início) com:
```
__pycache__/
*.pyc
.env
chaves.json
```

---

## 💻 Passo 3: Fazer Upload para GitHub (Windows)

### 3.1 Abra Git Bash
- Clique direito na pasta `prompt-b3`
- Escolha: **Git Bash Here**

### 3.2 Execute estes comandos (um por um)

```bash
# 1. Inicializar repositório
git init

# 2. Adicionar todos os arquivos
git add .

# 3. Fazer commit
git commit -m "Primeira versão do Prompt Fundamentalista B3"

# 4. Renomear branch para main
git branch -M main

# 5. Adicionar origem (substitua SEU_USUARIO e REPO_NAME)
git remote add origin https://github.com/SEU_USUARIO/prompt-fundamentalista-b3.git

# 6. Fazer push (enviar para GitHub)
git push -u origin main
```

### 3.3 Digite suas credenciais
- **Username**: Seu usuário do GitHub
- **Password**: Seu token (veja abaixo como gerar)

---

## 🔑 Passo 4: Gerar Token do GitHub (Se Pedir Senha)

### 4.1 Acesse GitHub Settings
```
https://github.com/settings/tokens
```

### 4.2 Clique: Generate new token
- Name: `render-deploy`
- Expiration: 90 days
- Selecione: `repo` (checkbox)
- Clique: **Generate token**

### 4.3 Copie o token
- Guarde em um lugar seguro
- Use como "senha" no Git Bash

---

## 🌐 Passo 5: Conectar ao Render

### 5.1 Acesse Render
```
https://dashboard.render.com
```

### 5.2 Clique: New +
- Escolha: **Web Service**

### 5.3 Conecte seu GitHub
- Clique: **Connect account**
- Autorize o Render
- Selecione seu repositório: `prompt-fundamentalista-b3`

### 5.4 Configure o serviço
- **Name**: `prompt-fundamentalista-b3`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python render_app.py`
- **Plan**: `Free` (grátis!)

### 5.5 Clique: Create Web Service
- Render vai fazer deploy automático
- Aguarde 2-3 minutos

---

## ✅ Passo 6: Seu Site Está Online!

### 6.1 Você vai receber um link
```
https://prompt-fundamentalista-b3.onrender.com
```

### 6.2 Teste
- Abra o link no navegador
- Veja sua página funcionando!

---

## 🎁 Passo 7: Comprar Domínio (Opcional)

### 7.1 Compre um domínio
- Acesse: namecheap.com ou godaddy.com
- Compre: `seu-site.com` (R$ 30-50/ano)

### 7.2 Configure no Render
- No Render, vá em: **Settings**
- Clique: **Add Custom Domain**
- Digite: `seu-site.com`
- Siga as instruções para apontar o domínio

---

## 🚀 Pronto!

Seu site está online e funcionando!

```
https://seu-site.com
```

---

## 📝 Próximos Passos

1. **Teste a validação de chaves**
   - Gere uma chave com: `python gerar_chave_trial.py seu_email@gmail.com`
   - Acesse seu site
   - Digite a chave
   - Veja se funciona!

2. **Customize o prompt**
   - Edite `render_app.py`
   - Procure: `[AQUI VAI O PROMPT COMPLETO]`
   - Coloque seu prompt lá
   - Faça commit: `git add . && git commit -m "Atualizar prompt" && git push`
   - Render faz deploy automático!

3. **Comece a vender!**
   - Compartilhe seu link
   - Gere chaves para clientes
   - Lucre!

---

## 🆘 Problemas Comuns

### Problema: "Git não encontrado"
**Solução**: Instale Git em git-scm.com

### Problema: "Erro ao fazer push"
**Solução**: Verifique suas credenciais do GitHub

### Problema: "Render não conecta ao GitHub"
**Solução**: Autorize o Render em github.com/settings/applications

### Problema: "Site mostra erro 500"
**Solução**: Verifique os logs no Render (clique em "Logs")

---

## 💡 Dicas

- Sempre faça `git push` depois de fazer mudanças
- Render faz deploy automático após cada push
- Seu site fica online 24/7 (mesmo dormindo!)
- Plano grátis é suficiente para começar

---

**Sucesso!** 🎉

Seu prompt está online e pronto para vender!
