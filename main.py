import os
from flask import Flask, session, redirect, request, render_template_string, jsonify

app = Flask(__name__)
app.secret_key = "myblle-final-2024"

USUARIOS = {
    "admin": {"senha": "myblle123", "papel": "gerente"},
    "gerente": {"senha": "gerente123", "papel": "gerente"},
    "caixa": {"senha": "caixa123", "papel": "operador"},
}

LOGIN_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"><title>Login</title>
<style>body{font-family:Arial;background:#f3f4f6;display:flex;justify-content:center;align-items:center;height:100vh}
.card{background:white;padding:30px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,.1);width:300px}
input{width:100%;padding:10px;margin:8px 0;border-radius:8px;border:1px solid #ccc}
button{width:100%;padding:10px;background:#111827;color:white;border:none;border-radius:8px}</style></head>
<body><div class="card"><h2>MyBlle</h2>
<form method="POST" action="/login">
<input name="user" placeholder="Usuario" required>
<input name="senha" type="password" placeholder="Senha" required>
<button>Entrar</button></form>
<p style="font-size:12px;color:#666">admin / myblle123 = Gerente<br>caixa / caixa123 = Operador</p></div></body></html>"""

@app.route("/")
def index():
    if "user" not in session: return redirect("/login")
    if session.get("papel")=="gerente":
        return f"<h1>Gerente {session['user']}</h1><p>Pode cadastrar e ver relatorios</p><a href='/logout'>Sair</a>"
    else:
        return f"<h1>Caixa {session['user']}</h1><p>Só vende</p><a href='/logout'>Sair</a>"

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="GET": return render_template_string(LOGIN_HTML)
    user=request.form.get("user"); senha=request.form.get("senha")
    u=USUARIOS.get(user)
    if u and u["senha"]==senha:
        session["user"]=user; session["papel"]=u["papel"]; return redirect("/")
    return "Senha errada <a href='/login'>voltar</a>"

@app.route("/logout")
def logout():
    session.clear(); return redirect("/login")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
