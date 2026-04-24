from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path


def tv_selecao_view(request):
    return render(request, "tv.html")


urlpatterns = [
    path("tv/", tv_selecao_view, name="tv_selecao"),
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("administrador/", include("administrador.urls")),
    path("recepcionista/", include("recepcionista.urls")),
    path("guiche/", include("guiche.urls")),
    path(
        "profissional_saude/",
        include("profissional_saude.urls", namespace="profissional_saude"),
    ),
]

admin.site.site_header = "SGA - Admin"
admin.site.site_title = "SGA - Admin Portal"
admin.site.index_title = "Bem-vindo ao portal SGA"
