from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import CustomUser, Chama, Contribution, Member, SupportMessage
from django.core.exceptions import ValidationError

User = get_user_model()

# create your forms here
class SupportMessageForm(forms.ModelForm):
    class Meta:
        model = SupportMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Your Message'})
        }

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = [
            'member',
            'amount',
            'payment_method'
        ]

        labels = {
            'member': 'Select Member',
            'amount': 'Contribution Amount',
            'payment_method': 'Payment Method'
        }

        widgets = {
            'member': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Amount'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        chama = kwargs.pop('chama', None) # get chama passed from view
        super().__init__(*args, **kwargs)
        if chama:
            self.fields['member'].queryset = Member.objects.filter(chama=chama)
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError("Contribution amount must be greater than zero.")
        return amount

class AddMemberForm(forms.Form):
    email = forms.EmailField(
        label='Member Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter member email'
        })
    )

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

class UpdateUserForm(UserChangeForm):
    password = None  # Exclude password field

    # get other fields
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
        )

    def __init__(self, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'input_field'
        self.fields['username'].widget.attrs['placeholder'] = ''
        self.fields['username'].label = ''
        self.fields['username'].help_text = ''

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
