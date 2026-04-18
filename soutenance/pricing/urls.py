from django.urls import path

from .views_web import (
    AdminHistoriqueValidationsView,
    AdminReleveDeciderView,
    AdminReleveDetailView,
    AdminValidationQueueView,
    MesRelevesListView,
    PublicPricesView,
    RelevePrixCreateView,
    RelevePrixUpdateView,
)

urlpatterns = [
    # Public
    path("prix/", PublicPricesView.as_view(), name="public_prices"),
    # Collecteur
    path("releves/", MesRelevesListView.as_view(), name="mes_releves"),
    path("releves/nouveau/", RelevePrixCreateView.as_view(), name="releve_create"),
    path("releves/<int:pk>/modifier/", RelevePrixUpdateView.as_view(), name="releve_update"),
    # Admin
    path(
        "validation/",
        AdminValidationQueueView.as_view(),
        name="admin_validation_queue",
    ),
    path(
        "validation/<int:pk>/",
        AdminReleveDetailView.as_view(),
        name="admin_releve_detail",
    ),
    path(
        "validation/<int:pk>/<str:decision>/",
        AdminReleveDeciderView.as_view(),
        name="admin_releve_decider",
    ),
    path(
        "validation/historique/",
        AdminHistoriqueValidationsView.as_view(),
        name="admin_validations_historique",
    ),
]
