

import customtkinter as ctk
import psycopg2
from datetime import datetime
from banco import conectar
from PIL import Image
import os
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
import threading


def gerar_comprovante_pdf(venda_id, cliente_nome, itens, total, forma_pagamento, nome_empresa):
    if not os.path.exists("comprovantes"):
        os.makedirs("comprovantes")
        
    caminho_arquivo = os.path.abspath(f"comprovantes/Comprovante_Venda_{venda_id}.pdf")
    pdf = canvas.Canvas(caminho_arquivo, pagesize=A6)
    largura, altura = A6
    
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(largura / 2, altura - 25, str(nome_empresa))
    
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(largura / 2, altura - 37, "Rua Azaleia, 04 - Vargem Grande | Tel: (11) 94326-1287")
    pdf.line(10, altura - 45, largura - 10, altura - 45)
    
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(15, altura - 60, f"Comprovante nº: {int(venda_id):04d}")
    
    pdf.setFont("Helvetica", 8)
    data_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.drawString(15, altura - 72, f"Data: {data_str}")
    pdf.drawString(15, altura - 84, f"Cliente: {str(cliente_nome)}")
    pdf.line(10, altura - 92, largura - 10, altura - 92)
    
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(15, altura - 105, "Descrição / Serviço")
    pdf.drawRightString(largura - 15, altura - 105, "Valor (R$)")
    
    y = altura - 120
    pdf.setFont("Helvetica", 8)
    
    for item in itens:
        desc = str(item[0])
        valor = float(item[1])
        if len(desc) > 28:
            desc = desc[:25] + "..."
        pdf.drawString(15, y, desc)
        pdf.drawRightString(largura - 15, y, f"{valor:.2f}")
        y -= 14
        
    pdf.line(10, y + 4, largura - 10, y + 4)
    y -= 14
    
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(15, y, "Total Pago:")
    pdf.drawRightString(largura - 15, y, f"R$ {float(total):.2f}")
    
    y -= 14
    pdf.setFont("Helvetica", 8)
    pdf.drawString(15, y, f"Forma de Pagamento: {str(forma_pagamento)}")
    
    pdf.setFont("Helvetica-Oblique", 7)
    pdf.drawCentredString(largura / 2, 15, "Obrigado pela preferência!")
    
    pdf.save()
    
    try:
        os.startfile(caminho_arquivo)
    except Exception as e:
        print(f"Erro ao abrir o PDF automaticamente: {e}")
        
    return caminho_arquivo


# ==========================================
# CONFIGURAÇÕES DE INTERFACE E CORES
# ==========================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COR_FUNDO = "#0b1329"
COR_CARD = "#17233d"
COR_CARD_ITEM = "#202d4a"
COR_PRIMARIA = "#2563eb"
COR_PRIMARIA_HOVER = "#1d4ed8"
COR_SUCESSO = "#16a34a"
COR_SUCESSO_HOVER = "#15803d"
COR_ERRO = "#dc2626"
COR_TEXTO = "white"
COR_DESTAQUE = "#f59e0b"
COR_TEXTO_SECUNDARIO = "#94a3b8"
COR_TEXTO_VALOR = "#38bdf8"

FONTE_TITULO = ("Arial", 20, "bold")
FONTE_SUBTITULO = ("Arial", 14, "bold")
FONTE_CORPO = ("Arial", 12)
FONTE_LEGENDA = ("Arial", 10)

