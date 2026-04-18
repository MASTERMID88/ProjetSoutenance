from rest_framework.routers import DefaultRouter

from core.views import MarcheViewSet, ProduitViewSet, UniteViewSet
from pricing.views import PrevisionViewSet, PrixPublicViewSet, RelevePrixViewSet

router = DefaultRouter()
# Referentiels
router.register(r"unites", UniteViewSet, basename="unite")
router.register(r"produits", ProduitViewSet, basename="produit")
router.register(r"marches", MarcheViewSet, basename="marche")
# Prix publics (lecture, uniquement les valides)
router.register(r"prix", PrixPublicViewSet, basename="prix-public")
# Releves (collecteurs + admin)
router.register(r"releves", RelevePrixViewSet, basename="releve")
# Previsions ML
router.register(r"previsions", PrevisionViewSet, basename="prevision")

urlpatterns = router.urls
