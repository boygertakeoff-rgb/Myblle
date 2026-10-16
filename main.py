from flask import Flask
app = Flask(__name__)
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MyBlle Carrinho Grande</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
body{height:100dvh;width:100vw;background:#0a3d8f;display:flex;flex-direction:column;overflow:hidden}
.top{height:44px;background:#052a6b;color:white;display:flex;align-items:center;padding:0 12px;font-weight:bold;font-size:14px}
.main{flex:1;display:flex;overflow:hidden;background:white}
.left{width:45%;background:white;display:flex;flex-direction:column;border-right:4px solid #0a3d8f}
.cart{flex:1;overflow-y:auto;padding:10px;background:white}
.footer{background:#0a3d8f;color:white;padding:14px;font-size:18px;font-weight:bold;display:flex;justify-content:space-between}
.right{width:55%;background:#eef4ff;display:flex;flex-direction:column;overflow:hidden}
.search{padding:8px;background:white;display:flex;gap:6px;border-bottom:3px solid #0a3d8f}
.search input{flex:1;padding:12px;border:2px solid #0a3d8f;border-radius:10px;font-size:14px}
.grid{flex:1;overflow-y:auto;padding:8px;display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.card{background:white;border-radius:12px;padding:10px;text-align:center;border:2px solid #c7d8ff}
.btn-pagar{padding:16px;background:#0a3d8f;color:white;border:none;font-size:18px;font-weight:bold;width:100%}
.item{padding:10px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;font-size:14px}
</style>
</head>
<body>
<div class="top">☰ MyBlle AZUL - CARRINHO GRANDE 45%</div>
<div class="main">
<div class="left">
<div style="background:#dbeafe;padding:8px;font-size:12px;font-weight:bold;color:#0a3d8f;text-align:center">CARRINHO - 45% DA TELA - GRANDE</div>
<div class="cart" id="lista"><div style="text-align:center;color:#999;margin-top:40px">Carrinho vazio<br>Toque nos produtos →</div></div>
<div class="footer"><span>TOTAL</span><span id="total">MT 0.00</span></div>
<button class="btn-pagar">PAGAR - GRANDE AZUL</button>
</div>
<div class="right">
<div class="search"><input placeholder="Busca 23b12-107"><button style="padding:10px;background:#0a3d8f;color:white;border:none;border-radius:8px">📷</button><button style="padding:10px;background:white;color:#0a3d8f;border:2px solid #0a3d8f;border-radius:8px">+ Prod</button></div>
<div class="grid" id="grid"></div>
</div>
</div>
<script>
let prods=[
{id:'23b12-107',nome:'Copo Sorvete',preco:120},
{id:'IP-3Copo',nome:'Copo Cabo',preco:15},
{id:'Chaleira',nome:'Chaleira Plast',preco:45},
{id:'Bacia',nome:'Bacia 10L',preco:80},
{id:'Balde',nome:'Balde 20L',preco:120},
{id:'Cadeira',nome:'Cadeira',preco:350},
{id:'Pote',nome:'Pote',preco:25},
{id:'Tigela',nome:'Tigela',preco:35}
];
let car=[];
function render(){
document.getElementById('grid').innerHTML=prods.map(p=>`<div class="card" onclick="addCar('${p.id}')"><div style="font-size:28px">📦</div><b style="font-size:11px;color:#0a3d8f">${p.id}</b><br><small style="font-size:10px">${p.nome}</small><br><b style="color:#0a3d8f">MT ${p.preco}</b></div>`).join('');
}
function addCar(id){let p=prods.find(x=>x.id==id);car.push({...p,qtd:1});draw();}
function draw(){
let t=0;
document.getElementById('lista').innerHTML=car.map((c,i)=>{t+=c.preco;return `<div class="item"><span><b>${c.id}</b> x1<br><small>${c.nome}</small></span><span><b>MT ${c.preco}</b><br><span onclick="car.splice(${i},1);draw()" style="color:red;font-weight:bold;cursor:pointer">X Apagar</span></span></div>`}).join('');
document.getElementById('total').innerText='MT '+t+'.00';
}
render();
</script>
</body>
</html>
"""
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
