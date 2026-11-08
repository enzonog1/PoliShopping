import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.utils import timezone


def validar_email_usp(valor):
    if not valor.lower().endswith("@usp.br"):
        raise ValidationError("O cadastro é restrito a e-mails institucionais da USP (@usp.br)")


class Usuario(AbstractUser):
    """Herda do Django: senha com hash, is_active (conta suspensa = False), login e sessão."""
    nome_completo = models.CharField(max_length=150)
    email = models.EmailField(max_length=100, unique=True, validators=[validar_email_usp])
    nusp = models.PositiveIntegerField(
        unique=True, validators=[MinValueValidator(10_000_000), MaxValueValidator(99_999_999)]
    )
    is_moderador = models.BooleanField(default=False)
    # Confirmação do e-mail USP (CAD001). False só entre o cadastro e a digitação do código.
    email_verificado = models.BooleanField(default=True)
    codigo_verificacao = models.CharField(max_length=6, blank=True)
    codigo_expira_em = models.DateTimeField(null=True, blank=True)

    REQUIRED_FIELDS = ["email", "nome_completo", "nusp"]  # usados pelo createsuperuser

    def gerar_codigo(self):
        self.codigo_verificacao = f"{secrets.randbelow(10**6):06d}"
        self.codigo_expira_em = timezone.now() + timedelta(minutes=15)
        self.save(update_fields=["codigo_verificacao", "codigo_expira_em"])
        return self.codigo_verificacao

    def codigo_valido(self, codigo):
        return bool(self.codigo_verificacao and self.codigo_expira_em and timezone.now() <= self.codigo_expira_em
                    and secrets.compare_digest(self.codigo_verificacao, codigo))

    @property
    def reputacao_media(self):
        """Valor calculado (3FN): média das notas recebidas, sem coluna própria."""
        return self.avaliacoes_recebidas.aggregate(m=Avg("nota"))["m"]

    def __str__(self):
        return self.nome_completo or self.username


class Categoria(models.Model):
    nome = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.nome


class Anuncio(models.Model):
    class Modalidade(models.TextChoices):
        VENDA = "venda", "Venda"
        EMPRESTIMO = "emprestimo", "Empréstimo/Aluguel"
        TROCA = "troca", "Troca"
        GERAL = "geral", "Anúncio geral"

    class Estado(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        EM_NEGOCIACAO = "em_negociacao", "Em negociação"
        CONCLUIDO = "concluido", "Concluído"
        INATIVO = "inativo", "Inativo"
        PENDENTE = "pendente_moderacao", "Pendente de moderação"
        REMOVIDO = "removido", "Bloqueado/Removido"

    dono = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="anuncios")
    titulo = models.CharField(max_length=150)
    descricao = models.TextField(max_length=1000)
    modalidade = models.CharField(max_length=12, choices=Modalidade.choices)
    preco = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # nulo em troca e geral
    quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    ponto_encontro = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ATIVO)
    # O Django cria sozinho a tabela anuncio_categoria (N:N com chave composta).
    categorias = models.ManyToManyField(Categoria, related_name="anuncios")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class FotoAnuncio(models.Model):
    anuncio = models.ForeignKey(Anuncio, on_delete=models.CASCADE, related_name="fotos")
    arquivo = models.ImageField(upload_to="anuncios/")

    def clean(self):
        if self._state.adding and self.anuncio.fotos.count() >= 3:
            raise ValidationError("Cada anúncio aceita no máximo 3 fotos.")


class Proposta(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente de resposta"
        ACEITA = "aceita", "Aceita"
        RECUSADA = "recusada", "Recusada"
        CONCLUIDA = "concluida", "Concluída"

    anuncio = models.ForeignKey(Anuncio, on_delete=models.CASCADE, related_name="propostas")
    interessado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="propostas")
    mensagem = models.TextField(max_length=500, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    justificativa_recusa = models.CharField(max_length=300, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)


class Avaliacao(models.Model):
    proposta = models.ForeignKey(Proposta, on_delete=models.CASCADE, related_name="avaliacoes")
    avaliador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="avaliacoes_feitas")
    avaliado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="avaliacoes_recebidas")
    nota = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.CharField(max_length=300, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["proposta", "avaliador"], name="uma_avaliacao_por_parte")]


class Denuncia(models.Model):
    class Motivo(models.TextChoices):
        IMPROPRIO = "improprio", "Conteúdo impróprio"
        GOLPE = "golpe", "Preço abusivo/golpe"
        PROIBIDO = "proibido", "Item proibido"
        OUTROS = "outros", "Outros"

    class Status(models.TextChoices):
        ABERTA = "aberta", "Aberta"
        PROCEDENTE = "procedente", "Procedente"
        IMPROCEDENTE = "improcedente", "Improcedente"

    anuncio = models.ForeignKey(Anuncio, on_delete=models.CASCADE, related_name="denuncias")
    denunciante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="denuncias_feitas")
    motivo = models.CharField(max_length=12, choices=Motivo.choices)
    detalhamento = models.TextField(max_length=500)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ABERTA)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["anuncio", "denunciante"], name="uma_denuncia_por_usuario")]


class AcaoModeracao(models.Model):
    """Log de auditoria. O anúncio e o dono dele saem da denúncia, então não há FK redundante."""
    class Tipo(models.TextChoices):
        REJEITAR = "rejeitar", "Rejeitar denúncia (anúncio segue ativo)"
        ADVERTIR = "advertir", "Advertir anunciante"
        REMOVER = "remover", "Remover anúncio"
        SUSPENDER = "suspender", "Suspender usuário"

    denuncia = models.ForeignKey(Denuncia, on_delete=models.CASCADE, related_name="acoes")
    moderador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="acoes_moderacao")
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    justificativa = models.CharField(max_length=300, blank=True)  # obrigatória ao remover (validar no form)
    criado_em = models.DateTimeField(auto_now_add=True)
