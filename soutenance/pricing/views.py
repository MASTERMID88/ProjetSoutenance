import django_filters
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from rest_framework import decorators, mixins, response, status, viewsets
from rest_framework.permissions import AllowAny

from accounts.permissions import IsAdminRole, IsCollecteur

from .models import Prevision, RelevePrix, ValidationReleve
from .serializers import (
    PrevisionSerializer,
    RelevePrixSerializer,
    ValidationReleveSerializer,
)


class RelevePrixFilter(django_filters.FilterSet):
    produit = django_filters.NumberFilter(field_name="produit_id")
    marche = django_filters.NumberFilter(field_name="marche_id")
    region = django_filters.CharFilter(field_name="marche__region", lookup_expr="iexact")
    commune = django_filters.CharFilter(field_name="marche__commune", lookup_expr="iexact")
    date_min = django_filters.DateTimeFilter(field_name="date_releve", lookup_expr="gte")
    date_max = django_filters.DateTimeFilter(field_name="date_releve", lookup_expr="lte")
    statut = django_filters.CharFilter(field_name="statut")

    class Meta:
        model = RelevePrix
        fields = ["produit", "marche", "region", "commune", "statut", "date_min", "date_max"]


class PrixPublicViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Endpoints publics : uniquement les relevés VALIDES."""

    serializer_class = RelevePrixSerializer
    permission_classes = [AllowAny]
    filterset_class = RelevePrixFilter
    search_fields = ["produit__nom", "marche__nom", "marche__region"]
    ordering_fields = ["date_releve", "prix", "created_at"]
    ordering = ["-date_releve"]

    def get_queryset(self):
        return (
            RelevePrix.objects.filter(statut=RelevePrix.Statut.VALIDE)
            .select_related("produit", "produit__unite", "marche", "collecteur")
        )

    @decorators.action(detail=False, methods=["get"], url_path="derniers")
    def derniers(self, request):
        """Dernier prix validé par (produit, marché)."""
        base = self.get_queryset()
        latest = base.filter(
            produit_id=OuterRef("produit_id"),
            marche_id=OuterRef("marche_id"),
        ).order_by("-date_releve")
        qs = base.filter(
            id=Subquery(latest.values("id")[:1])
        ).order_by("produit__nom", "marche__nom")
        qs = self.filter_queryset(qs)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return response.Response(serializer.data)

    @decorators.action(detail=False, methods=["get"], url_path="historique")
    def historique(self, request):
        """Serie temporelle agregee par jour pour graphiques.

        Parametres : produit, marche (optionnel), jours (def. 90).
        Retourne [{date, prix_moyen, prix_min, prix_max, nb}].
        """
        from datetime import timedelta
        from django.db.models import Avg, Count, Max, Min
        from django.utils import timezone

        produit = request.query_params.get("produit")
        marche = request.query_params.get("marche")
        region = request.query_params.get("region")
        commune = request.query_params.get("commune")
        try:
            jours = int(request.query_params.get("jours", 90))
        except ValueError:
            jours = 90
        jours = max(1, min(jours, 365))

        qs = self.get_queryset().filter(
            date_releve__gte=timezone.now() - timedelta(days=jours)
        )
        if produit:
            qs = qs.filter(produit_id=produit)
        if marche:
            qs = qs.filter(marche_id=marche)
        if region:
            qs = qs.filter(marche__region__iexact=region)
        if commune:
            qs = qs.filter(marche__commune__iexact=commune)

        data = (
            qs.values("date_jour")
            .annotate(
                prix_moyen=Avg("prix"),
                prix_min=Min("prix"),
                prix_max=Max("prix"),
                nb=Count("id"),
            )
            .order_by("date_jour")
        )
        return response.Response(list(data))


class RelevePrixViewSet(viewsets.ModelViewSet):
    """CRUD relevés pour les collecteurs (et admins)."""

    serializer_class = RelevePrixSerializer
    permission_classes = [IsCollecteur]
    filterset_class = RelevePrixFilter
    ordering_fields = ["date_releve", "prix", "created_at"]
    ordering = ["-date_releve"]

    def get_queryset(self):
        user = self.request.user
        qs = RelevePrix.objects.select_related(
            "produit", "produit__unite", "marche", "collecteur"
        )
        if getattr(user, "is_superuser", False) or getattr(user, "role", None) == "ADMIN":
            return qs
        return qs.filter(collecteur=user)

    def perform_create(self, serializer):
        serializer.save(
            collecteur=self.request.user,
            statut=RelevePrix.Statut.EN_ATTENTE,
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.statut == RelevePrix.Statut.VALIDE:
            raise PermissionError("Un relevé validé ne peut pas être modifié.")
        serializer.save()

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="valider",
        permission_classes=[IsAdminRole],
    )
    def valider(self, request, pk=None):
        return self._decider(request, decision=ValidationReleve.Decision.VALIDE)

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="rejeter",
        permission_classes=[IsAdminRole],
    )
    def rejeter(self, request, pk=None):
        return self._decider(request, decision=ValidationReleve.Decision.REJETE)

    def _decider(self, request, decision):
        releve = self.get_object()
        motif = request.data.get("motif", "")
        ValidationReleve.objects.create(
            releve=releve,
            admin=request.user,
            decision=decision,
            motif=motif,
        )
        releve.statut = (
            RelevePrix.Statut.VALIDE
            if decision == ValidationReleve.Decision.VALIDE
            else RelevePrix.Statut.REJETE
        )
        releve.save(update_fields=["statut"])
        return response.Response(
            RelevePrixSerializer(releve, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class PrevisionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = PrevisionSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["produit", "marche"]
    ordering_fields = ["date_prevision", "created_at"]
    ordering = ["-date_prevision"]

    def get_queryset(self):
        qs = Prevision.objects.select_related("produit", "produit__unite", "marche")
        if self.request.query_params.get("futures"):
            qs = qs.filter(date_prevision__gte=timezone.now())
        return qs
