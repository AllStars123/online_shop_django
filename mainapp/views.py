from django.contrib import messages
from django.shortcuts import render
from django.views.generic import DetailView, View
from django.http import HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from .models import *
from .mixins import *
from .forms import *
from .utils import calc_cart


class BaseView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Categories.objects.get_categories_for_shop()
        products = LatestProducts.objects.get_products_for_main_page('notebook', 'smartphone',
                                                                     with_respect_to='smartphone')
        context = {
            'categories': categories,
            'products': products,
            'cart': self.cart
        }
        return render(request, 'mainapp/base.html', context)


class ProductDetailView(CartMixin, CategoryDetailMixin, DetailView):
    CT_MODEL_MODEL_CLASS = {
        'notebook': Notebook,
        'smartphone': Smartphone
    }

    def dispatch(self, request, *args, **kwargs):
        self.model = self.CT_MODEL_MODEL_CLASS[kwargs['ct_model']]
        self.queryset = self.model._base_manager.all()
        return super().dispatch(request, *args, **kwargs)

    context_object_name = 'product'
    template_name = 'mainapp/product_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ct_model'] = self.model._meta.model_name
        context['cart'] = self.cart
        return context


class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product, created = CartProducts.objects.get_or_create(
            user=self.cart.owner,
            cart=self.cart,
            content_type=content_type,
            object_id=product.id,
            # final_price=product.price
        )
        if created:
            self.cart.products.add(cart_product)
        calc_cart(self.cart)
        messages.add_message(request, messages.INFO, 'Товар успешно добавлен')
        return HttpResponseRedirect('/cart/')


class CategoryDetailView(CartMixin, CategoryDetailMixin, DetailView):
    model = Categories
    queryset = Categories.objects.all()
    context_object_name = 'category'
    template_name = 'mainapp/category_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.cart
        return context


class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Categories.objects.get_categories_for_shop()
        context = {
            'cart': self.cart,
            'categories': categories
        }

        return render(request, 'mainapp/cart.html', context)


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product = CartProducts.objects.get(
            user=self.cart.owner,
            cart=self.cart,
            content_type=content_type,
            object_id=product.id
        )
        self.cart.products.remove(cart_product)
        cart_product.delete()
        calc_cart(self.cart)
        messages.add_message(request, messages.INFO, 'Товар успешно удалён')
        return HttpResponseRedirect('/cart/')


class ChangeQuantityView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product = CartProducts.objects.get(
            user=self.cart.owner,
            cart=self.cart,
            content_type=content_type,
            object_id=product.id
        )
        quantity = int(request.POST.get('quantity'))
        cart_product.quantity = quantity
        cart_product.save()
        calc_cart(self.cart)
        messages.add_message(request, messages.INFO, 'Количество товара успешно изменено')
        return HttpResponseRedirect('/cart/')


class CheckoutView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        categories = Categories.objects.get_categories_for_shop()
        form = OrderForm(request.POST or None)
        context = {
            'cart': self.cart,
            'categories': categories,
            'form': form
        }

        return render(request, 'mainapp/checkout.html', context)


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        customer = Customers.objects.get(user=request.user)
        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.customer = customer
            new_order.first_name = form.cleaned_data['first_name']
            new_order.last_name = form.cleaned_data['last_name']
            new_order.phone = form.cleaned_data['phone']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            new_order.order_at = form.cleaned_data['order_at']
            new_order.comment = form.cleaned_data['comment']
            new_order.save()
            self.cart.in_order = True
            self.cart.save()
            new_order.cart = self.cart
            new_order.save()
            customer.orders.add(new_order)
            messages.add_message(request, messages.INFO, 'Спасибоа за заказ!')
            return HttpResponseRedirect('/')
        return HttpResponseRedirect('/checkout/')
