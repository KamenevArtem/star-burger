from phonenumber_field.modelfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import Order, OrderElement


class OrderElementSerializer(ModelSerializer):
    class Meta:
        model = OrderElement
        fields = [
            'product',
            'quantity'
            ]


class OrderSerializer(ModelSerializer):
    products = OrderElementSerializer(
        many=True,
        allow_empty=False,
        write_only=True
        )
    phonenumber = PhoneNumberField(region='RU')

    def create(self, validated_data):
        products = validated_data.get('products')
        del validated_data['products']
        order = Order.objects.create(
            **validated_data
        )
        for order_element in products:
            OrderElement.objects.create(
                order=order,
                product=order_element['product'],
                quantity=order_element['quantity'],
                price=order_element['product'].price
                )
        return order
        
    class Meta:
        model = Order
        fields = [
            'id',
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'products'
        ]
