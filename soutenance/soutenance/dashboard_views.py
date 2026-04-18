from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.shortcuts import render

from accounts.models import UserRole
from orders.models import Commande, OffreVente
from pricing.models import RelevePrix


def _effective_role(user):
    """Retourne le role fonctionnel d'un utilisateur."""
    if user.is_superuser or user.is_staff:
        return UserRole.ADMIN
    return getattr(user, "role", UserRole.COMMERCANT)


@login_required
def dashboard(request):
    """Dispatch vers le tableau de bord correspondant au role."""
    role = _effective_role(request.user)
    if role == UserRole.ADMIN:
        return _admin_dashboard(request)
    if role == UserRole.COLLECTEUR:
        return _collecteur_dashboard(request)
    return _commercant_dashboard(request)


def _admin_dashboard(request):
    releves = RelevePrix.objects.select_related("produit", "marche", "collecteur")
    ctx = {
        "parent": "pages",
        "segment": "dashboard",
        "segment_label": "Tableau de bord administrateur",
        "role": "ADMIN",
        "total_releves": releves.count(),
        "releves_en_attente": releves.filter(statut=RelevePrix.Statut.EN_ATTENTE).count(),
        "releves_valides": releves.filter(statut=RelevePrix.Statut.VALIDE).count(),
        "releves_rejetes": releves.filter(statut=RelevePrix.Statut.REJETE).count(),
        "prix_moyen_global": releves.filter(statut=RelevePrix.Statut.VALIDE).aggregate(
            avg=Avg("prix")
        )["avg"],
        "derniers_releves": releves.order_by("-date_releve")[:10],
        "a_valider": releves.filter(statut=RelevePrix.Statut.EN_ATTENTE).order_by(
            "-date_releve"
        )[:10],
    }
    return render(request, "pages/dashboard_admin.html", ctx)


def _collecteur_dashboard(request):
    mes_releves = RelevePrix.objects.filter(collecteur=request.user).select_related(
        "produit", "marche"
    )
    ctx = {
        "parent": "pages",
        "segment": "dashboard",
        "segment_label": "Espace collecteur",
        "role": "COLLECTEUR",
        "total_releves": mes_releves.count(),
        "en_attente": mes_releves.filter(statut=RelevePrix.Statut.EN_ATTENTE).count(),
        "valides": mes_releves.filter(statut=RelevePrix.Statut.VALIDE).count(),
        "rejetes": mes_releves.filter(statut=RelevePrix.Statut.REJETE).count(),
        "derniers_releves": mes_releves.order_by("-date_releve")[:10],
    }
    return render(request, "pages/dashboard_collecteur.html", ctx)


def _commercant_dashboard(request):
    offres = OffreVente.objects.filter(commercant=request.user).select_related(
        "produit", "marche"
    )
    commandes = Commande.objects.filter(acheteur=request.user).select_related("offre")
    prix_valides = RelevePrix.objects.filter(
        statut=RelevePrix.Statut.VALIDE
    ).select_related("produit", "marche")
    ctx = {
        "parent": "pages",
        "segment": "dashboard",
        "segment_label": "Espace commercant",
        "role": "COMMERCANT",
        "mes_offres": offres.count(),
        "offres_actives": offres.filter(statut="ACTIVE").count(),
        "mes_commandes": commandes.count(),
        "ca_total": commandes.aggregate(total=Sum("montant_total"))["total"] or 0,
        "dernieres_offres": offres.order_by("-date_publication")[:5],
        "derniers_prix": prix_valides.order_by("-date_releve")[:10],
    }
    return render(request, "pages/dashboard_commercant.html", ctx)
