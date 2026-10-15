import sqlite3, re
from flask import Flask, request, session, redirect, render_template_string, jsonify
from datetime import datetime
app = Flask(__name__)
app.secret_key = "myblle-v13-dono-filiais-final"

def get_db(): return sqlite3.connect('myblle.db')
def init_db():
    conn=get_db(); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS lojas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cidade TEXT, parent_id INTEGER, dono_user TEXT, telefone TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, senha TEXT, nome TEXT, papel TEXT, loja_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS produtos (id TEXT, loja_id INTEGER, nome TEXT, preco REAL, stock INTEGER, codigo_barras TEXT, imagem TEXT, PRIMARY KEY(id, loja_id))")
    c.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, loja_id INTEGER, total REAL, recebido REAL, troco REAL, data TEXT, vendedor TEXT, cliente TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS venda_itens (venda_id INTEGER, produto_id TEXT, qtd INTEGER, preco REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS transferencias (id INTEGER PRIMARY KEY AUTOINCREMENT, origem INTEGER, destino INTEGER, produto_id TEXT, qtd INTEGER, data TEXT, status TEXT, autor TEXT)")
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0]==0:
        c.execute("INSERT INTO lojas (nome,cidade,dono_user) VALUES ('Matriz Matola','Matola','dono')")
        matriz=c.lastrowid
        c.execute("INSERT INTO lojas (nome,cidade,parent_id,dono_user) VALUES ('Filial Nampula','Nampula',?, 'dono')", (matriz,))
        c.execute("INSERT INTO lojas (nome,cidade,parent_id,dono_user) VALUES ('Filial Maputo','Maputo',?, 'dono')", (matriz,))
        # DONO vê tudo
        c.execute("INSERT INTO usuarios VALUES ('dono','dono123','DONO DAS LOJAS','dono',?)", (matriz,))
        c.execute("INSERT INTO usuarios VALUES ('1001','1001','Gerente Matola','gerente',?)", (matriz,))
        c.execute("INSERT INTO usuarios VALUES ('1002','1002','Caixa Matola','operador',?)", (matriz,))
        c.execute("INSERT INTO usuarios VALUES ('2001','2001','Gerente Nampula','gerente',2)")
        c.execute("INSERT INTO usuarios VALUES ('2002','2002','Caixa Nampula','operador',2)")
        # produtos iniciais
        for pid,nome,preco in [('23b12-107','Copo de Sorvete',120),('IP-3Copo','Copo com Cabo',15),('IP-27Chaleira','Chaleira Plastico',45)]:
            c.execute("INSERT OR IGNORE INTO produtos VALUES (?,?,?,?,?,?,?)", (pid,matriz,nome,preco,50,pid,''))
            c.execute("INSERT OR IGNORE INTO produtos VALUES (?,?,?,?,?,?,?)", (pid,2,nome,preco,20,pid,''))
            c.execute("INSERT OR IGNORE INTO produtos VALUES (?,?,?,?,?,?,?)", (pid,3,nome,preco,10,pid,''))
    conn.commit(); conn.close()
init_db()

def get_loja_nome(lid):
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT nome FROM lojas WHERE id=?", (lid,))
    r=c.fetchone(); conn.close()
    return r[0] if r else "Loja"

LOGIN = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#ff6a00;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;font-family:Arial}.box{background:white;padding:25px;border-radius:16px;width:90%;max-width:400px;text-align:center}input{width:100%;padding:14px;margin:8px 0;border:1px solid #ddd;border-radius:8px}button{width:100%;padding:14px;background:#ff6a00;color:white;border:none;border-radius:8px;font-weight:bold;font-size:18px}small{color:#666;font-size:11px}</style></head><body><div class="box"><h2 style="color:#ff6a00">MyBlle - Dono</h2><form method="POST" action="/login"><input name="user" placeholder="Usuário" value="dono" required><input name="senha" type="password" placeholder="Senha" value="dono123" required><button>ENTRAR</button></form><small>dono/dono123 = DONO (vê todas)<br>1001/1001 = Gerente Matola<br>2001/2001 = Gerente Nampula<br>1002/1002 = Caixa</small></div></body></html>"""

