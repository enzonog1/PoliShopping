from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("categorias", views.CategoriaViewSet, basename="categoria")
router.register("anuncios", views.AnuncioViewSet, basename="anuncio")
router.register("propostas", views.PropostaViewSet, basename="proposta")
router.register("denuncias", views.DenunciaViewSet, basename="denuncia")
router.register("moderacao", views.AcaoModeracaoViewSet, basename="moderacao")

urlpatterns = [
    path("auth/registro/", views.RegistroView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/eu/", views.EuView.as_view()),
    path("auth/verificar/", views.VerificarView.as_view()),
    path("auth/reenviar-codigo/", views.ReenviarCodigoView.as_view()),
    path("auth/senha/", views.AlterarSenhaView.as_view()),
    path("dashboard/", views.DashboardView.as_view()),
] + router.urls