class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Sistema de Gestão - Loja BVC (Supabase)")
        self.geometry("1150x700")
        self.configure(fg_color=COR_FUNDO)

        self.usuario_atual = ""
        self.carrinho_pdv = []
        self.peca_em_edicao_id = None
        self.header_frame = None  # Variável para controlar o cabeçalho

        # 1. Container principal da janela (mantém tudo)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # 2. Container exclusivo na parte de baixo para alternar as telas
        self.body_container = ctk.CTkFrame(self.container, fg_color="transparent")
        self.body_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Inicia direto na tela de login
        self.mostrar_tela_login()

    def limpar_container(self):
        for widget in self.body_container.winfo_children():
            widget.destroy()

    def criar_cabecalho(self):
        if self.header_frame:
            self.header_frame.destroy()

        self.header_frame = ctk.CTkFrame(
            self.container, height=45, fg_color=COR_CARD, corner_radius=0
        )
        self.header_frame.pack(fill="x", side="top", before=self.body_container)

        lbl_user = ctk.CTkLabel(
            self.header_frame,
            text=f"👤 Usuário: {self.usuario_atual}",
            font=("Arial", 12, "bold"),
        )
        lbl_user.pack(side="left", padx=15, pady=8)

        # Botão Sair na extrema direita
        btn_sair = ctk.CTkButton(
            self.header_frame,
            text="🚪 Sair",
            width=65,
            fg_color="#b91c1c",
            hover_color="#991b1b",
            command=self.mostrar_tela_login,
        )
        btn_sair.pack(side="right", padx=10, pady=8)

        # Container para alinhar os botões de navegação no topo perfeitamente
        btn_nav_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        btn_nav_frame.pack(side="right", padx=5, pady=6)

        ctk.CTkButton(
            btn_nav_frame,
            text="🛒 PDV",
            width=80,
            command=self.mostrar_tela_pdv,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btn_nav_frame,
            text="📦 Comandas",
            width=95,
            command=self.mostrar_tela_comandas,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btn_nav_frame,
            text="🛠️ O.S.",
            width=80,
            command=self.mostrar_tela_os,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btn_nav_frame,
            text="📦 Estoque",
            width=80,
            command=self.mostrar_tela_estoque,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btn_nav_frame,
            text="📊 Relatórios",
            width=80,
            command=self.mostrar_tela_relatorios,
        ).pack(side="left", padx=3)

    def mostrar_tela_login(self):
        self.limpar_container()

        if self.header_frame:
            self.header_frame.destroy()
            self.header_frame = None

        self.usuario_atual = ""

        try:
            self.iconbitmap("icone.ico")
        except:
            pass

        try:
            self.imagem_fundo_raw = Image.open("fundo.png")
            largura = self.winfo_width() if self.winfo_width() > 700 else 1380
            altura = self.winfo_height() if self.winfo_height() > 700 else 730
            self.bg_image = ctk.CTkImage(
                light_image=self.imagem_fundo_raw,
                dark_image=self.imagem_fundo_raw,
                size=(largura, altura),
            )
            self.lbl_fundo = ctk.CTkLabel(
                self.body_container, image=self.bg_image, text=""
            )
            self.lbl_fundo.place(relwidth=1, relheight=1)
        except Exception as e:
            print(f"Erro ao carregar fundo: {e}")

        frame_login = ctk.CTkFrame(
            self.body_container, width=360, height=480, fg_color=COR_CARD, corner_radius=12
        )
        frame_login.place(relx=0.5, rely=0.5, anchor="center")
        frame_login.pack_propagate(False)

        ctk.CTkLabel(
            frame_login, text="Acesso ao Sistema", font=FONTE_TITULO
        ).pack(pady=(20, 10))

        ent_usuario = ctk.CTkEntry(
            frame_login, placeholder_text="Usuário", width=280
        )
        ent_usuario.pack(pady=6)

        ent_senha = ctk.CTkEntry(
            frame_login, placeholder_text="Senha", show="*", width=280
        )
        ent_senha.pack(pady=6)

        lbl_erro = ctk.CTkLabel(
            frame_login, text="", text_color=COR_ERRO, font=FONTE_LEGENDA
        )
        lbl_erro.pack(pady=2)

        def autenticar():
            usr = ent_usuario.get().strip()
            pwd = ent_senha.get().strip()

            if not usr or not pwd:
                lbl_erro.configure(text="Preencha todos os campos!")
                return

            try:
                conn = conectar()
                if not conn:
                    lbl_erro.configure(text="Erro de conexão com o banco!")
                    return

                cursor = conn.cursor()
                sql = "SELECT * FROM usuarios WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) AND senha = %s"
                cursor.execute(sql, (usr, pwd))
                user_db = cursor.fetchone()

                cursor.close()
                conn.close()

                if user_db:
                    self.usuario_atual = usr
                    self.criar_cabecalho()
                    self.mostrar_tela_pdv()
                else:
                    lbl_erro.configure(text="Usuário ou senha incorretos!")
            except Exception as ex:
                print(f"[LOGIN EXCEPTION] {ex}")
                lbl_erro.configure(text="Erro ao conectar ao banco!")

        btn_entrar = ctk.CTkButton(
            frame_login,
            text="Entrar",
            command=autenticar,
            width=280,
            fg_color=COR_PRIMARIA,
            hover_color=COR_PRIMARIA_HOVER,
        )
        btn_entrar.pack(pady=(8, 5))

        btn_ir_cadastro = ctk.CTkButton(
            frame_login,
            text="Criar Nova Conta",
            fg_color="transparent",
            text_color="#38bdf8",
            hover_color="#334155",
            command=self.mostrar_tela_cadastro,
            width=280,
        )
        btn_ir_cadastro.pack(pady=2)

        btn_ir_recuperar = ctk.CTkButton(
            frame_login,
            text="Esqueci minha senha",
            fg_color="transparent",
            text_color="#94a3b8",
            hover_color="#334155",
            command=self.mostrar_tela_recuperar,
            width=280,
        )
        btn_ir_recuperar.pack(pady=2)

    def mostrar_tela_pdv(self):
        self.limpar_container()
        body = ctk.CTkFrame(self.body_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(
            body, text="Tela de PDV - Vendas Rápidas", font=FONTE_TITULO
        ).pack(pady=20)

    def mostrar_tela_comandas(self):
        self.limpar_container()

        body = ctk.CTkFrame(self.body_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        left = ctk.CTkFrame(body, width=300, fg_color=COR_CARD)
        left.pack(side="left", fill="both", padx=(0, 5))
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Lojistas / Comandas", font=FONTE_SUBTITULO).pack(
            pady=(12, 6)
        )

        scroll_clientes = ctk.CTkScrollableFrame(left, fg_color="transparent")
        scroll_clientes.pack(fill="both", expand=True, padx=5, pady=5)

        right = ctk.CTkFrame(body, fg_color=COR_CARD)
        right.pack(side="right", fill="both", expand=True, padx=(5, 0))

        lbl_titulo_comanda = ctk.CTkLabel(
            right, text="Selecione um lojista ao lado", font=FONTE_SUBTITULO
        )
        lbl_titulo_comanda.pack(pady=(10, 2))

        # Campo de Frete visível no topo do painel direito
        frame_frete = ctk.CTkFrame(right, fg_color="transparent")
        frame_frete.pack(fill="x", padx=10, pady=4)
        
        ctk.CTkLabel(frame_frete, text="Valor do Frete (R$):", font=FONTE_CORPO).pack(side="left", padx=5)
        ent_frete = ctk.CTkEntry(frame_frete, width=120, placeholder_text="0.00")
        ent_frete.pack(side="left", padx=5)
        ent_frete.insert(0, "0,00")

        # --- CAIXA DE OBSERVAÇÃO DA COMANDA ---
        frame_obs = ctk.CTkFrame(right, fg_color="transparent")
        frame_obs.pack(fill="x", padx=10, pady=4)
        
        ctk.CTkLabel(frame_obs, text="Observações do Pedido:", font=FONTE_LEGENDA, anchor="w").pack(fill="x", padx=5, pady=(0, 2))
        txt_observacao = ctk.CTkTextbox(frame_obs, height=45, font=FONTE_CORPO)
        txt_observacao.pack(fill="x", padx=5)

        scroll_itens_comanda = ctk.CTkScrollableFrame(
            right, fg_color="transparent"
        )
        scroll_itens_comanda.pack(fill="both", expand=True, padx=10, pady=5)

        lbl_total_comanda = ctk.CTkLabel(
            right,
            text="Total da Comanda: R$ 0,00",
            font=FONTE_TITULO,
            text_color=COR_TEXTO_VALOR,
        )
        lbl_total_comanda.pack(pady=5)

        btn_fechar_comanda = ctk.CTkButton(
            right,
            text="✔️ Fechar Comanda e Gerar Venda / PDF",
            fg_color=COR_SUCESSO,
            hover_color=COR_SUCESSO_HOVER,
            height=36,
            state="disabled",
        )
        btn_fechar_comanda.pack(pady=(0, 10), padx=10, fill="x")

        def desenhar_itens_comanda(cliente_nome, itens):
            lbl_titulo_comanda.configure(text=f"Comanda de: {cliente_nome}")
            for child in scroll_itens_comanda.winfo_children():
                child.destroy()

            total_itens = 0.0

            if not itens:
                ctk.CTkLabel(
                    scroll_itens_comanda,
                    text="Nenhum item nesta comanda ainda.",
                    font=FONTE_CORPO,
                    text_color=COR_TEXTO_SECUNDARIO,
                ).pack(pady=20)
                
                atualizar_total_geral(0.0)
                btn_fechar_comanda.configure(state="disabled")
                return

            btn_fechar_comanda.configure(state="normal")

            for item_id, prod_id, desc, qtd, preco in itens:
                subtotal = qtd * float(preco)
                total_itens += subtotal

                row = ctk.CTkFrame(
                    scroll_itens_comanda,
                    fg_color=COR_CARD_ITEM,
                    corner_radius=6,
                )
                row.pack(fill="x", pady=3, padx=2)

                info_txt = f"{qtd}x {desc} - R$ {subtotal:.2f}"
                ctk.CTkLabel(
                    row, text=info_txt, font=FONTE_CORPO, anchor="w", text_color="white"
                ).pack(side="left", padx=10, pady=8, fill="x", expand=True)

                btn_remover_item = ctk.CTkButton(
                    row,
                    text="🗑️ Devolver",
                    width=90,
                    height=26,
                    fg_color="#b91c1c",
                    hover_color="#991b1b",
                    font=FONTE_LEGENDA,
                    command=lambda i_id=item_id, p_id=prod_id, q=qtd, c=cliente_nome: devolver_item_comanda(
                        i_id, p_id, q, c
                    ),
                )
                btn_remover_item.pack(side="right", padx=10, pady=6)

            atualizar_total_geral(total_itens)
            
            btn_fechar_comanda.configure(
                command=lambda: faturar_comanda_thread(cliente_nome, itens, total_itens)
            )

        def obter_valor_frete():
            try:
                frete_texto = ent_frete.get().strip().replace(",", ".")
                return float(frete_texto) if frete_texto else 0.0
            except ValueError:
                return 0.0

        _ultimo_total_itens = 0.0

        def atualizar_total_geral(total_itens=None):
            nonlocal _ultimo_total_itens
            if total_itens is not None:
                _ultimo_total_itens = total_itens
            
            frete = obter_valor_frete()
            total_geral = _ultimo_total_itens + frete
            lbl_total_comanda.configure(
                text=f"Total da Comanda: R$ {total_geral:.2f} (Itens: R$ {_ultimo_total_itens:.2f} + Frete: R$ {frete:.2f})"
            )

        ent_frete.bind("<KeyRelease>", lambda event: atualizar_total_geral())

        def carregar_detalhes_comanda(cliente_nome):
            lbl_titulo_comanda.configure(text=f"Comanda de: {cliente_nome} (Carregando...)")
            for child in scroll_itens_comanda.winfo_children():
                child.destroy()

            ctk.CTkLabel(
                scroll_itens_comanda,
                text="Buscando itens na nuvem...",
                font=FONTE_CORPO,
                text_color=COR_TEXTO_SECUNDARIO,
            ).pack(pady=20)
            btn_fechar_comanda.configure(state="disabled")

            def background_carregar():
                try:
                    conn = conectar()
                    if not conn:
                        return
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, produto_id, descricao, quantidade, preco FROM comandas_abertas WHERE cliente = %s",
                        (cliente_nome,),
                    )
                    itens = cursor.fetchall()
                    cursor.close()
                    conn.close()

                    scroll_itens_comanda.after(0, lambda: desenhar_itens_comanda(cliente_nome, itens))
                except Exception as e:
                    print(f"Erro ao carregar detalhes da comanda: {e}")

            threading.Thread(target=background_carregar, daemon=True).start()

        def devolver_item_comanda(item_id, produto_id, quantidade, cliente_nome):
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE estoque SET quantidade = quantidade + %s WHERE id = %s",
                        (quantidade, produto_id),
                    )
                    cursor.execute(
                        "DELETE FROM comandas_abertas WHERE id = %s",
                        (item_id,),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    carregar_detalhes_comanda(cliente_nome)
            except Exception as e:
                print(f"Erro ao devolver item da comanda: {e}")

        def faturar_comanda_thread(cliente_nome, itens, total_itens):
            btn_fechar_comanda.update_idletasks()

            valor_frete = obter_valor_frete()
            total_venda = total_itens + valor_frete
            observacao_texto = txt_observacao.get("1.0", "end-1c").strip()
            data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pagto = "Faturado / Lojista"

            btn_fechar_comanda.configure(text="Processando Venda...", state="disabled")

            def background_faturamento():
                try:
                    conn = conectar()
                    if conn:
                        cursor = conn.cursor()
                        # Salva a venda incluindo a observação no banco
                        cursor.execute(
                            "INSERT INTO vendas (cliente, data_hora, total, frete, pagamento, observacao) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                            (cliente_nome, data_hoje, total_venda, valor_frete, pagto, observacao_texto),
                        )
                        venda_id = cursor.fetchone()[0]

                        itens_comprovante = []
                        for _, _, desc, qtd, preco in itens:
                            sub = qtd * float(preco)
                            cursor.execute(
                                "INSERT INTO itens_venda (venda_id, descricao, valor) VALUES (%s, %s, %s)",
                                (venda_id, f"{qtd}x {desc}", sub),
                            )
                            itens_comprovante.append((f"{qtd}x {desc}", sub))

                        if valor_frete > 0:
                            itens_comprovante.append(("Valor do Frete", valor_frete))

                        if observacao_texto:
                            itens_comprovante.append((f"Obs: {observacao_texto}", 0.0))

                        cursor.execute(
                            "DELETE FROM comandas_abertas WHERE cliente = %s",
                            (cliente_nome,),
                        )
                        conn.commit()
                        cursor.close()
                        conn.close()

                        try:
                            gerar_comprovante_pdf(
                                venda_id=venda_id,
                                cliente_nome=cliente_nome,
                                itens=itens_comprovante,
                                total=total_venda,
                                forma_pagamento=pagto,
                                nome_empresa="BVC Assistência",
                            )
                        except Exception as pdf_err:
                            print(f"Erro ao gerar PDF da comanda: {pdf_err}")

                        btn_fechar_comanda.after(0, lambda: self.mostrar_tela_comandas())

                except Exception as e:
                    print(f"Erro ao faturar comanda: {e}")
                    btn_fechar_comanda.after(0, lambda: btn_fechar_comanda.configure(
                        text="✔️ Fechar Comanda e Gerar Venda / PDF", state="normal"
                    ))

            threading.Thread(target=background_faturamento, daemon=True).start()

        def carregar_lista_clientes():
            for child in scroll_clientes.winfo_children():
                child.destroy()
            try:
                conn = conectar()
                if not conn:
                    return
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT cliente FROM comandas_abertas ORDER BY cliente"
                )
                clientes = cursor.fetchall()
                cursor.close()
                conn.close()

                if not clientes:
                    ctk.CTkLabel(scroll_clientes, text="Nenhuma comanda.", font=FONTE_CORPO, text_color=COR_TEXTO_SECUNDARIO).pack(pady=20)
                    return

                for (cli,) in clientes:
                    btn_cli = ctk.CTkButton(
                        scroll_clientes,
                        text=cli,
                        fg_color=COR_CARD_ITEM,
                        text_color="white",
                        hover_color=COR_DESTAQUE,
                        anchor="w",
                        height=32,
                        command=lambda c=cli: carregar_detalhes_comanda(c),
                    )
                    btn_cli.pack(fill="x", pady=2, padx=2)
            except Exception as e:
                print(f"Erro ao listar clientes de comandas: {e}")

        carregar_lista_clientes()

     # ==========================================
    # 3. TELA DE ORDENS DE SERVIÇO (O.S.)
    # ==========================================
    def mostrar_tela_os(self):
        self.limpar_container()

        main_os_frame = ctk.CTkFrame(self.body_container, fg_color="transparent")
        main_os_frame.pack(fill="both", expand=True, padx=10, pady=10)

        def gerar_pdf_os(os_id, cliente, aparelho, valor, status):
            try:
                if not os.path.exists("comprovantes"):
                    os.makedirs("comprovantes")

                caminho_arquivo = os.path.abspath(
                    f"comprovantes/Ordem_Servico_{os_id}.pdf"
                )
                c = canvas.Canvas(caminho_arquivo, pagesize=A6)
                largura, altura = A6

                c.setFont("Helvetica-Bold", 14)
                c.drawString(20, altura - 30, "LOJA BVC - ORDEM DE SERVIÇO")

                c.setFont("Helvetica", 10)
                c.drawString(20, altura - 55, f"O.S. Nº: #{os_id}")
                c.drawString(20, altura - 70, f"Cliente: {cliente}")
                c.drawString(20, altura - 85, f"Aparelho: {aparelho}")
                c.drawString(
                    20, altura - 100, f"Valor: R$ {float(valor or 0):.2f}"
                )
                c.drawString(20, altura - 115, f"Status: {status}")

                c.save()

                if os.name == "nt":
                    os.startfile(caminho_arquivo)
                else:
                    subprocess.call(["xdg-open", caminho_arquivo])
            except Exception as e:
                print(f"Erro ao gerar PDF da O.S.: {e}")

        left_os = ctk.CTkFrame(main_os_frame, width=300, fg_color=COR_CARD)
        left_os.pack(side="left", fill="y", padx=(0, 5))
        left_os.pack_propagate(False)

        ctk.CTkLabel(
            left_os, text="Nova Ordem de Serviço", font=("Arial", 14, "bold")
        ).pack(pady=10)

        ent_cliente_os = ctk.CTkEntry(
            left_os, placeholder_text="Nome do Cliente", width=260
        )
        ent_cliente_os.pack(pady=5)

        ent_aparelho = ctk.CTkEntry(
            left_os, placeholder_text="Aparelho / Defeito", width=260
        )
        ent_aparelho.pack(pady=5)

        ent_valor_os = ctk.CTkEntry(
            left_os, placeholder_text="Valor Estimado (R$)", width=260
        )
        ent_valor_os.pack(pady=5)

        combo_status = ctk.CTkOptionMenu(
            left_os, values=["Pendente", "Em Andamento", "Concluído"], width=260
        )
        combo_status.pack(pady=5)
        combo_status.set("Pendente")

        lbl_msg_os = ctk.CTkLabel(left_os, text="", font=FONTE_LEGENDA)
        lbl_msg_os.pack(pady=2)

        def salvar_os():
            cliente = ent_cliente_os.get().strip()
            aparelho = ent_aparelho.get().strip()
            valor = ent_valor_os.get().strip().replace(",", ".") or "0"
            status = combo_status.get()

            if not cliente or not aparelho:
                lbl_msg_os.configure(
                    text="Preencha Cliente e Aparelho!", text_color=COR_ERRO
                )
                return

            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO ordens_servico (cliente, aparelho, valor, status) VALUES (%s, %s, %s, %s)",
                        (cliente, aparelho, float(valor), status),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()

                    ent_cliente_os.delete(0, "end")
                    ent_aparelho.delete(0, "end")
                    ent_valor_os.delete(0, "end")
                    combo_status.set("Pendente")
                    lbl_msg_os.configure(
                        text="O.S. aberta com sucesso!",
                        text_color=COR_SUCESSO,
                    )
                    carregar_dados_os()
            except Exception as e:
                lbl_msg_os.configure(text=f"Erro: {e}", text_color=COR_ERRO)

        btn_salvar_os = ctk.CTkButton(
            left_os,
            text="Abrir O.S.",
            fg_color=COR_SUCESSO,
            hover_color=COR_SUCESSO_HOVER,
            command=salvar_os,
            width=260,
        )
        btn_salvar_os.pack(pady=10)

        right_os = ctk.CTkFrame(main_os_frame, fg_color=COR_CARD)
        right_os.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            right_os,
            text="Ordens de Serviço Registradas",
            font=("Arial", 12, "bold"),
        ).pack(pady=10, padx=10, anchor="w")

        lista_scroll_os = ctk.CTkScrollableFrame(
            right_os, fg_color="transparent"
        )
        lista_scroll_os.pack(fill="both", expand=True, padx=10, pady=5)

        def alterar_status(os_id, novo_status):
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE ordens_servico SET status = %s WHERE id = %s",
                        (novo_status, os_id),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    carregar_dados_os()
            except Exception as e:
                print(f"Erro ao alterar status: {e}")

        def excluir_os(os_id):
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM ordens_servico WHERE id = %s", (os_id,)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    carregar_dados_os()
            except Exception as e:
                print(f"Erro ao excluir O.S.: {e}")

        def carregar_dados_os():
            for widget in lista_scroll_os.winfo_children():
                widget.destroy()
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, cliente, aparelho, valor, status FROM ordens_servico ORDER BY id DESC"
                    )
                    resultados = cursor.fetchall()
                    cursor.close()
                    conn.close()

                    if not resultados:
                        ctk.CTkLabel(
                            lista_scroll_os,
                            text="Nenhuma O.S. cadastrada.",
                            text_color=COR_TEXTO_SECUNDARIO,
                        ).pack(pady=20)
                        return

                    for os_item in resultados:
                        o_id, cli, ap, val, st = os_item

                        if st == "Concluído":
                            cor_st = "#14532d"
                        elif st == "Em Andamento":
                            cor_st = "#b45309"
                        else:
                            cor_st = "#7f1d1d"

                        card = ctk.CTkFrame(
                            lista_scroll_os, fg_color=COR_CARD_ITEM
                        )
                        card.pack(fill="x", padx=5, pady=6)

                        info = ctk.CTkFrame(card, fg_color="transparent")
                        info.pack(
                            side="left", fill="both", expand=True, padx=10, pady=5
                        )

                        ctk.CTkLabel(
                            info,
                            text=f"O.S. #{o_id} | Cliente: {cli}",
                            font=("Arial", 12, "bold"),
                            anchor="w",
                        ).pack(fill="x")
                        ctk.CTkLabel(
                            info,
                            text=f"Descrição: {ap}",
                            font=("Arial", 11),
                            text_color="#cbd5e1",
                            anchor="w",
                            wraplength=430,
                        ).pack(fill="x", pady=2)
                        ctk.CTkLabel(
                            info,
                            text=f"Valor Estimado: R$ {float(val or 0):.2f}",
                            font=("Arial", 10),
                            text_color="#94a3b8",
                            anchor="w",
                        ).pack(fill="x")

                        ctk.CTkLabel(
                            card,
                            text=st,
                            fg_color=cor_st,
                            corner_radius=6,
                            font=("Arial", 10, "bold"),
                            width=90,
                        ).pack(side="left", padx=10)

                        btn_pdf = ctk.CTkButton(
                            card,
                            text="📄 PDF",
                            width=60,
                            fg_color="#0284c7",
                            hover_color="#0369a1",
                            command=lambda oid=o_id, c=cli, desc=ap, v=val, status=st: gerar_pdf_os(
                                oid, c, desc, v, status
                            ),
                        )
                        btn_pdf.pack(side="right", padx=2)

                        btn_status = ctk.CTkButton(
                            card,
                            text="🔄 Status",
                            width=70,
                            fg_color="#334155",
                            hover_color="#475569",
                            command=lambda oid=o_id, atual=st: alterar_status(
                                oid,
                                "Concluído" if atual != "Concluído" else "Pendente",
                            ),
                        )
                        btn_status.pack(side="right", padx=2)

                        btn_del = ctk.CTkButton(
                            card,
                            text="🗑️",
                            width=30,
                            fg_color="#b91c1c",
                            hover_color="#991b1b",
                            command=lambda oid=o_id: excluir_os(oid),
                        )
                        btn_del.pack(side="right", padx=5)
            except Exception as e:
                print(f"Erro ao carregar O.S.: {e}")

        carregar_dados_os()

