from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import CustomUser, Chama, Contribution

User = get_user_model()

# create your forms here
class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = [
            'member',
            'amount',
            'payment_method'
        ]

class AddMemberForm(forms.Form):
    email = forms.EmailField(label='Member Email')

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError('No user with this email exists.')
        return email

class ChamaForm(forms.ModelForm):
    class Meta:
        model = Chama
        fields = ['name', 'description']

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label="",
        widget=forms.TextInput(attrs={'class':'input_field', 'placeholder':''})
    )
    first_name = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(attrs={'class':'input_field', 'placeholder':''})
    )
    last_name = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(attrs={'class':'input_field', 'placeholder':''})
    )
    phone_number = forms.CharField(
        label="",
        max_length=15,
        widget=forms.TextInput(attrs={'class':'input_field', 'placeholder':''})
    )

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'password1',
            'password2'
        )

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'input_field'
        self.fields['username'].widget.attrs['placeholder'] = ''
        self.fields['username'].label = ''
        self.fields['username'].help_text = ''

        self.fields['password1'].widget.attrs['class'] = 'input_field'
        self.fields['password1'].widget.attrs['placeholder'] = ''
        self.fields['password1'].label = ''
        self.fields['password1'].help_text = ''

        self.fields['password2'].widget.attrs['class'] = 'input_field'
        self.fields['password2'].widget.attrs['placeholder'] = ''
        self.fields['password2'].label = ''
        self.fields['password2'].help_text = ''
