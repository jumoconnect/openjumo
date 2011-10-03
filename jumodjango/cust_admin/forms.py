from django import forms

class HiddenRankModelForm(forms.ModelForm):
    class Meta:
        widgets = {
            'rank': forms.HiddenInput,
            'position': forms.HiddenInput,
        }
