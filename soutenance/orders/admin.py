from django.contrib import admin

from .models import Commande, LigneCommande, OffreVente, SuiviStatut


admin.site.register(OffreVente)
admin.site.register(Commande)
admin.site.register(LigneCommande)
admin.site.register(SuiviStatut)
