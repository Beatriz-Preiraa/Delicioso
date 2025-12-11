from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime
import os

app = Flask(__name__)
# Nome do arquivo de banco de dados
DB_NAME = "delivery_web.db"

# Função para obter a conexão com o banco de dados
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Retorna linhas como dicionários (acessíveis por nome da coluna)
    return conn

# Função para inicializar o banco de dados e criar tabelas
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Tabela Embalagens (Estoque)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embalagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            quantidade INTEGER DEFAULT 0
        )
    """)
    
    # 2. Tabela Produtos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            preco REAL NOT NULL,
            id_embalagem INTEGER,
            FOREIGN KEY(id_embalagem) REFERENCES embalagens(id)
        )
    """)
    
    # 3. Tabela Pedidos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            endereco TEXT,
            frete REAL,
            pagamento TEXT,
            data_hora TIMESTAMP,
            total REAL
        )
    """)
    
    # 4. Tabela Itens do Pedido
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pedido INTEGER,
            produto_nome TEXT,
            quantidade INTEGER,
            valor_unitario REAL,
            FOREIGN KEY(id_pedido) REFERENCES pedidos(id)
        )
    """)
    conn.commit()
    conn.close()

# Função auxiliar para remover o banco de dados (para começar do zero)
def excluir_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Banco de dados '{DB_NAME}' excluído.")
    # Recria o banco vazio
    init_db()
    print(f"Banco de dados '{DB_NAME}' reinicializado.")


# --- ROTAS DE NAVEGAÇÃO ---

@app.route('/')
def index():
    # Renderiza a página principal
    return render_template('index.html')

@app.route('/limpar_tudo')
def limpar_tudo():
    # Rota para limpar o banco de dados
    excluir_db()
    return "Banco de dados limpo! <a href='/'>Voltar para o Início</a>"


# --- API: DASHBOARD ---
@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    hoje = datetime.datetime.now().strftime("%Y-%m-%d")
    if not data_inicio: data_inicio = hoje
    if not data_fim: data_fim = hoje

    conn = get_db_connection()
    
    # Busca pedidos dentro do intervalo (do inicio do dia até o fim do dia)
    query = "SELECT * FROM pedidos WHERE data_hora >= ? AND data_hora <= ?"
    pedidos = conn.execute(query, (f"{data_inicio} 00:00:00", f"{data_fim} 23:59:59")).fetchall()
    conn.close()

    stats = {
        "faturamento_total": 0.0,
        "frete_maior_2": 0.0, 
        "qtd_frete_maior_2": 0, 
        "frete_menor_2": 0.0, 
        "qtd_frete_menor_2": 0, 
        "pagamentos": {}, 
        "a_pagar_total": 0.0, 
        "devedores": [] 
    }

    for p in pedidos:
        valor_total = p['total']
        valor_frete = p['frete'] if p['frete'] is not None else 0.0
        metodo = p['pagamento']
        cliente = p['cliente']

        stats["faturamento_total"] += valor_total

        if valor_frete > 2:
            stats["frete_maior_2"] += valor_frete
            stats["qtd_frete_maior_2"] += 1
        else:
            stats["frete_menor_2"] += valor_frete
            stats["qtd_frete_menor_2"] += 1

        if metodo not in stats["pagamentos"]:
            stats["pagamentos"][metodo] = 0.0
        stats["pagamentos"][metodo] += valor_total

        if metodo == "A Pagar":
            stats["a_pagar_total"] += valor_total
            stats["devedores"].append({
                "id_pedido": p['id'],
                "nome": cliente,
                "valor": valor_total
            })

    return jsonify(stats)

