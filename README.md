# Lanchonete — Python + Flask + Supabase

Aplicação web simples para entrar com uma conta Supabase, consultar produtos, registrar vendas, ver o histórico e consultar o faturamento.

## 1. Requisitos

- Python 3.10 ou mais recente
- VS Code
- Projeto criado no Supabase

## 2. Preparar o banco de dados

1. Abra seu projeto no Supabase.
2. Entre em **SQL Editor**.
3. Clique em **New query**.
4. Abra o arquivo `schema.sql`, copie todo o conteúdo e cole no SQL Editor.
5. Clique em **Run**. As tabelas `produtos` e `vendas` e os produtos iniciais serão criados.

## 3. Configurar o projeto no VS Code

Abra a pasta `lanchonete_supabase` no VS Code e abra o terminal.

Crie o ambiente virtual:

```bash
python -m venv .venv
```

Ative no Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Instale as bibliotecas:

```bash
pip install -r requirements.txt
```

Copie `.env.example` e renomeie a cópia para `.env`. Preencha com a URL e a chave **publishable** do seu projeto Supabase (Project Settings > API Keys). Não coloque a chave `service_role` no navegador ou neste projeto.

Gere uma chave aleatória para `FLASK_SECRET_KEY` ou troque o valor de exemplo por uma sequência longa e privada.

## 4. Criar usuário para entrar

No Supabase, abra **Authentication > Users > Add user** e crie um usuário com e-mail e senha. Se a confirmação de e-mail estiver ativada, confirme o e-mail antes de entrar.

## 5. Configurar a recuperação de senha

No Supabase, abra **Authentication > URL Configuration** e adicione a URL local aos Redirect URLs:

`http://127.0.0.1:5000/redefinir-senha`

Para testar a recuperação, rode o site, clique em “Esqueci minha senha” e informe o e-mail cadastrado. O link enviado por e-mail deverá retornar para a página de redefinição.

## 6. Executar

No terminal do VS Code:

```bash
python app.py
```

Abra no navegador:

`http://127.0.0.1:5000`

## O que o projeto faz

- Login com Supabase Auth
- Solicitação de recuperação de senha por e-mail
- Redefinição de senha pelo link recebido
- Consulta dos produtos cadastrados
- Carrinho com quantidades e cálculo de total
- Registro de vendas no Supabase
- Histórico das vendas
- Consulta do faturamento

## Observações

- O projeto usa a chave `sb_publishable` no arquivo `.env`. Nunca compartilhe sua senha, tokens ou chave `service_role`.
- O faturamento e o histórico mostram os registros que o usuário autenticado tem permissão para consultar.
- Para publicar na internet, configure variáveis de ambiente e uma URL HTTPS no provedor de hospedagem; não use `debug=True` em produção.
