from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from accounts.mixins import AdminRoleRequiredMixin, CollecteurRequiredMixin

from .forms import RelevePrixForm, ValidationReleveForm
from .models import RelevePrix, ValidationReleve


class MesRelevesListView(CollecteurRequiredMixin, ListView):
    """Liste des releves du collecteur connecte."""

    model = RelevePrix
    template_name = "pricing/releve_list.html"
    context_object_name = "releves"
    paginate_by = 20

    def get_queryset(self):
        return (
            RelevePrix.objects.filter(collecteur=self.request.user)
            .select_related("produit", "produit__unite", "marche")
            .order_by("-date_releve")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent"] = "pricing"
        ctx["segment"] = "releves"
        ctx["segment_label"] = "Mes releves"
        return ctx


class RelevePrixCreateView(CollecteurRequiredMixin, CreateView):
    model = RelevePrix
    form_class = RelevePrixForm
    template_name = "pricing/releve_form.html"
    success_url = reverse_lazy("mes_releves")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["collecteur"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.collecteur = self.request.user
        form.instance.statut = RelevePrix.Statut.EN_ATTENTE
        messages.success(self.request, "Releve soumis pour validation.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent"] = "pricing"
        ctx["segment"] = "releves"
        ctx["segment_label"] = "Nouveau releve"
        ctx["mode"] = "create"
        return ctx


class RelevePrixUpdateView(CollecteurRequiredMixin, UpdateView):
    model = RelevePrix
    form_class = RelevePrixForm
    template_name = "pricing/releve_form.html"
    success_url = reverse_lazy("mes_releves")

    def get_queryset(self):
        # Le collecteur ne peut modifier que ses releves non valides
        return RelevePrix.objects.filter(collecteur=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["collecteur"] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.statut == RelevePrix.Statut.VALIDE:
            messages.error(
                request,
                "Ce releve a deja ete valide par l'administrateur : il ne peut plus etre modifie.",
            )
            return redirect("mes_releves")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if form.instance.statut == RelevePrix.Statut.REJETE:
            form.instance.statut = RelevePrix.Statut.EN_ATTENTE
        messages.success(self.request, "Releve mis a jour.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent"] = "pricing"
        ctx["segment"] = "releves"
        ctx["segment_label"] = "Modifier un releve"
        ctx["mode"] = "update"
        return ctx


# ===================== ESPACE ADMINISTRATEUR =====================

class AdminValidationQueueView(AdminRoleRequiredMixin, ListView):
    """File d'attente des releves a valider (statut EN_ATTENTE)."""

    model = RelevePrix
    template_name = "pricing/admin_validation_queue.html"
    context_object_name = "releves"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            RelevePrix.objects
            .select_related("produit", "produit__unite", "marche", "collecteur")
            .order_by("date_releve")
        )
        statut = self.request.GET.get("statut", RelevePrix.Statut.EN_ATTENTE)
        if statut in {s.value for s in RelevePrix.Statut}:
            qs = qs.filter(statut=statut)
        produit = self.request.GET.get("produit")
        if produit:
            qs = qs.filter(produit_id=produit)
        marche = self.request.GET.get("marche")
        if marche:
            qs = qs.filter(marche_id=marche)
        return qs

    def get_context_data(self, **kwargs):
        from core.models import Marche, Produit
        ctx = super().get_context_data(**kwargs)
        ctx["parent"] = "admin"
        ctx["segment"] = "validation"
        ctx["segment_label"] = "Validation des releves"
        ctx["statut_courant"] = self.request.GET.get("statut", RelevePrix.Statut.EN_ATTENTE)
        ctx["statuts"] = RelevePrix.Statut.choices
        ctx["produits"] = Produit.objects.filter(actif=True).order_by("nom")
        ctx["marches"] = Marche.objects.filter(actif=True).order_by("region", "nom")
        ctx["nb_en_attente"] = RelevePrix.objects.filter(
            statut=RelevePrix.Statut.EN_ATTENTE
        ).count()
        return ctx


class AdminReleveDetailView(AdminRoleRequiredMixin, DetailView):
    """Detail d'un releve avec historique de validation et formulaire motif."""

    model = RelevePrix
    template_name = "pricing/admin_releve_detail.html"
    context_object_name = "releve"

    def get_queryset(self):
        return RelevePrix.objects.select_related(
            "produit", "produit__unite", "marche", "collecteur"
        ).prefetch_related("validations__admin")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent"] = "admin"
        ctx["segment"] = "validation"
        ctx["segment_label"] = "Detail du releve"
        ctx["form"] = ValidationReleveForm()
        # Autres relevés le meme jour sur le meme (produit, marché) pour comparaison
        releve = ctx["releve"]
        ctx["autres_releves_jour"] = (
            RelevePrix.objects
            .filter(produit=releve.produit, marche=releve.marche, date_jour=releve.date_jour)
            .exclude(pk=releve.pk)
            .select_related("collecteur")
        )
        return ctx


class AdminReleveDeciderView(AdminRoleRequiredMixin, View):
    """Applique une decision (valider / rejeter) sur un releve EN_ATTENTE."""

    def post(self, request, pk, decision):
        releve = get_object_or_404(RelevePrix, pk=pk)
        if releve.statut != RelevePrix.Statut.EN_ATTENTE:
            messages.error(request, "Ce releve n'est plus en attente de validation.")
            return redirect("admin_validation_queue")

        if decision not in {"valider", "rejeter"}:
            messages.error(request, "Action inconnue.")
            return redirect("admin_releve_detail", pk=pk)

        form = ValidationReleveForm(request.POST)
        motif = request.POST.get("motif", "").strip()

        if decision == "rejeter" and not motif:
            messages.error(request, "Le motif est obligatoire pour un rejet.")
            return redirect("admin_releve_detail", pk=pk)

        with transaction.atomic():
            nouveau_statut = (
                RelevePrix.Statut.VALIDE
                if decision == "valider"
                else RelevePrix.Statut.REJETE
            )
            ValidationReleve.objects.create(
                releve=releve,
                admin=request.user,
                decision=(
                    ValidationReleve.Decision.VALIDE
                    if decision == "valider"
                    else ValidationReleve.Decision.REJETE
                ),
                motif=motif,
            )
            releve.statut = nouveau_statut
            releve.save(update_fields=["statut"])

        messages.success(
            request,
            f"Releve {'valide' if decision == 'valider' else 'rejete'} avec succes.",
        )
        return redirect("admin_validation_queue")


class AdminHistoriqueValidationsView(AdminRoleRequiredMixin, ListView):
    """Historique de toutes les validations effectuees."""

    model = ValidationReleve
    template_name = "pricing/admin_validations_historique.html"
    context_object_name = "validations"
    paginate_by = 30

    def get_queryset(self):
        qs = (
            ValidationReleve.objects
            .select_related(
                "releve__produit", "releve__marche", "releve__collecteur", "admin"
            )
            .order_by("-date_validation")
        )
        decision = self.request.GET.get("decision")
        if decision in {"VALIDE", "REJETE"}:
            qs = qs.filter(decision=decision)
        if self.request.GET.get("mes_decisions"):
            qs = qs.filter(admin=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent"] = "admin"
        ctx["segment"] = "historique"
        ctx["segment_label"] = "Historique des validations"
        ctx["decision_courante"] = self.request.GET.get("decision", "")
        ctx["mes_decisions"] = bool(self.request.GET.get("mes_decisions"))
        return ctx


# ===================== PUBLICATION PUBLIQUE =====================

class PublicPricesView(TemplateView):
    """Page publique : carte des marches de Bamako + tableau des prix + graphique.

    Restreinte au District de Bamako : seuls les marches dont la region est
    'Bamako' (insensible a la casse) sont affiches, et tous les appels API
    cote client ajoutent automatiquement region=Bamako.
    """

    template_name = "pricing/public_prices.html"
    BAMAKO_REGION = "Bamako"

    def get_context_data(self, **kwargs):
        from core.models import Marche, Produit
        ctx = super().get_context_data(**kwargs)
        ctx["bamako_region"] = self.BAMAKO_REGION
        ctx["produits"] = Produit.objects.filter(actif=True).order_by("nom")
        ctx["marches"] = (
            Marche.objects.filter(actif=True, region__iexact=self.BAMAKO_REGION)
            .order_by("commune", "nom")
        )
        ctx["communes"] = (
            Marche.objects.filter(actif=True, region__iexact=self.BAMAKO_REGION)
            .exclude(commune="")
            .values_list("commune", flat=True)
            .distinct()
            .order_by("commune")
        )
        return ctx


