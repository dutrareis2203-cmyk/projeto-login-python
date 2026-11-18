import os
import uuid
from decimal import Decimal, InvalidOperation
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from supabase import create_client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "troque-esta-chave-por-uma-chave-segura")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env")

def novo_cliente():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def cliente_autenticado():
    if not session.get("access_token") or not session.get("refresh_token"):
        return None
    sb = novo_cliente()
    sb.auth.set_session(session["access_token"], session["refresh_token"])
    return sb

def exige_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("access_token"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

@app.route("/")
def inicio():
    if session.get("access_token"):
        return redirect(url_for("painel"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        try:
            resposta = novo_cliente().auth.sign_in_with_password({
                "email": email,
                "password": senha
            })
            session["access_token"] = resposta.session.access_token
            session["refresh_token"] = resposta.session.refresh_token
            session["usuario_email"] = resposta.user.email
            flash("Login realizado com sucesso!", "sucesso")
            return redirect(url_for("painel"))
        except Exception:
            flash("Não foi possível entrar. Confira o e-mail e a senha.", "erro")
    return render_template("login.html")

@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))

@app.route("/recuperar-senha", methods=["GET", "POST"])
def recuperar_senha():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        try:
            novo_cliente().auth.reset_password_for_email(
                email,
                {"redirect_to": url_for("redefinir_senha", _external=True)}
            )
            flash("Se o e-mail estiver cadastrado, você receberá um link para redefinir a senha.", "sucesso")
        except Exception:
            flash("Não foi possível solicitar a recuperação. Confira as configurações do Supabase.", "erro")
    return render_template("recuperar.html")

@app.route("/redefinir-senha")
def redefinir_senha():
    # O JavaScript da página lê os tokens de recuperação que chegam na URL.
    return render_template("redefinir.html")

@app.route("/api/redefinir-senha", methods=["POST"])
def api_redefinir_senha():
    dados = request.get_json(silent=True) or {}
    access_token = dados.get("access_token", "")
    refresh_token = dados.get("refresh_token", "")
    senha = dados.get("senha", "")
    if not access_token or not refresh_token:
        return jsonify(ok=False, mensagem="O link de recuperação é inválido ou expirou."), 400
    if len(senha) < 6:
        return jsonify(ok=False, mensagem="A senha deve ter pelo menos 6 caracteres."), 400
    try:
        sb = novo_cliente()
        sb.auth.set_session(access_token, refresh_token)
        sb.auth.update_user({"password": senha})
        return jsonify(ok=True, mensagem="Senha alterada! Faça login com a nova senha.")
    except Exception:
        return jsonify(ok=False, mensagem="Não foi possível alterar a senha. Solicite um novo link."), 400

@app.route("/painel")
@exige_login
def painel():
    sb = cliente_autenticado()
    try:
        produtos = sb.table("produtos").select("id,nome,preco").order("nome").execute().data or []
        vendas = sb.table("vendas").select("pedido_id,produto_id,quantidade,preco_unitario,subtotal,criado_em").order("criado_em", desc=True).limit(8).execute().data or []
        total = sum((Decimal(str(v["subtotal"])) for v in vendas), Decimal("0.00"))
        return render_template("painel.html", produtos=produtos, vendas=vendas, total=total)
    except Exception:
        flash("Não foi possível carregar os dados. Confira se executou o SQL do projeto no Supabase.", "erro")
        return render_template("painel.html", produtos=[], vendas=[], total=Decimal("0.00"))

@app.route("/vender", methods=["POST"])
@exige_login
def vender():
    sb = cliente_autenticado()
    dados = request.get_json(silent=True) or {}
    itens = dados.get("itens", [])
    if not itens:
        return jsonify(ok=False, mensagem="Adicione pelo menos um produto."), 400

    try:
        produtos = sb.table("produtos").select("id,nome,preco").execute().data or []
        por_id = {str(p["id"]): p for p in produtos}
        pedido_id = str(uuid.uuid4())
        registros = []
        for item in itens:
            produto_id = str(item.get("produto_id", ""))
            quantidade = int(item.get("quantidade", 0))
            if produto_id not in por_id or quantidade < 1 or quantidade > 100:
                return jsonify(ok=False, mensagem="Confira os produtos e as quantidades (de 1 a 100)."), 400
            produto = por_id[produto_id]
            preco = Decimal(str(produto["preco"]))
            subtotal = preco * quantidade
            registros.append({
                "pedido_id": pedido_id,
                "produto_id": int(produto_id),
                "quantidade": quantidade,
                "preco_unitario": str(preco),
                "subtotal": str(subtotal)
            })
        sb.table("vendas").insert(registros).execute()
        return jsonify(ok=True, mensagem="Venda registrada com sucesso!", pedido_id=pedido_id)
    except (ValueError, InvalidOperation):
        return jsonify(ok=False, mensagem="Quantidade ou valor inválido."), 400
    except Exception:
        return jsonify(ok=False, mensagem="Erro ao registrar a venda. Confira as permissões e a conexão com o Supabase."), 400

@app.route("/historico")
@exige_login
def historico():
    sb = cliente_autenticado()
    try:
        vendas = sb.table("vendas").select("id,pedido_id,produto_id,quantidade,preco_unitario,subtotal,criado_em,produtos(nome)").order("criado_em", desc=True).limit(200).execute().data or []
    except Exception:
        vendas = []
        flash("Não foi possível consultar o histórico.", "erro")
    return render_template("historico.html", vendas=vendas)

@app.route("/faturamento")
@exige_login
def faturamento():
    sb = cliente_autenticado()
    try:
        vendas = sb.table("vendas").select("subtotal,criado_em").execute().data or []
        total = sum((Decimal(str(v["subtotal"])) for v in vendas), Decimal("0.00"))
        quantidade = len(vendas)
    except Exception:
        total, quantidade = Decimal("0.00"), 0
        flash("Não foi possível consultar o faturamento.", "erro")
    return render_template("faturamento.html", total=total, quantidade=quantidade)

if __name__ == "__main__":
    app.run(debug=True)
