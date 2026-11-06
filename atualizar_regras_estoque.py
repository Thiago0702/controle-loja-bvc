from banco import conectar

def atualizar_limites_categorias():
    conn = conectar()
    if not conn:
        print("❌ Erro ao conectar ao banco.")
        return

    cursor = conn.cursor()

    print("🚀 Atualizando limites de Mínimo e Máximo por categoria...")

    # Define os limites específicos exigidos por categoria
    regras = [
        ("Tela", 1, 3),
        ("Bateria", 1, 2),
        ("Tampa Traseira", 3, 4),
        ("Doc de Carga", 1, 5)
    ]

    for categoria, min_qtd, max_qtd in regras:
        cursor.execute("""
            UPDATE estoque 
            SET qtd_minima = %s, qtd_maxima = %s 
            WHERE categoria = %s;
        """, (min_qtd, max_qtd, categoria))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Limites atualizados com sucesso no banco de dados!")


def obter_status_estoque(quantidade, min_qtd, max_qtd):
    """
    Retorna o status e a cor correspondente para alertas visuais:
    🔴 VERMELHO: Crítico / Necessita de reposição imediata (<= Mínimo)
    🟡 AMARELO: Atenção / Próximo do limite
    🟢 VERDE: OK / Nível ideal de estoque
    🔵 AZUL: Excesso / Acima do limite máximo
    """
    if quantidade <= min_qtd:
        return {"status": "CRÍTICO (REPOR)", "cor": "🔴 VERMELHO", "codigo_hex": "#FF4D4D"}
    elif quantidade >= max_qtd:
        return {"status": "EXCESSO DE ESTOQUE", "cor": "🔵 AZUL", "codigo_hex": "#4DA6FF"}
    elif quantidade == min_qtd + 1 and max_qtd - min_qtd > 1:
        return {"status": "ATENÇÃO", "cor": "🟡 AMARELO", "codigo_hex": "#FFD700"}
    else:
        return {"status": "OK", "cor": "🟢 VERDE", "codigo_hex": "#4CAF50"}


def consultar_alertas():
    conn = conectar()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute("""
        SELECT nome_produto, categoria, quantidade, qtd_minima, qtd_maxima 
        FROM estoque 
        ORDER BY categoria, nome_produto;
    """)
    produtos = cursor.fetchall()

    print("\n--- RELATÓRIO DE ALERTAS DE ESTOQUE ---")
    for nome, categoria, qtd, min_q, max_q in produtos:
        alerta = obter_status_estoque(qtd, min_q, max_q)
        # Exibe apenas itens críticos ou com alerta ativo no console
        if alerta["cor"] in ["🔴 VERMELHO", "🟡 AMARELO", "🔵 AZUL"]:
            print(f"{alerta['cor']} | [{categoria}] {nome} | Qtd: {qtd} (Min: {min_q} / Max: {max_q}) -> Status: {alerta['status']}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    atualizar_limites_categorias()
    consultar_alertas()