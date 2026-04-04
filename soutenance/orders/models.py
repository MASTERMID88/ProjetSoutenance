from django.conf import settings
from django.db import models


class OffreVente(models.Model):
    commercant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="offres_publiees",
    )
    produit = models.ForeignKey("core.Produit", on_delete=models.PROTECT, related_name="offres")
    marche = models.ForeignKey("core.Marche", on_delete=models.PROTECT, related_name="offres")
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    quantite_totale = models.FloatField()
    quantite_disponible = models.FloatField()
    date_publication = models.DateTimeField(auto_now_add=True)
    date_limite = models.DateTimeField(null=True, blank=True)
    mode_livraison = models.CharField(max_length=120, blank=True)
    statut = models.CharField(max_length=30, default="ACTIVE")


class Commande(models.Model):
    class ModeReception(models.TextChoices):
        LIVRAISON = "LIVRAISON", "Livraison"
        RETRAIT = "RETRAIT", "Retrait"

    class Statut(models.TextChoices):
        BROUILLON = "BROUILLON", "Brouillon"
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        CONFIRMEE = "CONFIRMEE", "Confirmee"
        EN_COURS = "EN_COURS", "En cours"
        LIVREE = "LIVREE", "Livree"
        ANNULEE = "ANNULEE", "Annulee"

    acheteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="commandes_passees",
    )
    offre = models.ForeignKey(OffreVente, on_delete=models.PROTECT, related_name="commandes")
    date_commande = models.DateTimeField(auto_now_add=True)
    adresse_livraison = models.CharField(max_length=255, blank=True)
    mode_reception = models.CharField(
        max_length=20,
        choices=ModeReception.choices,
        default=ModeReception.LIVRAISON,
    )
    date_expedition = models.DateTimeField(null=True, blank=True)
    date_livraison = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="lignes")
    produit = models.ForeignKey("core.Produit", on_delete=models.PROTECT, related_name="lignes_commande")
    quantite = models.FloatField()
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    montant = models.DecimalField(max_digits=12, decimal_places=2)


class SuiviStatut(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="historique_statuts")
    date_changement = models.DateTimeField(auto_now_add=True)
    ancien_statut = models.CharField(max_length=30, blank=True)
    nouveau_statut = models.CharField(max_length=30)
    raison = models.TextField(blank=True)
    utilisateur_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="modifications_statut",
    )