# ==========================================
    # 4. TELA DE CONTROLE DE ESTOQUE (COMPLETA)
    # ==========================================
    def mostrar_tela_estoque(
        self, filtro_categoria="Todas", filtro_marca="Todas", termo_busca=""
    ):
        self.limpar_container()

        body = ctk.CTkFrame(self.body_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            body, text="Módulo de Controle de Estoque", font=FONTE_TITULO
        ).pack(pady=(0, 5))

        # --- BARRA DE FILTROS POR CATEGORIA (Com Telas, Baterias, Tampa, Diversos, Flex, FlexPower) ---
        frame_cat_container = ctk.CTkFrame(body, fg_color="transparent")
        frame_cat_container.pack(fill="x", padx=5, pady=(0, 5))

        categorias = ["Todas", "Telas", "Baterias", "Tampa", "Diversos", "Flex", "FlexPower"]
        for cat_f in categorias:
            cor_cat_btn = COR_PRIMARIA if filtro_categoria == cat_f else COR_CARD_ITEM
            ctk.CTkButton(
                frame_cat_container,
                text=cat_f,
                width=85,
                height=30,
                fg_color=cor_cat_btn,
                hover_color=COR_PRIMARIA,
                command=lambda c=cat_f: self.mostrar_tela_estoque(
                    filtro_categoria=c,
                    filtro_marca=filtro_marca,
                    termo_busca=ent_busca_estoque.get() if 'ent_busca_estoque' in locals() else ""
                ),
            ).pack(side="left", padx=2, pady=2)

        main_layout = ctk.CTkFrame(body, fg_color="transparent")
        main_layout.pack(fill="both", expand=True, pady=(5, 0))

        left_panel = ctk.CTkFrame(
            main_layout, width=320, fg_color=COR_CARD, corner_radius=10
        )
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        lbl_titulo_form = ctk.CTkLabel(
            left_panel, text="Cadastrar Item", font=FONTE_SUBTITULO
        )
        lbl_titulo_form.pack(pady=(15, 10))

        # Combobox do formulário de cadastro (incluindo Flex e FlexPower)
        combo_categoria = ctk.CTkComboBox(
            left_panel,
            values=["Telas", "Baterias", "Tampa", "Diversos", "Flex", "FlexPower"],
            width=280,
        )
        combo_categoria.pack(pady=8)
        combo_categoria.set("Telas")

        combo_marca = ctk.CTkComboBox(
            left_panel,
            values=[
                "Samsung", "Motorola", "Apple", "Xiaomi", "Redmi",
                "Realme", "Philco", "Infinix", "Itel", "Oppo", "Cubot", "Outras",
            ],
            width=280,
        )
        combo_marca.pack(pady=8)
        combo_marca.set("Samsung")

        ent_modelo = ctk.CTkEntry(
            left_panel,
            placeholder_text="Modelo (ex: A12, G52, 11 Pro)",
            width=280,
        )
        ent_modelo.pack(pady=8)

        ent_quantidade = ctk.CTkEntry(
            left_panel, placeholder_text="Quantidade Atual", width=280
        )
        ent_quantidade.pack(pady=8)

        frame_limites = ctk.CTkFrame(left_panel, fg_color="transparent", width=280)
        frame_limites.pack(pady=4)
        ent_min = ctk.CTkEntry(frame_limites, placeholder_text="Mín", width=130)
        ent_min.pack(side="left", padx=(0, 10))
        ent_max = ctk.CTkEntry(frame_limites, placeholder_text="Máx", width=130)
        ent_max.pack(side="right")

        ent_preco_rev = ctk.CTkEntry(
            left_panel, placeholder_text="Preço Revendedor (R$)", width=280
        )
        ent_preco_rev.pack(pady=8)

        ent_preco_final = ctk.CTkEntry(
            left_panel, placeholder_text="Preço Final / Balcão (R$)", width=280
        )
        ent_preco_final.pack(pady=8)

        lbl_msg_estoque = ctk.CTkLabel(
            left_panel, text="", font=FONTE_LEGENDA, text_color=COR_ERRO
        )
        lbl_msg_estoque.pack(pady=2)

        def salvar_item_estoque():
            cat = combo_categoria.get()
            mar = combo_marca.get()
            mod = ent_modelo.get().strip()
            qtd = ent_quantidade.get().strip()
            pmin = ent_min.get().strip()
            pmax = ent_max.get().strip()
            prc_rev = ent_preco_rev.get().strip()
            prc_fin = ent_preco_final.get().strip()

            if not mod or not qtd or not prc_fin:
                lbl_msg_estoque.configure(text="Preencha modelo, qtd e preço final!")
                return

            try:
                q_val = int(qtd)
                min_val = int(pmin) if pmin else 2
                max_val = int(pmax) if pmax else 10
                p_rev_val = float(prc_rev.replace(",", ".")) if prc_rev else 0.00
                p_fin_val = float(prc_fin.replace(",", "."))
            except ValueError:
                lbl_msg_estoque.configure(text="Valores numéricos inválidos!")
                return

            btn_salvar_estoque.configure(text="Salvando...", state="disabled")
            lbl_msg_estoque.configure(text="Salvando no banco...")

            def processo_em_segundo_plano():
                try:
                    conn = conectar()
                    cursor = conn.cursor()

                    if self.peca_em_edicao_id:
                        cursor.execute(
                            "UPDATE estoque SET categoria=%s, marca=%s, modelo=%s, quantidade=%s, min_alerta=%s, max_estoque=%s, preco_revendedor=%s, preco_final=%s WHERE id=%s",
                            (cat, mar, mod, q_val, min_val, max_val, p_rev_val, p_fin_val, self.peca_em_edicao_id),
                        )
                        edit_id_usado = self.peca_em_edicao_id
                        self.peca_em_edicao_id = None
                    else:
                        cursor.execute(
                            "INSERT INTO estoque (categoria, marca, modelo, quantidade, min_alerta, max_estoque, preco_revendedor, preco_final) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                            (cat, mar, mod, q_val, min_val, max_val, p_rev_val, p_fin_val),
                        )
                        edit_id_usado = None

                    conn.commit()
                    cursor.close()
                    conn.close()

                    btn_salvar_estoque.after(0, lambda: finalizar_sucesso(edit_id_usado))

                except Exception as ex:
                    print(ex)
                    btn_salvar_estoque.after(0, lambda: lbl_msg_estoque.configure(text="Erro ao salvar item."))
                    btn_salvar_estoque.after(0, lambda: btn_salvar_estoque.configure(text="Salvar Item", state="normal"))

            def finalizar_sucesso(foiEdicao):
                if foiEdicao:
                    lbl_titulo_form.configure(text="Cadastrar Item")
                
                btn_salvar_estoque.configure(
                    text="Salvar Item",
                    state="normal",
                    fg_color=COR_SUCESSO,
                    hover_color=COR_SUCESSO_HOVER,
                )

                ent_modelo.delete(0, "end")
                ent_quantidade.delete(0, "end")
                ent_min.delete(0, "end")
                ent_max.delete(0, "end")
                ent_preco_rev.delete(0, "end")
                ent_preco_final.delete(0, "end")
                lbl_msg_estoque.configure(text="")

                self.mostrar_tela_estoque(filtro_categoria, filtro_marca, termo_busca)

            threading.Thread(target=processo_em_segundo_plano, daemon=True).start()

        btn_salvar_estoque = ctk.CTkButton(
            left_panel,
            text="Salvar Item",
            command=salvar_item_estoque,
            width=280,
            fg_color=COR_SUCESSO,
            hover_color=COR_SUCESSO_HOVER,
        )
        btn_salvar_estoque.pack(pady=(15, 5))

        # --- PAINEL DIREITO (Busca, Filtro de Marcas e Lista de Itens) ---
        right_panel = ctk.CTkFrame(main_layout, fg_color=COR_CARD, corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)

        # Barra de Pesquisa de Texto
        ent_busca_estoque = ctk.CTkEntry(
            right_panel, placeholder_text="🔍 Buscar modelo ou marca no estoque...", width=320
        )
        ent_busca_estoque.pack(pady=(15, 5), padx=10, anchor="w")
        if termo_busca:
            ent_busca_estoque.insert(0, termo_busca)

        # Barra de Marcas Horizontal (Scrollável)
        frame_marcas_container = ctk.CTkScrollableFrame(
            right_panel, orientation="horizontal", height=45, fg_color="transparent"
        )
        frame_marcas_container.pack(fill="x", padx=10, pady=(0, 5))

        marcas = [
            "Todas", "Samsung", "Motorola", "Apple", "Xiaomi", "Redmi",
            "Realme", "Philco", "Infinix", "Itel", "Oppo", "Cubot", "Outras"
        ]
        for marca in marcas:
            cor_m_btn = COR_PRIMARIA if filtro_marca == marca else COR_CARD_ITEM
            ctk.CTkButton(
                frame_marcas_container,
                text=marca,
                width=90,
                height=30,
                fg_color=cor_m_btn,
                hover_color=COR_PRIMARIA,
                command=lambda m=marca: self.mostrar_tela_estoque(
                    filtro_categoria=filtro_categoria,
                    filtro_marca=m,
                    termo_busca=ent_busca_estoque.get(),
                ),
            ).pack(side="left", padx=3, pady=2)

        # Scroll principal com os cards dos itens do estoque
        scroll_itens_estoque = ctk.CTkScrollableFrame(
            right_panel, fg_color="transparent"
        )
        scroll_itens_estoque.pack(fill="both", expand=True, padx=10, pady=10)

        def excluir_item(item_id):
            try:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM estoque WHERE id = %s", (item_id,))
                conn.commit()
                cursor.close()
                conn.close()
                self.mostrar_tela_estoque(filtro_categoria, filtro_marca, ent_busca_estoque.get())
            except Exception as e:
                print(f"Erro ao excluir item: {e}")

        def preparar_edicao(item_id, cat, marca, modelo, qtd, min_alt, max_alt, p_rev, p_fin):
            self.peca_em_edicao_id = item_id
            lbl_titulo_form.configure(text="Editar Item")
            btn_salvar_estoque.configure(
                text="Atualizar Item",
                fg_color="#F0AD4E",
                hover_color="#EEA236",
            )
            combo_categoria.set(cat)
            combo_marca.set(marca)
            ent_modelo.delete(0, "end")
            ent_modelo.insert(0, modelo)
            ent_quantidade.delete(0, "end")
            ent_quantidade.insert(0, str(qtd))
            ent_min.delete(0, "end")
            ent_min.insert(0, str(min_alt))
            ent_max.delete(0, "end")
            ent_max.insert(0, str(max_alt))
            ent_preco_rev.delete(0, "end")
            ent_preco_rev.insert(0, str(p_rev))
            ent_preco_final.delete(0, "end")
            ent_preco_final.insert(0, str(p_fin))

        # --- BUSCA E EXIBIÇÃO DOS DADOS NO BANCO ---
        try:
            conn = conectar()
            if conn:
                cursor = conn.cursor()
                query = "SELECT id, categoria, marca, modelo, quantidade, min_alerta, max_estoque, preco_revendedor, preco_final FROM estoque WHERE 1=1"
                params = []

                if filtro_categoria != "Todas":
                    query += " AND categoria = %s"
                    params.append(filtro_categoria)

                if filtro_marca != "Todas":
                    query += " AND marca = %s"
                    params.append(filtro_marca)

                termo_atual = ent_busca_estoque.get().strip()
                if termo_atual:
                    query += " AND (LOWER(modelo) LIKE %s OR LOWER(marca) LIKE %s)"
                    params.extend([f"%{termo_atual.lower()}%", f"%{termo_atual.lower()}%"])

                query += " ORDER BY id DESC"

                cursor.execute(query, tuple(params))
                itens = cursor.fetchall()
                cursor.close()
                conn.close()

                if not itens:
                    ctk.CTkLabel(
                        scroll_itens_estoque,
                        text="Nenhum item encontrado com esses filtros.",
                        text_color=COR_TEXTO_SECUNDARIO,
                    ).pack(pady=20)
                else:
                    for it_id, cat, marca, modelo, qtd, min_alt, max_alt, p_rev, p_fin in itens:
                        row_item = ctk.CTkFrame(
                            scroll_itens_estoque,
                            fg_color=COR_CARD_ITEM,
                            corner_radius=6,
                        )
                        row_item.pack(fill="x", pady=4, padx=5)

                        cor_texto_qtd = COR_SUCESSO if qtd > min_alt else COR_ERRO

                        ctk.CTkLabel(
                            row_item,
                            text=f"[{cat}] {marca} - {modelo}",
                            font=FONTE_SUBTITULO,
                        ).pack(side="left", padx=10, pady=8)

                        btn_excluir = ctk.CTkButton(
                            row_item,
                            text="X",
                            width=35,
                            fg_color="#D9534F",
                            hover_color="#C9302C",
                            command=lambda i=it_id: excluir_item(i),
                        )
                        btn_excluir.pack(side="right", padx=5, pady=8)

                        btn_editar = ctk.CTkButton(
                            row_item,
                            text="Editar",
                            width=55,
                            fg_color="#F0AD4E",
                            hover_color="#EEA236",
                            command=lambda i=it_id, c=cat, m=marca, mod=modelo, q=qtd, mn=min_alt, mx=max_alt, pr=p_rev, pf=p_fin: preparar_edicao(
                                i, c, m, mod, q, mn, mx, pr, pf
                            ),
                        )
                        btn_editar.pack(side="right", padx=2, pady=8)

                        txt_valores = f"Qtd: {qtd} | Rev: R$ {float(p_rev):.2f} | Final: R$ {float(p_fin):.2f}"
                        ctk.CTkLabel(
                            row_item,
                            text=txt_valores,
                            font=FONTE_CORPO,
                            text_color=cor_texto_qtd,
                        ).pack(side="right", padx=10, pady=8)
        except Exception as e:
            print(f"Erro ao carregar estoque: {e}")

        ent_busca_estoque.bind(
            "<KeyRelease>",
            lambda e: self.mostrar_tela_estoque(
                filtro_categoria, filtro_marca, ent_busca_estoque.get()
            ),
        )

    def mostrar_tela_relatorios(self):
        self.limpar_container()

        body = ctk.CTkFrame(self.body_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        top_bar = ctk.CTkFrame(body, height=50, fg_color=COR_CARD)
        top_bar.pack(fill="x", padx=5, pady=5)

        lbl_faturamento = ctk.CTkLabel(
            top_bar,
            text="Faturamento Total: R$ 0,00",
            font=FONTE_SUBTITULO,
            text_color=COR_DESTAQUE,
        )

        lbl_faturamento.pack(side="left", padx=15)

        scroll_vendas = ctk.CTkScrollableFrame(body, fg_color="transparent")
        scroll_vendas.pack(fill="both", expand=True, padx=5, pady=5)

        def excluir_venda(venda_id):
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM itens_venda WHERE venda_id = %s",
                        (venda_id,),
                    )
                    cursor.execute(
                        "DELETE FROM vendas WHERE id = %s", (venda_id,)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    self.mostrar_tela_relatorios()

            except Exception as e:
                print(f"Erro ao excluir venda #{venda_id}: {e}")

        try:
            conn = conectar()
            if not conn:
                return

            cursor = conn.cursor()
            cursor.execute(

                "SELECT id, cliente, data_hora, total, pagamento FROM vendas ORDER BY id DESC LIMIT 50"
            )
            vendas = cursor.fetchall()

            cursor.execute("SELECT SUM(total) FROM vendas")
            res_sum = cursor.fetchone()
            total_acumulado = (
                float(res_sum[0])
                if res_sum and res_sum[0] is not None
                else 0.0
            )
            lbl_faturamento.configure(
                text=f"Faturamento Total: R$ {total_acumulado:.2f}"
            )
            cursor.close()
            conn.close()

            if not vendas:

                ctk.CTkLabel(
                    scroll_vendas,
                    text="Nenhuma venda registrada até o momento.",
                    font=FONTE_CORPO,
                    text_color=COR_TEXTO_SECUNDARIO,
                ).pack(pady=20)
                return

            for v_id, cliente, data_h, total, pag in vendas:
                card_venda = ctk.CTkFrame(
                    scroll_vendas, fg_color=COR_CARD, corner_radius=8
                )
                card_venda.pack(fill="x", pady=5, padx=5)
                top_row = ctk.CTkFrame(card_venda, fg_color="transparent")
                top_row.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(
                    top_row,
                    text=f"Venda #{v_id:04d} - {cliente}",
                    font=FONTE_SUBTITULO,
                ).pack(side="left")

                ctk.CTkLabel(

                    top_row,
                    text=f"Data: {data_h} | Pgto: {pag}",
                    font=FONTE_LEGENDA,
                    text_color=COR_TEXTO_SECUNDARIO,
                ).pack(side="right")

                try:
                    conn_item = conectar()
                    if conn_item:
                        cur_item = conn_item.cursor()
                        cur_item.execute(
                            "SELECT descricao, valor FROM itens_venda WHERE venda_id = %s",
                            (v_id,),
                        )
                        itens = cur_item.fetchall()
                        cur_item.close()
                        conn_item.close()
                        for desc, val in itens:
                            item_row = ctk.CTkFrame(
                                card_venda, fg_color="transparent"
                            )
                            item_row.pack(fill="x", padx=20, pady=1)
                            ctk.CTkLabel(
                                item_row, text=f"• {desc}", font=FONTE_LEGENDA
                            ).pack(side="left")

                            ctk.CTkLabel(
                                item_row,
                                text=f"R$ {float(val):.2f}",
                                font=FONTE_LEGENDA,
                            ).pack(side="right")

                except Exception as ex_item:
                    print(
                        f"Erro ao buscar itens da venda {v_id}: {ex_item}"

                    )

                bot_row = ctk.CTkFrame(card_venda, fg_color="transparent")
                bot_row.pack(fill="x", padx=10, pady=5)

                btn_excluir_venda = ctk.CTkButton(
                    bot_row,
                    text="🗑️ Excluir Venda",
                    width=110,
                    height=26,
                    fg_color="#b91c1c",
                    hover_color="#991b1b",
                    font=FONTE_LEGENDA,
                    command=lambda id_v=v_id: excluir_venda(id_v),
                )

                btn_excluir_venda.pack(side="left")

                ctk.CTkLabel(
                    bot_row,
                    text=f"Total Venda: R$ {float(total):.2f}",
                    font=FONTE_SUBTITULO,
                    text_color=COR_TEXTO_VALOR,
                ).pack(side="right")

        except Exception as e:

            print(f"Erro ao carregar relatórios: {e}")

    def mostrar_tela_cadastro(self):
        pass

    def mostrar_tela_recuperar(self):
        pass 

    # ==========================================
    # TELA DE LOGIN (Com Cadastro e Recuperação)
    # ==========================================
    def mostrar_tela_login(self):
        self.limpar_container()
        
        # Se o usuário deslogou, remove o cabeçalho da tela
        if self.header_frame:
            self.header_frame.destroy()
            self.header_frame = None

        self.usuario_atual = ""

        try:
            self.iconbitmap("icone.ico")
        except:
            pass

        try:
            self.imagem_fundo_raw = Image.open("fundo.png")
            largura = self.winfo_width() if self.winfo_width() > 700 else 1380
            altura = self.winfo_height() if self.winfo_height() > 700 else 730
            self.bg_image = ctk.CTkImage(light_image=self.imagem_fundo_raw, dark_image=self.imagem_fundo_raw, size=(largura, altura))
            # CORRIGIDO: Colocado no body_container para sumir ao limpar
            self.lbl_fundo = ctk.CTkLabel(self.body_container, image=self.bg_image, text="")
            self.lbl_fundo.place(relwidth=1, relheight=1)
        except Exception as e:
            print(f"Erro ao carregar fundo: {e}")

        # CORRIGIDO: Colocado no body_container
        frame_login = ctk.CTkFrame(self.body_container, width=360, height=480, fg_color=COR_CARD, corner_radius=12)
        frame_login.place(relx=0.5, rely=0.5, anchor="center")
        frame_login.pack_propagate(False)

        ctk.CTkLabel(frame_login, text="Acesso ao Sistema", font=FONTE_TITULO).pack(pady=(20, 10))

        ent_usuario = ctk.CTkEntry(frame_login, placeholder_text="Usuário", width=280)
        ent_usuario.pack(pady=6)

        ent_senha = ctk.CTkEntry(frame_login, placeholder_text="Senha", show="*", width=280)
        ent_senha.pack(pady=6)

        lbl_erro = ctk.CTkLabel(frame_login, text="", text_color=COR_ERRO, font=FONTE_LEGENDA)
        lbl_erro.pack(pady=2)

        def autenticar():
            usr = ent_usuario.get().strip()
            pwd = ent_senha.get().strip()
            
            if not usr or not pwd:
                lbl_erro.configure(text="Preencha todos os campos!")
                return

            try:
                conn = conectar()
                if not conn:
                    lbl_erro.configure(text="Erro de conexão com o banco!")
                    return
                
                cursor = conn.cursor()
                sql = "SELECT * FROM usuarios WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) AND senha = %s"
                cursor.execute(sql, (usr, pwd))
                user_db = cursor.fetchone()

                cursor.close()
                conn.close()

                if user_db:
                    self.usuario_atual = usr
                    self.criar_cabecalho()  # Cria o cabeçalho agora que logou
                    self.mostrar_tela_pdv()  # Vai para o PDV e limpa o body_container inteiro
                else:
                    lbl_erro.configure(text="Usuário ou senha incorretos!")
            except Exception as ex:
                print(f"[LOGIN EXCEPTION] {ex}")
                lbl_erro.configure(text="Erro ao conectar ao banco!")

        btn_entrar = ctk.CTkButton(frame_login, text="Entrar", command=autenticar, width=280, fg_color=COR_PRIMARIA, hover_color=COR_PRIMARIA_HOVER)
        btn_entrar.pack(pady=(8, 5))

        btn_ir_cadastro = ctk.CTkButton(frame_login, text="Criar Nova Conta", fg_color="transparent", text_color="#38bdf8", hover_color="#334155", command=self.mostrar_tela_cadastro, width=280)
        btn_ir_cadastro.pack(pady=2)

        btn_ir_recuperar = ctk.CTkButton(frame_login, text="Esqueci minha senha", fg_color="transparent", text_color="#94a3b8", hover_color="#334155", command=self.mostrar_tela_recuperar, width=280)
        btn_ir_recuperar.pack(pady=2)

    # ==========================================
    # TELA DE CADASTRO DE NOVO USUÁRIO
    # ==========================================
    def mostrar_tela_cadastro(self):
        self.limpar_container()

        try:
            # CORRIGIDO: Colocado no body_container
            self.lbl_fundo = ctk.CTkLabel(self.body_container, image=self.bg_image, text="")
            self.lbl_fundo.place(relwidth=1, relheight=1)
        except:
            pass

        # CORRIGIDO: Colocado no body_container
        frame_cad = ctk.CTkFrame(self.body_container, width=360, height=480, fg_color=COR_CARD, corner_radius=12)
        frame_cad.place(relx=0.5, rely=0.5, anchor="center")
        frame_cad.pack_propagate(False)

        ctk.CTkLabel(frame_cad, text="Criar Nova Conta", font=FONTE_TITULO).pack(pady=(20, 15))

        ent_usuario = ctk.CTkEntry(frame_cad, placeholder_text="Novo Usuário", width=280)
        ent_usuario.pack(pady=8)

        ent_senha = ctk.CTkEntry(frame_cad, placeholder_text="Senha", show="*", width=280)
        ent_senha.pack(pady=8)

        ent_palavra = ctk.CTkEntry(frame_cad, placeholder_text="Palavra-chave (ex: nome do seu pet)", width=280)
        ent_palavra.pack(pady=8)

        lbl_msg = ctk.CTkLabel(frame_cad, text="", text_color=COR_ERRO, font=FONTE_LEGENDA)
        lbl_msg.pack(pady=2)

        def salvar_cadastro():
            usr = ent_usuario.get().strip()
            pwd = ent_senha.get().strip()
            palavra = ent_palavra.get().strip().lower()

            if not usr or not pwd or not palavra:
                lbl_msg.configure(text="Preencha todos os campos!")
                return

            try:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM usuarios WHERE usuario = %s", (usr,))
                if cursor.fetchone():
                    lbl_msg.configure(text="Este usuário já existe!")
                    cursor.close()
                    conn.close()
                    return

                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, palavra_chave) VALUES (%s, %s, %s)",
                    (usr, pwd, palavra)
                )
                conn.commit()
                cursor.close()
                conn.close()

                lbl_msg.configure(text_color="#16a34a", text="Conta criada com sucesso! Retornando...")
                self.after(1500, self.mostrar_tela_login)
            except Exception as ex:
                lbl_msg.configure(text="Erro ao registrar usuário no banco.")
                print(ex)

        btn_salvar = ctk.CTkButton(frame_cad, text="Cadastrar", command=salvar_cadastro, width=280, fg_color=COR_SUCESSO, hover_color=COR_SUCESSO_HOVER)
        btn_salvar.pack(pady=(12, 5))

        btn_voltar = ctk.CTkButton(frame_cad, text="Voltar ao Login", fg_color="transparent", text_color="#94a3b8", command=self.mostrar_tela_login, width=280)
        btn_voltar.pack(pady=5)

    # ==========================================
    # TELA DE RECUPERAÇÃO DE SENHA
    # ==========================================
    def mostrar_tela_recuperar(self):
        self.limpar_container()

        try:
            # CORRIGIDO: Colocado no body_container
            self.lbl_fundo = ctk.CTkLabel(self.body_container, image=self.bg_image, text="")
            self.lbl_fundo.place(relwidth=1, relheight=1)
        except:
            pass

        # CORRIGIDO: Colocado no body_container
            # Card menor
        frame_login = ctk.CTkFrame(self.body_container, width=320, height=380, fg_color="transparent", corner_radius=12)
        frame_login.place(relx=0.5, rely=0.5, anchor="center")
        frame_login.pack_propagate(False)

        ctk.CTkLabel(frame_login, text="Acesso ao Sistema", font=FONTE_TITULO).pack(pady=(15, 8))

        # Campos menores (width=240)
        ent_usuario = ctk.CTkEntry(frame_login, placeholder_text="Usuário", width=240)
        ent_usuario.pack(pady=5)

        ent_senha = ctk.CTkEntry(frame_login, placeholder_text="Senha", show="*", width=240)
        ent_senha.pack(pady=5)

        lbl_erro = ctk.CTkLabel(frame_login, text="", text_color=COR_ERRO, font=FONTE_LEGENDA)
        lbl_erro.pack(pady=2)

        # Botões menores (width=240)
        btn_entrar = ctk.CTkButton(frame_login, text="Entrar", command=autenticar, width=240, fg_color=COR_PRIMARIA, hover_color=COR_PRIMARIA_HOVER)
        btn_entrar.pack(pady=(6, 4))

        btn_ir_cadastro = ctk.CTkButton(frame_login, text="Criar Nova Conta", fg_color="transparent", text_color="#38bdf8", hover_color="#334155", command=self.mostrar_tela_cadastro, width=240)
        btn_ir_cadastro.pack(pady=2)

        btn_ir_recuperar = ctk.CTkButton(frame_login, text="Esqueci minha senha", fg_color="transparent", text_color="#94a3b8", hover_color="#334155", command=self.mostrar_tela_recuperar, width=240)
        btn_ir_recuperar.pack(pady=2)

        def redefinir_senha():
            usr = ent_usuario.get().strip()
            palavra = ent_palavra.get().strip().lower()
            nova_pwd = ent_nova_senha.get().strip()

            if not usr or not palavra or not nova_pwd:
                lbl_msg.configure(text="Preencha todos os campos!")
                return

            try:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM usuarios WHERE usuario = %s AND palavra_chave = %s", (usr, palavra))
                res = cursor.fetchone()

                if not res:
                    lbl_msg.configure(text="Usuário ou palavra-chave incorretos!")
                    cursor.close()
                    conn.close()
                    return

                cursor.execute("UPDATE usuarios SET senha = %s WHERE usuario = %s", (nova_pwd, usr))
                conn.commit()
                cursor.close()
                conn.close()

                lbl_msg.configure(text_color="#16a34a", text="Senha alterada com sucesso! Faça login.")
                self.after(1500, self.mostrar_tela_login)
            except Exception as ex:
                lbl_msg.configure(text="Erro ao redefinir senha.")
                print(ex)

        btn_Redefinir = ctk.CTkButton(frame_rec, text="Redefinir Senha", command=redefinir_senha, width=280, fg_color=COR_PRIMARIA, hover_color=COR_PRIMARIA_HOVER)
        btn_Redefinir.pack(pady=(12, 5))

        btn_voltar = ctk.CTkButton(frame_rec, text="Voltar ao Login", fg_color="transparent", text_color="#94a3b8", command=self.mostrar_tela_login, width=280)
        btn_voltar.pack(pady=5)
