from django.db import models
from django.db.models import F, Sum
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from .geo_utils import fetch_coordinates
from star_burger.settings import YA_API_KEY


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=300,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def count_order_price(self):
        return self.exclude(status='DN').order_by('status').annotate(
            order_price = Sum(
                F('elements__price')*F('elements__quantity')
            )
        )
    
    def fetch_restaurant(self):
        restaurants = Restaurant.objects.all()
        known_locations = {
            'address': (lon, lat) for address, lon, lat in
            Location.objects.values_list(
                'address',
                'longitude',
                'latitude')
        }
        restaurants_coordinates = {
            restaurant.id: known_locations[restaurant.address]
            if restaurant.address in known_locations.keys()
            else Location.objects.create_location(restaurant.address)
            for restaurant in restaurants
        }
        

class Order(models.Model):
    
    class OrderStatusChoice(models.TextChoices):
        CREATED = 'C', _('Создан')
        ACCEPTED = 'A', _('Принят')
        PREPAIRING = 'P', _('Готовится')
        DELIVERY = 'D', _('Передан в доставку')
        DONE = 'DN', _('Заказ выполнен')
    
    class OrderPaymentChoice(models.TextChoices):
        CASH = 'C', _(
            'Оплата наличными при получении'
            )
        CARD = 'CD', _(
            'Оплата картой при получении'
        )
        ONLINE = 'O', _(
            'Оплата картой онлайн'
        )
    
    firstname = models.CharField(
        verbose_name='Имя',
        max_length=100
    )
    lastname = models.CharField(
        verbose_name='Фамилия',
        blank=True,
        max_length=200
    )
    phonenumber=PhoneNumberField(
        verbose_name="Номер телефона",
        db_index=True
    )
    address = models.CharField(
        verbose_name='Адрес',
        db_index=True,
        max_length=300
    )
    status = models.CharField(
        verbose_name='Статус заказа',
        choices=OrderStatusChoice.choices,
        max_length=30,
        default=OrderStatusChoice.CREATED,
        db_index=True
    )
    payment = models.CharField(
        verbose_name='Способ оплаты',
        choices=OrderPaymentChoice.choices,
        max_length=30,
        blank=True
    )
    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True,
        max_length=400
    )
    created_time = models.DateTimeField(
        'Заказ создан',
        default=timezone.now,
        db_index=True
        )
    called_time = models.DateTimeField(
        'Время звонка',
        null=True,
        blank=True,
        db_index=True
        )
    delivered_time = models.DateTimeField(
        'Время доставки',
        null=True,
        blank=True,
        db_index=True
        )
    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Ресторан',
        on_delete=models.PROTECT,
        related_name='orders',
        blank=True,
        null=True,
        help_text='Выберите ресторан для исполнения заказа'
    )
    
    objects = OrderQuerySet.as_manager()
    
    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f"{self.firstname} {self.lastname}: {self.phonenumber}"


class OrderElement(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        on_delete=models.CASCADE,
        related_name='elements'
    )
    product = models.ForeignKey(
        Product,
        verbose_name='Позиция',
        on_delete=models.CASCADE,
        related_name='elements'
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Цена',
    )
    
    class Meta:
        verbose_name = 'Содержание заказа'
        verbose_name_plural = 'Содержание заказа'
        unique_together = [
            ['order', 'product', 'quantity']
        ]
    
    def __str__(self):
        return f"{self.order.firstname} {self.order.phonenumber} {self.order.address}"


class LocationQuerySet(models.QuerySet):
    def create_location(self, address):
        current_coordinates = fetch_coordinates(
            YA_API_KEY,
            address
        )
        if not current_coordinates:
            return current_coordinates
        else:
            current_address, created = self \
                .update_or_create(
                    address=address,
                    defaults={
                        'created_at': timezone.now,
                        **fetch_coordinates(
                            YA_API_KEY,
                            address
                        )
                    }
                )
            return current_address.longitude \
                ,current_address.latitude


class Location(models.Model):
    address = models.CharField(
        verbose_name='Адрес',
        max_length=100,
        blank=True,
        unique=True
    )
    latitude = models.FloatField(
        verbose_name='Широта',
        blank=True,
        null=True
    )
    longitude = models.FloatField(
        verbose_name='Долгота',
        blank=True,
        null=True
    )
    created_at = models.DateField(
        verbose_name='Дата запроса',
    )
    objects = LocationQuerySet.as_manager()
    
    class Meta:
        verbose_name = 'Геолокация'
        verbose_name_plural = 'Геолокации'
    
    def __str__(self):
        return self.address
