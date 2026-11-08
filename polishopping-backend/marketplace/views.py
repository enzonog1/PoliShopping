from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import mixins, permissions, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import AcaoModeracao, Anuncio, Categoria, Denuncia, Proposta
from .serializers import (AcaoModeracaoSerializer, AnuncioSerializer, AvaliacaoSerializer, CategoriaSerializer,
                          DenunciaSerializer, FotoAnuncioSerializer, LoginSerializer, PropostaSerializer, RegistroSerializer,
                          UsuarioSerializer, AlterarSenhaSerializer, ReenviarSerializer, VerificarSerializer)


class IsModerador(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_moderador)


class IsDonoOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.dono_id == request.user.id


def avisar(destino, assunto, texto):
    send_mail(assunto, texto, "nao-responda@polishopping.local", [destino], fail_silently=True)


def enviar_codigo(user):
    codigo = user.gerar_codigo()
    avisar(user.email, "Seu código de verificação do PoliShopping", f"Seu código é {codigo}. Ele vale por 15 minutos.")


# ---------- Autenticação (AUT001) ----------
class RegistroView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = RegistroSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        enviar_codigo(user)
        return Response({"detail": "Enviamos um código de 6 dígitos para o seu e-mail USP.", "email": user.email}, status=201)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "usuario": UsuarioSerializer(user).data})


class EuView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class VerificarView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verificacao"

    def post(self, request):
        s = VerificarSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = get_user_model().objects.filter(email__iexact=s.validated_data["email"], email_verificado=False).first()
        if not user or not user.codigo_valido(s.validated_data["codigo"]):
            return Response({"detail": "Código inválido ou expirado."}, status=400)
        user.email_verificado, user.codigo_verificacao, user.codigo_expira_em = True, "", None
        user.save(update_fields=["email_verificado", "codigo_verificacao", "codigo_expira_em"])
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "usuario": UsuarioSerializer(user).data})


class ReenviarCodigoView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verificacao"

    def post(self, request):
        s = ReenviarSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = get_user_model().objects.filter(email__iexact=s.validated_data["email"], email_verificado=False).first()
        if user:
            enviar_codigo(user)
        return Response({"detail": "Se o e-mail estiver aguardando confirmação, enviamos um novo código."})


class AlterarSenhaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = AlterarSenhaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        u = request.user
        if not u.check_password(s.validated_data["senha_atual"]):
            return Response({"detail": "A senha atual está incorreta."}, status=400)
        u.set_password(s.validated_data["nova_senha"])
        u.save(update_fields=["password"])
        Token.objects.filter(user=u).delete()          # o token antigo deixa de valer
        token = Token.objects.create(user=u)
        return Response({"token": token.key, "detail": "Senha atualizada."})


# ---------- Anúncios (PRO001, PRO002, PRO003) ----------
class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categoria.objects.order_by("nome")
    serializer_class = CategoriaSerializer
    pagination_class = None


