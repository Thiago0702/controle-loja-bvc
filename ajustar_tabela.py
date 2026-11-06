from banco import conectar

def recriar_estrutura_estoque():
    conn = conectar()
    if not conn:
        print("❌ Erro ao conectar ao banco.")
        return

    cursor = conn.cursor()

    print("🛠️ Ajustando colunas da tabela 'estoque'...")

    # Garante que a coluna nome_produto exista na tabela existente
    cursor.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='estoque' AND column_name='nome_produto'
            ) THEN
                ALTER TABLE estoque ADD COLUMN nome_produto VARCHAR(255);
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='estoque' AND column_name='marca'
            ) THEN
                ALTER TABLE estoque ADD COLUMN marca VARCHAR(100);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='estoque' AND column_name='modelo'
            ) THEN
                ALTER TABLE estoque ADD COLUMN modelo VARCHAR(150);
            END IF;
        END $$;
    """)

    # Adiciona restrição de Unicidade no nome do produto para evitar duplicados
    try:
        cursor.execute("ALTER TABLE estoque ADD CONSTRAINT unique_nome_produto UNIQUE (nome_produto);")
    except Exception:
        conn.rollback()  # Caso a restrição já exista
        cursor = conn.cursor()

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Colunas ajustadas com sucesso!")

if __name__ == "__main__":
    recriar_estrutura_estoque()