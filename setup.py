#!/usr/bin/env python3
"""
Script de configuração inicial do Sistema Delicioso
Facilita a configuração do ambiente de desenvolvimento
"""

import os
import sys
import secrets
import getpass

def generate_secret_key():
    """Gera uma chave secreta segura"""
    return secrets.token_urlsafe(32)

def setup_environment():
    """Configura o arquivo .env interativamente"""
    print("🍲 Configuração Inicial do Sistema Delicioso")
    print("=" * 50)
    
    # Verifica se .env já existe
    if os.path.exists('.env'):
        response = input("📄 Arquivo .env já existe. Deseja recriar? (s/N): ")
        if response.lower() not in ['s', 'sim', 'y', 'yes']:
            print("✅ Mantendo configuração existente")
            return
    
    print("\n🔧 Configurando ambiente de desenvolvimento...")
    
    # Coleta informações do usuário
    admin_user = input("👤 Usuário admin (padrão: admin): ") or "admin"
    admin_password = getpass.getpass("🔐 Senha admin (padrão: 1234): ") or "1234"
    port = input("🌐 Porta do servidor (padrão: 5000): ") or "5000"
    debug = input("🐛 Modo debug? (S/n): ").lower() not in ['n', 'no', 'não']
    
    # Gera chave secreta
    secret_key = generate_secret_key()
    
    # Cria conteúdo do .env
    env_content = f"""# Configurações do Sistema Delicioso
# Arquivo gerado automaticamente pelo setup.py

# Configurações do Flask
FLASK_ENV=development
FLASK_DEBUG={str(debug).lower()}
SECRET_KEY={secret_key}

# Configurações do Banco de Dados
DATABASE_URL=sqlite:///delicioso.db

# Configurações de Autenticação
ADMIN_USER={admin_user}
ADMIN_PASSWORD={admin_password}

# Configurações do Servidor
PORT={port}
HOST=0.0.0.0

# Configurações de CORS
CORS_ORIGINS=*

# Configurações de Log
LOG_LEVEL=INFO
"""
    
    # Escreve o arquivo .env
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("\n✅ Arquivo .env criado com sucesso!")
    print(f"👤 Usuário: {admin_user}")
    print(f"🔐 Senha: {'*' * len(admin_password)}")
    print(f"🌐 Porta: {port}")
    print(f"🐛 Debug: {debug}")

def install_dependencies():
    """Instala as dependências do projeto"""
    print("\n📦 Instalando dependências...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependências instaladas com sucesso!")
        else:
            print(f"❌ Erro ao instalar dependências: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False
    
    return True

def initialize_database():
    """Inicializa o banco de dados"""
    print("\n🗄️  Inicializando banco de dados...")
    
    try:
        from app import init_db
        init_db()
        print("✅ Banco de dados inicializado!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False
    
    return True

def main():
    """Função principal do setup"""
    print("🍲 Setup do Sistema Delicioso")
    print("=" * 50)
    
    # Verifica se está no diretório correto
    if not os.path.exists('app.py'):
        print("❌ Execute este script no diretório raiz do projeto")
        sys.exit(1)
    
    # Menu de opções
    print("\nEscolha uma opção:")
    print("1. Configuração completa (recomendado)")
    print("2. Apenas configurar .env")
    print("3. Apenas instalar dependências")
    print("4. Apenas inicializar banco")
    print("0. Sair")
    
    choice = input("\nOpção: ")
    
    if choice == '1':
        # Configuração completa
        setup_environment()
        if install_dependencies():
            initialize_database()
        print("\n🎉 Configuração completa!")
        print("\n🚀 Para iniciar o sistema:")
        print("   python app.py")
        print("   ou")
        print("   python run.py")
        
    elif choice == '2':
        setup_environment()
        
    elif choice == '3':
        install_dependencies()
        
    elif choice == '4':
        initialize_database()
        
    elif choice == '0':
        print("👋 Saindo...")
        
    else:
        print("❌ Opção inválida")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante o setup: {e}")
        sys.exit(1)