from flask import Flask
app = Flask(__name__)
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>MyBlle Compacto</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
body{height:100dvh;width:100vw;background:#0a3d8f;display:flex;flex-direction:column;overflow:hidden}
.top{height:44px;background:#052a6b;color:white;display:flex;align-items:center;justify-content:space-between;padding:0 10px;font-size:14px;font-weight:bold}
.main{flex:1;display:flex;overflow:hidden}
.left{width:260px;background:white;display:flex;flex-direction:column}
.cart{flex:1;overflow-y:auto;padding:6px}
.footer{background:#0a3d8f;color:white;padding:10px;font-size:14px;font-weight:bold;display:flex;justify-content:space-between}
.right{flex:1;background:#eef4ff;display:flex;flex-direction:column;overflow:hidden}
.search{padding:6px;background:white;display:flex;gap:4px;border-bottom:2px solid #0a3d8f}
.search input{flex:1;padding:8px;border:1.5px solid #0a3d8f;border-radius:8px;font-size:13px}
.grid{flex:1;overflow-y:auto;padding:6px;display:grid;grid-template-columns:repeat(auto-fill,minmax(85px,1fr));gap:6px}
.card{background:white;border-radius:10px;padding:6px;text-align:center;border:1px solid #c7d8ff}
.card b{font-size:10px;color:#0a3d8f;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card small{font-size:9px}
.card .preco{font-size:11px;color:#0a3d8f;font-weight:bold}
.btn-pagar{padding:12px;background:#0a3d8f;color:white;border:none;font-size:14px;font-weight:bold;width:100%}
@media(max-width:768px){
.main{flex-direction:column}
.right{height:58dvh}
.left{width:100vw;height:42dvh;border-top:3px solid #0a3d8f}
.grid{grid-template-columns:repeat(4,1fr);gap:4px}
}
</style>
</head>
<body>
<div class="top"><span>☰ MyBlle AZUL Compacto</span><button onclick="document.documentElement.requestFullscreen()" style="background:white;color:#0a3d8f;border:none;padding:4px 8px;border-radius:6px;font-size:10px;font-weight:bold">⛶ CHEIA</button></div>
<div class="main">
<div class="right">
<div class="search"><input id="busca" placeholder="Busca"><button style="padding:8px;background:#0a3d8f;color:white;border:none;border-radius:6px;font-size:11px">📷</button></div>
<div class="grid" id="grid"></div>
</div>
<div class="left">
<div style="background:#dbeafe;padding:4px;font-size:9px;color:#0a3d8f;font-weight:bold;text-align:center">dono - Matriz - COMPACTO</div>
<div class="cart" id="lista"><div style="text-align:center;color:#999;margin-top:20px;font-size:11px">Toque no produto →</div></div>
<div class="footer"><span>TOTAL</span><span id="total">MT 0</span></div>
<button class="btn-pagar">PAGAR - AZUL</button>
</div>
</div>
<script>
let prods=[
{id:'23b12-107',nome:'Copo Sorvete',preco:120},
{id:'IP-3Copo',nome:'Copo Cabo',preco:15},
{id:'Chaleira',nome:'Chaleira',preco:45},
{id:'Bacia',nome:'Bacia 10L',preco:80},
{id:'Balde',nome:'Balde',preco:120},
{id:'Cadeira',nome:'Cadeira',preco:350},
{id:'Pote',nome:'Pote',preco:25},
{id:'Tigela',nome:'Tigela',preco:35}
];
let car=[];
function render(){
document.getElementById('grid').innerHTML=prods.map(p=>`<div class="card" onclick="addCar('${p.id}')"><div style="font-size:20px">📦</div><b>${p.id}</b><small>${p.nome}</small><div class="preco">MT ${p.preco}</div></div>`).join('');
}
function addCar(id){let p=prods.find(x=>x.id==id);car.push(p);draw();}
function draw(){
let t=0;
document.getElementById('lista').innerHTML=car.map((c,i)=>{t+=c.preco;return `<div style="display:flex;justify-content:space-between;padding:4px;border-bottom:1px solid #eee;font-size:11px"><span>${c.id}</span><span>MT ${c.preco} <span onclick="car.splice(${i},1);draw()" style="color:red">X</span></span></div>`}).join('');
document.getElementById('total').innerText='MT '+t;
}
render();
</script>
</body>
</html>
"""
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
