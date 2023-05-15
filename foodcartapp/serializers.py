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
        firstname = validated_data.get('firstname')
        lastname = validated_data.get('lastname')
        phonenumber = validated_data.get('phonenumber')
        address = validated_data.get('address')
        products = validated_data.get('products')
        order = Order.objects.create(
            firstname=firstname,
            lastname=lastname,
            phonenumber=phonenumber,
            address=address
        )
        for order_element in products:
            OrderElement.objects.create(
                order=order,
                product=order_element['product'],
                quantity=order_element['quantity']
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