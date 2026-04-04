from django.conf import settings
from django.db import models


class Alerte(models.Model):
    class Canal(models.TextChoices):
        APP = "APP", "Application"
        SMS = "SMS", "SMS"
        WHATSAPP = "WHATSAPP", "WhatsApp"

    commercant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alertes",
    )
    produit = models.ForeignKey("core.Produit", on_delete=models.CASCADE, related_name="alertes")
    marche = models.ForeignKey("core.Marche", on_delete=models.CASCADE, related_name="alertes")
    seuil_haut = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    seuil_bas = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    canal = models.CharField(max_length=20, choices=Canal.choices, default=Canal.APP)
    frequence = models.CharField(max_length=30, default="QUOTIDIEN")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class HistoriqueAlerte(models.Model):
    class TypeDeclenchement(models.TextChoices):
        SEUIL_HAUT = "SEUIL_HAUT", "Seuil haut"
        SEUIL_BAS = "SEUIL_BAS", "Seuil bas"

    alerte = models.ForeignKey(Alerte, on_delete=models.CASCADE, related_name="historique")
    prix_au_moment = models.DecimalField(max_digits=12, decimal_places=2)
    type_declenchement = models.CharField(max_length=20, choices=TypeDeclenchement.choices)
    date_declenchement = models.DateTimeField(auto_now_add=True)
    action_utilisateur = models.CharField(max_length=120, blank=True)
    date_action = models.DateTimeField(null=True, blank=True)