# --- API: PEDIDOS ---
@app.route('/api/pedidos', methods=['GET', 'POST'])
def api_pedidos():
    conn = get_db_connection()
    
    # Criar Novo Pedido
    if request.method == 'POST':
        data = request.json
        carrinho = data.get('carrinho', [])
        cliente = data.get('cliente')
        
        try:
            # Garante que frete seja um float, mesmo se a string for vazia
            frete_val = float(cliente.get('frete') or 0)
        except:
            frete_val = 0.0

        total_produtos = sum(item['subtotal'] for item in carrinho)
        total_pedido = total_produtos + frete_val
        data_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor = conn.execute("""
                INSERT INTO pedidos (cliente, endereco, frete, pagamento, data_hora, total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cliente['nome'], cliente['endereco'], frete_val, cliente['pagamento'], data_hora, total_pedido))
            
            id_pedido = cursor.lastrowid
            avisos = []

            # Inserir itens e baixar estoque
            for item in carrinho:
                conn.execute("""
                    INSERT INTO itens_pedido (id_pedido, produto_nome, quantidade, valor_unitario)
                    VALUES (?, ?, ?, ?)
                """, (id_pedido, item['nome'], item['qtd'], item['preco']))
                
                if item.get('id_embalagem'):
                    emb = conn.execute("SELECT id, nome, quantidade FROM embalagens WHERE id = ?", (item['id_embalagem'],)).fetchone()
                    if emb:
                        novo_estoque = emb['quantidade'] - item['qtd']
                        conn.execute("UPDATE embalagens SET quantidade = ? WHERE id = ?", (novo_estoque, emb['id']))
                        
                        if novo_estoque < 5:
                            avisos.append(f"Estoque de {emb['nome']} está baixo ({novo_estoque})!")

            conn.commit()
            return jsonify({"message": "Pedido realizado com sucesso!", "avisos": avisos})
        except Exception as e:
            conn.rollback()
            return jsonify({"message": f"Erro ao salvar pedido: {str(e)}", "avisos": []}), 500
        finally:
            conn.close()


    # Listar Pedidos com Filtro de Data
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    try:
        query = "SELECT * FROM pedidos"
        params = []

        if data_inicio and data_fim:
            query += " WHERE data_hora >= ? AND data_hora <= ?"
            params.append(f"{data_inicio} 00:00:00")
            params.append(f"{data_fim} 23:59:59")
        
        query += " ORDER BY id DESC"
        
        pedidos = conn.execute(query, params).fetchall()
        
        lista_pedidos = []
        for p in pedidos:
            p_dict = dict(p)
            # Busca itens do pedido em uma nova conexão (para evitar problemas de thread se o app crescer)
            itens_conn = get_db_connection() 
            itens = itens_conn.execute("SELECT produto_nome, quantidade FROM itens_pedido WHERE id_pedido = ?", (p['id'],)).fetchall()
            itens_conn.close()
            
            descricao_itens = ", ".join([f"{i['quantidade']}x {i['produto_nome']}" for i in itens])
            p_dict['descricao'] = descricao_itens
            lista_pedidos.append(p_dict)
            
        return jsonify(lista_pedidos)
    finally:
        conn.close()

# --- API: EMBALAGENS (ADICIONAR/CRIAR) ---
@app.route('/api/embalagens', methods=['GET', 'POST'])
def api_embalagens():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.json
        nome = data.get('nome').strip()
        qtd = int(data.get('quantidade'))
        
        try:
            # Tenta encontrar embalagem existente
            existing = conn.execute("SELECT id, quantidade FROM embalagens WHERE nome = ?", (nome,)).fetchone()
            if existing:
                # Se existe, soma a quantidade
                nova_qtd = existing['quantidade'] + qtd
                conn.execute("UPDATE embalagens SET quantidade = ? WHERE id = ?", (nova_qtd, existing['id']))
            else:
                # Se não existe, insere
                conn.execute("INSERT INTO embalagens (nome, quantidade) VALUES (?, ?)", (nome, qtd))
            
            conn.commit()
            return jsonify({"message": "Estoque atualizado!"})
        except Exception as e:
            conn.rollback()
            return jsonify({"message": f"Erro ao atualizar estoque: {str(e)}"}, 500)
        finally:
            conn.close()
    
    # Listar embalagens
    try:
        embalagens = conn.execute("SELECT * FROM embalagens ORDER BY nome ASC").fetchall()
        return jsonify([dict(ix) for ix in embalagens])
    finally:
        conn.close()

# --- API: EMBALAGENS (EDITAR QUANTIDADE DIRETAMENTE) ---
@app.route('/api/embalagens/editar', methods=['POST'])
def api_embalagens_editar():
    conn = get_db_connection()
    data = request.json
    id_emb = data.get('id')
    
    try:
        nova_quantidade = int(data.get('quantidade'))
        conn.execute("UPDATE embalagens SET quantidade = ? WHERE id = ?", (nova_quantidade, id_emb))
        conn.commit()
        return jsonify({"message": "Quantidade corrigida com sucesso!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Erro ao corrigir quantidade: {str(e)}"}, 500)
    finally:
        conn.close()

# --- API: PRODUTOS ---
@app.route('/api/produtos', methods=['GET', 'POST'])
def api_produtos():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.json
        nome = data['nome'].strip()
        preco = float(data['preco'])
        id_embalagem = data.get('id_embalagem')
        
        try:
            conn.execute("INSERT INTO produtos (nome, preco, id_embalagem) VALUES (?, ?, ?)",
                         (nome, preco, id_embalagem))
            conn.commit()
            return jsonify({"message": "Produto cadastrado com sucesso!"})
        except sqlite3.IntegrityError:
             return jsonify({"message": "Erro: Produto com este nome já existe ou embalagem inválida."}, 400)
        except Exception as e:
            conn.rollback()
            return jsonify({"message": f"Erro ao cadastrar produto: {str(e)}"}, 500)
        finally:
            conn.close()

    # Listar produtos (GET)
    try:
        query = """
            SELECT p.id, p.nome, p.preco, p.id_embalagem, IFNULL(e.nome, 'Nenhuma') as nome_embalagem
            FROM produtos p
            LEFT JOIN embalagens e ON p.id_embalagem = e.id
            ORDER BY p.nome ASC
        """
        produtos = conn.execute(query).fetchall()
        return jsonify([dict(ix) for ix in produtos])
    finally:
        conn.close()

if __name__ == '__main__':
    # Verifica se o arquivo DB existe. Se não existir, inicializa as tabelas.
    if not os.path.exists(DB_NAME):
        init_db()
    app.run(debug=True, port=5000)