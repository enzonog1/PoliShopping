# popular.py - cria usuários (e dados de exemplo) do PoliShopping a cada deploy.
# Rodado pelo build.sh com:  python manage.py shell < popular.py
# Idempotente: pode rodar quantas vezes quiser, não duplica nada.
import os

from marketplace.models import Anuncio, Categoria, Proposta, Usuario

SENHA = os.environ.get("SENHA_PADRAO", "senha1234")  # letras + números

# (e-mail, nome, NUSP, papel)
USUARIOS = [
    ("carlos.duarte@usp.br", "Carlos Duarte", 12345601, "anunciante"),
    ("marina.lima@usp.br", "Marina Lima", 12345602, "anunciante"),
    ("rafael.tavares@usp.br", "Rafael Tavares", 12345603, "interessado"),
    ("juliana.prado@usp.br", "Juliana Prado", 12345604, "interessado"),
]

CATEGORIAS = ["Livros", "Eletrônicos", "Material de estudo"]

# (e-mail do dono, título, descrição, modalidade, preço, quantidade, ponto de encontro, categoria)
ANUNCIOS = [
    ("carlos.duarte@usp.br", "Calculadora científica HP 50g",
     "Pouco usada, funcionando perfeitamente, acompanha capa.",
     "venda", "250.00", 1, "Vão livre da Poli", "Eletrônicos"),
    ("marina.lima@usp.br", "Livro Termodinâmica (Çengel)",
     "Edição recente, sem anotações.",
     "venda", "90.00", 1, "Biblioteca da Elétrica", "Livros"),
]

# (e-mail do interessado, título do anúncio, mensagem)
PROPOSTAS = [
    ("rafael.tavares@usp.br", "Calculadora científica HP 50g", "Ainda está disponível?"),
    ("juliana.prado@usp.br", "Livro Termodinâmica (Çengel)", "Tenho interesse, podemos combinar?"),
]

usuarios = {}
for email, nome, nusp, papel in USUARIOS:
    u, criado = Usuario.objects.get_or_create(
        email=email,
        defaults=dict(username=email, nome_completo=nome, nusp=nusp, email_verificado=True),
    )
    if criado:
        u.set_password(SENHA)
        u.save()
        print(f"+ usuário {papel}: {email}")
    usuarios[email] = u

categorias = {n: Categoria.objects.get_or_create(nome=n)[0] for n in CATEGORIAS}

anuncios = {}
for dono, titulo, desc, modalidade, preco, qtd, ponto, cat in ANUNCIOS:
    a, criado = Anuncio.objects.get_or_create(
        dono=usuarios[dono], titulo=titulo,
        defaults=dict(descricao=desc, modalidade=modalidade, preco=preco,
                      quantidade=qtd, ponto_encontro=ponto),
    )
    if criado:
        a.categorias.add(categorias[cat])
        print(f"+ anúncio: {titulo}")
    anuncios[titulo] = a

for email, titulo, msg in PROPOSTAS:
    _, criado = Proposta.objects.get_or_create(
        anuncio=anuncios[titulo], interessado=usuarios[email], defaults=dict(mensagem=msg))
    if criado:
        print(f"+ proposta de {email} em '{titulo}'")

print("popular.py concluído.")
