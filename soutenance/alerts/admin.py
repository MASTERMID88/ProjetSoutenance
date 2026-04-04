from django.contrib import admin

from .models import Alerte, HistoriqueAlerte


admin.site.register(Alerte)
admin.site.register(HistoriqueAlerte)
