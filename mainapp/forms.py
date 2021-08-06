from django import forms

from .models import Orders


class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_at'].label = 'Дата получения заказа'

    order_at = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))

    class Meta:
        model = Orders
        fields = ('first_name', 'last_name', 'phone', 'address', 'buying_type', 'order_at', 'comment')
