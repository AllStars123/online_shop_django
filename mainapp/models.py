from django.db import models
from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
import sys

from django.utils import timezone

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_url_product(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


class MinResolutionException(Exception):
    pass


class MaxResolutionException(Exception):
    pass


class MaxImageSizeException(Exception):
    pass


class LatestProductsManager:
    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to),
                                  reverse=True)
        return products


class LatestProducts:
    objects = LatestProductsManager()


class CategoryManager(models.Manager):
    CATEGORY_NAME_COUNT_NAME = {
        'Ноутбуки': 'notebook__count',
        'Смартфоны': 'smartphone__count'
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_shop(self):
        models = get_models_for_count('notebook', 'smartphone')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url(), count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data


class Categories(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название категории')
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Products(models.Model):
    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (3800, 3800)
    MAX_IMAGE_SIZE = 3145728

    class Meta:
        abstract = True

    title = models.CharField(max_length=255, verbose_name="Название товара")
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение')
    description = models.TextField(verbose_name='Описание товара', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена')

    category = models.ForeignKey(Categories, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_model_name(self):
        return self.__class__.__name__.lower()

    def save(self, *args, **kwargs):
        # Если мы хотим чтобы пользователь сам загружал фото нужного размера
        image = self.image
        img = Image.open(image)

        min_width, min_height = self.MIN_RESOLUTION
        max_width, max_height = self.MAX_RESOLUTION

        if image.size > self.MAX_IMAGE_SIZE:
            raise MaxImageSizeException('Размер изображения больше 3MB')
        if img.width < min_width or img.height < min_height:
            raise MinResolutionException('Загруженное изображение меньше допустимого значения')
        if img.width > max_width or img.height > max_height:
            raise MaxResolutionException('Загруженное изображение больше допустимого значения')

        # Если мы хотим сами сжимать изображение до нужного размера (Способ 1)
        # image = self.image
        # img = Image.open(image)
        # new_img = img.convert('RGB')
        # resized_new_img = new_img.resize((200, 200), Image.ANTIALIAS)
        # filestream = BytesIO()
        # resized_new_img.save(filestream, 'JPEG', quality=90)
        # filestream.seek(0)
        # self.image = InMemoryUploadedFile(filestream, 'ImageField', self.image.name, 'jpeg/image',
        #                                   sys.getsizeof(filestream), None)
        super().save(*args, **kwargs)

        # Пропорциональное сжатие (Способ 2)
        # image = self.image
        # img = Image.open(image)
        # new_img = img.convert('RGB')
        # w_percent = (self.MAX_RESOLUTION[0] / float(img.size[0]))
        # h_size = int((float(img.size[1]) * float(w_percent)))
        # resized_new_img = new_img.resize((self.MAX_RESOLUTION[0], h_size), Image.ANTIALIAS)
        # self.image = resized_new_img
        # super().save(*args, **kwargs)


class Notebook(Products):
    diagonal = models.CharField(max_length=255, verbose_name='Диагональ')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    processor_freq = models.CharField(max_length=255, verbose_name='Частота процессора')
    ram = models.CharField(max_length=255, verbose_name='Оперативная память')
    video = models.CharField(max_length=255, verbose_name='Видеокарта')
    time_without_charge = models.CharField(max_length=255, verbose_name='Время автономной работы')

    def __str__(self):
        return f'{self.category.name}: {self.title}'

    def get_absolute_url(self):
        return get_url_product(self, 'product_detail')


class Smartphone(Products):
    diagonal = models.CharField(max_length=255, verbose_name='Диагональ')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    resolution = models.CharField(max_length=255, verbose_name='Разрешение экрана')
    accum_volume = models.CharField(max_length=255, verbose_name='Объем аккамулятора')
    ram = models.CharField(max_length=255, verbose_name='Оперативная память')
    sd = models.BooleanField(default=True, verbose_name='Наличие SD карты')
    sd_max_volume = models.CharField(max_length=255, null=True, blank=True,
                                     verbose_name='Максимальное объём встраиваемой памяти')
    main_cam_mp = models.CharField(max_length=255, verbose_name='Главная камера')
    front_cam_mp = models.CharField(max_length=255, verbose_name='Фронтальная камера')

    def __str__(self):
        return f'{self.category.name}: {self.title}'

    def get_absolute_url(self):
        return get_url_product(self, 'product_detail')


class CartProducts(models.Model):
    quantity = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Итоговая цена')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    user = models.ForeignKey('Customers', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    def __str__(self):
        return f'Продукты: {self.content_object.title} (Для корзины)'

    def save(self, *args, **kwargs):
        self.final_price = self.quantity * self.content_object.price
        super().save(*args, **kwargs)

    # def get_model_name(self):
    #     return self.__class__._meta.model_name


class Cart(models.Model):
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, default=0, verbose_name='Итоговая цена')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    owner = models.ForeignKey('Customers', null=True,
                              on_delete=models.CASCADE, related_name='Владелец')
    products = models.ManyToManyField(CartProducts, blank=True, related_name='related_cart')

    def __str__(self):
        return str(self.id)


class Customers(models.Model):
    phone = models.CharField(max_length=255, null=True, blank=True, verbose_name='Номер телефона')
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name='Адрес')

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    orders = models.ManyToManyField('Orders', verbose_name='Заказы покупателя', related_name='related_customer')

    def __str__(self):
        return f'Покупатель {self.user.first_name, self.user.last_name}'


class Orders(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый заказ'),
        (STATUS_IN_PROGRESS, 'Заказ в обработке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ выполнен')
    )

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка')
    )

    first_name = models.CharField(max_length=255, verbose_name='Имя')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    phone = models.CharField(max_length=12, verbose_name='Телефон')
    address = models.CharField(max_length=1024, verbose_name='Адрес', null=True, blank=True)
    status = models.CharField(max_length=100, verbose_name='Статус заказа', choices=STATUS_CHOICES, default=STATUS_NEW)
    buying_type = models.CharField(max_length=100, verbose_name='Тип доставки', choices=BUYING_TYPE_CHOICES,
                                   default=BUYING_TYPE_SELF)
    comment = models.TextField(verbose_name='Комментарий к заказу', null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Дата создания заказа')
    order_at = models.DateField(verbose_name='Дата получения заказа', default=timezone.now)

    customer = models.ForeignKey(Customers, verbose_name='Покупатель', on_delete=models.CASCADE,
                                 related_name='related_orders')
    cart = models.ForeignKey(Cart, null=True, blank=True,
                             verbose_name='Корзина', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)
