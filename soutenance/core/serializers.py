from rest_framework import serializers

from .models import Marche, Produit, Unite


class UniteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unite
        fields = ["id", "libelle", "symbole"]


class ProduitSerializer(serializers.ModelSerializer):
    unite = UniteSerializer(read_only=True)
    unite_id = serializers.PrimaryKeyRelatedField(
        queryset=Unite.objects.all(), source="unite", write_only=True
    )

    class Meta:
        model = Produit
        fields = [
            "id",
            "nom",
            "variete",
            "categorie",
            "description",
            "unite",
            "unite_id",
            "actif",
        ]


class MarcheSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marche
        fields = [
            "id",
            "nom",
            "quartier",
            "commune",
            "region",
            "latitude",
            "longitude",
            "actif",
        ]
