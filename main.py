import sqlite3, base64, re
from flask import Flask, request, session, redirect, render_template_string, jsonify
app = Flask(__name__)
app.secret_key = "myblle-v9-fixa-tudo"

def get_db(): return sqlite3.connect('myblle.db')
def init_db():
    conn=get_db(); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS lojas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, categoria_loja TEXT, dono TEXT, telefone TEXT, endereco TEXT, cidade TEXT, data TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, senha TEXT, nome TEXT, papel TEXT, loja_id INTEGER, telefone TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS produtos (id TEXT, loja_id INTEGER, nome TEXT, categoria TEXT, preco REAL, stock INTEGER, barras TEXT, codigo_barras TEXT, imagem TEXT, PRIMARY KEY(id, loja_id))")
    c.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, loja_id INTEGER, total REAL, data TEXT, vendedor TEXT)")
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0]==0:
        c.execute("INSERT INTO lojas (nome,categoria_loja,dono,telefone,cidade,data) VALUES ('Loja Demo Matola','Mercearia','Admin','820000000','Matola',datetime('now'))")
        lid=c.lastrowid
        c.execute("INSERT INTO usuarios VALUES ('admin','myblle123','Admin','gerente',?, '')", (lid,))
        c.execute("INSERT INTO usuarios VALUES ('1001','1001','Gerente','gerente',?, '')", (lid,))
        c.execute("INSERT INTO usuarios VALUES ('1002','1002','Caixa','operador',?, '')", (lid,))
    conn.commit(); conn.close()
init_db()

def is_gerente():
    # FIX DEFINITIVO DO ERRO SÓ GERENTE
    if session.get("papel") == "gerente": return True
    if session.get("user") in ["admin","1001","gerente"]: return True
    # busca no banco
    try:
        conn=get_db(); c=conn.cursor()
        c.execute("SELECT papel FROM usuarios WHERE user=?", (session.get("user",""),))
        r=c.fetchone(); conn.close()
        if r and r[0]=="gerente": return True
    except: pass
    return False

LOGIN = """<body style="font-family:Arial;background:#0a3d8f;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0"><div style="background:white;padding:25px;border-radius:16px;width:90%;max-width:360px"><h2 style="color:#0a3d8f;text-align:center">MyBlle Azul</h2><form method="POST" action="/login"><input name="user" value="1001" style="width:100%;padding:14px;border:1px solid #ddd;border-radius:8px"><input name="senha" type="password" value="1001" style="width:100%;padding:14px;margin-top:10px;border:1px solid #ddd;border-radius:8px"><button style="width:100%;padding:14px;background:#0a3d8f;color:white;margin-top:12px;border:none;border-radius:8px">ENTRAR</button></form></div></body>"""

