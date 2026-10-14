from flask import Flask, render_template, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({"app":"Myblle POS SaaS","status":"online","MZN":"Mozambique"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
