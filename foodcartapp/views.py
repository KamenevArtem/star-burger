from pandas import isnull


from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


from .models import Product, Order, OrderElement


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    data = request.data
    if ('products' not in data
        or isnull(data['products'])
        or len(data['products'])==0):
        return Response('error: products key is not presented')
    products_list = data['products']
    if not isinstance(products_list, list):
        return Response('error: products key is not list type')
    order = Order.objects.create(
        first_name=data['firstname'],
        second_name=data['lastname'],
        phone=data['phonenumber'],
        address=data['address'], 
    )
    for product in products_list:
        product_element = Product.objects.get(id=product['product'])
        OrderElement.objects.update_or_create(
            order=order,
            product=product_element,
            quantity=product['quantity']
        )
    return Response(request.data)
