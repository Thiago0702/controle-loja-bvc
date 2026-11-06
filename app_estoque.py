import streamlit as st
import math
from banco import conectar  # Função de conexão com o banco

def exibir_tela_estoque():
    st.title("📱 Gestão de Estoque de Peças")

    # --- GERENCIAMENTO DE ESTADO ---
    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = 1

    if 'termo_busca_anterior' not in st.session_state:
        st.session_state.termo_busca_anterior = ""

    # 1. Seleção por Abas (Radio Button)
    abas = ["📱 Telas", "🔋 Baterias", "📦 Tampas Traseiras", "🔌 Doc de Carga"]
    aba_selecionada = st.radio("Selecione a Categoria:", abas, horizontal=True)

    categoria_map = {
        "📱 Telas": "Tela",
        "🔋 Baterias": "Bateria",
        "📦 Tampas Traseiras": "Tampa Traseira",
        "🔌 Doc de Carga": "Doc de Carga"
    }
    categoria_atual = categoria_map[aba_selecionada]

    # Reset da página se mudar a aba
    if 'aba_anterior' not in st.session_state or st.session_state.aba_anterior != aba_selecionada:
        st.session_state.pagina_atual = 1
        st.session_state.aba_anterior = aba_selecionada

    # 2. Barra de Pesquisa Rápida
    st.markdown("---")
    termo_busca = st.text_input("🔍 Buscar por Modelo ou Marca (ex: A10, Moto G8, iPhone 11):", value="")

    # Reset da página se o termo de busca mudar
    if termo_busca != st.session_state.termo_busca_anterior:
        st.session_state.pagina_atual = 1
        st.session_state.termo_busca_anterior = termo_busca

    ITENS_POR_PAGINA = 15

    # 3. Funções de Banco de Dados
    def buscar_estoque(categoria, busca="", pagina=1):
        conn = conectar()
        if not conn:
            st.error("Erro de conexão com o banco de dados.")
            return [], 0

        try:
            cursor = conn.cursor()
            offset = (pagina - 1) * ITENS_POR_PAGINA

            condicao_busca = ""
            parametros = [categoria]

            if busca.strip():
                condicao_busca = " AND (nome_produto ILIKE %s OR marca ILIKE %s OR modelo ILIKE %s)"
                termo = f"%{busca.strip()}%"
                parametros.extend([termo, termo, termo])

            # Contagem total para a paginação
            query_count = f"SELECT COUNT(*) FROM estoque WHERE categoria = %s {condicao_busca};"
            cursor.execute(query_count, parametros)
            total_registros = cursor.fetchone()[0]

            # Busca dos registros paginados
            query_dados = f"""
                SELECT id, nome_produto, marca, modelo, quantidade, preco_custo, preco_venda
                FROM estoque
                WHERE categoria = %s {condicao_busca}
                ORDER BY marca ASC, modelo ASC
                LIMIT %s OFFSET %s;
            """
            parametros_busca = parametros + [ITENS_POR_PAGINA, offset]
            cursor.execute(query_dados, parametros_busca)
            produtos = cursor.fetchall()

            return produtos, total_registros
        except Exception as e:
            st.error(f"Erro ao consultar banco de dados: {e}")
            return [], 0
        finally:
            cursor.close()
            conn.close()

    def atualizar_produto(produto_id, nova_qtd, novo_custo, novo_venda):
        conn = conectar()
        if not conn:
            st.error("Erro ao conectar ao banco de dados.")
            return False

        try:
            cursor = conn.cursor()
            query = """
                UPDATE estoque 
                SET quantidade = %s, preco_custo = %s, preco_venda = %s 
                WHERE id = %s;
            """
            cursor.execute(query, (nova_qtd, novo_custo, novo_venda, produto_id))
            conn.commit()
            return True
        except Exception as e:
            st.error(f"Erro ao atualizar produto #{produto_id}: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    # 4. Carregamento dos dados sob demanda
    produtos, total_registros = buscar_estoque(categoria_atual, termo_busca, st.session_state.pagina_atual)
    total_paginas = math.ceil(total_registros / ITENS_POR_PAGINA) if total_registros > 0 else 1

    st.subheader(f"Catálogo: {aba_selecionada} — {total_registros} modelos encontrados")

    # 5. Lista de Produtos Interativa
    if produtos:
        c_id, c_nome, c_qtd, c_custo, c_venda, c_acao = st.columns([1, 4, 2, 2, 2, 2])
        c_id.markdown("**ID**")
        c_nome.markdown("**Produto / Modelo**")
        c_qtd.markdown("**Qtd Atual**")
        c_custo.markdown("**Custo (R$)**")
        c_venda.markdown("**Venda (R$)**")
        c_acao.markdown("**Ação**")

        st.markdown("---")

        for prod in produtos:
            p_id, p_nome, p_marca, p_modelo, p_qtd, p_custo, p_venda = prod

            col1, col2, col3, col4, col5, col6 = st.columns([1, 4, 2, 2, 2, 2])

            col1.write(f"#{p_id}")
            col2.write(f"**{p_marca}** - {p_modelo}")

            nova_qtd = col3.number_input(f"Qtd {p_id}", min_value=0, value=int(p_qtd), key=f"qtd_{p_id}", label_visibility="collapsed")
            novo_custo = col4.number_input(f"Custo {p_id}", min_value=0.0, value=float(p_custo), step=5.0, key=f"custo_{p_id}", label_visibility="collapsed")
            novo_venda = col5.number_input(f"Venda {p_id}", min_value=0.0, value=float(p_venda), step=5.0, key=f"venda_{p_id}", label_visibility="collapsed")

            if col6.button("💾 Salvar", key=f"btn_{p_id}"):
                if atualizar_produto(p_id, nova_qtd, novo_custo, novo_venda):
                    st.toast(f"✅ {p_modelo} atualizado com sucesso!", icon="🎉")
                    st.rerun()
    else:
        st.info("Nenhum item encontrado nesta categoria ou com esse filtro de busca.")

    # 6. Rodapé com Controles de Paginação
    st.markdown("---")
    col_prev, col_info, col_next = st.columns([1, 2, 1])

    with col_prev:
        if st.button("⬅️ Página Anterior", disabled=(st.session_state.pagina_atual <= 1), use_container_width=True):
            st.session_state.pagina_atual -= 1
            st.rerun()

    with col_info:
        st.markdown(f"<h5 style='text-align: center;'>Página {st.session_state.pagina_atual} de {total_paginas}</h5>", unsafe_allow_html=True)

    with col_next:
        if st.button("Próxima Página ➡️", disabled=(st.session_state.pagina_atual >= total_paginas), use_container_width=True):
            st.session_state.pagina_atual += 1
            st.rerun()