import io
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from .models import Anuncio, Categoria, Denuncia, Usuario


def novo(nome, nusp, moderador=False):
    return Usuario.objects.create_user(
        username=f"{nome}@usp.br", email=f"{nome}@usp.br", password="senha1234",
        nome_completo=nome, nusp=nusp, is_moderador=moderador)


class FluxoTests(APITestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Calculadoras")
        self.ana, self.beto, self.carla = novo("ana", 10000001), novo("beto", 10000002), novo("carla", 10000004)
        self.mod = novo("mod", 10000003, moderador=True)

    def test_cadastro_exige_email_usp(self):
        r = self.client.post("/api/auth/registro/", {
            "nome_completo": "X", "email": "x@gmail.com", "nusp": 12345678, "password": "senha1234"})
        self.assertEqual(r.status_code, 400)

    def test_negociacao_e_avaliacao(self):
        self.client.force_authenticate(self.ana)
        r = self.client.post("/api/anuncios/", {
            "titulo": "HP 12C", "descricao": "Boa", "modalidade": "venda", "preco": "150.00", "quantidade": 1,
            "ponto_encontro": "Biênio", "categorias": [self.cat.id]}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        anuncio = r.data["id"]
        self.client.force_authenticate(self.beto)
        r = self.client.post("/api/propostas/", {"anuncio": anuncio, "mensagem": "Tenho interesse"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        proposta = r.data["id"]
        self.client.force_authenticate(self.ana)
        r = self.client.post(f"/api/propostas/{proposta}/aceitar/")
        self.assertEqual(r.data["contato"], "beto@usp.br")
        r = self.client.post(f"/api/propostas/{proposta}/avaliar/", {"nota": 5}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(Anuncio.objects.get(pk=anuncio).estado, "concluido")
        r = self.client.post(f"/api/propostas/{proposta}/avaliar/", {"nota": 4}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.beto.reputacao_media, 5)

    def test_tres_denuncias_ocultam_e_moderador_remove(self):
        a = Anuncio.objects.create(dono=self.ana, titulo="Golpe", descricao="x", modalidade="venda",
                                   preco=1, quantidade=1, ponto_encontro="Biênio")
        a.categorias.add(self.cat)
        for u in (self.beto, self.carla, self.mod):
            self.client.force_authenticate(u)
            r = self.client.post("/api/denuncias/", {"anuncio": a.id, "motivo": "golpe", "detalhamento": "suspeito"})
            self.assertEqual(r.status_code, 201, r.data)
        a.refresh_from_db()
        self.assertEqual(a.estado, "pendente_moderacao")
        d = Denuncia.objects.first()
        r = self.client.post("/api/moderacao/", {"denuncia": d.id, "tipo": "remover"})
        self.assertEqual(r.status_code, 400)                      # remover exige justificativa
        r = self.client.post("/api/moderacao/", {"denuncia": d.id, "tipo": "remover", "justificativa": "Golpe"})
        self.assertEqual(r.status_code, 201, r.data)
        a.refresh_from_db()
        self.assertEqual(a.estado, "removido")


def imagem(nome="f.png"):
    buf = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buf, "PNG")
    return SimpleUploadedFile(nome, buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class FotoTests(APITestCase):
    def setUp(self):
        self.ana, self.beto = novo("ana", 10000001), novo("beto", 10000002)
        self.a = Anuncio.objects.create(dono=self.ana, titulo="x", descricao="x", modalidade="troca",
                                        quantidade=1, ponto_encontro="Biênio")
        self.url = f"/api/anuncios/{self.a.id}/fotos/"

    def test_upload_limite_permissao_e_remocao(self):
        self.client.force_authenticate(self.beto)
        self.assertEqual(self.client.post(self.url, {"arquivo": imagem()}, format="multipart").status_code, 403)
        self.client.force_authenticate(self.ana)
        for i in range(3):
            r = self.client.post(self.url, {"arquivo": imagem(f"{i}.png")}, format="multipart")
            self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.client.post(self.url, {"arquivo": imagem()}, format="multipart").status_code, 400)
        foto = self.a.fotos.first()
        self.assertEqual(self.client.delete(f"{self.url}{foto.id}/").status_code, 204)
        self.assertEqual(self.client.post(self.url, {"arquivo": imagem()}, format="multipart").status_code, 201)

    def test_arquivo_que_nao_e_imagem_e_recusado(self):
        self.client.force_authenticate(self.ana)
        falso = SimpleUploadedFile("x.png", b"isto nao e uma imagem", content_type="image/png")
        self.assertEqual(self.client.post(self.url, {"arquivo": falso}, format="multipart").status_code, 400)


class CadastroSenhaTests(APITestCase):
    def test_cadastro_so_vale_depois_do_codigo(self):
        dados = {"nome_completo": "Dani", "email": "dani@usp.br", "nusp": 12345678, "password": "senha1234"}
        r = self.client.post("/api/auth/registro/", dados)
        self.assertEqual(r.status_code, 201)
        self.assertNotIn("token", r.data)
        login = {"email": "dani@usp.br", "password": "senha1234"}
        self.assertEqual(self.client.post("/api/auth/login/", login).status_code, 400)   # ainda não confirmou
        user = Usuario.objects.get(email="dani@usp.br")
        errado = "000000" if user.codigo_verificacao != "000000" else "111111"
        r = self.client.post("/api/auth/verificar/", {"email": "dani@usp.br", "codigo": errado})
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/auth/verificar/", {"email": "dani@usp.br", "codigo": user.codigo_verificacao})
        self.assertEqual(r.status_code, 200, r.data)
        self.assertIn("token", r.data)
        self.assertEqual(self.client.post("/api/auth/login/", login).status_code, 200)

    def test_codigo_expirado_e_recusado(self):
        u = Usuario.objects.create_user(username="x@usp.br", email="x@usp.br", password="senha1234",
                                        nome_completo="X", nusp=12345679, email_verificado=False)
        codigo = u.gerar_codigo()
        u.codigo_expira_em = u.codigo_expira_em.replace(year=2020)
        u.save(update_fields=["codigo_expira_em"])
        r = self.client.post("/api/auth/verificar/", {"email": "x@usp.br", "codigo": codigo})
        self.assertEqual(r.status_code, 400)

    def test_alterar_senha(self):
        u = novo("eva", 10000009)
        self.client.force_authenticate(u)
        r = self.client.post("/api/auth/senha/", {"senha_atual": "errada123", "nova_senha": "nova12345", "confirmacao": "nova12345"})
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/auth/senha/", {"senha_atual": "senha1234", "nova_senha": "nova12345", "confirmacao": "nova12345"})
        self.assertEqual(r.status_code, 200, r.data)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post("/api/auth/login/", {"email": "eva@usp.br", "password": "nova12345"}).status_code, 200)
