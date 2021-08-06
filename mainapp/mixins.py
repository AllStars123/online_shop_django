from django.views.generic.detail import SingleObjectMixin
from django.views.generic import View

from .models import *


class CategoryDetailMixin(SingleObjectMixin):
    CATEGORY_SLUG_TO_PRODUCT_MODEL = {
        'notebooks': Notebook,
        'smartphones': Smartphone
    }

    def get_context_data(self, **kwargs):
        if isinstance(self.get_object(), Categories):
            model = self.CATEGORY_SLUG_TO_PRODUCT_MODEL[self.get_object().slug]
            context = super().get_context_data(**kwargs)
            context['categories'] = Categories.objects.get_categories_for_shop()
            context['category_products'] = model.objects.all()
            return context
        context = super().get_context_data(**kwargs)
        context['categories'] = Categories.objects.get_categories_for_shop()
        return context


class CartMixin(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            customer = Customers.objects.filter(user=request.user).first()
            if not customer:
                customer = Customers.objects.create(
                    user=request.user
                )
            cart = Cart.objects.filter(owner=customer, in_order=False).first()
            if not cart:
                cart = Cart.objects.create(owner=customer)

        else:
            cart = Cart.objects.filter(for_anonymous_user=True).first()
            if not cart:
                cart = Cart.objects.create(for_anonymous_user=True)
        self.cart = cart
        # self.cart.save()
        return super().dispatch(request, *args, **kwargs)
