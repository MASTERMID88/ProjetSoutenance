from django.contrib import admin

from .models import Marche, Produit, Unite


admin.site.register(Unite)
admin.site.register(Produit)
admin.site.register(Marche)
