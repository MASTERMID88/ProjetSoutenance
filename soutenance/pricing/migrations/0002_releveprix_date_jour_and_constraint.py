from django.db import migrations, models
from django.db.models import Q


def _populate_date_jour(apps, schema_editor):
    RelevePrix = apps.get_model("pricing", "RelevePrix")
    for r in RelevePrix.objects.all():
        if r.date_releve:
            r.date_jour = r.date_releve.date()
            r.save(update_fields=["date_jour"])


class Migration(migrations.Migration):
    dependencies = [
        ("pricing", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="releveprix",
            name="date_jour",
            field=models.DateField(null=True, editable=False),
        ),
        migrations.RunPython(_populate_date_jour, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="releveprix",
            name="date_jour",
            field=models.DateField(editable=False),
        ),
        migrations.AddConstraint(
            model_name="releveprix",
            constraint=models.UniqueConstraint(
                fields=["collecteur", "produit", "marche", "date_jour"],
                condition=Q(statut__in=["BROUILLON", "EN_ATTENTE", "VALIDE"]),
                name="uniq_releve_actif_par_jour",
            ),
        ),
        migrations.AddIndex(
            model_name="releveprix",
            index=models.Index(
                fields=["produit", "marche", "-date_releve"],
                name="pricing_rel_prod_marche_date_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="releveprix",
            index=models.Index(fields=["statut"], name="pricing_rel_statut_idx"),
        ),
    ]
