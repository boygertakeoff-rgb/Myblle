import sqlite3, base64, re
from flask import Flask, request, session, redirect, render_template_string, jsonify
app = Flask(__name__)
app.secret_key = "myblle-v11-completo"

def get_db(): return sqlite3.connect('myblle.db')
def init_db():
    conn=get_db(); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS lojas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, categoria_loja TEXT, dono TEXT, telefone TEXT, cidade TEXT, data TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, senha TEXT, nome TEXT, papel TEXT, loja_id INTEGER, telefone TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS produtos (id TEXT, loja_id INTEGER, nome TEXT, categoria TEXT, preco REAL, stock INTEGER, codigo_barras TEXT, imagem TEXT, PRIMARY KEY(id, loja_id))")
    c.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, loja_id INTEGER, total REAL, recebido REAL, troco REAL, data TEXT, vendedor TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS venda_itens (venda_id INTEGER, produto_id TEXT, qtd INTEGER, preco REAL)")
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0]==0:
        c.execute("INSERT INTO lojas (nome,categoria_loja,dono,telefone,cidade,data) VALUES ('Loja Demo Matola','Mercearia','Admin','820000000','Matola',datetime('now'))")
        lid=c.lastrowid
        c.execute("INSERT INTO usuarios VALUES ('1001','1001','Gerente','gerente',?, '')", (lid,))
        c.execute("INSERT INTO usuarios VALUES ('1002','1002','Caixa','operador',?, '')", (lid,))
    conn.commit(); conn.close()
init_db()

def is_gerente():
    if session.get("papel")=="gerente": return True
    if session.get("user") in ["1001","admin"]: return True
    try:
        conn=get_db(); c=conn.cursor()
        c.execute("SELECT papel FROM usuarios WHERE user=?", (session.get("user"),))
        r=c.fetchone(); conn.close()
        if r and r[0]=="gerente": return True
    except: pass
    return False

