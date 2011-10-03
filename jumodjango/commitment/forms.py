from django import forms
from commitment.models import Commitment

class CommitmentForm(forms.ModelForm):
    class Meta:
        model = Commitment
        fields = ['content_type', 'object_id']
        widgets = {
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }
