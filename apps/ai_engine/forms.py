from django import forms


LANGUAGE_CHOICES = [
    ("fr", "Français"),
    ("ar", "العربية"),
]


class AiQueryForm(forms.Form):
    query = forms.CharField(
        label="Votre question",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": 'Ex: "Explique le concept de Tawakkul en Islam en français simple"',
                "class": "w-full rounded-lg border-emerald-300 focus:border-emerald-500 focus:ring-emerald-500",
                "dir": "auto",
            }
        ),
        max_length=1000,
        min_length=5,
    )
    language = forms.ChoiceField(
        label="Langue de réponse",
        choices=LANGUAGE_CHOICES,
        initial="fr",
        widget=forms.RadioSelect,
    )
