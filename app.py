from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')

# Configurações do Flask usando variáveis de ambiente
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'delicioso-default-secret-key')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Configuração CORS
cors_origins = os.getenv('CORS_ORIGINS', '*')
if cors_origins == '*':
    CORS(app)
else:
    CORS(app, origins=cors_origins.split(','))

# Configurações do banco de dados
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///delicioso.db')
DB_FILE = DATABASE_URL.replace('sqlite:///', '') if DATABASE_URL.startswith('sqlite:///') else 'delicioso.db'

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Pedidos
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT,
        endereco TEXT,
        pagamento TEXT,
        frete REAL,
        total REAL,
        descricao TEXT,
        data_hora TEXT
    )''')
    
    # Produtos
    c.execute('''CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        preco REAL,
        id_embalagem INTEGER
    )''')
    
    # Embalagens
    c.execute('''CREATE TABLE IF NOT EXISTS embalagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        quantidade INTEGER
    )''')
    
    conn.commit()
    conn.close()

init_db()

# --- ROTAS FRONTEND ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# --- ROTAS API ---
@app.route('/api/dashboard')
def dashboard():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    filtros = []
    params = []
    if data_inicio:
        filtros.append("date(data_hora) >= ?")
        params.append(data_inicio)
    if data_fim:
        filtros.append("date(data_hora) <= ?")
        params.append(data_fim)
    
    where_clause = "WHERE " + " AND ".join(filtros) if filtros else ""
    
    # Total faturamento
    c.execute(f"SELECT SUM(total) FROM pedidos {where_clause}", params)
    faturamento_total = c.fetchone()[0] or 0.0
    
    # Total A Pagar
    c.execute(f"SELECT SUM(total) FROM pedidos {where_clause} AND pagamento='A Pagar'" if where_clause else "WHERE pagamento='A Pagar'")
    a_pagar_total = c.fetchone()[0] or 0.0
    
    # Frete
    c.execute(f"SELECT SUM(frete), COUNT(*) FROM pedidos {where_clause} AND frete>2" if where_clause else "WHERE frete>2")
    frete_maior_2, qtd_frete_maior_2 = c.fetchone() or (0,0)
    frete_maior_2 = frete_maior_2 or 0.0
    
    c.execute(f"SELECT SUM(frete), COUNT(*) FROM pedidos {where_clause} AND frete<=2" if where_clause else "WHERE frete<=2")
    frete_menor_2, qtd_frete_menor_2 = c.fetchone() or (0,0)
    frete_menor_2 = frete_menor_2 or 0.0
    
    # Pagamentos
    c.execute(f"SELECT pagamento, SUM(total) FROM pedidos {where_clause} GROUP BY pagamento", params)
    pagamentos = {row[0]: row[1] for row in c.fetchall()}
    
    # Devedores
    c.execute(f"SELECT id, cliente, total FROM pedidos {where_clause} AND pagamento='A Pagar'" if where_clause else "WHERE pagamento='A Pagar'")
    devedores = [{"id_pedido": row[0], "nome": row[1], "valor": row[2]} for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({
        "faturamento_total": faturamento_total,
        "a_pagar_total": a_pagar_total,
        "frete_maior_2": frete_maior_2,
        "qtd_frete_maior_2": qtd_frete_maior_2,
        "frete_menor_2": frete_menor_2,
        "qtd_frete_menor_2": qtd_frete_menor_2,
        "pagamentos": pagamentos,
        "devedores": devedores
    })

@app.route('/api/pedidos', methods=['GET', 'POST'])
def pedidos():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        cliente = data['cliente']
        carrinho = data['carrinho']
        
        total_itens = sum([item['subtotal'] for item in carrinho])
        frete = float(cliente.get('frete') or 0)
        total = total_itens + frete
        
        descricao = ", ".join([f"{item['qtd']}x {item['nome']}" for item in carrinho])
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        c.execute("INSERT INTO pedidos (cliente, endereco, pagamento, frete, total, descricao, data_hora) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (cliente['nome'], cliente['endereco'], cliente['pagamento'], frete, total, descricao, data_hora))
        
        # Atualiza estoque de embalagens
        avisos = []
        for item in carrinho:
            if item.get('id_embalagem'):
                c.execute("SELECT quantidade, nome FROM embalagens WHERE id=?", (item['id_embalagem'],))
                emb = c.fetchone()
                if emb:
                    qtd_atual, nome_emb = emb
                    if qtd_atual < item['qtd']:
                        avisos.append(f"Estoque insuficiente de {nome_emb}: {qtd_atual} restante.")
                        novo_qtd = 0
                    else:
                        novo_qtd = qtd_atual - item['qtd']
                    c.execute("UPDATE embalagens SET quantidade=? WHERE id=?", (novo_qtd, item['id_embalagem']))
        
        conn.commit()
        conn.close()
        return jsonify({"message": "Pedido registrado com sucesso!", "avisos": avisos})
    
    # GET
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    filtros = []
    params = []
    if data_inicio:
        filtros.append("date(data_hora) >= ?")
        params.append(data_inicio)
    if data_fim:
        filtros.append("date(data_hora) <= ?")
        params.append(data_fim)
    
    where_clause = "WHERE " + " AND ".join(filtros) if filtros else ""
    c.execute(f"SELECT id, data_hora, cliente, descricao, pagamento, total FROM pedidos {where_clause} ORDER BY id DESC", params)
    pedidos_list = [
        {
            "id": row[0],
            "data_hora": row[1],
            "cliente": row[2],
            "descricao": row[3],
            "pagamento": row[4],
            "total": row[5]
        } for row in c.fetchall()
    ]
    conn.close()
    return jsonify(pedidos_list)

@app.route('/api/produtos', methods=['GET', 'POST'])
def produtos():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        nome = data['nome']
        preco = float(data['preco'])
        id_emb = data.get('id_embalagem')
        c.execute("INSERT INTO produtos (nome, preco, id_embalagem) VALUES (?, ?, ?)", (nome, preco, id_emb))
        conn.commit()
        conn.close()
        return jsonify({"message": "Produto salvo com sucesso!"})
    
    # GET
    c.execute("SELECT p.id, p.nome, p.preco, e.nome FROM produtos p LEFT JOIN embalagens e ON p.id_embalagem=e.id")
    produtos_list = [{"id": row[0], "nome": row[1], "preco": row[2], "nome_embalagem": row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(produtos_list)

@app.route('/api/embalagens', methods=['GET', 'POST'])
def embalagens():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        nome = data['nome']
        quantidade = int(data['quantidade'])
        
        # Verifica se já existe
        c.execute("SELECT id, quantidade FROM embalagens WHERE nome=?", (nome,))
        row = c.fetchone()
        if row:
            novo_qtd = row[1] + quantidade
            c.execute("UPDATE embalagens SET quantidade=? WHERE id=?", (novo_qtd, row[0]))
        else:
            c.execute("INSERT INTO embalagens (nome, quantidade) VALUES (?, ?)", (nome, quantidade))
        conn.commit()
        conn.close()
        return jsonify({"message": "Embalagem salva com sucesso!"})
    
    # GET
    c.execute("SELECT id, nome, quantidade FROM embalagens")
    emb_list = [{"id": row[0], "nome": row[1], "quantidade": row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify(emb_list)

@app.route('/api/embalagens/editar', methods=['POST'])
def editar_estoque():
    data = request.json
    id_emb = data['id']
    quantidade = int(data['quantidade'])
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE embalagens SET quantidade=? WHERE id=?", (quantidade, id_emb))
    conn.commit()
    conn.close()
    return jsonify({"message": "Estoque atualizado com sucesso!"})

# --- ROTA RESET DB (OPCIONAL) ---
@app.route('/limpar_tudo')
def limpar_tudo():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM pedidos")
    c.execute("DELETE FROM produtos")
    c.execute("DELETE FROM embalagens")
    conn.commit()
    conn.close()
    return "Banco de dados limpo!"

# --- RUN ---
if __name__ == '__main__':
    # Configurações do servidor usando variáveis de ambiente
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🍲 Iniciando Sistema Delicioso...")
    print(f"🌐 Servidor: http://{host}:{port}")
    print(f"🔧 Debug: {debug}")
    print(f"🗄️  Banco: {DB_FILE}")
    print("=" * 50)
    
    app.run(host=host, port=port, debug=debug)
