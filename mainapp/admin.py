from django.contrib import admin
from django.forms import ModelChoiceField, ModelForm, ValidationError
from PIL import Image
from django.utils.safestring import mark_safe

from .models import *


class SmartphoneAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and not instance.sd:
            self.fields['sd_max_volume'].widget.attrs.update({
                'readonly': True, 'style': 'background: lightgray;'
            })

    def clean(self):
        if not self.cleaned_data['sd']:
            self.cleaned_data['sd_max_volume'] = None
        return self.cleaned_data


class NotebookAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            'image'].help_text = mark_safe(
            """<span style="color:red; font-size:14px;">При загрузке изображения большего разрешения чем {}x{} оно будет обрезано</span>""".format(
                *Products.MAX_RESOLUTION))

    def clean_image(self):
        image = self.cleaned_data['image']
        img = Image.open(image)
        min_width, min_height = Products.MIN_RESOLUTION
        max_width, max_height = Products.MAX_RESOLUTION

        if image.size > Products.MAX_IMAGE_SIZE:
            raise ValidationError('Размер изображения больше 3MB')
        if img.width < min_width or img.height < min_height:
            raise ValidationError('Загруженное изображение меньше допустимого значения')
        if img.width > max_width or img.height > max_height:
            raise ValidationError('Загруженное изображение больше допустимого значения')
        return image


# f'Загружайте изображания с минимальным разрешением {self.min_resolution[0]}x{self.min_resolution[1]}'
# format(*self.min_resolution)

class NotebookAdmin(admin.ModelAdmin):
    form = NotebookAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Categories.objects.filter(slug='notebooks'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SmartphoneAdmin(admin.ModelAdmin):
    form = SmartphoneAdminForm
    change_form_template = 'mainapp/admin.html'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Categories.objects.filter(slug='smartphones'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Categories)
admin.site.register(Notebook, NotebookAdmin)
admin.site.register(Smartphone, SmartphoneAdmin)
admin.site.register(CartProducts)
admin.site.register(Cart)
admin.site.register(Customers)
admin.site.register(Orders)