LOGIN = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0a3d8f;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;min-height:100dvh;padding:16px}.box{background:white;width:100%;max-width:400px;padding:28px 22px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,.3)}h2{color:#0a3d8f;text-align:center;font-size:26px;margin-bottom:20px}input{width:100%;padding:16px;border:2px solid #e2e8f0;border-radius:12px;font-size:16px;margin-bottom:12px}button{width:100%;padding:16px;background:#0a3d8f;color:white;border:none;border-radius:12px;font-size:18px;font-weight:bold}</style></head><body><div class="box"><h2>MyBlle Azul</h2><form method="POST" action="/login"><input name="user" value="1001" required><input name="senha" type="password" value="1001" required><button>ENTRAR</button></form><p style="font-size:11px;text-align:center;margin-top:12px;color:#666">1001/1001 Gerente - 1002/1002 Caixa</p></div></body></html>"""

POS = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}.header{background:#0a3d8f;color:white;height:54px;display:flex;align-items:center;padding:0 12px;gap:8px}.main{display:flex;height:calc(100vh - 54px)}.left{width:300px;background:white;border-right:1px solid #ddd;display:flex;flex-direction:column}.produtos{flex:1;background:#f8fafc;display:flex;flex-direction:column}.cats{background:#0a3d8f;display:flex;overflow-x:auto}.cats button{background:transparent;color:white;border:none;padding:10px 14px;font-weight:bold;white-space:nowrap}.cats button.active{background:white;color:#0a3d8f;border-radius:6px 6px 0 0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;padding:12px;overflow-y:auto}.card{border:1px solid #e2e8f0;padding:8px;border-radius:12px;text-align:center;background:white;cursor:pointer}.card img{width:100%;height:80px;object-fit:cover;border-radius:8px;background:#f1f5f9}.preco{color:#0a3d8f;font-weight:bold}.footer{background:#0a3d8f;color:white;padding:12px}.btn{width:100%;padding:14px;background:#0a3d8f;color:white;border:none;border-radius:10px;font-weight:bold;font-size:16px}.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);display:none;justify-content:center;align-items:center;z-index:100;padding:10px}.modal-content{background:white;padding:20px;border-radius:16px;width:100%;max-width:480px;max-height:95vh;overflow-y:auto}.input{width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;margin:6px 0}.preview{width:100%;height:150px;border:2px dashed #0a3d8f;border-radius:12px;display:flex;align-items:center;justify-content:center;background:#f8fafc;cursor:pointer}.preview img{width:100%;height:100%;object-fit:cover}.menu{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.3);display:none;z-index:200}.menu-box{background:white;width:92%;max-width:650px;height:100%;overflow-y:auto;padding:18px}
.item-menu{border:1px solid #e2e8f0;padding:14px;border-radius:12px;margin:8px 0;cursor:pointer;font-weight:bold;background:white}
.item-menu.azul{border:2px solid #0a3d8f;background:#dbeafe;color:#0a3d8f}
.item-menu.verde{border:2px solid #16a34a;background:#dcfce7;color:#166534}
</style></head><body>
<div class="header"><button onclick="document.getElementById('menu').style.display='flex'" style="background:transparent;border:none;color:white;font-size:24px">☰</button><b>Loja Demo Matola - {{user}}</b><a href="/logout" style="color:white;margin-left:auto;text-decoration:none">Sair</a></div>
<div class="main"><div class="left"><div style="padding:10px;font-weight:bold">Carrinho</div><div id="lista" style="flex:1;overflow-y:auto"></div><div class="footer"><div style="display:flex;justify-content:space-between;margin-bottom:6px"><span id="total">MT 0.00</span><span id="count">0 itens</span></div><button class="btn" onclick="abrirPag()">PAGAR (F9)</button></div></div>
<div class="produtos"><input id="busca" placeholder="📷 Código de barras / Nome" style="margin:10px;padding:12px;border:1px solid #ccc;border-radius:10px" oninput="render()"><div class="cats" id="cats"></div><div class="grid" id="grid"></div></div></div>

<!-- PRODUTO COM IMAGEM -->
<div class="modal" id="modalProd"><div class="modal-content"><h3 style="color:#0a3d8f">📦 Produto com Foto</h3>
<form id="formProd"><div class="preview" id="preview" onclick="document.getElementById('fileImg').click()"><span id="previewTxt">📷 Clique para foto</span><img id="previewImg" style="display:none"></div><input type="file" id="fileImg" accept="image/*" capture="environment" style="display:none" onchange="previewFile()">
<input id="p_id" required placeholder="Código (ex: 23b12-107)" class="input"><input id="p_nome" required placeholder="Nome (ex: Copo de Sorvete)" class="input"><div style="display:flex;gap:8px"><input id="p_preco" required placeholder="Preço ex: 120" class="input"><input id="p_stock" required placeholder="Stock ex: 20" class="input"></div><input id="p_barra" placeholder="Código de barras (igual ao código se quiser)" class="input"><input id="p_cat" value="Mercearia" class="input"><div style="display:flex;gap:10px;margin-top:10px"><button type="button" onclick="document.getElementById('modalProd').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button type="submit" style="flex:1;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Salvar</button></div></form></div></div>

<div class="modal" id="modalQtd"><div class="modal-content"><div id="qtdImg" style="text-align:center"></div><h3 id="mNome"></h3><p id="mPreco" style="color:#0a3d8f;font-weight:bold"></p><input id="inputQtd" type="number" value="1" style="width:100%;padding:14px;font-size:20px;text-align:center;border:2px solid #0a3d8f;border-radius:10px;margin:10px 0"><div style="display:flex;gap:10px"><button onclick="document.getElementById('modalQtd').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="conf()" style="flex:1;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Adicionar</button></div></div></div>
<div class="modal" id="modalPag"><div class="modal-content"><h3>Pagamento</h3><div>Total: <b id="pagTotal">MT 0</b></div><input id="pagRec" style="width:100%;padding:14px;font-size:22px;border:2px solid #0a3d8f;border-radius:10px;margin:10px 0" oninput="troco()"><div>Troco: <b id="pagTroco">MT 0</b></div><div style="display:flex;gap:10px;margin-top:10px"><button onclick="document.getElementById('modalPag').style.display='none'" style="flex:1;padding:12px;background:#e2e8f0;border:none;border-radius:10px">Cancelar</button><button onclick="finalizar()" style="flex:1;padding:12px;background:#16a34a;color:white;border:none;border-radius:10px">Confirmar</button></div></div></div>

<!-- MENU COMPLETO -->
<div class="menu" id="menu" onclick="if(event.target==this) this.style.display='none'"><div class="menu-box">
<h2 style="color:#0a3d8f">Menu Completo</h2><p style="font-size:12px;color:#666">Loja Demo Matola - Gerente: {{user}}</p>

<div class="item-menu azul" onclick="document.getElementById('modalProd').style.display='flex';document.getElementById('menu').style.display='none'">📦 Cadastrar Produto com Imagem e Código de Barras</div>
<div class="item-menu" onclick="window.location='/api/produtos'">📋 Ver Todos Produtos (JSON)</div>
<div class="item-menu verde" onclick="document.getElementById('modalCaixa').style.display='flex';loadCaixas();">👥 Equipe - Cadastrar Caixa</div>
<div class="item-menu" onclick="document.getElementById('modalCat').style.display='flex'">🏷️ Categorias da Loja</div>
<div class="item-menu azul" onclick="window.location='/relatorio'">📊 Relatório Completo de Vendas</div>
<div class="item-menu" onclick="alert('Backup: SQLite myblle.db')">💾 Backup / Exportar</div>
<button onclick="document.getElementById('menu').style.display='none'" style="width:100%;padding:14px;background:#0a3d8f;color:white;border:none;border-radius:10px;margin-top:15px">Fechar Menu</button>
</div></div>

<div class="modal" id="modalCaixa"><div class="modal-content"><h3 style="color:#0a3d8f">👥 Cadastrar Caixa</h3><input id="c_user" class="input" placeholder="Usuário ex: joao"><input id="c_nome" class="input" placeholder="Nome completo"><input id="c_senha" type="password" class="input" placeholder="Senha"><input id="c_tel" class="input" placeholder="Telefone"><button onclick="salvarCaixa()" style="width:100%;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px;margin-top:8px">Salvar Caixa</button><div id="listaCaixas" style="margin-top:12px"></div><button onclick="document.getElementById('modalCaixa').style.display='none'" style="width:100%;padding:10px;margin-top:10px;background:#e2e8f0;border:none;border-radius:8px">Fechar</button></div></div>
<div class="modal" id="modalCat"><div class="modal-content"><h3>🏷️ Categorias</h3><p>Mercearia, Casa, Cozinha, Alimentação, Bebidas, Limpeza, Outro</p><input id="novaCat" class="input" placeholder="Nova categoria"><button onclick="alert('Categoria adicionada no próximo produto');document.getElementById('modalCat').style.display='none'" style="width:100%;padding:12px;background:#0a3d8f;color:white;border:none;border-radius:10px">Adicionar</button></div></div>

<script>
let prods=[]; let car=[]; let sel=null; let cat='Todos'; let imgBase64="";
async function load(){ prods=await (await fetch('/api/produtos')).json(); renderCats(); render(); }
function renderCats(){ let cats=['Todos',...new Set(prods.map(p=>p.categoria))]; document.getElementById('cats').innerHTML=cats.map(c=>`<button class="${c==cat?'active':''}" onclick="cat='${c}';render()">${c}</button>`).join(''); }
function render(){ let b=document.getElementById('busca').value.toLowerCase(); let f=prods.filter(p=>(cat=='Todos'||p.categoria==cat)&&(!b||p.nome.toLowerCase().includes(b)||p.id.toLowerCase().includes(b)||(p.codigo_barras&&p.codigo_barras.toLowerCase().includes(b)))); document.getElementById('grid').innerHTML=f.map(p=>`<div class="card" onclick="openQtd('${p.id}')">${p.imagem?`<img src="${p.imagem}">`:`<div style="height:80px;display:flex;align-items:center;justify-content:center;font-size:30px">📦</div>`}<b>${p.id}<br>${p.nome}</b><div class="preco">MT ${p.preco}</div><div style="font-size:9px;color:#64748b">${p.codigo_barras||''} | Stock:${p.stock}</div></div>`).join(''); }
function openQtd(id){ sel=prods.find(p=>p.id==id); document.getElementById('mNome').innerText=sel.nome; document.getElementById('mPreco').innerText='MT '+sel.preco+' | Stock '+sel.stock; document.getElementById('qtdImg').innerHTML=sel.imagem?`<img src="${sel.imagem}" style="width:120px;height:120px;object-fit:cover;border-radius:12px">`:''; document.getElementById('inputQtd').value=1; document.getElementById('modalQtd').style.display='flex'; }
function conf(){ let q=parseInt(document.getElementById('inputQtd').value)||1; car.push({id:sel.id,nome:sel.nome,preco:sel.preco,qtd:q}); draw(); document.getElementById('modalQtd').style.display='none'; }
function draw(){ let t=0; document.getElementById('lista').innerHTML=car.map((c,i)=>{t+=c.preco*c.qtd; return `<div style="display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #eee;font-size:13px"><span>${c.id} x${c.qtd}</span><span>MT ${(c.preco*c.qtd).toFixed(2)} <span onclick="car.splice(${i},1);draw()" style="color:red;cursor:pointer">X</span></span></div>`}).join(''); document.getElementById('total').innerText='MT '+t.toFixed(2); document.getElementById('count').innerText=car.length+' itens'; document.getElementById('pagTotal').innerText='MT '+t.toFixed(2); }
function abrirPag(){ if(car.length==0){alert('Carrinho vazio');return} document.getElementById('modalPag').style.display='flex'; document.getElementById('pagRec').value=document.getElementById('total').innerText.replace('MT','').trim(); troco(); }
function troco(){ let tot=parseFloat(document.getElementById('pagTotal').innerText.replace('MT',''))||0; let rec=parseFloat(document.getElementById('pagRec').value.replace(/[^0-9.]/g,''))||0; document.getElementById('pagTroco').innerText='MT '+(rec-tot).toFixed(2); }
async function finalizar(){ let tot=parseFloat(document.getElementById('pagTotal').innerText.replace('MT','')); let rec=parseFloat(document.getElementById('pagRec').value.replace(/[^0-9.]/g,''))||0; let r=await fetch('/api/vender',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({total:tot,recebido:rec,troco:rec-tot,itens:car})}); if(r.ok){alert('Venda MT '+tot+' OK!'); car=[]; draw(); document.getElementById('modalPag').style.display='none'; load(); } }
function previewFile(){ let file=document.getElementById('fileImg').files[0]; if(file){ let reader=new FileReader(); reader.onload=function(e){ imgBase64=e.target.result; document.getElementById('previewImg').src=imgBase64; document.getElementById('previewImg').style.display='block'; document.getElementById('previewTxt').style.display='none'; }; reader.readAsDataURL(file); } }
document.getElementById('formProd').addEventListener('submit', async function(e){
 e.preventDefault();
 let preco=document.getElementById('p_preco').value.replace(/[^0-9.]/g,'')||'0';
 let stock=document.getElementById('p_stock').value.replace(/[^0-9]/g,'')||'0';
 let body={id:document.getElementById('p_id').value.trim(), nome:document.getElementById('p_nome').value.trim(), preco:preco, stock:stock, codigo_barras:document.getElementById('p_barra').value.trim()||document.getElementById('p_id').value.trim(), categoria:document.getElementById('p_cat').value.trim(), imagem:imgBase64};
 let res=await fetch('/api/produtos',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 if(res.ok){ alert('✅ Produto salvo!'); document.getElementById('modalProd').style.display='none'; document.getElementById('formProd').reset(); imgBase64=""; document.getElementById('previewImg').style.display='none'; document.getElementById('previewTxt').style.display='block'; load(); } else { let j=await res.json(); alert(j.erro); }
});
async function loadCaixas(){ let caixas=await (await fetch('/api/caixas')).json(); document.getElementById('listaCaixas').innerHTML=caixas.map(c=>`<div style="padding:8px;border-bottom:1px solid #eee;font-size:13px">${c.user} - ${c.nome} (${c.papel}) - ${c.telefone||''}</div>`).join(''); }
async function salvarCaixa(){ let user=document.getElementById('c_user').value.trim(); let nome=document.getElementById('c_nome').value.trim(); let senha=document.getElementById('c_senha').value.trim(); let tel=document.getElementById('c_tel').value.trim(); if(!user||!senha) return alert('Usuário e senha obrigatórios'); let r=await fetch('/api/caixas',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user,senha,nome,telefone:tel,papel:'operador'})}); if(r.ok){ alert('Caixa criado!'); loadCaixas(); } else { let e=await r.json(); alert(e.erro); } }
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
    return render_template_string(POS, user=session["user"])

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
        if not is_gerente(): return jsonify({"erro":"Só Gerente pode cadastrar"}),403
        d=request.json
        pid=d.get("id","").strip()
        if not pid: return jsonify({"erro":"Código vazio"}),400
        nome=d.get("nome","").strip() or pid
        preco=re.sub(r'[^0-9.]','', str(d.get("preco","0"))) or '0'
        stock=re.sub(r'[^0-9]','', str(d.get("stock","0"))) or '0'
        barra=d.get("codigo_barras","") or pid
        cat=d.get("categoria","Mercearia")
        img=d.get("imagem","")
        if not img:
            c.execute("SELECT imagem FROM produtos WHERE id=? AND loja_id=?", (pid, loja_id))
            old=c.fetchone()
            if old: img=old[0] or ""
        c.execute("INSERT OR REPLACE INTO produtos (id,loja_id,nome,categoria,preco,stock,codigo_barras,imagem) VALUES (?,?,?,?,?,?,?,?)", (pid,loja_id,nome,cat,float(preco),int(stock),barra,img))
        conn.commit(); conn.close()
        return jsonify({"ok":True})
    c.execute("SELECT id,nome,categoria,preco,stock,codigo_barras,imagem FROM produtos WHERE loja_id=?", (loja_id,))
    rows=c.fetchall(); conn.close()
    return jsonify([{"id":r[0],"nome":r[1],"categoria":r[2],"preco":r[3],"stock":r[4],"codigo_barras":r[5],"imagem":r[6]} for r in rows])

@app.route("/api/caixas", methods=["GET","POST"])
def caixas():
    if "loja_id" not in session: return jsonify([]),401
    if not is_gerente(): return jsonify({"erro":"Só gerente"}),403
    conn=get_db(); c=conn.cursor()
    if request.method=="POST":
  
