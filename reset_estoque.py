from banco import conectar

def resetar_tabela_estoque():
    conn = conectar()
    if not conn:
        print("❌ Erro ao conectar ao banco.")
        return

    cursor = conn.cursor()

    print("⚠️ Deletando tabela antiga de estoque e recriando com as colunas corretas...")

    # Exclui a tabela antiga com estrutura incompatível
    cursor.execute("DROP TABLE IF EXISTS estoque CASCADE;")

    # Cria a nova tabela pronta para a importação
    cursor.execute("""
        CREATE TABLE estoque (
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

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tabela 'estoque' recriada com sucesso do zero!")

if __name__ == "__main__":
    resetar_tabela_estoque()