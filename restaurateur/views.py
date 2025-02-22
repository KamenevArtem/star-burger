from geopy import distance

from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem, Location
from star_burger.settings import YA_API_KEY


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


def fetch_restaurant_menu():
    available_menu = RestaurantMenuItem.objects \
        .prefetch_related('restaurant', 'product') \
        .filter(availability=True) \
        .order_by('product') \
        .values_list('product', 'restaurant')
    restaurant_products = {
            product: set() for product, restaurant in available_menu
        }
    for product, restaurant in available_menu:
        restaurant_products[product].add(restaurant)
    return restaurant_products


def create_order_description(
    order,
    restaurant_products,
    restaurants,
    order_coordinates,
    restaurant_coordinates
    ):
    orders_to_show_descriptions = {
        'id': order.id,
        'status': order.get_status_display(),
        'payment': order.get_payment_display(),
        'client': f'{order.firstname} {order.lastname}',
        'phone': f'+{order.phonenumber.country_code}'
                 f'{order.phonenumber.national_number}',
        'address': order.address,
        'order_price': f'{order.order_price} рублей',
        'comment': order.comment,
        'restaurant': order.restaurant,
    }
    order_elements = order.elements.select_related('product')
    if order_elements != 0:
        suitable_restaurants_ids = set.intersection(
                *[restaurant_products[order_element.product.id] for order_element in order_elements]
            )
        distances = []
        errors = []
        if order_coordinates == 'Ошибка':
            errors = {
                'name': 'Ошибка определения координат'
            }
        else:
            distances = [
                {
                    'id': restaurant.id,
                    'name': restaurant.name,
                    'distance': distance.distance(
                        order_coordinates, restaurant_coordinates[restaurant.id]
                    ).km,
                } for restaurant in restaurants
                if restaurant.id in suitable_restaurants_ids
            ]
            sorted(
                distances,
                key=lambda distance: distance['distance'],
            )
        order.distances = distances
        order.errors = errors
    return order


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))
    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    restaurants = Restaurant.objects.all()
    restaurant_products = fetch_restaurant_menu()
    orders = Order.objects \
        .count_order_price()
    known_locations = {
            'address': (longitude, latitude) \
                for address, longitude, latitude in
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
    orders_to_show = []
    for order in orders:
        if order.restaurant:
            order.status = 'P'
            order.save()
        order_location = known_locations[order.address] if order.address \
            in known_locations.keys() \
            else Location.objects.create_location(order.address)
        create_order_description(
            order,
            restaurant_products,
            restaurants,
            order_location,
            restaurants_coordinates
        )
        order_to_show = {
            'id': order.id,
            'status': order.get_status_display(),
            'payment': order.get_payment_display(),
            'client': f'{order.firstname} {order.lastname}',
            'phone': f'+{order.phonenumber.country_code}'
                     f'{order.phonenumber.national_number}',
            'address': order.address,
            'order_price': f'{order.order_price} рублей',
            'comment': order.comment,
            'restaurant': order.restaurant,
            'errors': order.errors,
            'restaurants': order.distances
        }
        orders_to_show.append(order_to_show)
    return render(
        request,
        template_name='order_items.html',
        context={
            'order_items': orders_to_show,
            }
        )
