from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import Listing, User, ProductImage, Report


class CreateListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'title', 
            'description', 
            'starting_bid', 
            'min_increment',
            'deposit_percentage',
            'image', 
            'category', 
            'end_time',
            'seller_name', 
            'phone_number'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Məs: Apple iPhone 15 Pro Max 256GB',
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Məhsulun vəziyyəti, xüsusiyyətləri, komplektasiyası haqqında ətraflı məlumat...',
                'class': 'form-control',
                'rows': 4,
                'required': True
            }),
            'starting_bid': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'class': 'form-control',
                'step': '0.50',
                'min': '0.50',
                'required': True
            }),
            'min_increment': forms.NumberInput(attrs={
                'placeholder': '1.00',
                'class': 'form-control',
                'step': '0.50',
                'min': '0.50',
                'value': '1.00',
                'required': True
            }),
            'deposit_percentage': forms.Select(attrs={
                'class': 'form-select',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'end_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'required': True
            }),
            'seller_name': forms.TextInput(attrs={
                'placeholder': 'Adınız və ya Mağaza adı',
                'class': 'form-control'
            }),
            'phone_number': forms.TextInput(attrs={
                'placeholder': '+994 50 123 45 67',
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Məhsulun Başlığı',
            'description': 'Məhsul Haqqında Təsvir',
            'starting_bid': 'Başlanğıc Qiymət (₼ AZN)',
            'min_increment': 'Minimum Artım Addımı (₼ AZN - BR-4)',
            'deposit_percentage': 'Tələb Olunan Beh / Depozit Faizi (%)',
            'image': 'Əsas Şəkil',
            'category': 'Kateqoriya',
            'end_time': 'Hərracın Dəqiq Bitmə Vaxtı (BR-5, BR-6)',
            'seller_name': 'Satıcının Adı',
            'phone_number': 'Əlaqə Nömrəsi / WhatsApp',
        }

    def clean_starting_bid(self):
        starting_bid = self.cleaned_data.get('starting_bid')
        if starting_bid and starting_bid <= 0:
            raise forms.ValidationError("Başlanğıc qiymət 0-dan böyük olmalıdır (BR-3).")
        return starting_bid

    def clean_min_increment(self):
        min_increment = self.cleaned_data.get('min_increment')
        if min_increment and min_increment <= 0:
            raise forms.ValidationError("Minimum artım addımı 0-dan böyük olmalıdır (BR-4).")
        return min_increment

    def clean_end_time(self):
        end_time = self.cleaned_data.get('end_time')
        if end_time and end_time <= timezone.now():
            raise forms.ValidationError("Hərracın bitmə vaxtı gələcək bir tarix və saat olmalıdır (BR-5).")
        return end_time


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'fin_code', 'id_card_number', 'birth_date',
            'city', 'address', 'postal_code'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adınız'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soyadınız'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'elektron@poct.az'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+994 50 123 45 67'}),
            'fin_code': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Məs: 7ABC123', 'maxlength': '7'}),
            'id_card_number': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Məs: AZE12345678'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bakı, Sumqayıt, Gəncə...'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Rayon, küçə, bina, mənzil'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AZ1000'}),
        }
        labels = {
            'first_name': 'Ad',
            'last_name': 'Soyad',
            'email': 'E-poçt Ünvanı',
            'phone': 'Əlaqə Nömrəsi',
            'fin_code': 'Ş/V FİN Kodu (7 simvol)',
            'id_card_number': 'Şəxsiyyət Vəsiqəsinin Seriya və Nömrəsi',
            'birth_date': 'Doğum Tarixi',
            'city': 'Şəhər / Rayon',
            'address': 'Dəqiq Çatdırılma Ünvanı',
            'postal_code': 'Poçt İndeksi',
        }


class CheckoutOrderForm(forms.Form):
    delivery_name = forms.CharField(
        max_length=128, 
        label="Qəbul Edən Şəxsin Adı və Soyadı",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ad və Soyad', 'required': True})
    )
    delivery_phone = forms.CharField(
        max_length=20, 
        label="Əlaqə Nömrəsi",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+994 50 123 45 67', 'required': True})
    )
    delivery_city = forms.CharField(
        max_length=64, 
        label="Şəhər / Rayon",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bakı, Sumqayıt...', 'required': True})
    )
    delivery_address = forms.CharField(
        label="Dəqiq Çatdırılma Ünvanı",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Küçə, bina, blok, mənzil', 'required': True})
    )
    delivery_notes = forms.CharField(
        required=False,
        label="Kuryer Üçün Xüsusi Qeyd (İstəyə görə)",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Məs: Saat 18:00-dan sonra çatdırılsın'})
    )


class WalletDepositForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=Decimal('1.00'), 
        label="Artırılacaq Məbləğ (₼ AZN)",
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg fw-bold', 'placeholder': '0.00', 'step': '1.00', 'required': True})
    )
    card_number = forms.CharField(
        max_length=19, 
        label="Bank Kartının Nömrəsi",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000 0000 0000 0000', 'maxlength': '19', 'required': True})
    )
    card_expiry = forms.CharField(
        max_length=5, 
        label="Bitmə Tarixi (AA/İL)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12/28', 'maxlength': '5', 'required': True})
    )
    card_cvv = forms.CharField(
        max_length=4, 
        label="CVV / CVC",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '•••', 'maxlength': '4', 'required': True})
    )
    card_holder = forms.CharField(
        max_length=64, 
        label="Kart Sahibinin Adı və Soyadı",
        widget=forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'ALI ALIYEV', 'required': True})
    )


class WalletWithdrawForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=Decimal('5.00'), 
        label="Çıxarılacaq Məbləğ (₼ AZN)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '1.00', 'required': True})
    )
    card_number = forms.CharField(
        max_length=19, 
        label="Köçürüləcək Bank Kartı",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000 0000 0000 0000', 'maxlength': '19', 'required': True})
    )
    full_name = forms.CharField(
        max_length=64, 
        label="Kart Sahibinin Adı və Soyadı",
        widget=forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'ALI ALIYEV', 'required': True})
    )


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'title', 'description', 'screenshot', 'reporter_email', 'listing']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Xətanın və ya problemin qısa başlığı', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Xətanı və ya şikayəti ətraflı təsvir edin. Harada baş verdi, necə təkrarlamaq olar?', 'required': True}),
            'reporter_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Əlaqə üçün e-poçtunuz'}),
            'screenshot': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'listing': forms.HiddenInput(),
        }
        labels = {
            'report_type': 'Xətanın / Şikayətin Növü',
            'title': 'Başlıq',
            'description': 'Ətraflı Məlumat',
            'reporter_email': 'Əlaqə E-poçtu',
            'screenshot': 'Ekran Görüntüsü (Skrinşot)',
        }
