import re

from rest_framework import serializers

from .models import AcaoModeracao, Anuncio, Avaliacao, Categoria, Denuncia, FotoAnuncio, Proposta, Usuario


def validar_senha_forte(valor):
    if not (re.search(r"[A-Za-z]", valor) and re.search(r"\d", valor)):
        raise serializers.ValidationError("A senha deve ter letras e números.")
    return valor


class UsuarioSerializer(serializers.ModelSerializer):
    """Dados completos: só o próprio usuário vê (rota /auth/eu/)."""
    reputacao_media = serializers.FloatField(read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "nome_completo", "email", "nusp", "is_moderador", "reputacao_media"]
        read_only_fields = fields


class UsuarioPublicoSerializer(serializers.ModelSerializer):
    """O que os outros usuários podem ver (sem e-mail nem NUSP)."""
    reputacao_media = serializers.FloatField(read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "nome_completo", "reputacao_media"]
        read_only_fields = fields


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ["nome_completo", "email", "nusp", "password"]

    def validate_password(self, valor):
        return validar_senha_forte(valor)

    def create(self, dados):
        return Usuario.objects.create_user(
            username=dados["email"], email=dados["email"], password=dados["password"],
            nome_completo=dados["nome_completo"], nusp=dados["nusp"], email_verificado=False,
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, dados):
        user = Usuario.objects.filter(email__iexact=dados["email"]).first()
        if not user or not user.check_password(dados["password"]):
            raise serializers.ValidationError("E-mail ou senha incorretos")
        if not user.email_verificado:
            raise serializers.ValidationError("Confirme seu e-mail USP com o código enviado antes de entrar.")
        if not user.is_active:
            raise serializers.ValidationError("Sua conta foi suspensa temporariamente por infração às regras da comunidade")
        dados["user"] = user
        return dados


class VerificarSerializer(serializers.Serializer):
    email = serializers.EmailField()
    codigo = serializers.RegexField(r"^[0-9]{6}$")


class ReenviarSerializer(serializers.Serializer):
    email = serializers.EmailField()


class AlterarSenhaSerializer(serializers.Serializer):
    senha_atual = serializers.CharField()
    nova_senha = serializers.CharField(min_length=8, validators=[validar_senha_forte])
    confirmacao = serializers.CharField()

    def validate(self, dados):
        if dados["nova_senha"] != dados["confirmacao"]:
            raise serializers.ValidationError("A confirmação de senha não confere.")
        return dados


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nome"]


class FotoAnuncioSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoAnuncio
        fields = ["id", "arquivo"]


class AnuncioSerializer(serializers.ModelSerializer):
    dono = UsuarioPublicoSerializer(read_only=True)
    fotos = FotoAnuncioSerializer(many=True, read_only=True)
    categorias = serializers.PrimaryKeyRelatedField(many=True, queryset=Categoria.objects.all(), allow_empty=False)

    class Meta:
        model = Anuncio
        fields = ["id", "dono", "titulo", "descricao", "modalidade", "preco", "quantidade",
                  "ponto_encontro", "estado", "categorias", "fotos", "criado_em"]
        read_only_fields = ["estado"]

    def validate(self, dados):
        modalidade = dados.get("modalidade", getattr(self.instance, "modalidade", None))
        if modalidade in (Anuncio.Modalidade.TROCA, Anuncio.Modalidade.GERAL):
            dados["preco"] = None
        elif dados.get("preco", getattr(self.instance, "preco", None)) is None:
            raise serializers.ValidationError({"preco": "Obrigatório para venda e empréstimo (pode ser 0,00)."})
        return dados


class PropostaSerializer(serializers.ModelSerializer):
    interessado = UsuarioPublicoSerializer(read_only=True)
    anuncio_titulo = serializers.CharField(source="anuncio.titulo", read_only=True)
    contato = serializers.SerializerMethodField()

    class Meta:
        model = Proposta
        fields = ["id", "anuncio", "anuncio_titulo", "interessado", "mensagem", "status",
                  "justificativa_recusa", "contato", "criado_em"]
        read_only_fields = ["status", "justificativa_recusa"]

    def get_contato(self, p):
        """Depois do aceite, cada parte vê o e-mail da outra para combinar o encontro."""
        if p.status not in (Proposta.Status.ACEITA, Proposta.Status.CONCLUIDA):
            return None
        eu = self.context["request"].user
        return p.interessado.email if eu.id == p.anuncio.dono_id else p.anuncio.dono.email

    def validate_anuncio(self, anuncio):
        if anuncio.dono_id == self.context["request"].user.id:
            raise serializers.ValidationError("Você não pode negociar um item anunciado por você mesmo")
        if anuncio.estado != Anuncio.Estado.ATIVO:
            raise serializers.ValidationError("Este anúncio não está disponível para negociação.")
        return anuncio


class AvaliacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avaliacao
        fields = ["id", "nota", "comentario", "criado_em"]


class DenunciaSerializer(serializers.ModelSerializer):
    anuncio_titulo = serializers.CharField(source="anuncio.titulo", read_only=True)

    class Meta:
        model = Denuncia
        fields = ["id", "anuncio", "anuncio_titulo", "motivo", "detalhamento", "status", "criado_em"]
        read_only_fields = ["status"]

    def validate_anuncio(self, anuncio):
        if Denuncia.objects.filter(anuncio=anuncio, denunciante=self.context["request"].user).exists():
            raise serializers.ValidationError("Você já denunciou este anúncio.")
        return anuncio


class AcaoModeracaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcaoModeracao
        fields = ["id", "denuncia", "tipo", "justificativa", "moderador", "criado_em"]
        read_only_fields = ["moderador"]

    def validate(self, dados):
        if dados["denuncia"].status != Denuncia.Status.ABERTA:
            raise serializers.ValidationError("Esta denúncia já foi analisada.")
        if dados["tipo"] == AcaoModeracao.Tipo.REMOVER and not dados.get("justificativa"):
            raise serializers.ValidationError({"justificativa": "Obrigatória ao remover um anúncio."})
        return dados
