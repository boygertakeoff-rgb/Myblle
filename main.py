from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>MyBlle Azul - Tela Cheia</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
html,body{height:100%;width:100%;overflow:hidden;background:#0a3d8f}
.top{height:56px;background:#082f6b;color:white;display:flex;align-items:center;padding:0 14px;font-weight:bold;font-size:18px;justify-content:space-between}
.main{display:flex;height:calc(100vh - 56px);width:100vw}
.left{width:340px;background:white;display:flex;flex-direction:column;border-right:3px solid #0a3d8f}
.cart{flex:1;overflow-y:auto;padding:10px}
.footer{background:#0a3d8f;color:white;padding:14px;font-size:18px;font-weight:bold;display:flex;justify-content:space-between}
.right{flex:1;background:#eef3ff;display:flex;flex-direction:column}
.search{padding:10px;background:white;display:flex;gap:8px;border-bottom:2px solid #0a3d8f}
.search input{flex:1;padding:14px;border:2px solid #0a3d8f;border-radius:10px;font-size:16px}
.search button{padding:14px 18px;background:#0a3d8f;color:white;border:none;border-radius:10px;font-weight:bold}
.grid{flex:1;overflow-y:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;padding:12px}
.card{background:white;border:2px solid #dbeafe;border-radius:14px;padding:12px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.1)}
.card b{color:#0a3d8f}
.btn-pagar{width:100%;padding:18px;background:#0a3d8f;color:white;border:none;font-size:20px;font-weight:bold}
@media(max-width:700px){.left{width:100%;position:absolute;height:50%;bottom:0;z-index:10;border-top:4px solid #0a3d8f}.right{height:50%}.grid{grid-template-columns:repeat(3,1fr)}}
</style>
</head>
<body>
<div class="top"><span>☰ MyBlle Azul - Matriz Matola</span><span style="background:white;color:#0a3d8f;padding:6px 12px;border-radius:8px;font-size:12px">📷 SCANNER</span></div>
<div class="main">
<div class="left">
<div style="padding:10px;background:#dbeafe;font-size:12px;font-weight:bold;color:#0a3d8f">Vendedor: dono | Cliente: VIP</div>
<div class="cart" id="lista"><p style="text-align:center;color:#999;margin-top:40px">Carrinho vazio<br>Toque num produto →</p></div>
<div class="footer"><span>Pagar</span><span id="total">MT 0.00</span></div>
<button class="btn-pagar" onclick="alert('TELA CHEIA OK - Agora vou colocar scanner e produtos')">PAGAR (F9) - TELA CHEIA AZUL</button>
</div>
<div class="right">
<div class="search"><input id="busca" placeholder="🔍 Código barras ex: 23b12-107"><button>📷</button><button style="background:white;color:#0a3d8f;border:2px solid #0a3d8f">+ Produto</button></div>
<div class="grid" id="grid"></div>
</div>
</div>
<script>
let prods=[
{id:'23b12-107',nome:'Copo de Sorvete',preco:120,stock:50},
{id:'IP-3Copo',nome:'Copo com Cabo',preco:15,stock:30},
{id:'IP-27Chaleira',nome:'Chaleira Plastico',preco:45,stock:20},
{id:'Bacia Azul',nome:'Bacia 10L',preco:80,stock:15},
{id:'Balde 20L',nome:'Balde 20L',preco:120,stock:10},
{id:'Cadeira',nome:'Cadeira Plastico',preco:350,stock:8}
];
let car=[];
function render(){
let b=document.getElementById('busca').value.toLowerCase();
let f=prods.filter(p=>!b||p.nome.toLowerCase().includes(b)||p.id.toLowerCase().includes(b));
document.getElementById('grid').innerHTML=f.map(p=>`
<div class="card" onclick="addCar('${p.id}')">
<div style="font-size:36px">📦</div>
<b>${p.id}</b><br>
<span style="font-size:12px">${p.nome}</span><br>
<b style="color:#0a3d8f;font-size:16px">MT ${p.preco}</b><br>
<small>Stock:${p.stock} | ${p.id}</small>
</div>`).join('');
}
function addCar(id){
let p=prods.find(x=>x.id==id);
car.push({id:p.id,nome:p.nome,preco:p.preco,qtd:1});
draw();
}
function draw(){
let t=0;
document.getElementById('lista').innerHTML=car.map((c,i)=>{
t+=c.preco*c.qtd;
return `<div style="display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #eee;font-size:13px"><span>${c.id} x${c.qtd}<br><small>${c.nome}</small></span><span>MT ${(c.preco*c.qtd).toFixed(2)} <span onclick="car.splice(${i},1);draw()" style="color:red;font-weight:bold;cursor:pointer"> X</span></span></div>`
}).join('');
document.getElementById('total').innerText='MT '+t.toFixed(2);
}
render();
</script>
</body>
</html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
