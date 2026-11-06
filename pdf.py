import os
from datetime import datetime
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas

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