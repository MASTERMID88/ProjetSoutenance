from django.conf import settings
from django.db import models
from django.db.models import Q


class RelevePrix(models.Model):
    class Statut(models.TextChoices):
        BROUILLON = "BROUILLON", "Brouillon"
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        VALIDE = "VALIDE", "Valide"
        REJETE = "REJETE", "Rejete"

    STATUTS_ACTIFS = [Statut.BROUILLON, Statut.EN_ATTENTE, Statut.VALIDE]

    produit = models.ForeignKey("core.Produit", on_delete=models.PROTECT, related_name="releves")
    marche = models.ForeignKey("core.Marche", on_delete=models.PROTECT, related_name="releves")
    collecteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="releves_saisis",
    )
    prix = models.DecimalField(max_digits=12, decimal_places=2)
    date_releve = models.DateTimeField()
    date_jour = models.DateField(
        editable=False,
        help_text="Jour du releve - renseigne automatiquement depuis date_releve.",
    )
    commentaire = models.TextField(blank=True)
    source = models.CharField(max_length=120, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["collecteur", "produit", "marche", "date_jour"],
                condition=Q(statut__in=["BROUILLON", "EN_ATTENTE", "VALIDE"]),
                name="uniq_releve_actif_par_jour",
            )
        ]
        indexes = [
            models.Index(fields=["produit", "marche", "-date_releve"]),
            models.Index(fields=["statut"]),
        ]

    def save(self, *args, **kwargs):
        if self.date_releve:
            self.date_jour = self.date_releve.date()
        super().save(*args, **kwargs)


class ValidationReleve(models.Model):
    class Decision(models.TextChoices):
        VALIDE = "VALIDE", "Valide"
        REJETE = "REJETE", "Rejete"

    releve = models.ForeignKey(RelevePrix, on_delete=models.CASCADE, related_name="validations")
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="validations_effectuees",
    )
    decision = models.CharField(max_length=10, choices=Decision.choices)
    motif = models.TextField(blank=True)
    date_validation = models.DateTimeField(auto_now_add=True)


class Prevision(models.Model):
    produit = models.ForeignKey("core.Produit", on_delete=models.CASCADE, related_name="previsions")
    marche = models.ForeignKey("core.Marche", on_delete=models.CASCADE, related_name="previsions")
    date_prevision = models.DateTimeField()
    prix_predit = models.DecimalField(max_digits=12, decimal_places=2)
    intervalle_bas = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    intervalle_haut = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    modele = models.CharField(max_length=100, blank=True)
    mae = models.FloatField(null=True, blank=True)
    rmse = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
