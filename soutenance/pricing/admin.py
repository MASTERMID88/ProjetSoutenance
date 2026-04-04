from django.contrib import admin

from .models import Prevision, RelevePrix, ValidationReleve


admin.site.register(RelevePrix)
admin.site.register(ValidationReleve)
admin.site.register(Prevision)