POS = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}.header{background:#0a3d8f;color:white;height:54px;display:flex;align-items:center;padding:0 12px;gap:8px}.main{display:flex;height:calc(100vh - 54px)}.left{width:280px;background:white;border-right:1px solid #ddd;display:flex;flex-direction:column}.produtos{flex:1;background:#f8fafc;display:flex;flex-direction:column}.cats{background:#0a3d8f;display:flex;overflow-x:auto}.cats button{background:transparent;color:white;border:none;padding:10px 14px;font-weight:bold}.cats button.active{background:white;color:#0a3d8f}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;padding:12px;overflow-y:auto}.card{border:1px solid #e2e8f0;padding:8px;border-radius:12px;text-align:center;background:white}.card img{width:100%;height:80px;object-fit:cover;border-radius:8px}.preco{color:#0a3d8f;font-weight:bold}.footer{background:#0a3d8f;color:white;padding:12px}.btn{background:#0a3d8f;color:white;border:none;width:100%;padding:14px;font-size:18px;font-weight:bold;border-radius:10px}.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);display:none;justify-content:center;align-items:center;z-index:100;padding:10px}.modal-content{background:white;padding:20px;border-radius:16px;width:100%;max-width:460px;max-height:95vh;overflow-y:auto}.input{width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;margin:6px 0}.preview{width:100%;height:150px;border:2px dashed #0a3d8f;border-radius:12px;display:flex;align-items:center;justify-content:center;background:#f8fafc;cursor:pointer}.preview img{width:100%;height:100%;object-fit:cover}.menu{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.3);display:none;z-index:200}.menu-box{background:white;width:90%;max-width:600px;height:100%;overflow-y:auto;padding:18px}
</style></head><body>
<div class="header"><button onclick="document.getElementById('menu').style.display='flex'" style="background:transparent;border:none;color:white;font-size:22px">☰</button><b>Loja Demo Matola - {{user}}</b><a href="/logout" style="color:white;margin-left:auto">Sair</a></div>
<div class="main"><div class="left"><div style="padding:10px;font-weight:bold">Carrinho</div><div id="lista" style="flex:1;overflow-y:auto"></div><div class="footer"><span id="total">MT 0.00</span><button class="btn" onclick="abrirPag()">PAGAR</button></div></div>
<div class="produtos"><input id="busca" placeholder="Código de barras / Nome" style="margin:10px;padding:12px;border:1px solid #ccc;border-radius:10px" oninput="render()"><div class="cats" id="cats"></div><div class="grid" id="grid"></div></div></div>

<div class="modal" id="modalProd"><div class="modal-content">
<h3 style="color:#0a3d8f">📦 Cadastrar com Imagem + Código de Barras</h3>
<form id="formProd">
<div class="preview" id="preview" onclick="document.getElementById('fileImg').click()"><span id="previewTxt">📷 Clique para foto<br>do produto</span><img id="previewImg" style="display:none"></div>
<input type="file" id="fileImg" accept="image/*" capture="environment" style="display:none" onchange="previewFile()">
<input id="p_id" required placeholder="Código (ex: 23bl12-107)" class="input">
<input id="p_nome" required placeholder="Nome (ex: Copo de Sorvete)" class="input">
<div style="display:flex;gap:8px"><input id="p_preco" type="text" required placeholder="Preço ex: 150" class="input"><input id="p_stock" type="text" required placeholder="Stock ex: 100" class="input"></div>
<input id="p_barra" placeholder="Código de barras ex: 123456" class="input">
<input id="p_cat" placeholder="Categoria ex: Mercadoria" value="Mercearia" class="input">
<div style="display:flex;gap:10px;margin-top:10px"><button type="button" onclick="document.getElementById('modalProd').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button type="submit" style="flex:1;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Salvar</button></div>
</form>
</div></div>

<div class="modal" id="modalQtd"><div class="modal-content"><div id="qtdImg" style="text-align:center"></div><h3 id="mNome"></h3><p id="mPreco" style="color:#0a3d8f;font-weight:bold"></p><input id="inputQtd" type="number" value="1" style="width:100%;padding:14px;font-size:20px;text-align:center;border:2px solid #0a3d8f;border-radius:10px;margin:10px 0"><div style="display:flex;gap:10px"><button onclick="document.getElementById('modalQtd').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="conf()" style="flex:1;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Add</button></div></div></div>
<div class="modal" id="modalPag"><div class="modal-content"><h3>Pagar</h3><div>Total: <b id="pagTotal">MT 0</b></div><input id="pagRec" style="width:100%;padding:14px;font-size:20px;border:2px solid #0a3d8f;border-radius:10px;margin:10px 0" oninput="troco()"><div>Troco: <b id="pagTroco">MT 0</b></div><div style="display:flex;gap:10px;margin-top:10px"><button onclick="document.getElementById('modalPag').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="finalizar()" style="flex:1;padding:12px;background:#16a34a;color:white;border:none;border-radius:10px">Confirmar</button></div></div></div>
<div class="menu" id="menu" onclick="if(event.target==this) this.style.display='none'"><div class="menu-box"><h3 style="color:#0a3d8f">Menu - {{loja_nome}}</h3><div style="border:2px solid #0a3d8f;background:#dbeafe;padding:14px;border-radius:12px;font-weight:bold;margin:15px 0" onclick="document.getElementById('modalProd').style.display='flex';document.getElementById('menu').style.display='none'">➕ Cadastrar Produto com Imagem e Código de Barras</div><div style="border:1px solid #e2e8f0;padding:12px;border-radius:12px;margin-bottom:10px" onclick="window.location='/api/relatorio'">📊 Relatório</div><button onclick="document.getElementById('menu').style.display='none'" style="width:100%;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Fechar</button></div></div>
<script>
let prods=[]; let car=[]; let sel=null; let cat='Todos'; let imgBase64="";
async function load(){ prods=await (await fetch('/api/produtos')).json(); renderCats(); render(); }
function renderCats(){ let cats=['Todos',...new Set(prods.map(p=>p.categoria))]; document.getElementById('cats').innerHTML=cats.map(c=>`<button class="${c==cat?'active':''}" onclick="cat='${c}';render()">${c}</button>`).join(''); }
function render(){ let b=document.getElementById('busca').value.toLowerCase(); let f=prods.filter(p=>(cat=='Todos'||p.categoria==cat)&&(!b||p.nome.toLowerCase().includes(b)||p.id.toLowerCase().includes(b)||(p.codigo_barras&&p.codigo_barras.toLowerCase().includes(b)))); document.getElementById('grid').innerHTML=f.map(p=>`<div class="card" onclick="openQtd('${p.id}')">${p.imagem?`<img src="${p.imagem}">`:`<div style="height:80px;display:flex;align-items:center;justify-content:center;font-size:30px">📦</div>`}<b>${p.id}<br>${p.nome}</b><div class="preco">MT ${p.preco}</div><div style="font-size:9px">${p.codigo_barras||''} Stock:${p.stock}</div></div>`).join(''); }
function openQtd(id){ sel=prods.find(p=>p.id==id); document.getElementById('mNome').innerText=sel.nome; document.getElementById('mPreco').innerText='MT '+sel.preco; document.getElementById('qtdImg').innerHTML=sel.imagem?`<img src="${sel.imagem}" style="width:100px;height:100px;object-fit:cover;border-radius:12px">`:''; document.getElementById('inputQtd').value=1; document.getElementById('modalQtd').style.display='flex'; }
function conf(){ let q=parseInt(document.getElementById('inputQtd').value)||1; car.push({id:sel.id,nome:sel.nome,preco:sel.preco,qtd:q}); draw(); document.getElementById('modalQtd').style.display='none'; }
function draw(){ let t=0; document.getElementById('lista').innerHTML=car.map(c=>{t+=c.preco*c.qtd; return `<div style="display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #eee"><span>${c.id} x${c.qtd}</span><span>MT ${(c.preco*c.qtd).toFixed(2)}</span></div>`}).join(''); document.getElementById('total').innerText='MT '+t.toFixed(2); document.getElementById('pagTotal').innerText='MT '+t.toFixed(2); }
function abrirPag(){ if(car.length==0){alert('Carrinho vazio');return} document.getElementById('modalPag').style.display='flex'; document.getElementById('pagRec').value=document.getElementById('total').innerText.replace('MT',''); troco(); }
function troco(){ let tot=parseFloat(document.getElementById('pagTotal').innerText.replace('MT',''))||0; let rec=parseFloat(document.getElementById('pagRec').value.replace(/[^0-9.]/g,''))||0; document.getElementById('pagTroco').innerText='MT '+(rec-tot).toFixed(2); }
async function finalizar(){ let tot=parseFloat(document.getElementById('pagTotal').innerText.replace('MT','')); let rec=parseFloat(document.getElementById('pagRec').value.replace(/[^0-9.]/g,''))||0; await fetch('/api/vender',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({total:tot,recebido:rec,troco:rec-tot,itens:car})}); alert('Venda OK'); car=[]; draw(); document.getElementById('modalPag').style.display='none'; }
function previewFile(){ let file=document.getElementById('fileImg').files[0]; if(file){ let r=new FileReader(); r.onload=function(e){ imgBase64=e.target.result; document.getElementById('previewImg').src=imgBase64; document.getElementById('previewImg').style.display='block'; document.getElementById('previewTxt').style.display='none'; }; r.readAsDataURL(file); } }
document.getElementById('formProd').addEventListener('submit', async function(e){
 e.preventDefault();
 let preco=document.getElementById('p_preco').value.replace(/[^0-9.]/g,'')||'0';
 let stock=document.getElementById('p_stock').value.replace(/[^0-9]/g,'')||'0';
 let body={id:document.getElementById('p_id').value, nome:document.getElementById('p_nome').value, preco:preco, stock:stock, codigo_barras:document.getElementById('p_barra').value, categoria:document.getElementById('p_cat').value, imagem:imgBase64};
 let res=await fetch('/api/produtos',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 if(res.ok){ alert('✅ Copo de Sorvete salvo com foto!'); document.getElementById('modalProd').style.display='none'; load(); } else { let j=await res.json(); alert('Erro: '+(j.erro||'falha')); }
});
load();
</script></body></html>
"""

@app.route("/")
def index():
    if "user" not in session: return redirect("/login")
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT loja_id FROM usuarios WHERE user=?", (session["user"],))
    r=c.fetchone()
    if not r: session.clear(); return redirect("/login")
    c.execute("SELECT nome FROM lojas WHERE id=?", (r[0],))
    ln=c.fetchone()
    conn.close()
    return render_template_string(POS, user=session["user"], loja_nome=ln[0] if ln else "Loja")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="GET": return render_template_string(LOGIN)
    u=request.form.get("user"); s=request.form.get("senha")
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT user,papel,loja_id FROM usuarios WHERE user=? AND senha=?", (u,s))
    row=c.fetchone(); conn.close()
    if row: session["user"]=row[0]; session["papel"]=row[1]; session["loja_id"]=row[2]; return redirect("/")
    return "Login inválido <a href='/login'>Voltar</a>"

@app.route("/logout")
def logout(): session.clear(); return redirect("/login")

@app.route("/api/produtos", methods=["GET","POST"])
def produtos():
    if "loja_id" not in session: return jsonify([]),401
    loja_id=session["loja_id"]
    conn=get_db(); c=conn.cursor()
    if request.method=="POST":
        if not is_gerente(): return jsonify({"erro":"Só Gerente! Mas você está como "+str(session.get('user'))+" papel="+str(session.get('papel'))}),403
        # Aceita JSON e form-data
        if request.is_json: d=request.json
        else: d=request.form.to_dict()
        pid=d.get("id","").strip()
        if not pid: return jsonify({"erro":"Código vazio"}),400
        nome=d.get("nome","").strip() or pid
        preco=re.sub(r'[^0-9.]','', str(d.get("preco","0"))) or '0'
        stock=re.sub(r'[^0-9]','', str(d.get("stock","0"))) or '0'
        barra=d.get("codigo_barras","") or d.get("barras","")
        cat=d.get("categoria","Mercearia")
        img=d.get("imagem","")
        c.execute("INSERT OR REPLACE INTO produtos (id,loja_id,nome,categoria,preco,stock,barras,codigo_barras,imagem) VALUES (?,?,?,?,?,?,?,?,?)",
                  (pid,loja_id,nome,cat,float(preco),int(stock),barra,barra,img))
        conn.commit(); conn.close()
        return jsonify({"ok":True})
    c.execute("SELECT id,nome,categoria,preco,stock,codigo_barras,imagem FROM produtos WHERE loja_id=?", (loja_id,))
    rows=c.fetchall(); conn.close()
    return jsonify([{"id":r[0],"nome":r[1],"categoria":r[2],"preco":r[3],"stock":r[4],"codigo_barras":r[5],"imagem":r[6]} for r in rows])

@app.route("/api/vender", methods=["POST"])
def vender():
    d=request.json; conn=get_db(); c=conn.cursor()
    c.execute("INSERT INTO vendas (loja_id,total,data,vendedor) VALUES (?,?,datetime('now'),?)", (session["loja_id"],d["total"],session.get("user","")))
    for it in d.get("itens",[]): c.execute("UPDATE produtos SET stock=stock-? WHERE id=? AND loja_id=?", (it["qtd"],it["id"],session["loja_id"]))
    conn.commit(); conn.close(); return jsonify({"ok":True})

@app.route("/api/relatorio")
def rel(): return "<h2>Relatório</h2><a href='/'>Voltar</a>"

if __name__=="__main__": app.run(host="0.0.0.0", port=10000)
