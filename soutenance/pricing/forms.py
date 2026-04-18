from django import forms

from .models import ValidationReleve
from core.models import Marche, Produit
from django.utils import timezone

from .models import RelevePrix


class RelevePrixForm(forms.ModelForm):
    """Formulaire de saisie d'un releve par un collecteur."""

    class Meta:
        model = RelevePrix
        fields = ["produit", "marche", "prix", "date_releve", "source", "commentaire"]
        widgets = {
            "date_releve": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "prix": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": "form-control"}),
            "source": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: vendeur, grossiste..."}),
            "commentaire": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "produit": forms.Select(attrs={"class": "form-control"}),
            "marche": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, collecteur=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.collecteur = collecteur
        self.fields["produit"].queryset = Produit.objects.filter(actif=True).order_by("nom")
        self.fields["marche"].queryset = Marche.objects.filter(actif=True).order_by("region", "nom")
        if not self.initial.get("date_releve") and not self.instance.pk:
            self.initial["date_releve"] = timezone.now().strftime("%Y-%m-%dT%H:%M")

    def clean_prix(self):
        prix = self.cleaned_data.get("prix")
        if prix is not None and prix <= 0:
            raise forms.ValidationError("Le prix doit etre strictement positif.")
        return prix

    def clean_date_releve(self):
        d = self.cleaned_data.get("date_releve")
        if d and d > timezone.now():
            raise forms.ValidationError("La date du releve ne peut pas etre dans le futur.")
        return d

    def clean(self):
        cleaned = super().clean()
        produit = cleaned.get("produit")
        marche = cleaned.get("marche")
        date_releve = cleaned.get("date_releve")
        collecteur = self.collecteur or getattr(self.instance, "collecteur", None)

        if produit and marche and date_releve and collecteur:
            doublon = RelevePrix.objects.filter(
                collecteur=collecteur,
                produit=produit,
                marche=marche,
                date_jour=date_releve.date(),
                statut__in=RelevePrix.STATUTS_ACTIFS,
            )
            if self.instance.pk:
                doublon = doublon.exclude(pk=self.instance.pk)
            if doublon.exists():
                raise forms.ValidationError(
                    "Vous avez deja un releve actif pour ce produit sur ce marche aujourd'hui. "
                    "Modifiez-le plutot que d'en creer un nouveau."
                )
        return cleaned


class ValidationReleveForm(forms.ModelForm):
    """Formulaire utilise par l'admin pour valider ou rejeter un releve."""

    class Meta:
        model = ValidationReleve
        fields = ["motif"]
        widgets = {
            "motif": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Motif (obligatoire en cas de rejet)",
                }
            ),
        }
