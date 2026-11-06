from PIL import Image

# Abre a imagem original (seja ela .png ou .jpg)
img = Image.open('fundo.png')  # Ou o nome da sua imagem original

# Redimensiona e salva em formato ICO nativo de alta qualidade
icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save('icone.ico', sizes=icon_sizes)

print('Ícone gerado com sucesso!')