#!/usr/bin/env python3
"""
Script de inicialização do Sistema Delicioso
Facilita o desenvolvimento e deploy local
"""

import os
import sys
from app import app, init_db

def setup_environment():
    """Configura o ambiente de desenvolvimento"""
    # Carrega variáveis de ambiente se existir arquivo .env
    if os.path.exists('.env'):
        print("📄 Carregando variáveis de ambiente...")
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Variáveis de ambiente carregadas")
        except ImportError:
            print("⚠️  python-dotenv não instalado, carregando manualmente...")
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    else:
        print("⚠️  Arquivo .env não encontrado, usando configurações padrão")

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    try:
        import flask
        import flask_cors
        try:
            import dotenv
            print("✅ Todas as dependências verificadas (incluindo python-dotenv)")
        except ImportError:
            print("✅ Dependências básicas verificadas (python-dotenv opcional)")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("Execute: pip install -r requirements.txt")
        return False

def initialize_database():
    """Inicializa o banco de dados"""
    print("🗄️  Inicializando banco de dados...")
    init_db()
    print("✅ Banco de dados pronto")

def main():
    """Função principal"""
    print("🍲 Iniciando Sistema Delicioso...")
    print("=" * 50)
    
    # Verifica dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Configura ambiente
    setup_environment()
    
    # Inicializa banco
    initialize_database()
    
    # Configurações do servidor
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🌐 Servidor iniciando em http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print("=" * 50)
    
    # Inicia o servidor
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n👋 Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()