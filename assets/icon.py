from PIL import Image, ImageDraw

def create_icon():
    # Cria uma imagem 64x64 com fundo transparente
    img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Desenha um círculo azul como fundo
    draw.ellipse([4, 4, 60, 60], fill='#2196F3')
    
    # Desenha uma seta para cima no centro
    arrow_points = [
        (32, 15),  # Ponta da seta
        (42, 30),  # Direita
        (37, 30),  # Interno direita
        (37, 49),  # Base direita
        (27, 49),  # Base esquerda
        (27, 30),  # Interno esquerda
        (22, 30),  # Esquerda
    ]
    draw.polygon(arrow_points, fill='white')
    
    return img

if __name__ == "__main__":
    # Cria e salva o ícone
    icon = create_icon()
    icon.save("icon.png")
