from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Marche, Produit, Unite
from .serializers import MarcheSerializer, ProduitSerializer, UniteSerializer


class UniteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Unite.objects.all().order_by("libelle")
    serializer_class = UniteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ProduitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Produit.objects.select_related("unite").filter(actif=True).order_by("nom")
    serializer_class = ProduitSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ["nom", "variete", "categorie"]
    filterset_fields = ["categorie"]


class MarcheViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Marche.objects.filter(actif=True).order_by("region", "nom")
    serializer_class = MarcheSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ["nom", "quartier", "commune", "region"]
    filterset_fields = ["region", "commune"]