class AnuncioViewSet(viewsets.ModelViewSet):
    serializer_class = AnuncioSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsDonoOrReadOnly]

    def get_queryset(self):
        qs = Anuncio.objects.select_related("dono").prefetch_related("categorias", "fotos").order_by("-criado_em")
        u, p = self.request.user, self.request.query_params
        if u.is_authenticated and p.get("meus") and self.action == "list":
            qs = qs.filter(dono=u)                      # "Meus anúncios": todos os estados
        elif not (u.is_authenticated and u.is_moderador):
            visivel = Q(estado=Anuncio.Estado.ATIVO)    # público só vê anúncios ativos
            if u.is_authenticated and self.action != "list":
                visivel |= Q(dono=u)                    # dono acessa os próprios em qualquer estado
            qs = qs.filter(visivel)
        if self.action == "list":
            if p.get("q"):
                qs = qs.filter(Q(titulo__icontains=p["q"]) | Q(descricao__icontains=p["q"]))
            if p.getlist("categoria"):
                qs = qs.filter(categorias__in=p.getlist("categoria")).distinct()
            if p.get("modalidade"):
                qs = qs.filter(modalidade=p["modalidade"])
            if p.get("preco_min"):
                qs = qs.filter(preco__gte=p["preco_min"])
            if p.get("preco_max"):
                qs = qs.filter(preco__lte=p["preco_max"])
        return qs

    def perform_create(self, serializer):
        serializer.save(dono=self.request.user)

    @action(detail=True, methods=["post"])
    def pausar(self, request, pk=None):
        """Alterna entre ativo e inativo (só o dono; ver IsDonoOrReadOnly)."""
        a = self.get_object()
        if a.estado == Anuncio.Estado.ATIVO:
            a.estado = Anuncio.Estado.INATIVO
        elif a.estado == Anuncio.Estado.INATIVO:
            a.estado = Anuncio.Estado.ATIVO
        else:
            return Response({"detail": "Só anúncios ativos ou pausados podem ser alterados."}, status=400)
        a.save(update_fields=["estado"])
        return Response(self.get_serializer(a).data)

    @action(detail=True, methods=["post"], url_path="fotos")
    def fotos(self, request, pk=None):
        """Envia uma foto (multipart, campo "arquivo"). Só o dono; até 3 fotos de 5 MB."""
        a = self.get_object()
        arquivo = request.FILES.get("arquivo")
        if arquivo is None:
            return Response({"detail": "Envie a imagem no campo arquivo."}, status=400)
        if arquivo.size > 5 * 1024 * 1024:
            return Response({"detail": "Cada foto pode ter no máximo 5 MB."}, status=400)
        if a.fotos.count() >= 3:
            return Response({"detail": "Cada anúncio aceita no máximo 3 fotos."}, status=400)
        s = FotoAnuncioSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)   # confere que o arquivo é mesmo uma imagem
        s.save(anuncio=a)
        return Response(s.data, status=201)

    @action(detail=True, methods=["delete"], url_path=r"fotos/(?P<foto_id>\d+)")
    def remover_foto(self, request, pk=None, foto_id=None):
        a = self.get_object()
        foto = get_object_or_404(a.fotos, pk=foto_id)
        foto.arquivo.delete(save=False)
        foto.delete()
        return Response(status=204)


# ---------- Negociação e avaliação (NEG001, NEG002, AVAL001) ----------
class PropostaViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = PropostaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u, p = self.request.user, self.request.query_params
        qs = Proposta.objects.select_related("anuncio", "interessado").order_by("-criado_em")
        if p.get("recebidas"):
            return qs.filter(anuncio__dono=u)
        if p.get("enviadas"):
            return qs.filter(interessado=u)
        return qs.filter(Q(interessado=u) | Q(anuncio__dono=u))

    def perform_create(self, serializer):
        proposta = serializer.save(interessado=self.request.user)
        avisar(proposta.anuncio.dono.email, "Nova proposta no PoliShopping",
               f"{self.request.user.nome_completo} tem interesse em: {proposta.anuncio.titulo}")

    def _responder(self, request, pk):
        p = self.get_object()
        if p.anuncio.dono_id != request.user.id:
            return None, Response({"detail": "Apenas o anunciante pode responder."}, status=403)
        if p.status != Proposta.Status.PENDENTE:
            return None, Response({"detail": "Esta proposta já foi respondida."}, status=400)
        return p, None

    @action(detail=True, methods=["post"])
    def aceitar(self, request, pk=None):
        p, erro = self._responder(request, pk)
        if erro:
            return erro
        with transaction.atomic():
            p.status = Proposta.Status.ACEITA
            p.save(update_fields=["status"])
            p.anuncio.estado = Anuncio.Estado.EM_NEGOCIACAO
            p.anuncio.save(update_fields=["estado"])
        avisar(p.interessado.email, "Sua proposta foi aceita",
               f"Combine o encontro na Poli ({p.anuncio.ponto_encontro}) com {request.user.email}.")
        return Response({"proposta": self.get_serializer(p).data, "contato": p.interessado.email})

    @action(detail=True, methods=["post"])
    def recusar(self, request, pk=None):
        p, erro = self._responder(request, pk)
        if erro:
            return erro
        p.status = Proposta.Status.RECUSADA
        p.justificativa_recusa = request.data.get("justificativa", "")[:300]
        p.save(update_fields=["status", "justificativa_recusa"])
        avisar(p.interessado.email, "Sua proposta foi recusada", p.justificativa_recusa or "Sem justificativa.")
        return Response(self.get_serializer(p).data)

    @action(detail=True, methods=["post"])
    def avaliar(self, request, pk=None):
        p = self.get_object()
        u = request.user
        if p.status not in (Proposta.Status.ACEITA, Proposta.Status.CONCLUIDA):
            return Response({"detail": "Só é possível avaliar negociações aceitas."}, status=400)
        avaliado = p.interessado if u.id == p.anuncio.dono_id else p.anuncio.dono
        s = AvaliacaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                s.save(proposta=p, avaliador=u, avaliado=avaliado)
                p.status = Proposta.Status.CONCLUIDA
                p.save(update_fields=["status"])
                p.anuncio.estado = Anuncio.Estado.CONCLUIDO
                p.anuncio.save(update_fields=["estado"])
        except IntegrityError:
            return Response({"detail": "Você já avaliou esta transação."}, status=400)
        return Response(s.data, status=201)


