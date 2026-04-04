from django.db import models


class Unite(models.Model):
    libelle = models.CharField(max_length=50, unique=True)
    symbole = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.libelle


class Produit(models.Model):
    nom = models.CharField(max_length=100)
    variete = models.CharField(max_length=100, blank=True)
    categorie = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    unite = models.ForeignKey(Unite, on_delete=models.PROTECT, related_name="produits")
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.nom


class Marche(models.Model):
    nom = models.CharField(max_length=120)
    quartier = models.CharField(max_length=120, blank=True)
    commune = models.CharField(max_length=120, blank=True)
    region = models.CharField(max_length=120)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} ({self.region})"
