from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "app": "Myblle POS SaaS",
        "status": "online",
        "versao": "Mozambique MZN",
        "mensagem": "Servidor no ar! Próximo passo: PDV bonito"
    })

@app.route('/api/teste')
def teste():
    return jsonify({"ok": True})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
