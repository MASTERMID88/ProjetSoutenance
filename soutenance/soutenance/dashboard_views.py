from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg
from django.shortcuts import render

from pricing.models import RelevePrix


def _is_admin_like(user):
    if not user.is_authenticated:
        return False
    role = getattr(user, "role", "")
    return user.is_superuser or user.is_staff or role == "ADMIN"


@login_required
@user_passes_test(_is_admin_like)
def dashboard(request):
    releves = RelevePrix.objects.select_related("produit", "marche", "collecteur")

    ctx = {
        "parent": "pages",
        "segment": "dashboard",
        "segment_label": "Tableau de bord",
        "total_releves": releves.count(),
        "releves_en_attente": releves.filter(statut=RelevePrix.Statut.EN_ATTENTE).count(),
        "releves_valides": releves.filter(statut=RelevePrix.Statut.VALIDE).count(),
        "prix_moyen_global": releves.aggregate(avg=Avg("prix"))["avg"],
        "derniers_releves": releves.order_by("-date_releve")[:10],
    }
    return render(request, "pages/dashboard.html", ctx)