# ==========================================
    # 2. TELA DE PDV (UNIFICADA E CORRIGIDA)
    # ==========================================
    def mostrar_tela_pdv(self):
        self.limpar_container()
        
        # Garante que a flag do lojista inicia como False ao abrir o PDV padrão (a menos que chamado por comanda)
        if not hasattr(self, 'modo_lojista'):
            self.modo_lojista = False

        body = ctk.CTkFrame(self.body_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        left = ctk.CTkFrame(body, fg_color=COR_CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(left, text="Produtos Disponíveis (Supabase)", font=FONTE_SUBTITULO).pack(pady=(12, 6))

        ent_busca = ctk.CTkEntry(left, placeholder_text="🔍 Buscar marca ou modelo...", width=320)
        ent_busca.pack(pady=(0, 10))

        scroll_produtos = ctk.CTkScrollableFrame(left, fg_color="transparent")
        scroll_produtos.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        right = ctk.CTkFrame(body, width=380, fg_color=COR_CARD)
        right.pack(side="right", fill="both", padx=(5, 0))
        right.pack_propagate(False)

        ctk.CTkLabel(right, text="Carrinho de Compras", font=FONTE_SUBTITULO).pack(pady=(12, 6))

        ent_cliente = ctk.CTkEntry(right, placeholder_text="Nome do Cliente / Lojista", width=340)
        ent_cliente.pack(pady=5)

        scroll_carrinho = ctk.CTkScrollableFrame(right, fg_color="transparent")
        scroll_carrinho.pack(fill="both", expand=True, padx=10, pady=5)

        lbl_total = ctk.CTkLabel(right, text="Total: R$ 0,00", font=FONTE_TITULO, text_color=COR_TEXTO_VALOR)
        lbl_total.pack(pady=10)

        combo_pagto = ctk.CTkOptionMenu(right, values=["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"], width=340)
        combo_pagto.pack(pady=5)

        def atualizar_carrinho():
            for child in scroll_carrinho.winfo_children():
                child.destroy()

            total = 0.0
            for index, item in enumerate(self.carrinho_pdv):
                subtotal = item['qtd'] * item['preco']
                total += subtotal

                row = ctk.CTkFrame(scroll_carrinho, fg_color=COR_CARD_ITEM, corner_radius=6)
                row.pack(fill="x", pady=3, padx=2)

                btn_remover = ctk.CTkButton(
                    row, text="🗑️", width=28, height=24,
                    fg_color="#b91c1c", hover_color="#991b1b",
                    command=lambda idx=index: remover_item_carrinho(idx)
                )
                btn_remover.pack(side="right", padx=5, pady=6)

                btn_mais = ctk.CTkButton(
                    row, text="+", width=24, height=24, fg_color="#16a34a", hover_color="#15803d",
                    command=lambda idx=index: alterar_qtd_item(idx, 1)
                )
                btn_mais.pack(side="right", padx=2, pady=6)

                btn_menos = ctk.CTkButton(
                    row, text="-", width=24, height=24, fg_color="#ca8a04", hover_color="#a16207",
                    command=lambda idx=index: alterar_qtd_item(idx, -1)
                )
                btn_menos.pack(side="right", padx=2, pady=6)

                texto_item = f"{item['qtd']}x {item['nome']}" if item['qtd'] > 1 else item['nome']
                info = ctk.CTkLabel(row, text=texto_item, font=FONTE_CORPO, anchor="w")
                info.pack(side="left", padx=8, pady=6, fill="x", expand=True)

            lbl_total.configure(text=f"Total: R$ {total:.2f}")

        def adicionar_ao_carrinho(prod_id, nome, preco):
            for item in self.carrinho_pdv:
                if item['id'] == prod_id:
                    item['qtd'] += 1
                    atualizar_carrinho()
                    return
            self.carrinho_pdv.append({'id': prod_id, 'nome': nome, 'preco': float(preco), 'qtd': 1})
            atualizar_carrinho()

        def alterar_qtd_item(index, delta):
            if 0 <= index < len(self.carrinho_pdv):
                self.carrinho_pdv[index]['qtd'] += delta
                if self.carrinho_pdv[index]['qtd'] <= 0:
                    self.carrinho_pdv.pop(index)
                atualizar_carrinho()

        def remover_item_carrinho(index):
            if 0 <= index < len(self.carrinho_pdv):
                self.carrinho_pdv.pop(index)
                atualizar_carrinho()

        def carregar_produtos(filtro=""):
            for child in scroll_produtos.winfo_children():
                child.destroy()

            conn = conectar()
            if not conn:
                ctk.CTkLabel(scroll_produtos, text="🔴 Erro ao conectar ao Supabase!", font=FONTE_SUBTITULO, text_color=COR_ERRO).pack(pady=20)
                return

            try:
                cursor = conn.cursor()
                if filtro:
                    query = "SELECT id, categoria, marca, modelo, quantidade, preco_final, preco_revendedor FROM estoque WHERE LOWER(marca) LIKE %s OR LOWER(modelo) LIKE %s OR LOWER(categoria) LIKE %s ORDER BY id DESC LIMIT 100"
                    params = (f"%{filtro.lower()}%", f"%{filtro.lower()}%", f"%{filtro.lower()}%")
                else:
                    query = "SELECT id, categoria, marca, modelo, quantidade, preco_final, preco_revendedor FROM estoque ORDER BY id DESC LIMIT 100"
                    params = None

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                produtos = cursor.fetchall()
                cursor.close()
                conn.close()

                if not produtos:
                    ctk.CTkLabel(scroll_produtos, text="Nenhum produto encontrado na nuvem.", font=FONTE_CORPO, text_color=COR_TEXTO_SECUNDARIO).pack(pady=20)
                    return

                for p_id, cat, marca, modelo, qtd, preco_fin, preco_rev in produtos:
                    card = ctk.CTkFrame(scroll_produtos, fg_color=COR_CARD_ITEM, corner_radius=8)
                    card.pack(fill="x", pady=4, padx=2)

                    cat_txt = cat if cat else "Geral"
                    mar_txt = marca if marca else ""
                    mod_txt = modelo if modelo else "Peça"
                    nome_formatado = f"[{cat_txt}] {mar_txt} - {mod_txt}"
                    
                    p_final = float(preco_fin) if preco_fin is not None else 0.00
                    p_rev = float(preco_rev) if preco_rev is not None else p_final

                    # Botão Adicionar Lojista (Azul/Destaque)
                    btn_add_rev = ctk.CTkButton(
                        card, text="+ Lojista (R$ " + f"{p_rev:.2f})", width=120, 
                        fg_color="#2563eb", hover_color="#1d4ed8", font=("Arial", 11, "bold"),
                        command=lambda p=p_id, n=nome_formatado + " [Lojista]", pr=p_rev: adicionar_ao_carrinho(p, n, pr)
                    )
                    btn_add_rev.pack(side="right", padx=5, pady=8)

                    # Botão Adicionar Varejo (Verde)
                    btn_add_fin = ctk.CTkButton(
                        card, text="+ Varejo (R$ " + f"{p_final:.2f})", width=120, 
                        fg_color=COR_SUCESSO, hover_color=COR_SUCESSO_HOVER, font=("Arial", 11, "bold"),
                        command=lambda p=p_id, n=nome_formatado + " [Varejo]", pr=p_final: adicionar_ao_carrinho(p, n, pr)
                    )
                    btn_add_fin.pack(side="right", padx=5, pady=8)

                    info_frame = ctk.CTkFrame(card, fg_color="transparent")
                    info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

                    ctk.CTkLabel(info_frame, text=nome_formatado, font=FONTE_SUBTITULO, anchor="w").pack(fill="x")
                    q_val = qtd if qtd is not None else 0
                    ctk.CTkLabel(info_frame, text=f"Estoque: {q_val} un.", font=FONTE_LEGENDA, text_color=COR_TEXTO_SECUNDARIO, anchor="w").pack(fill="x")
            except Exception as e:
                print(f"ERRO CRITICO PDV: {e}")
                ctk.CTkLabel(scroll_produtos, text=f"Erro ao ler banco Supabase:\n{e}", font=FONTE_CORPO, text_color=COR_ERRO).pack(pady=20)

        def finalizar_venda():
            cliente = ent_cliente.get().strip() or "Consumidor Final"
            pagto = combo_pagto.get()

            if not self.carrinho_pdv:
                return

            total_venda = sum(i['qtd'] * i['preco'] for i in self.carrinho_pdv)
            data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO vendas (cliente, data_hora, total, pagamento) VALUES (%s, %s, %s, %s) RETURNING id",
                        (cliente, data_hoje, total_venda, pagto)
                    )
                    venda_id = cursor.fetchone()[0]

                    for item in self.carrinho_pdv:
                        cursor.execute(
                            "INSERT INTO itens_venda (venda_id, descricao, valor) VALUES (%s, %s, %s)",
                            (venda_id, f"{item['qtd']}x {item['nome']}", item['preco'] * item['qtd'])
                        )
                        cursor.execute("UPDATE estoque SET quantidade = quantidade - %s WHERE id = %s", (item['qtd'], item['id']))

                    conn.commit()
                    itens_comprovante = [(f"{item['qtd']}x {item['nome']}", item['preco'] * item['qtd']) for item in self.carrinho_pdv]
                    
                    cursor.close()
                    conn.close()

                    try:
                        gerar_comprovante_pdf(
                            venda_id=venda_id,
                            cliente_nome=cliente,
                            itens=itens_comprovante,
                            total=total_venda,
                            forma_pagamento=pagto,
                            nome_empresa="BVC Assistência"
                        )
                    except Exception as pdf_err:
                        print(f"Erro ao gerar PDF: {pdf_err}")

                    self.carrinho_pdv.clear()
                    ent_cliente.delete(0, "end")
                    atualizar_carrinho()
                    carregar_produtos()
            except Exception as e:
                print(f"Erro ao finalizar venda: {e}")

        def abrir_comanda():
            cliente_bruto = ent_cliente.get().strip()
            if not cliente_bruto:
                print("Digite o nome do lojista para abrir a comanda!")
                return
            
            cliente = cliente_bruto.title()
            if not self.carrinho_pdv:
                return

            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    # Ativa o modo lojista para garantir que o preço salvo use o de revenda
                    self.modo_lojista = True

                    for item in self.carrinho_pdv:
                        cursor.execute(
                            "SELECT id, quantidade FROM comandas_abertas WHERE cliente = %s AND produto_id = %s",
                            (cliente, item['id'])
                        )
                        item_existente = cursor.fetchone()

                        if item_existente:
                            comanda_item_id, qtd_atual = item_existente
                            nova_qtd = qtd_atual + item['qtd']
                            cursor.execute(
                                "UPDATE comandas_abertas SET quantidade = %s WHERE id = %s",
                                (nova_qtd, comanda_item_id)
                            )
                        else:
                            cursor.execute(
                                "INSERT INTO comandas_abertas (cliente, produto_id, descricao, quantidade, preco) VALUES (%s, %s, %s, %s, %s)",
                                (cliente, item['id'], item['nome'], item['qtd'], item['preco'])
                            )

                        cursor.execute("UPDATE estoque SET quantidade = quantidade - %s WHERE id = %s", (item['qtd'], item['id']))

                    conn.commit()
                    cursor.close()
                    conn.close()

                    self.carrinho_pdv.clear()
                    ent_cliente.delete(0, "end")
                    atualizar_carrinho()
                    carregar_produtos()
                    print(f"Comanda aberta/atualizada com sucesso para {cliente}!")
            except Exception as e:
                print(f"Erro ao abrir/atualizar comanda: {e}")

        # ==========================================================
        # CRIAÇÃO DOS BOTÕES NA COLUNA DA DIREITA
        # ==========================================================
        btn_finalizar = ctk.CTkButton(
            right, text="Finalizar Venda", 
            fg_color="#16a34a", hover_color="#15803d", 
            font=("Arial", 14, "bold"), height=35,
            command=finalizar_venda
        )
        btn_finalizar.pack(pady=(10, 5), fill="x", padx=10)

        btn_comanda = ctk.CTkButton(
            right, text="📋 Abrir Comanda / Lojista", 
            fg_color="#2563eb", hover_color="#1d4ed8", 
            font=("Arial", 14, "bold"), height=35,
            command=abrir_comanda
        )
        btn_comanda.pack(pady=(0, 10), fill="x", padx=10)

        # Associa o evento de busca e faz o carregamento inicial
        ent_busca.bind("<KeyRelease>", lambda e: carregar_produtos(ent_busca.get()))
        carregar_produtos()
    # ==========================================
    # 3. TELA DE ORDENS DE SERVIÇO (O.S.)
    # ==========================================
def mostrar_tela_os(self):
        # Limpa o container e recria o cabeçalho padrão do sistema
        self.limpar_container()
                    
        main_os_frame = ctk.CTkFrame(self.body_container, fg_color="transparent")
        main_os_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ----------------- FUNÇÃO INTERNA PARA GERAR PDF DA O.S. -----------------
        def gerar_pdf_os(os_id, cliente, aparelho, valor, status):
            try:
                if not os.path.exists("comprovantes"):
                    os.makedirs("comprovantes")
                    
                caminho_arquivo = os.path.abspath(f"comprovantes/Ordem_Servico_{os_id}.pdf")
                c = canvas.Canvas(caminho_arquivo, pagesize=A6)
                largura, altura = A6
                
                c.setFont("Helvetica-Bold", 14)
                c.drawString(20, altura - 30, "LOJA BVC - ORDEM DE SERVIÇO")
                
                c.setFont("Helvetica", 10)
                c.drawString(20, altura - 55, f"O.S. Nº: #{os_id}")
                c.drawString(20, altura - 70, f"Cliente: {cliente}")
                c.drawString(20, altura - 85, f"Aparelho: {aparelho}")
                c.drawString(20, altura - 100, f"Valor: R$ {float(valor or 0):.2f}")
                c.drawString(20, altura - 115, f"Status: {status}")
                
                c.save()
                
                if os.name == 'nt':
                    os.startfile(caminho_arquivo)
                else:
                    subprocess.call(['xdg-open', caminho_arquivo])
            except Exception as e:
                print(f"Erro ao gerar PDF da O.S.: {e}")

        # ----------------- PAINEL ESQUERDO: FORMULÁRIO O.S. -----------------
        left_os = ctk.CTkFrame(main_os_frame, width=300, fg_color=COR_CARD)
        left_os.pack(side="left", fill="y", padx=(0, 5))
        left_os.pack_propagate(False)

        ctk.CTkLabel(left_os, text="Nova Ordem de Serviço", font=("Arial", 14, "bold")).pack(pady=10)

        ent_cliente_os = ctk.CTkEntry(left_os, placeholder_text="Nome do Cliente", width=260)
        ent_cliente_os.pack(pady=5)
        
        ent_aparelho = ctk.CTkEntry(left_os, placeholder_text="Aparelho / Defeito", width=260)
        ent_aparelho.pack(pady=5)
        
        ent_valor_os = ctk.CTkEntry(left_os, placeholder_text="Valor Estimado (R$)", width=260)
        ent_valor_os.pack(pady=5)

        combo_status = ctk.CTkOptionMenu(left_os, values=["Pendente", "Em Andamento", "Concluído"], width=260)
        combo_status.pack(pady=5)
        combo_status.set("Pendente")

        lbl_msg_os = ctk.CTkLabel(left_os, text="", font=FONTE_LEGENDA)
        lbl_msg_os.pack(pady=2)

        def salvar_os():
            cliente = ent_cliente_os.get().strip()
            aparelho = ent_aparelho.get().strip()
            valor = ent_valor_os.get().strip().replace(",", ".") or "0"
            status = combo_status.get()
            
            if not cliente or not aparelho:
                lbl_msg_os.configure(text="Preencha Cliente e Aparelho!", text_color=COR_ERRO)
                return
                
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO ordens_servico (cliente, aparelho, valor, status) VALUES (%s, %s, %s, %s)",
                        (cliente, aparelho, float(valor), status)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    ent_cliente_os.delete(0, "end")
                    ent_aparelho.delete(0, "end")
                    ent_valor_os.delete(0, "end")
                    combo_status.set("Pendente")
                    lbl_msg_os.configure(text="O.S. aberta com sucesso!", text_color=COR_SUCESSO)
                    carregar_dados_os()
            except Exception as e:
                lbl_msg_os.configure(text=f"Erro: {e}", text_color=COR_ERRO)

        btn_salvar_os = ctk.CTkButton(left_os, text="Abrir O.S.", fg_color=COR_SUCESSO, hover_color=COR_SUCESSO_HOVER, command=salvar_os, width=260)
        btn_salvar_os.pack(pady=10)

        # ----------------- PAINEL DIREITO: LISTAGEM DE O.S. -----------------
        right_os = ctk.CTkFrame(main_os_frame, fg_color=COR_CARD)
        right_os.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(right_os, text="Ordens de Serviço Registradas", font=("Arial", 12, "bold")).pack(pady=10, padx=10, anchor="w")

        lista_scroll_os = ctk.CTkScrollableFrame(right_os, fg_color="transparent")
        lista_scroll_os.pack(fill="both", expand=True, padx=10, pady=5)

        def alterar_status(os_id, novo_status):
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE ordens_servico SET status = %s WHERE id = %s", (novo_status, os_id))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    carregar_dados_os()
            except Exception as e:
                print(f"Erro ao alterar status: {e}")

        def excluir_os(os_id):
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM ordens_servico WHERE id = %s", (os_id,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    carregar_dados_os()
            except Exception as e:
                print(f"Erro ao excluir O.S.: {e}")

        def carregar_dados_os():
            for widget in lista_scroll_os.winfo_children():
                widget.destroy()
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, cliente, aparelho, valor, status FROM ordens_servico ORDER BY id DESC")
                    resultados = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    
                    if not resultados:
                        ctk.CTkLabel(lista_scroll_os, text="Nenhuma O.S. cadastrada.", text_color=COR_TEXTO_SECUNDARIO).pack(pady=20)
                        return

                    for os_item in resultados:
                        o_id, cli, ap, val, st = os_item
                        
                        if st == "Concluído":
                            cor_st = "#14532d"
                        elif st == "Em Andamento":
                            cor_st = "#b45309"
                        else:
                            cor_st = "#7f1d1d"

                        card = ctk.CTkFrame(lista_scroll_os, fg_color=COR_CARD_ITEM)
                        card.pack(fill="x", padx=5, pady=6)

                        info = ctk.CTkFrame(card, fg_color="transparent")
                        info.pack(side="left", fill="both", expand=True, padx=10, pady=5)

                        ctk.CTkLabel(info, text=f"O.S. #{o_id} | Cliente: {cli}", font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
                        ctk.CTkLabel(info, text=f"Descrição: {ap}", font=("Arial", 11), text_color="#cbd5e1", anchor="w", wraplength=430).pack(fill="x", pady=2)
                        ctk.CTkLabel(info, text=f"Valor Estimado: R$ {float(val or 0):.2f}", font=("Arial", 10), text_color="#94a3b8", anchor="w").pack(fill="x")

                        ctk.CTkLabel(card, text=st, fg_color=cor_st, corner_radius=6, font=("Arial", 10, "bold"), width=90).pack(side="left", padx=10)

                        btn_pdf = ctk.CTkButton(card, text="📄 PDF", width=60, fg_color="#0284c7", hover_color="#0369a1",
                            command=lambda oid=o_id, c=cli, desc=ap, v=val, status=st: gerar_pdf_os(oid, c, desc, v, status))
                        btn_pdf.pack(side="right", padx=2)

                        btn_status = ctk.CTkButton(card, text="🔄 Status", width=70, fg_color="#334155", hover_color="#475569",
                            command=lambda oid=o_id, atual=st: alterar_status(oid, "Concluído" if atual != "Concluído" else "Pendente"))
                        btn_status.pack(side="right", padx=2)

                        btn_del = ctk.CTkButton(card, text="🗑️", width=30, fg_color="#b91c1c", hover_color="#991b1b", command=lambda oid=o_id: excluir_os(oid))
                        btn_del.pack(side="right", padx=5)
            except Exception as e:
                print(f"Erro ao carregar O.S.: {e}")

        carregar_dados_os()    
# ==========================================
    # 4. TELA DE CONTROLE DE ESTOQUE
    # ==========================================
def mostrar_tela_estoque(self, filtro_categoria="Todas", filtro_marca="Todas", termo_busca=""):
        self.limpar_container()

        body = ctk.CTkFrame(self.body_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        # Título da Tela
        ctk.CTkLabel(body, text="Módulo de Controle de Estoque", font=FONTE_TITULO).pack(pady=(0, 10))

        # Layout em 2 colunas (Esquerda: Cadastro/Edição | Direita: Listagem e Filtros)
        main_layout = ctk.CTkFrame(body, fg_color="transparent")
        main_layout.pack(fill="both", expand=True)

        # PAINEL ESQUERDO: Formulário de Cadastro / Edição
        left_panel = ctk.CTkFrame(main_layout, width=320, fg_color=COR_CARD, corner_radius=10)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        lbl_titulo_form = ctk.CTkLabel(left_panel, text="Cadastrar Item", font=FONTE_SUBTITULO)
        lbl_titulo_form.pack(pady=(15, 10))

        # Campos do formulário
        combo_categoria = ctk.CTkComboBox(left_panel, values=["Telas", "Baterias", "Tampa", "Diversos"], width=280)
        combo_categoria.pack(pady=8)
        combo_categoria.set("Telas") # Valor padrão seguro

        combo_marca = ctk.CTkComboBox(left_panel, values=["Samsung", "Motorola", "Apple", "Xiaomi", "Redmi", "Realme", "Philco", "Infinix", "Itel", "Oppo", "Cubot", "Outras"], width=280)
        combo_marca.pack(pady=8)
        combo_marca.set("Samsung") # Valor padrão seguro

        ent_modelo = ctk.CTkEntry(left_panel, placeholder_text="Modelo (ex: A12, G52, 11 Pro)", width=280)
        ent_modelo.pack(pady=8)

        ent_quantidade = ctk.CTkEntry(left_panel, placeholder_text="Quantidade Atual", width=280)
        ent_quantidade.pack(pady=8)

        # Limites mínimos e máximos automáticos (ou manuais)
        frame_limites = ctk.CTkFrame(left_panel, fg_color="transparent", width=280)
        frame_limites.pack(pady=4)
        ent_min = ctk.CTkEntry(frame_limites, placeholder_text="Mín", width=130)
        ent_min.pack(side="left", padx=(0, 10))
        ent_max = ctk.CTkEntry(frame_limites, placeholder_text="Máx", width=130)
        ent_max.pack(side="right")

        # Campos de Preços Separados
        ent_preco_rev = ctk.CTkEntry(left_panel, placeholder_text="Preço Revendedor (R$)", width=280)
        ent_preco_rev.pack(pady=8)

        ent_preco_final = ctk.CTkEntry(left_panel, placeholder_text="Preço Final / Balcão (R$)", width=280)
        ent_preco_final.pack(pady=8)

        lbl_msg_estoque = ctk.CTkLabel(left_panel, text="", font=FONTE_LEGENDA, text_color=COR_ERRO)
        lbl_msg_estoque.pack(pady=2)

        # Função interna para salvar item no estoque
        def salvar_item_estoque():
            cat = combo_categoria.get()
            mar = combo_marca.get()
            mod = ent_modelo.get().strip()
            qtd = ent_quantidade.get().strip()
            pmin = ent_min.get().strip()
            pmax = ent_max.get().strip()
            prc_rev = ent_preco_rev.get().strip()
            prc_fin = ent_preco_final.get().strip()

            if not mod or not qtd or not prc_fin:
                lbl_msg_estoque.configure(text="Preencha modelo, qtd e preço final!")
                return

            try:
                q_val = int(qtd)
                min_val = int(pmin) if pmin else 2
                max_val = int(pmax) if pmax else 10
                p_rev_val = float(prc_rev.replace(",", ".")) if prc_rev else 0.00
                p_fin_val = float(prc_fin.replace(",", "."))

                conn = conectar()
                cursor = conn.cursor()

                if self.peca_em_edicao_id:
                    cursor.execute(
                        "UPDATE estoque SET categoria=%s, marca=%s, modelo=%s, quantidade=%s, min_alerta=%s, max_estoque=%s, preco_revendedor=%s, preco_final=%s WHERE id=%s",
                        (cat, mar, mod, q_val, min_val, max_val, p_rev_val, p_fin_val, self.peca_em_edicao_id)
                    )
                    self.peca_em_edicao_id = None
                    lbl_titulo_form.configure(text="Cadastrar Item")
                    btn_salvar_estoque.configure(text="Salvar Item", fg_color=COR_SUCESSO, hover_color=COR_SUCESSO_HOVER)
                else:
                    cursor.execute(
                        "INSERT INTO estoque (categoria, marca, modelo, quantidade, min_alerta, max_estoque, preco_revendedor, preco_final) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (cat, mar, mod, q_val, min_val, max_val, p_rev_val, p_fin_val)
                    )

                conn.commit()
                cursor.close()
                conn.close()

                # Limpar campos mantendo os combos resetados
                ent_modelo.delete(0, "end")
                ent_quantidade.delete(0, "end")
                ent_min.delete(0, "end")
                ent_max.delete(0, "end")
                ent_preco_rev.delete(0, "end")
                ent_preco_final.delete(0, "end")
                lbl_msg_estoque.configure(text="")
                
                self.mostrar_tela_estoque(filtro_categoria, filtro_marca, termo_busca)
            except Exception as ex:
                lbl_msg_estoque.configure(text="Erro ao salvar item.")
                print(ex)

        btn_salvar_estoque = ctk.CTkButton(left_panel, text="Salvar Item", command=salvar_item_estoque, width=280, fg_color=COR_SUCESSO, hover_color=COR_SUCESSO_HOVER)
        btn_salvar_estoque.pack(pady=(15, 5))

        # PAINEL DIREITO: Busca, Filtros de Marcas com Barra de Rolagem e Lista
        right_panel = ctk.CTkFrame(main_layout, fg_color=COR_CARD, corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)

        # Barra de Pesquisa
        ent_busca_estoque = ctk.CTkEntry(right_panel, placeholder_text="Buscar marca ou modelo...", width=400)
        ent_busca_estoque.pack(padx=15, pady=(15, 5), anchor="w")
        if termo_busca:
            ent_busca_estoque.insert(0, termo_busca)

        # Filtro de Categorias (Botões superiores)
        cat_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        cat_frame.pack(fill="x", padx=15, pady=2)
        
        categorias = [("Todas", "Todas"), ("Telas", "Telas"), ("Baterias", "Baterias"), ("Tampa", "Tampa"), ("Diversos", "Diversos"),]
        for label_btn, val_cat in categorias:
            cor_btn = COR_PRIMARIA if filtro_categoria == val_cat else COR_CARD_ITEM
            ctk.CTkButton(
                cat_frame, text=label_btn, width=80, fg_color=cor_btn, 
                command=lambda c=val_cat: self.mostrar_tela_estoque(filtro_categoria=c, filtro_marca=filtro_marca, termo_busca=ent_busca_estoque.get())
            ).pack(side="left", padx=2)

        # BARRA DE ROLAGEM HORIZONTAL PARA AS MARCAS
        canvas_marcas = ctk.CTkCanvas(right_panel, height=45, bg=COR_CARD, highlightthickness=0)
        scrollbar_marcas = ctk.CTkScrollbar(right_panel, orientation="horizontal", command=canvas_marcas.xview)
        canvas_marcas.configure(xscrollcommand=scrollbar_marcas.set)

        scrollbar_marcas.pack(fill="x", padx=15, pady=(5, 0))
        canvas_marcas.pack(fill="x", padx=15, pady=2)

        frame_marcas_interno = ctk.CTkFrame(canvas_marcas, fg_color="transparent")
        canvas_marcas.create_window((0, 0), window=frame_marcas_interno, anchor="nw")

        def atualizar_scroll_marcas(event):
            canvas_marcas.configure(scrollregion=canvas_marcas.bbox("all"))
        frame_marcas_interno.bind("<Configure>", atualizar_scroll_marcas)

        marcas = ["Todas", "Samsung", "Motorola", "Apple", "Xiaomi", "Redmi", "Realme", "Philco", "Infinix", "Itel", "Oppo", "Cubot", "Outras"]
        for marca in marcas:
            cor_m_btn = COR_PRIMARIA if filtro_marca == marca else COR_CARD_ITEM
            ctk.CTkButton(
                frame_marcas_interno, 
                text=marca, 
                width=90, 
                fg_color=cor_m_btn, 
                hover_color=COR_PRIMARIA,
                command=lambda m=marca: self.mostrar_tela_estoque(filtro_categoria=filtro_categoria, filtro_marca=m, termo_busca=ent_busca_estoque.get())
            ).pack(side="left", padx=3, pady=2)

        scroll_itens_estoque = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        scroll_itens_estoque.pack(fill="both", expand=True, padx=10, pady=10)

        def excluir_item(item_id):
            try:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM estoque WHERE id = %s", (item_id,))
                conn.commit()
                cursor.close()
                conn.close()
                self.mostrar_tela_estoque(filtro_categoria, filtro_marca, ent_busca_estoque.get())
            except Exception as e:
                print(f"Erro ao excluir item: {e}")

        def preparar_edicao(item_id, cat, marca, modelo, qtd, min_alt, max_alt, p_rev, p_fin):
            self.peca_em_edicao_id = item_id
            lbl_titulo_form.configure(text="Editar Item")
            btn_salvar_estoque.configure(text="Atualizar Item", fg_color="#F0AD4E", hover_color="#EEA236")
            
            combo_categoria.set(cat)
            combo_marca.set(marca)
            ent_modelo.delete(0, "end")
            ent_modelo.insert(0, modelo)
            ent_quantidade.delete(0, "end")
            ent_quantidade.insert(0, str(qtd))
            ent_min.delete(0, "end")
            ent_min.insert(0, str(min_alt))
            ent_max.delete(0, "end")
            ent_max.insert(0, str(max_alt))
            ent_preco_rev.delete(0, "end")
            ent_preco_rev.insert(0, str(p_rev))
            ent_preco_final.delete(0, "end")
            ent_preco_final.insert(0, str(p_fin))

        # Carregamento inteligente dos itens filtrados do Banco de Dados
        try:
            conn = conectar()
            if conn:
                cursor = conn.cursor()
                
                # Montagem dinâmica da query com base nos filtros ativos
                query = "SELECT id, categoria, marca, modelo, quantidade, min_alerta, max_estoque, preco_revendedor, preco_final FROM estoque WHERE 1=1"
                params = []

                if filtro_categoria != "Todas":
                    query += " AND categoria = %s"
                    params.append(filtro_categoria)

                if filtro_marca != "Todas":
                    query += " AND marca = %s"
                    params.append(filtro_marca)

                termo_atual = ent_busca_estoque.get().strip()
                if termo_atual:
                    query += " AND (LOWER(modelo) LIKE %s OR LOWER(marca) LIKE %s)"
                    params.extend([f"%{termo_atual.lower()}%", f"%{termo_atual.lower()}%"])

                query += " ORDER BY id DESC"

                cursor.execute(query, tuple(params))
                itens = cursor.fetchall()
                cursor.close()
                conn.close()

                if not itens:
                    ctk.CTkLabel(scroll_itens_estoque, text="Nenhum item encontrado com esses filtros.", text_color=COR_TEXTO_SECUNDARIO).pack(pady=20)
                else:
                    for it_id, cat, marca, modelo, qtd, min_alt, max_alt, p_rev, p_fin in itens:
                        row_item = ctk.CTkFrame(scroll_itens_estoque, fg_color=COR_CARD_ITEM, corner_radius=6)
                        row_item.pack(fill="x", pady=4, padx=5)

                        cor_texto_qtd = COR_SUCESSO if qtd > min_alt else COR_ERRO

                        ctk.CTkLabel(row_item, text=f"[{cat}] {marca} - {modelo}", font=FONTE_SUBTITULO).pack(side="left", padx=10, pady=8)
                        
                        btn_excluir = ctk.CTkButton(row_item, text="X", width=35, fg_color="#D9534F", hover_color="#C9302C", 
                                                    command=lambda i=it_id: excluir_item(i))
                        btn_excluir.pack(side="right", padx=5, pady=8)

                        btn_editar = ctk.CTkButton(row_item, text="Editar", width=55, fg_color="#F0AD4E", hover_color="#EEA236", 
                                                   command=lambda i=it_id, c=cat, m=marca, mod=modelo, q=qtd, mn=min_alt, mx=max_alt, pr=p_rev, pf=p_fin: preparar_edicao(i, c, m, mod, q, mn, mx, pr, pf))
                        btn_editar.pack(side="right", padx=2, pady=8)

                        txt_valores = f"Qtd: {qtd} | Rev: R$ {float(p_rev):.2f} | Final: R$ {float(p_fin):.2f}"
                        ctk.CTkLabel(row_item, text=txt_valores, font=FONTE_CORPO, text_color=cor_texto_qtd).pack(side="right", padx=10, pady=8)
        except Exception as e:
            print(f"Erro ao carregar estoque: {e}")

        # Evento de digitação na busca para atualizar instantaneamente
        ent_busca_estoque.bind("<KeyRelease>", lambda e: self.mostrar_tela_estoque(filtro_categoria, filtro_marca, ent_busca_estoque.get()))
# ==========================================
    # 5. TELA DE RELATÓRIOS
    # ==========================================
def mostrar_tela_relatorios(self):
        self.limpar_container()
        
        body = ctk.CTkFrame(self.body_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        top_bar = ctk.CTkFrame(body, height=50, fg_color=COR_CARD)
        top_bar.pack(fill="x", padx=5, pady=5)

        lbl_faturamento = ctk.CTkLabel(top_bar, text="Faturamento Total: R$ 0,00", font=FONTE_SUBTITULO, text_color=COR_DESTAQUE)
        lbl_faturamento.pack(side="left", padx=15)

        scroll_vendas = ctk.CTkScrollableFrame(body, fg_color="transparent")
        scroll_vendas.pack(fill="both", expand=True, padx=5, pady=5)

        def excluir_venda(venda_id):
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM itens_venda WHERE venda_id = %s", (venda_id,))
                    cursor.execute("DELETE FROM vendas WHERE id = %s", (venda_id,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    self.mostrar_tela_relatorios()
            except Exception as e:
                print(f"Erro ao excluir venda #{venda_id}: {e}")

        try:
            conn = conectar()
            if not conn:
                return
            
            cursor = conn.cursor()
            cursor.execute("SELECT id, cliente, data_hora, total, pagamento FROM vendas ORDER BY id DESC LIMIT 50")
            vendas = cursor.fetchall()

            cursor.execute("SELECT SUM(total) FROM vendas")
            res_sum = cursor.fetchone()
            total_acumulado = float(res_sum[0]) if res_sum and res_sum[0] is not None else 0.0
            lbl_faturamento.configure(text=f"Faturamento Total: R$ {total_acumulado:.2f}")
            cursor.close()
            conn.close()

            if not vendas:
                ctk.CTkLabel(scroll_vendas, text="Nenhuma venda registrada até o momento.", font=FONTE_CORPO, text_color=COR_TEXTO_SECUNDARIO).pack(pady=20)
                return

            for v_id, cliente, data_h, total, pag in vendas:
                card_venda = ctk.CTkFrame(scroll_vendas, fg_color=COR_CARD, corner_radius=8)
                card_venda.pack(fill="x", pady=5, padx=5)

                top_row = ctk.CTkFrame(card_venda, fg_color="transparent")
                top_row.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(top_row, text=f"Venda #{v_id:04d} - {cliente}", font=FONTE_SUBTITULO).pack(side="left")
                ctk.CTkLabel(top_row, text=f"Data: {data_h} | Pgto: {pag}", font=FONTE_LEGENDA, text_color=COR_TEXTO_SECUNDARIO).pack(side="right")

                # Abre uma nova conexão rápida por card para buscar os itens com segurança
                try:
                    conn_item = conectar()
                    if conn_item:
                        cur_item = conn_item.cursor()
                        cur_item.execute("SELECT descricao, valor FROM itens_venda WHERE venda_id = %s", (v_id,))
                        itens = cur_item.fetchall()
                        cur_item.close()
                        conn_item.close()

                        for desc, val in itens:
                            item_row = ctk.CTkFrame(card_venda, fg_color="transparent")
                            item_row.pack(fill="x", padx=20, pady=1)
                            ctk.CTkLabel(item_row, text=f"• {desc}", font=FONTE_LEGENDA).pack(side="left")
                            ctk.CTkLabel(item_row, text=f"R$ {float(val):.2f}", font=FONTE_LEGENDA).pack(side="right")
                except Exception as ex_item:
                    print(f"Erro ao buscar itens da venda {v_id}: {ex_item}")

                bot_row = ctk.CTkFrame(card_venda, fg_color="transparent")
                bot_row.pack(fill="x", padx=10, pady=5)

                btn_excluir_venda = ctk.CTkButton(
                    bot_row, text="🗑️ Excluir Venda", width=110, height=26,
                    fg_color="#b91c1c", hover_color="#991b1b", font=FONTE_LEGENDA,
                    command=lambda id_v=v_id: excluir_venda(id_v)
                )
                btn_excluir_venda.pack(side="left")

                ctk.CTkLabel(bot_row, text=f"Total Venda: R$ {float(total):.2f}", font=FONTE_SUBTITULO, text_color=COR_TEXTO_VALOR).pack(side="right")

        except Exception as e:
            print(f"Erro ao carregar relatórios: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()

def mostrar_tela_comandas(self):
        self.limpar_container()

        body = ctk.CTkFrame(self.body_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        left = ctk.CTkFrame(body, width=300, fg_color=COR_CARD)
        left.pack(side="left", fill="both", padx=(0, 5))
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Lojistas / Comandas", font=FONTE_SUBTITULO).pack(
            pady=(12, 6)
        )

        scroll_clientes = ctk.CTkScrollableFrame(left, fg_color="transparent")
        scroll_clientes.pack(fill="both", expand=True, padx=5, pady=5)

        right = ctk.CTkFrame(body, fg_color=COR_CARD)
        right.pack(side="right", fill="both", expand=True, padx=(5, 0))

        lbl_titulo_comanda = ctk.CTkLabel(
            right, text="Selecione um lojista ao lado", font=FONTE_SUBTITULO
        )
        lbl_titulo_comanda.pack(pady=(10, 2))

        # --- CAIXA DE OBSERVAÇÃO BEM NO TOPO (Garantido que aparece) ---
        frame_obs = ctk.CTkFrame(right, fg_color="transparent")
        frame_obs.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(frame_obs, text="Observações do Pedido:", font=FONTE_LEGENDA, anchor="w").pack(fill="x", pady=(0, 2))
        txt_observacao = ctk.CTkTextbox(frame_obs, height=45, font=FONTE_CORPO)
        txt_observacao.pack(fill="x")

        # Campo de Frete
        frame_frete = ctk.CTkFrame(right, fg_color="transparent")
        frame_frete.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(frame_frete, text="Valor do Frete (R$):", font=FONTE_CORPO).pack(side="left", padx=(0, 5))
        ent_frete = ctk.CTkEntry(frame_frete, width=120, placeholder_text="0.00")
        ent_frete.pack(side="left")
        ent_frete.insert(0, "0,00")

        scroll_itens_comanda = ctk.CTkScrollableFrame(
            right, fg_color="transparent"
        )
        scroll_itens_comanda.pack(fill="both", expand=True, padx=15, pady=5)

        lbl_total_comanda = ctk.CTkLabel(
            right,
            text="Total da Comanda: R$ 0,00",
            font=FONTE_TITULO,
            text_color=COR_TEXTO_VALOR,
        )
        lbl_total_comanda.pack(pady=5)

        btn_fechar_comanda = ctk.CTkButton(
            right,
            text="✔️ Fechar Comanda e Gerar Venda / PDF",
            fg_color=COR_SUCESSO,
            hover_color=COR_SUCESSO_HOVER,
            height=36,
            state="disabled",
        )
        btn_fechar_comanda.pack(pady=(0, 15), padx=15, fill="x")

        def obter_valor_frete():
            try:
                frete_texto = ent_frete.get().strip().replace(",", ".")
                return float(frete_texto) if frete_texto else 0.0
            except ValueError:
                return 0.0

        _ultimo_total_itens = 0.0

        def atualizar_total_geral(total_itens=None):
            nonlocal _ultimo_total_itens
            if total_itens is not None:
                _ultimo_total_itens = total_itens
            
            frete = obter_valor_frete()
            total_geral = _ultimo_total_itens + frete
            lbl_total_comanda.configure(
                text=f"Total da Comanda: R$ {total_geral:.2f} (Itens: R$ {_ultimo_total_itens:.2f} + Frete: R$ {frete:.2f})"
            )

        ent_frete.bind("<KeyRelease>", lambda event: atualizar_total_geral())

        def desenhar_itens_comanda(cliente_nome, itens):
            lbl_titulo_comanda.configure(text=f"Comanda de: {cliente_nome}")
            for child in scroll_itens_comanda.winfo_children():
                child.destroy()

            total_itens = 0.0

            if not itens:
                ctk.CTkLabel(
                    scroll_itens_comanda,
                    text="Nenhum item nesta comanda ainda.",
                    font=FONTE_CORPO,
                    text_color=COR_TEXTO_SECUNDARIO,
                ).pack(pady=20)
                
                atualizar_total_geral(0.0)
                btn_fechar_comanda.configure(state="disabled")
                return

            btn_fechar_comanda.configure(state="normal")

            for item_id, prod_id, desc, qtd, preco in itens:
                subtotal = qtd * float(preco)
                total_itens += subtotal

                row = ctk.CTkFrame(
                    scroll_itens_comanda,
                    fg_color=COR_CARD_ITEM,
                    corner_radius=6,
                )
                row.pack(fill="x", pady=3, padx=2)

                info_txt = f"{qtd}x {desc} - R$ {subtotal:.2f}"
                ctk.CTkLabel(
                    row, text=info_txt, font=FONTE_CORPO, anchor="w", text_color="white"
                ).pack(side="left", padx=10, pady=8, fill="x", expand=True)

                btn_remover_item = ctk.CTkButton(
                    row,
                    text="🗑️ Devolver",
                    width=90,
                    height=26,
                    fg_color="#b91c1c",
                    hover_color="#991b1b",
                    font=FONTE_LEGENDA,
                    command=lambda i_id=item_id, p_id=prod_id, q=qtd, c=cliente_nome: devolver_item_comanda(
                        i_id, p_id, q, c
                    ),
                )
                btn_remover_item.pack(side="right", padx=10, pady=6)

            atualizar_total_geral(total_itens)
            
            btn_fechar_comanda.configure(
                command=lambda: faturar_comanda_thread(cliente_nome, itens, total_itens)
            )

        def carregar_detalhes_comanda(cliente_nome):
            lbl_titulo_comanda.configure(text=f"Comanda de: {cliente_nome} (Carregando...)")
            for child in scroll_itens_comanda.winfo_children():
                child.destroy()

            ctk.CTkLabel(
                scroll_itens_comanda,
                text="Buscando itens na nuvem...",
                font=FONTE_CORPO,
                text_color=COR_TEXTO_SECUNDARIO,
            ).pack(pady=20)
            btn_fechar_comanda.configure(state="disabled")

            def background_carregar():
                try:
                    conn = conectar()
                    if not conn:
                        return
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, produto_id, descricao, quantidade, preco FROM comandas_abertas WHERE cliente = %s",
                        (cliente_nome,),
                    )
                    itens = cursor.fetchall()
                    cursor.close()
                    conn.close()

                    scroll_itens_comanda.after(0, lambda: desenhar_itens_comanda(cliente_nome, itens))
                except Exception as e:
                    print(f"Erro ao carregar detalhes da comanda: {e}")

            threading.Thread(target=background_carregar, daemon=True).start()

        def devolver_item_comanda(item_id, produto_id, quantidade, cliente_nome):
            try:
                conn = conectar()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE estoque SET quantidade = quantidade + %s WHERE id = %s",
                        (quantidade, produto_id),
                    )
                    cursor.execute(
                        "DELETE FROM comandas_abertas WHERE id = %s",
                        (item_id,),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    carregar_detalhes_comanda(cliente_nome)
            except Exception as e:
                print(f"Erro ao devolver item da comanda: {e}")

        def faturar_comanda_thread(cliente_nome, itens, total_itens):
            btn_fechar_comanda.update_idletasks()

            valor_frete = obter_valor_frete()
            total_venda = total_itens + valor_frete
            observacao_texto = txt_observacao.get("1.0", "end-1c").strip()
            data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pagto = "Faturado / Lojista"

            btn_fechar_comanda.configure(text="Processando Venda...", state="disabled")

            def background_faturamento():
                try:
                    conn = conectar()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO vendas (cliente, data_hora, total, frete, pagamento, observacao) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                            (cliente_nome, data_hoje, total_venda, valor_frete, pagto, observacao_texto),
                        )
                        venda_id = cursor.fetchone()[0]

                        itens_comprovante = []
                        for _, _, desc, qtd, preco in itens:
                            sub = qtd * float(preco)
                            cursor.execute(
                                "INSERT INTO itens_venda (venda_id, descricao, valor) VALUES (%s, %s, %s)",
                                (venda_id, f"{qtd}x {desc}", sub),
                            )
                            itens_comprovante.append((f"{qtd}x {desc}", sub))

                        if valor_frete > 0:
                            itens_comprovante.append(("Valor do Frete", valor_frete))

                        if observacao_texto:
                            itens_comprovante.append((f"Obs: {observacao_texto}", 0.0))

                        cursor.execute(
                            "DELETE FROM comandas_abertas WHERE cliente = %s",
                            (cliente_nome,),
                        )
                        conn.commit()
                        cursor.close()
                        conn.close()

                        try:
                            gerar_comprovante_pdf(
                                venda_id=venda_id,
                                cliente_nome=cliente_nome,
                                itens=itens_comprovante,
                                total=total_venda,
                                forma_pagamento=pagto,
                                nome_empresa="BVC Assistência",
                            )
                        except Exception as pdf_err:
                            print(f"Erro ao gerar PDF da comanda: {pdf_err}")

                        btn_fechar_comanda.after(0, lambda: self.mostrar_tela_comandas())

                except Exception as e:
                    print(f"Erro ao faturar comanda: {e}")
                    btn_fechar_comanda.after(0, lambda: btn_fechar_comanda.configure(
                        text="✔️ Fechar Comanda e Gerar Venda / PDF", state="normal"
                    ))

            threading.Thread(target=background_faturamento, daemon=True).start()

        def carregar_lista_clientes():
            for child in scroll_clientes.winfo_children():
                child.destroy()
            try:
                conn = conectar()
                if not conn:
                    return
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT cliente FROM comandas_abertas ORDER BY cliente"
                )
                clientes = cursor.fetchall()
                cursor.close()
                conn.close()

                if not clientes:
                    ctk.CTkLabel(scroll_clientes, text="Nenhuma comanda.", font=FONTE_CORPO, text_color=COR_TEXTO_SECUNDARIO).pack(pady=20)
                    return

                for (cli,) in clientes:
                    btn_cli = ctk.CTkButton(
                        scroll_clientes,
                        text=cli,
                        fg_color=COR_CARD_ITEM,
                        text_color="white",
                        hover_color=COR_DESTAQUE,
                        anchor="w",
                        height=32,
                        command=lambda c=cli: carregar_detalhes_comanda(c),
                    )
                    btn_cli.pack(fill="x", pady=2, padx=2)
            except Exception as e:
                print(f"Erro ao listar clientes de comandas: {e}")

        carregar_lista_clientes()