POS = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
.top{background:#ff6a00;color:white;height:46px;display:flex;align-items:center;padding:0 10px;font-weight:bold;gap:8px}
.main{display:flex;height:calc(100vh - 46px)}
.left{width:300px;background:#fff;border-right:1px solid #ddd;display:flex;flex-direction:column}
.cart{flex:1;overflow-y:auto}
.footer{background:#ff6a00;color:white;padding:8px}
.right{flex:1;background:#f5f5f5;display:flex;flex-direction:column}
.cats{background:#ff6a00;display:flex;color:white;overflow-x:auto}
.cats div{padding:10px 14px;white-space:nowrap;cursor:pointer;font-size:12px}
.cats div.active{background:white;color:#ff6a00;font-weight:bold}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;padding:10px;overflow-y:auto}
.card{background:white;border:1px solid #ddd;padding:8px;text-align:center;border-radius:6px;cursor:pointer}
.card img{width:100%;height:70px;object-fit:cover;border-radius:4px}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);display:none;justify-content:center;align-items:center;z-index:100;padding:8px}
.modal-box{background:white;width:98%;max-width:460px;border-radius:10px;overflow:hidden;max-height:95vh;overflow-y:auto}
.teclado{display:grid;grid-template-columns:repeat(3,1fr) 100px;gap:1px;background:#ddd}
.teclado button{padding:16px;background:white;border:none;font-size:18px}
.teclado button.laranja{background:#ff6a00;color:white;font-weight:bold}
.teclado button.cinza{background:#f0f0f0}
.menu{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.4);display:none;z-index:200}
.menu-box{background:#f5f5f5;width:95%;max-width:750px;height:100%;overflow-y:auto;padding:15px}
.menu-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.menu-item{background:white;padding:12px;border-radius:10px;text-align:center;font-size:10px;cursor:pointer;box-shadow:0 1px 2px rgba(0,0,0,.1);border:1px solid #eee}
.menu-item b{display:block;margin-top:4px;font-size:11px}
.input{width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;margin:6px 0}
.receipt{width:58mm;font-family:monospace;font-size:12px;padding:10px}
@media print{.no-print{display:none}.receipt{width:100%}}
</style></head><body>
<div class="top">
<span onclick="document.getElementById('menu').style.display='flex'" style="font-size:22px;cursor:pointer">☰</span>
<span id="lojaNome">{{loja_nome}} - {{user}} ({{papel}})</span>
<span style="margin-left:auto;cursor:pointer" onclick="document.getElementById('scannerDiv').style.display='flex'">📷 SCANNER</span>
<span onclick="location.href='/logout'" style="cursor:pointer">Sair</span>
</div>
<div class="main">
<div class="left"><div style="padding:8px;font-size:11px">Cliente: <input id="cliente" placeholder="VIP/Cliente" style="border:none;border-bottom:1px solid #ddd;width:120px"><br><span id="vendedorInfo">Vendedor: {{user}}</span></div><div class="cart" id="lista"></div><div class="footer"><div style="display:flex;justify-content:space-between"><span>Pagar</span><span id="total">MT 0</span></div></div><button onclick="abrirPag()" style="width:100%;padding:14px;background:#ff6a00;color:white;border:none;font-weight:bold;font-size:16px">PAGAR (F9)</button></div>
<div class="right">
<div style="display:flex;padding:8px;gap:6px;background:white"><input id="busca" placeholder="🔍 Código de barras / Nome" style="flex:1;padding:10px;border:1px solid #ccc;border-radius:6px" oninput="render()"><button onclick="startScan()" style="padding:10px;background:#ff6a00;color:white;border:none;border-radius:6px">📷</button><button onclick="document.getElementById('modalProd').style.display='flex'" style="padding:10px;background:white;border:1px solid #ff6a00;color:#ff6a00;border-radius:6px">+ Produto</button></div>
<div class="cats" id="cats"></div><div class="grid" id="grid"></div>
</div>
</div>

<!-- SCANNER -->
<div class="modal" id="scannerDiv"><div class="modal-box" style="padding:10px"><h3 style="color:#ff6a00">📷 Scanner Código de Barras</h3><div id="reader" style="width:100%"></div><button onclick="stopScan()" style="width:100%;padding:12px;background:#eee;border:none;border-radius:8px;margin-top:8px">Fechar Scanner</button></div></div>

<!-- QUANTIDADE -->
<div class="modal" id="modalQtd"><div class="modal-box"><div style="padding:10px;text-align:center"><b id="mNome"></b><br><small id="mStock"></small><br>Total: <b id="mTotal" style="color:#ff6a00">MT 0</b></div><div style="padding:0 10px"><input id="inputQtd" type="number" value="1" style="width:100%;padding:12px;text-align:center;border:2px solid #ff6a00;border-radius:8px;font-size:18px" oninput="updateTotal()"></div><div class="teclado"><button onclick="addQ('1')">1</button><button onclick="addQ('2')">2</button><button onclick="addQ('3')">3</button><button class="cinza" onclick="addQtd(10)">+10</button><button onclick="addQ('4')">4</button><button onclick="addQ('5')">5</button><button onclick="addQ('6')">6</button><button class="cinza" onclick="document.getElementById('inputQtd').value=''">Apagar</button><button onclick="addQ('7')">7</button><button onclick="addQ('8')">8</button><button onclick="addQ('9')">9</button><button class="cinza" onclick="addQtd(20)">+20</button><button onclick="addQ('00')">00</button><button onclick="addQ('0')">0</button><button onclick="document.getElementById('modalQtd').style.display='none'" style="background:#eee">X</button><button class="laranja" onclick="conf()">Confirmar</button></div></div></div>

<!-- PAGAMENTO COM RECIBO -->
<div class="modal" id="modalPag"><div class="modal-box"><div style="padding:10px;display:flex;justify-content:space-between"><div>Valor total<br><b id="pagTotal" style="font-size:22px">MT 0</b><br>Receber<br><input id="pagRec" style="border:2px solid #ff6a00;padding:8px;width:100px;font-size:18px" oninput="troco()"></div><div style="text-align:right">Troco<br><b id="pagTroco" style="font-size:22px;color:#ff6a00">MT 0</b><br><button onclick="imprimirRecibo()" style="margin-top:6px;padding:6px 10px;background:white;border:1px solid #ff6a00;color:#ff6a00;border-radius:6px">🖨️ Recibo</button></div></div><div class="teclado"><button onclick="addP('1')">1</button><button onclick="addP('2')">2</button><button onclick="addP('3')">3</button><button class="cinza" onclick="setRec(50)">50</button><button onclick="addP('4')">4</button><button onclick="addP('5')">5</button><button onclick="addP('6')">6</button><button class="cinza" onclick="setRec(100)">100</button><button onclick="addP('7')">7</button><button onclick="addP('8')">8</button><button onclick="addP('9')">9</button><button class="cinza" onclick="setRec(200)">200</button><button onclick="addP('00')">00</button><button onclick="addP('0')">0</button><button onclick="addP('.')">.</button><button class="laranja" onclick="finalizar()">Confirmar</button></div></div></div>

<!-- MENU COMPLETO DONO -->
<div class="menu" id="menu" onclick="if(event.target==this) this.style.display='none'"><div class="menu-box">
<div style="display:flex;justify-content:space-between;align-items:center"><b>Menu - {{papel}} - {{loja_nome}}</b><button onclick="document.getElementById('menu').style.display='none'" style="padding:8px 14px;background:#ff6a00;color:white;border:none;border-radius:8px">Fechar</button></div>

{% if papel in ['dono','gerente'] %}
<div style="background:#ff6a00;color:white;padding:10px;border-radius:8px;margin:10px 0;font-weight:bold" onclick="window.location='/dono'">👑 PAINEL DO DONO - CONTROLE REMOTO DE TODAS LOJAS (TEMPO REAL)</div>
{% endif %}

<h4 style="margin:10px 0 6px">Vendas e Caixa</h4>
<div class="menu-grid">
<div class="menu-item" onclick="abrirPag()">💰<b>Pagar</b></div>
<div class="menu-item" onclick="window.location='/recibos'">🧾<b>Recibos<br><small>{{ 'só meus' if papel=='operador' else 'todos' }}</small></b></div>
<div class="menu-item" onclick="window.location='/relatorio'">📊<b>Relatório Diário</b></div>
<div class="menu-item" onclick="window.location='/entrega'">🚚<b>Entrega Diária</b></div>
</div>

<h4 style="margin:10px 0 6px">Produto e Stock</h4>
<div class="menu-grid">
<div class="menu-item" onclick="document.getElementById('modalProd').style.display='flex';document.getElementById('menu').style.display='none'">📦<b>Produto Novo + Foto + Barra</b></div>
<div class="menu-item" onclick="window.location='/etiquetas'">🏷️<b>Imprimir Etiquetas</b></div>
<div class="menu-item" onclick="window.location='/stock'">📦<b>Gestão Stock</b></div>
<div class="menu-item" onclick="window.location='/despacho'">📤<b>Despacho Mercadoria</b></div>
</div>

<h4 style="margin:10px 0 6px">Lojas e Equipe (Dono)</h4>
<div class="menu-grid">
<div class="menu-item" onclick="document.getElementById('modalLoja').style.display='flex';loadLojas()">🏪<b>Cadastrar Loja/Filial</b></div>
<div class="menu-item" onclick="document.getElementById('modalCaixa').style.display='flex';loadCaixas()">👥<b>Cadastrar Caixa</b></div>
<div class="menu-item" onclick="document.getElementById('modalTransf').style.display='flex';loadLojas()">🔄<b>Transferir entre Filiais</b></div>
<div class="menu-item" onclick="window.location='/dono'">👑<b>Painel Dono Tempo Real</b></div>
</div>

<div style="margin-top:15px;background:white;padding:10px;border-radius:8px"><small>Loja atual: {{loja_nome}} - ID: {{loja_id}} - Não mistura dados com outras lojas. Cada filial tem stock separado.</small></div>
</div></div>

<!-- MODAIS CADASTROS -->
<div class="modal" id="modalProd"><div class="modal-box" style="padding:15px"><h3 style="color:#ff6a00">📦 Produto + Imagem + Barra</h3><div onclick="document.getElementById('fileImg').click()" style="width:100%;height:110px;border:2px dashed #ff6a00;display:flex;align-items:center;justify-content:center;border-radius:8px;margin:8px 0"><span id="previewTxt">📷 Foto</span><img id="previewImg" style="display:none;width:100%;height:100%;object-fit:cover"></div><input type="file" id="fileImg" accept="image/*" capture="environment" style="display:none" onchange="previewFile()"><input id="p_id" class="input" placeholder="Código ex: 23b12-107"><input id="p_nome" class="input" placeholder="Nome ex: Copo Sorvete"><div style="display:flex;gap:6px"><input id="p_preco" class="input" placeholder="Preço MT"><input id="p_stock" class="input" placeholder="Stock"></div><input id="p_barra" class="input" placeholder="Código barras"><div style="display:flex;gap:8px"><button onclick="document.getElementById('modalProd').style.display='none'" style="flex:1;padding:12px;background:#eee;border:none;border-radius:8px">Cancelar</button><button onclick="salvarProd()" style="flex:1;padding:12px;background:#ff6a00;color:white;border:none;border-radius:8px">Salvar</button></div></div></div>

<div class="modal" id="modalLoja"><div class="modal-box" style="padding:15px"><h3 style="color:#ff6a00">🏪 Cadastrar Loja/Filial</h3><input id="l_nome" class="input" placeholder="Nome ex: Filial Nampula"><input id="l_cidade" class="input" placeholder="Cidade ex: Nampula"><input id="l_tel" class="input" placeholder="Telefone"><button onclick="salvarLoja()" style="width:100%;padding:12px;background:#ff6a00;color:white;border:none;border-radius:8px">Salvar Loja</button><div id="listaLojas" style="margin-top:10px"></div><button onclick="document.getElementById('modalLoja').style.display='none'" style="width:100%;padding:8px;margin-top:8px;background:#eee;border:none;border-radius:6px">Fechar</button></div></div>

<div class="modal" id="modalCaixa"><div class="modal-box" style="padding:15px"><h3>👥 Cadastrar Caixa/Gerente</h3><input id="c_user" class="input" placeholder="User ex: 3001"><input id="c_nome" class="input" placeholder="Nome"><input id="c_senha" class="input" type="password" placeholder="Senha"><select id="c_papel" class="input"><option value="operador">Caixa (operador)</option><option value="gerente">Gerente</option></select><select id="c_loja" class="input"></select><button onclick="salvarCaixa()" style="width:100%;padding:12px;background:#ff6a00;color:white;border:none;border-radius:8px">Salvar</button><div id="listaCaixas"></div></div></div>

<div class="modal" id="modalTransf"><div class="modal-box" style="padding:15px"><h3>🔄 Transferir entre Filiais</h3><small>Dono transfere stock de uma loja para outra sem misturar dados</small><select id="t_origem" class="input"></select><select id="t_destino" class="input"></select><input id="t_prod" class="input" placeholder="Código produto ex: 23b12-107"><input id="t_qtd" type="number" class="input" placeholder="Quantidade"><button onclick="transferir()" style="width:100%;padding:12px;background:#ff6a00;color:white;border:none;border-radius:8px">Transferir Agora</button><div id="listaTransf" style="margin-top:10px"></div></div></div>

<div id="printArea" style="display:none"></div>

<script>
let prods=[]; let car=[]; let sel=null; let cat='Todos'; let imgBase64=""; let html5Qr=null;
async function load(){ let r=await fetch('/api/produtos'); prods=await r.json(); renderCats(); render(); }
function renderCats(){ let cats=['Todos',...new Set(prods.map(p=>'Mercadoria'))]; cats=['Todos','Mercearia','Casa']; document.getElementById('cats').innerHTML=cats.map(c=>`<div class="${c==cat?'active':''}" onclick="cat='${c}';render()">${c}</div>`).join(''); }
function render(){ let b=document.getElementById('busca').value.toLowerCase(); let f=prods.filter(p=>!b||p.nome.toLowerCase().includes(b)||p.id.toLowerCase().includes(b)||(p.codigo_barras&&p.codigo_barras.toLowerCase().includes(b))); document.getElementById('grid').innerHTML=f.map(p=>`<div class="card" onclick="openQtd('${p.id}')">${p.imagem?`<img src="${p.imagem}">`:`📦`}<b>${p.id}</b><div style="font-size:11px">${p.nome}</div><div style="color:#ff6a00;font-weight:bold">MT ${p.preco}</div><div style="font-size:9px">Stock:${p.stock}</div></div>`).join(''); }
function openQtd(id){ sel=prods.find(p=>p.id==id); document.getElementById('mNome').innerText=sel.id+' '+sel.nome; document.getElementById('mStock').innerText='Stock disponível: '+sel.stock+' | Loja: {{loja_nome}}'; document.getElementById('inputQtd').value=1; document.getElementById('mTotal').innerText='MT '+sel.preco; document.getElementById('modalQtd').style.display='flex'; }
function addQ(n){ document.getElementById('inputQtd').value+=n; updateTotal(); }
function addQtd(n){ let v=parseInt(document.getElementById('inputQtd').value)||0; document.getElementById('inputQtd').value=v+n; updateTotal(); }
function updateTotal(){ let q=parseInt(document.getElementById('inputQtd').value)||1; document.getElementById('mTotal').innerText='MT '+(sel.preco*q).toFixed(2); }
function conf(){ let q=parseInt(document.getElementById('inputQtd').value)||1; if(q>sel.stock){ alert('Stock insuficiente na {{loja_nome}}! Só '+sel.stock); return; } car.push({id:sel.id,nome:sel.nome,preco:sel.preco,qtd:q}); draw(); document.getElementById('modalQtd').style.display='none'; }
function draw(){ let t=0; document.getElementById('lista').innerHTML=car.map((c,i)=>{t+=c.preco*c.qtd; return `<div style="display:flex;justify-content:space-between;padding:6px;border-bottom:1px solid #f1f1f1;font-size:12px"><span>${c.id} x${c.qtd}</span><span>MT ${(c.preco*c.qtd).toFixed(2)} <span onclick="car.splice(${i},1);draw()" style="color:red">X</span></span></div>`}).join(''); document.getElementById('total').innerText='MT '+t.toFixed(2); document.getElementById('pagTotal').innerText='MT '+t.toFixed(2); }
function abrirPag(){ if(car.length==0){alert('Carrinho vazio');return} document.getElementById('modalPag').style.display='flex'; document.getElementById('pagRec').value=document.getElementById('total').innerText.replace('MT','').trim(); troco(); }
function troco(){ let tot=parseFloat(document.getElementById('pagT
