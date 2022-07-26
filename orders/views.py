from enum import Enum
import json

from django.views     import View
from django.http      import JsonResponse
from django.db.models import Q

from core.utils.login_decorator import login_decorator
from orders.models              import Order, OrderItem, OrderStatus
from products.models            import Product
from users.models               import User

class STATUS(Enum):
    CART                   = 1
    BEFORE_DEPOSIT         = 2
    PREPARING_FOR_DELIVERY = 3
    SHIPPING               = 4
    DELIVERY_COMPLETED     = 5
    EXCHANGE               = 6
    RETURN                 = 7

class CartView(View):
    @login_decorator
    def get(self, request):
        try:
            user = request.user

            user_cart = Q(user=user.id) & Q(order_status=STATUS.CART.value)

            cart_products = Order.objects.get(user_cart).orderitem_set.all()

            result = [{
                'title'   : order.product.title,
                'price'   : order.order_price,
                'quantity': order.order_quantity,
                'picture' : order.product.productimage.main_url
            } for order in cart_products]

            return JsonResponse({'result' : result}, status = 200)

        except Order.DoesNotExist:
            return JsonResponse({'message' : "EMPTY_CART"})
        
    @login_decorator
    def post(self, request, count):
        try:
            data = json.loads(request.body)

            user    = request.user
            product = data['product']

            selected_product = Product.objects.get(id=product)

            user_cart         = Q(user=user.id) & Q(order_status=STATUS.CART.value)
            user_cart_product = Q(product=Product.objects.get(id=product)) & Q(order__in=Order.objects.filter(user_cart))

            if Order.objects.filter(user_cart).exists():
                if OrderItem.objects.filter(user_cart_product).exists():
                    OrderItem.objects.filter(user_cart_product).update(order_quantity=OrderItem.objects.get(user_cart_product).order_quantity + count)
                else:
                    OrderItem.objects.create(
                        product        = selected_product,
                        order          = Order.objects.get(user=user.id),
                        order_quantity = count,
                        order_price    = selected_product.price
                    )

            else:
                Order.objects.create(
                    user         = User.objects.get(id=user.id),
                    order_status = OrderStatus.objects.get(id=STATUS.CART.value)
                )
                OrderItem.objects.create(
                    product        = selected_product,
                    order          = Order.objects.get(user=user.id),
                    order_quantity = count,
                    order_price    = selected_product.price
                )

            items = OrderItem.objects.filter(order__user_id=user)

            result = [{
                'title'   : item.product.title,
                'price'   : item.order_price,
                'quantity': item.order_quantity,
                'picture' : item.product.productimage.main_url
            } for item in items]
   
            return JsonResponse({'result' : result}, status = 200)

        except KeyError:
            return JsonResponse({'message' : 'KEY_ERROR'}, status = 400)

    @login_decorator
    def patch(self, request):
        try:
            data = json.loads(request.body)

            user        = request.user
            product     = data['product']
            calculation = data['calculation']

            user_cart         = Q(user=user.id) & Q(order_status=STATUS.CART.value)
            user_cart_product = Q(product=Product.objects.get(id=product)) & Q(order__in=Order.objects.filter(user_cart))

            if calculation == 'addition':
                OrderItem.objects.filter(user_cart_product).update(
                    order_quantity=(OrderItem.objects.get(user_cart_product).order_quantity + 1)
                )
            elif calculation == 'subtraction':
                OrderItem.objects.filter(user_cart_product).update(
                    order_quantity=(OrderItem.objects.get(user_cart_product).order_quantity - 1)
                )

            result = {'order_quantity' : OrderItem.objects.get(user_cart_product).order_quantity}

            return JsonResponse({'result' : result}, status = 200)
        
        except OrderItem.DoesNotExist:
            return JsonResponse({'message' : 'DATA_NOT_EXIST'}, status = 400)

        except KeyError:
            return JsonResponse({'message' : 'KEY_ERROR'}, status = 400)

    @login_decorator
    def delete(self, request):
        try:
            data = json.loads(request.body)

            user        = request.user
            product     = data['product']

            user_cart         = Q(user=user.id) & Q(order_status=STATUS.CART.value)
            user_cart_product = Q(product=Product.objects.get(id=product)) & Q(order__in=Order.objects.filter(user_cart))            

            OrderItem.objects.get(user_cart_product).delete()

            if OrderItem.objects.filter(order__in=Order.objects.filter(user_cart)).exists():
                pass
            else:
                Order.objects.get(user_cart).delete()

            return JsonResponse({'message' : 'SUCCESS'}, status = 200)

        except OrderItem.DoesNotExist:
            return JsonResponse({'message' : 'PRODUCT_NOT_EXIST'}, status = 400)