from rest_framework import serializers

from core.models import Marche, Produit
from core.serializers import MarcheSerializer, ProduitSerializer

from .models import Prevision, RelevePrix, ValidationReleve


class RelevePrixSerializer(serializers.ModelSerializer):
    produit = ProduitSerializer(read_only=True)
    marche = MarcheSerializer(read_only=True)
    produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.filter(actif=True),
        source="produit",
        write_only=True,
    )
    marche_id = serializers.PrimaryKeyRelatedField(
        queryset=Marche.objects.filter(actif=True),
        source="marche",
        write_only=True,
    )
    collecteur = serializers.StringRelatedField(read_only=True)
    statut = serializers.CharField(read_only=True)

    class Meta:
        model = RelevePrix
        fields = [
            "id",
            "produit",
            "marche",
            "produit_id",
            "marche_id",
            "collecteur",
            "prix",
            "date_releve",
            "commentaire",
            "source",
            "statut",
            "created_at",
        ]
        read_only_fields = ["id", "collecteur", "statut", "created_at"]

    def validate_prix(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit etre strictement positif.")
        return value

    def validate(self, attrs):
        produit = attrs.get("produit") or getattr(self.instance, "produit", None)
        marche = attrs.get("marche") or getattr(self.instance, "marche", None)
        date_releve = attrs.get("date_releve") or getattr(self.instance, "date_releve", None)
        request = self.context.get("request")
        collecteur = (
            getattr(self.instance, "collecteur", None)
            or (request.user if request and request.user.is_authenticated else None)
        )
        if produit and marche and date_releve and collecteur:
            qs = RelevePrix.objects.filter(
                collecteur=collecteur,
                produit=produit,
                marche=marche,
                date_jour=date_releve.date(),
                statut__in=RelevePrix.STATUTS_ACTIFS,
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Un releve actif existe deja pour ce produit sur ce marche aujourd'hui."
                )
        return attrs


class ValidationReleveSerializer(serializers.ModelSerializer):
    admin = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ValidationReleve
        fields = ["id", "releve", "admin", "decision", "motif", "date_validation"]
        read_only_fields = ["id", "admin", "date_validation"]


class PrevisionSerializer(serializers.ModelSerializer):
    produit = ProduitSerializer(read_only=True)
    marche = MarcheSerializer(read_only=True)

    class Meta:
        model = Prevision
        fields = [
            "id",
            "produit",
            "marche",
            "date_prevision",
            "prix_predit",
            "intervalle_bas",
            "intervalle_haut",
            "modele",
            "mae",
            "rmse",
            "created_at",
        ]
