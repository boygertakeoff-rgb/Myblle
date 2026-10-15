from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return """
    <body style="font-family:Arial;background:#0a3d8f;color:white;text-align:center;padding:40px">
    <h1>MyBlle Azul - ONLINE</h1>
    <p>Deploy funcionou!</p>
    <p>Login: dono / dono123</p>
    <a href="/login" style="background:white;color:#0a3d8f;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:bold">ENTRAR</a>
    </body>
    """

@app.route("/login")
def login():
    return """
    <body style="font-family:Arial;background:#0a3d8f;display:flex;justify-content:center;align-items:center;height:100vh;margin:0">
    <div style="background:white;padding:25px;border-radius:16px;width:90%;max-width:360px;text-align:center">
    <h2 style="color:#0a3d8f">MyBlle Azul</h2>
    <p style="color:green;font-weight:bold">DEPLOY OK!</p>
    <p>Agora vou colocar o sistema completo.</p>
    <a href="/" style="color:#0a3d8f">Voltar</a>
    </div></body>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