# ---------- Denúncia e moderação (DEN001, MOD001) ----------
class DenunciaViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = DenunciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        qs = Denuncia.objects.select_related("anuncio").order_by("-criado_em")
        if u.is_moderador:
            return qs.filter(status=self.request.query_params["status"]) if "status" in self.request.query_params else qs
        return qs.filter(denunciante=u)

    def perform_create(self, serializer):
        d = serializer.save(denunciante=self.request.user)
        a = d.anuncio
        if a.denuncias.count() >= 3 and a.estado == Anuncio.Estado.ATIVO:
            a.estado = Anuncio.Estado.PENDENTE   # 3 denúncias distintas: oculta até a decisão
            a.save(update_fields=["estado"])


class AcaoModeracaoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = AcaoModeracao.objects.select_related("denuncia", "moderador").order_by("-criado_em")
    serializer_class = AcaoModeracaoSerializer
    permission_classes = [IsModerador]

    @transaction.atomic
    def perform_create(self, serializer):
        acao = serializer.save(moderador=self.request.user)
        d, a = acao.denuncia, acao.denuncia.anuncio
        T = AcaoModeracao.Tipo
        d.status = Denuncia.Status.IMPROCEDENTE if acao.tipo == T.REJEITAR else Denuncia.Status.PROCEDENTE
        if acao.tipo in (T.REJEITAR, T.ADVERTIR) and a.estado == Anuncio.Estado.PENDENTE:
            a.estado = Anuncio.Estado.ATIVO
        elif acao.tipo == T.REMOVER:
            a.estado = Anuncio.Estado.REMOVIDO
            avisar(a.dono.email, "Seu anúncio foi removido", acao.justificativa)
        elif acao.tipo == T.SUSPENDER:
            a.dono.is_active = False
            a.dono.save(update_fields=["is_active"])
        d.save(update_fields=["status"])
        a.save(update_fields=["estado"])


# ---------- Dashboard multidimensional (DASH001) ----------
class DashboardView(APIView):
    permission_classes = [IsModerador]

    def get(self, request):
        p = request.query_params
        anuncios = Anuncio.objects.all()
        if parse_date(p.get("inicio", "")):
            anuncios = anuncios.filter(criado_em__date__gte=parse_date(p["inicio"]))
        if parse_date(p.get("fim", "")):
            anuncios = anuncios.filter(criado_em__date__lte=parse_date(p["fim"]))
        if p.get("categoria"):
            anuncios = anuncios.filter(categorias=p["categoria"])
        concluidas = Proposta.objects.filter(status=Proposta.Status.CONCLUIDA, anuncio__in=anuncios)
        return Response({
            "anuncios_por_categoria": list(anuncios.values("categorias__nome").annotate(
                total=Count("id", distinct=True)).order_by("-total")),
            "anuncios_por_modalidade": list(anuncios.values("modalidade").annotate(total=Count("id")).order_by("-total")),
            "matriz_categoria_modalidade": list(anuncios.values("categorias__nome", "modalidade").annotate(
                total=Count("id", distinct=True))),
            "negociacoes_concluidas_por_mes": list(concluidas.annotate(mes=TruncMonth("criado_em")).values(
                "mes").annotate(total=Count("id")).order_by("mes")),
            "valor_total_vendas": concluidas.filter(anuncio__modalidade=Anuncio.Modalidade.VENDA).aggregate(
                t=Sum("anuncio__preco"))["t"] or 0,
            "usuarios_ativos": get_user_model().objects.filter(is_active=True).count(),
            "denuncias_atendidas": Denuncia.objects.exclude(status=Denuncia.Status.ABERTA).count(),
            "denuncias_abertas": Denuncia.objects.filter(status=Denuncia.Status.ABERTA).count(),
        })

