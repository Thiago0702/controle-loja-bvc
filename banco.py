# banco.py
import psycopg2

# Configurações do Supabase
DB_HOST = "aws-0-sa-east-1.pooler.supabase.com"
DB_NAME = "postgres"
DB_USER = "postgres.nsnepywkqfhiyvphzyaz"
DB_PASS = "zayapereira220613"

# Tente primeiro a porta 5432 (Session Mode do Pooler), 
# se não funcionar altere para "6543"
DB_PORT = "5432" 

def conectar():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            sslmode="require"  # <--- OBRIGATÓRIO PARA O SUPABASE
        )
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao Supabase: {e}")
        return None

def criar_tabelas():
    conn = conectar()
    if not conn:
        print("❌ Não foi possível conectar ao banco de dados para criar as tabelas.")
        return

    cursor = conn.cursor()

    # Tabela de estoque
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id SERIAL PRIMARY KEY,
            nome_produto VARCHAR(255) UNIQUE NOT NULL,
            quantidade INT DEFAULT 0,
            qtd_minima INT DEFAULT 1,
            qtd_maxima INT DEFAULT 3,
            preco_custo NUMERIC(10, 2) DEFAULT 0.0,
            preco_venda NUMERIC(10, 2) DEFAULT 0.0,
            categoria VARCHAR(100),
            marca VARCHAR(100),
            modelo VARCHAR(150)
        );
    """)

    # Tabela de vendas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id SERIAL PRIMARY KEY,
            cliente VARCHAR(255) DEFAULT 'Consumidor Final',
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total NUMERIC(10, 2) DEFAULT 0.0,
            pagamento VARCHAR(50)
        );
    """)

    # Tabela de itens da venda
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_venda (
            id SERIAL PRIMARY KEY,
            venda_id INT REFERENCES vendas(id) ON DELETE CASCADE,
            descricao VARCHAR(255),
            valor NUMERIC(10, 2)
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Conexão estabelecida e tabelas prontas no Supabase!")

if __name__ == "__main__":
    criar_tabelas()