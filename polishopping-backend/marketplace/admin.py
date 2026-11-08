from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AcaoModeracao, Anuncio, Avaliacao, Categoria, Denuncia, FotoAnuncio, Proposta, Usuario


class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("PoliShopping", {"fields": ("nome_completo", "nusp", "is_moderador", "email_verificado")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("PoliShopping", {"fields": ("email", "nome_completo", "nusp", "is_moderador")}),
    )
    list_display = ("username", "nome_completo", "email", "nusp", "is_moderador", "is_active")


admin.site.register(Usuario, UsuarioAdmin)
for modelo in (Categoria, Anuncio, FotoAnuncio, Proposta, Avaliacao, Denuncia, AcaoModeracao):
    admin.site.register(modelo)
