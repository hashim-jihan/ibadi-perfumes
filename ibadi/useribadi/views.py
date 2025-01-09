from django.shortcuts import render,redirect,get_object_or_404,HttpResponse
from django.urls import reverse
import razorpay.errors
from .forms import SignupForm,userLoginForm
from django.contrib import messages
import re
from django.core.exceptions import ObjectDoesNotExist
from .models import User,Order,OrderItem,Payment, Wallet
from adminibadi.models import Product,ProductImage,ProductVariants,Category,Coupon
from django.core.mail import send_mail
from django.contrib.auth import authenticate,login,logout,update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.cache import cache_control
from datetime import datetime,timedelta
from django.utils.timezone import now,localtime
from django.utils.crypto import get_random_string
import random
from django.utils.cache import caches 
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Address,Cart,ShippingAddress,Order,OrderItem,Wishlist
from decimal import Decimal
from django.conf import settings
import pkg_resources
import razorpay
import json
from django.http import JsonResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa



cache = caches['default']


# Create your views here.
@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def index(request):
    if request.user.is_authenticated:
        return redirect('userHome')
    return render(request,'useribadi/index.html')




@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def userSignup(request):
    if request.user.is_authenticated:
        return redirect('userHome')
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            full_name = form.cleaned_data['full_name']
            password = form.cleaned_data['password']
            user = User.objects.create_user(full_name=full_name,email=email,password=password)

            user.is_active = False
            user.generated_otp()
            user.save()
            request.session['email'] = email
            send_mail(
                'Your One Time Password',
                f'Your OTP is {user.otp}',
                'ibadiperfumes111@gmail.com',
                [user.email],
                fail_silently=False
            )
            print(user.otp)
            return redirect('signupOtp') 
    else:
        form = SignupForm()
    return render(request,'useribadi/userSignup.html',{'form' : form}) 




@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def signupOtp(request):
    if request.user.is_authenticated:
        redirect('userHome')
    email = request.session.get('email')
    if not email:
        messages.error(request,'Please Signup again')
        return redirect ('userSignup')
    
    try:
        user = User.objects.get(email=email)
        if user.otp_created_at:
            otpExpirationTime = localtime(user.otp_created_at + timedelta(minutes=1))
        else:
            otpExpirationTime = None
    except User.DoesNotExist:
        messages.error(request,'Hey something went wrong')
        return redirect('userSignup')
    
    if request.method == 'POST':
        otp = request.POST.get('otp')

        if otpExpirationTime and otpExpirationTime < now():
            messages.error(request,'OTP expired, Resend OTP')
            return render(request,'useribadi/signupOtp.html')

        if user.otp == otp:
            user.is_active = True
            user.otp = None
            user.otp_created_at = None
            user.save()

            del request.session['email']
            messages.success(request,'User Registered, Please Login')
            return redirect('userLogin')
        else:
            messages.error(request,'Invalid OTP, Please try again')
    
    if otpExpirationTime and otpExpirationTime >= now():
        return render(request,'useribadi/signupOtp.html', {'otpExpirationTime' : otpExpirationTime})
    else:
        return render(request,'useribadi/signupOtp.html')




@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def resendOtp(request):
    email = request.session.get('email')
    
    if not email:
        messages.error(request,'Session expired!')
        return redirect('userSignup')
    try:
        user = User.objects.get(email=email)

        newOtp = get_random_string(6, allowed_chars='0123456789')
        user.otp = newOtp
        user.otp_created_at = now()
        user.save()

        send_mail(
            'Your New OTP Code',
            f'Your OTP is {newOtp}, Dont share it with anyone',
            'ibadiperfumes111@gmail.com',
            [email],
            fail_silently = False
        )    
        print(newOtp)
        messages.success(request,'Check your email again,There is new otp')
        return redirect('signupOtp')
    
    except User.DoesNotExist:
        messages.error(request, 'Something went wrong, Please try again')
        return redirect('userSignup')




@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def userLogin(request):
    if request.user.is_authenticated:
        return redirect('userHome')
    if request.method == 'POST':
        form = userLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request,email=email, password=password)

            if user is not None:
                if user.is_admin:
                    messages.error(request,'Admin is not allowed to login here')
                    return redirect('userLogin')
                
                login(request,user)
                messages.success(request,'User LoggedIn')
                return redirect('userHome')
            else:
                messages.error(request,'Invalid email or password')
    else:
        form = userLoginForm()
    return render(request,'useribadi/userLogin.html',{'form': form})


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)
            otp = random.randint(100000,999999)
            otpExpirationTime = now() + timedelta(minutes=1)

            cache.set(f'otp_{email}',otp,timeout=60)
            cache.set(f'otp_expiration_{email}',otpExpirationTime,timeout=60)


            subject = 'Your password reset OTP'
            message = f'Your OTP for resetting your password is : {otp}. This OTP is valid for 5 minutes'
            from_email = 'ibadiperfumes111@gmail.com'
            send_mail(subject,message,from_email, [email])
            print(otp)

            messages.success(request, 'Go to email,The otp is there')
            return redirect('forgotPasswordOtpVerify',email=email)
        except User.DoesNotExist:
            messages.error(request,'No account found with this email')
    return render(request, 'useribadi/forgotPassword.html')



def forgotPasswordOtpVerify(request,email):
    if request.method == 'POST':
        otpInput = request.POST.get('otp')
        otpStored = cache.get(f'otp_{email}')
        otpExpirationTime = cache.get(f'otp_expiration_{email}')


        if otpExpirationTime and now() > otpExpirationTime:
            messages.error(request, 'Your otp has been expired,sorry!')
        elif str(otpInput) == str(otpStored):
            cache.delete(f'otp_{email}')
            cache.delete(f'otp_expiration_{email}')
            return redirect('resetPassword',email=email)
        else:
            messages.error(request, 'Invalid or Expired OTP')

    otpExpirationTime = cache.get(f'otp_expiration_{email}')
    return render(request, 'useribadi/forgotPasswordOtpVerify.html',{'otpExpirationTime':otpExpirationTime, 'email':email} )


def resendOtpPassword(request,email):
    try:
        user = User.objects.get(email=email)
        otp = random.randint(100000,999999)
        otpExpirationTime = now() + timedelta(minutes=1)

        cache.set(f'otp_{email}',otp,timeout=60)
        cache.set(f'otp_expiration_{email}',otpExpirationTime,timeout=60)

        subject = 'Your Password Reset OTP'
        message = f'Your OTP for resetting your password is : {otp} . This OTP valid for one minutes'
        from_email = 'ibadiperfumes111@gmail.com'
        send_mail(subject,message,from_email,[email])
        print(otp)

        messages.success(request,'A new OTP has been sent to your email')
    except User.DoesNotExist:
        messages.error(request,'No account found with this email')
    return redirect('forgotPasswordOtpVerify',email=email)



def resetPassword(request,email):
    if request.method == 'POST':
         new_password = request.POST.get('new_password')
         confirm_password = request.POST.get('confirm_password')

         if new_password == confirm_password:
             user = User.objects.get(email=email)
             user.password = make_password(new_password)
             user.save()
             messages.success(request,'You password has been reset successfully')
             return redirect('userLogin')
         else:
             messages.error(request,'Passwords do not match')
    return render(request, 'useribadi/resetPassword.html')


@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def userHome(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')

    categories = Category.objects.filter(is_active=True)

    products = Product.objects.filter(is_active=True,variant_id=1).order_by('-created_at').prefetch_related('product_images')[:9]
    featured_products = []
    seenProductNames = set()

    for product in products:
        if product.product_name not in seenProductNames:
            seenProductNames.add(product.product_name)
            mainImage = product.product_images.filter(is_main=True).first()
            imageUrl = mainImage.images.url if mainImage else None
            featured_products.append(
                {
                'id':product.product_id,
                'name':product.product_name,
                'price':product.selling_price,
                'imageUrl':imageUrl,
                'variant_id':product.variant_id
                }

            )        
    return render(request,'useribadi/''userHome.html', {'featured_products' : featured_products, 'categories':categories})




@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def userLogout(request):
    logout(request)
    messages.success(request,'You have been successfuly Logout')
    return redirect('userLogin')



def shop(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')

    categories = Category.objects.filter(is_active=True)
    category_filter = request.GET.get('category')
    sort_by = request.GET.get('sort_by')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    searchQuery = request.GET.get('search_query')

    products = Product.objects.filter(is_active=True,variant_id=1).prefetch_related('product_images')


    if searchQuery:
        products = products.filter(product_name__icontains=searchQuery)

    if category_filter:
        products = products.filter(category__category_name__iexact=category_filter)

    if min_price:
        products = products.filter(selling_price__gte=min_price)
    if max_price:
        products = products.filter(selling_price__lte=max_price) 


    if sort_by == 'price_asc':
        products = products.order_by('selling_price')
    elif sort_by == 'price_desc':
        products = products.order_by('-selling_price')
    elif sort_by == 'name_asc':
        products = products.order_by('product_name')
    elif sort_by == 'name_desc':
        products = products.order_by('-product_name')

    product_list = []
    seenProductNames = set()

    for product in products:
        if product.product_name not in seenProductNames:
            seenProductNames.add(product.product_name)
            mainImage = product.product_images.filter(is_main=True).first()
            imageUrl = mainImage.images.url if mainImage else None
            product_list.append({
                'id' : product.product_id,
                'name' : product.product_name,
                'price' : product.selling_price,
                'imageUrl' : imageUrl,
                'variant_id':product.variant.variant_id
            })
    return render(request,'useribadi/shopPage.html',{
        'product_list' : product_list,
        'categories' : categories,
        'selected_category':category_filter,
        'sort_by':sort_by,
        'min_price' :min_price,
        'max_price' :max_price,
        'search_query':searchQuery
        })



def productPage(request, product_id, variant_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')

    product = get_object_or_404(Product, product_id=product_id, variant_id=variant_id, is_active=True)
    images = product.product_images.all()
    mainImage = images.filter(is_main=True).first()

    variants = Product.objects.filter(product_name=product.product_name, is_active=True)

    products = Product.objects.filter(category=product.category, is_active=True).exclude(product_id=product_id).exclude(product_name=product.product_name)

    related_products = []
    seenProductsName = set()

    for related_product in products:
        if related_product.product_name not in seenProductsName:
            seenProductsName.add(related_product.product_name)
            relatedMainImage = related_product.product_images.filter(is_main=True).first()
            relatedImageUrl = relatedMainImage.images.url if relatedMainImage else None
            related_products.append({
                'id':related_product.product_id,
                'name':related_product.product_name,
                'price':related_product.selling_price,
                'relatedImageUrl':relatedImageUrl,
                'variant_id':related_product.variant.variant_id
            })
    return render(request, 'useribadi/productPage.html', {
        'product': product,
        'images': images,
        'mainImage': mainImage,
        'variants': variants,
        'related_products': related_products,
    })


@login_required
def userProfile(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    return render(request, 'useribadi/userProfile.html', {'user':request.user})



def editProfile(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')
     
    if request.method == 'POST':
        full_name = request.POST.get('full_name').strip()

        if not full_name:
            messages.error(request,'Full Name cannot be empty! ')
            return redirect('userProfile')
        
        if not full_name.isalpha():
            messages.error(request,'Full name must contains alphabetic characters')
            return redirect('userProfile')
        
        request.user.full_name = full_name
        request.user.save()
        messages.success(request, 'Your profile has been updated successfully')
        return redirect(reverse('userProfile'))
    return redirect('userProfile')



@login_required
def changePassword(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')

    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request,'Current password is incorrect')
            return redirect('userProfile')
        
        if current_password == new_password:
            messages.error(request,'current password and new password is same')
            return redirect('userProfile')
        
        if len(new_password) < 8:
            messages.error(request,'Password must be 8 characters')
            return redirect('userProfile')
        
        if new_password != confirm_password:
            messages.error(request,'Passwords do not match')
            return redirect('userProfile')
        
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request,request.user)
        messages.success(request, 'Your password has been changed successfully')
        return redirect('userProfile')
    return redirect('userProfile')     


def userAddress(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    addresses = Address.objects.filter(user=request.user)
    addressCount = addresses.count()
    return render(request,'useribadi/userAddress.html', {'addresses':addresses, 'addressCount':addressCount})



def addAddress(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        phone = request.POST.get('phone').strip()
        address = request.POST.get('address').strip()
        city = request.POST.get('city').strip()
        pincode = request.POST.get('pincode').strip()
        landmark = request.POST.get('landmark').strip()

        if not all(char.isalpha() or char.isspace() for char in name):
            messages.error(request,'Name must be contain only alphabetic characters')
            return redirect('addAddress')
        
        if not re.fullmatch(r'^(?!([0-9])\1{9})\d{10}$', phone):
            messages.error(request,'Must be Valid Phone number')
            return redirect('addAddress')
        
        if not all(char.isalpha() or char.isspace() for char in city):
            messages.error(request,'City must contain only alphabetic characters')
            return redirect('addAddress')
        
        if not (pincode.isdigit() and len(pincode) == 6):
            messages.error(request,'Pincode must be 6 digits')
            return redirect('addAddress')
        
        if landmark and not all(char.isalpha() or char.isspace() for char in landmark):
            messages.error(request, 'Landmark must be contain only alphabetic characters')
            return redirect('addAddress')
        
        user = request.user
        newAddress = Address(user=user, name=name, phone=phone, address=address, city=city, pincode=pincode, landmark=landmark)
        newAddress.save()
        messages.success(request, 'Address successfully Added')
        return redirect('userAddress')
    return render(request,'useribadi/addAddress.html')




def editAddress(request,address_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    currentAddress = get_object_or_404(Address, address_id=address_id)

    if request.method == 'POST':
        if 'update' in request.POST:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            city = request.POST.get('city')
            pincode = request.POST.get('pincode')
            landmark = request.POST.get('landmark')

            if not all(char.isalpha() or char.isspace() for char in name):
                messages.error(request,'Name must be contain only alphabetic characters')
                return redirect('editAddress',address_id=address_id)
            
            if not re.fullmatch(r'^(?!([0-9])\1{9})\d{10}$', phone):
                messages.error(request,'Must be Valid Phone number')
                return redirect('editAddress',address_id=address_id)
            
            if not all(char.isalpha() or char.isspace() for char in city):
                messages.error(request,'City must contain only alphabetic characters')
                return redirect('editAddress',address_id=address_id)
        
            if not (pincode.isdigit() and len(pincode) == 6):
                messages.error(request,'Pincode must be 6 digits')
                return redirect('editAddress',address_id=address_id)
        
            if landmark and not all(char.isalpha() or char.isspace() for char in landmark):
                messages.error(request, 'Landmark must be contain only alphabetic characters')
                return redirect('editAddress',address_id=address_id)
            
            currentAddress.name = name
            currentAddress.phone = phone
            currentAddress.address = address
            currentAddress.city = city
            currentAddress.pincode = pincode
            currentAddress.landmark = landmark

            currentAddress.save()
            messages.success(request,'Address is updated successfully')
            return redirect('userAddress')
    return render(request,'useribadi/editAddress.html',{'currentAddress' : currentAddress})



def deleteAddress(request,address_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    currentAddess = get_object_or_404(Address,address_id=address_id)
    currentAddess.delete()
    messages.error(request,'Address Succesfully Deleted! ')
    return redirect('userAddress')



@csrf_exempt
def addToCart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')

    
    variant_id = request.POST.get('variant_id')
    product = get_object_or_404(Product,product_id=product_id,variant_id=variant_id)
 
    cartItem, created = Cart.objects.get_or_create(user=request.user,product_id=product_id)
    
    availableStock = product.quantity
    maxQuantity = min(5, availableStock)
    

    if not created:
        if cartItem.quantity >= maxQuantity:
            messages.error(request, f'You can only add up to {maxQuantity} of {product.product_name}')
        else:
            cartItem.quantity +=1
            if cartItem.quantity > availableStock:
                cartItem.quantity = availableStock
            cartItem.save()
            messages.success(request,f'updated the quantity of {product.product_name} in your cart')
    else:
        cartItem.quantity = 1
        cartItem.save()
        messages.success(request,f'Added {product.product_name} to your cart')

    return redirect('productPage',product_id=product_id,variant_id=variant_id)




def myCart(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    

    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
    
    cartItems = Cart.objects.filter(user=request.user)

    cartItemwithSubTotal = []
    for item in cartItems:
        productSubTotal = item.product.selling_price * item.quantity
        mainImage = item.product.product_images.filter(is_main=True).first()

        variant = None
        if hasattr(item.product, 'variant'):
            variant = item.product.variant
        cartItemwithSubTotal.append({
            'id' : item.product.product_id,
            'product':item.product,
            'image':mainImage.images.url,
            'quantity':item.quantity,
            'subTotal':productSubTotal,
            'variant':variant
        })

    cartSubTotal = sum(item['subTotal'] for item in cartItemwithSubTotal)
    deliveryCharge=50 if cartItems.exists() else 0
    cartTotal = cartSubTotal + deliveryCharge

    return render(request,'useribadi/myCart.html', {
        'cartItems':cartItemwithSubTotal,
        'cartSubTotal':cartSubTotal,
        'deliveryCharge':deliveryCharge,
        'cartTotal':cartTotal
        })



def updateCartQuantity(request, product_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
    
    if request.method == 'POST':
        action = request.POST.get('action')
        cartItem = get_object_or_404(Cart,product__product_id=product_id, user=request.user)

        maxQuantity = 5
        availableQuantity = cartItem.product.quantity

        if action == 'increase':
            if cartItem.quantity >= maxQuantity:
                messages.error(request,f'you can only add up to {maxQuantity} of {cartItem.product.product_name}')
            elif cartItem.quantity + 1 > availableQuantity:
                messages.error(request,f'only {availableQuantity} of {cartItem.product.product_name} is available in stock')  
            else:
                cartItem.quantity +=1
                cartItem.save()
        elif action == 'decrease' and cartItem.quantity > 1:
            cartItem.quantity -=1
            cartItem.save()
        return redirect('myCart')



def removeFromCart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
    
    product = get_object_or_404(Cart,product_id=product_id, user=request.user)
    product.delete()
    messages.error(request,'Item Removed from cart!')
    return redirect('myCart')




def applyCoupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code').upper()
        cartItems = Cart.objects.filter(user=request.user)
        cartSubTotal = sum(item.product.selling_price * item.quantity for item in cartItems)
        print(coupon_code)
        print(cartSubTotal)

        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code)

            if coupon.expiry_date < now():
                messages.error(request,'Coupon has been expired')
                return redirect('checkoutPage')

            if cartSubTotal < coupon.minimum_purchase:
                messages.error(request,f'Your total purchase amount must be at least {coupon.minimum_purchase} to use this coupon')
                return redirect('checkoutPage')
            
            if coupon.discount_percentage:
                productDiscounts = {}
                totalDiscount = 0

                for item in cartItems:
                    productSubTotal = item.product.selling_price * item.quantity
                    productDiscount = (productSubTotal * coupon.discount_percentage) / 100
                    productDiscounts [item.id] = round(float(productDiscount), 2)
                    totalDiscount += productDiscount

                print(productDiscounts)                    
                discount = min(totalDiscount, coupon.maximum_discount)
                finalAmount = cartSubTotal - discount
            

                request.session['applied_coupon'] = {
                    'coupon_code' : coupon.coupon_code,
                    'discount_amount':float(discount),
                    'final_amount':float(finalAmount),
                    'product_discounts':productDiscounts
                }
                messages.success(request, f'Coupon applied ! you saved ₹{discount} Rupees ')
            else:
                messages.error(request, 'Invalid discount configuration')
        except Coupon.DoesNotExist:
            messages.error(request,'Invalid coupon code, please try again')
    return redirect('checkoutPage')





@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def checkoutPage(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    
    cartItems = Cart.objects.filter(user=request.user)
    cartItemWithSubTotal = []

    for item in cartItems:
        productSubTotal = item.product.selling_price * item.quantity
        mainImage = item.product.product_images.filter(is_main=True).first()

        variant = None
        if hasattr(item.product,'variant'):
            variant = item.product.variant
        
        cartItemWithSubTotal.append({
            'id':item.product.product_id,
            'product':item.product,
            'image':mainImage.images.url,
            'quantity':item.quantity,
            'subtotal':productSubTotal,
            'variant':variant
        })

    cartSubTotal = sum(item['subtotal'] for item in cartItemWithSubTotal)
    deliveryCharge = 50 if cartItems.exists() else 0
    cartTotal = cartSubTotal + deliveryCharge 

    appliedCoupon = request.session.get('applied_coupon',None)
    if appliedCoupon:
        discount_amount = appliedCoupon['discount_amount']
        final_amount = appliedCoupon['final_amount'] + deliveryCharge
        product_discounts = appliedCoupon.get('product_discounts', {})
    else:
        discount_amount = 0
        final_amount = cartTotal
        product_discounts={}

    userAddress = Address.objects.filter(user=request.user)
    availableCoupons = Coupon.objects.filter(is_active=True)
    print(availableCoupons)

    payment_method = dict(Order.payment_method_choices)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        selected_address = request.POST.get('selected_address')

        if not payment_method:
            messages.error(request, 'Please select a payment method')
            return redirect('checkoutPage')
        
        if payment_method == 'COD' and final_amount > 1000:
            messages.error(request,'Cash on Delivery is not available for orders above ₹1000')
            return redirect('checkoutPage')

        if payment_method in ['WALLET']:
            messages.error(request, f'{payment_method} yet to be active! Please selcet cash on delivery ')
            return redirect('checkoutPage')

        if not selected_address:
            messages.error(request,'Please select a delivery address')
            return redirect('checkoutPage')

        try:
            selected_shipping_address = Address.objects.get(pk=selected_address,user=request.user)

            shipping_address = ShippingAddress(
                user = request.user,
                name = selected_shipping_address.name,
                address = selected_shipping_address.address,
                city = selected_shipping_address.city,
                pincode = selected_shipping_address.pincode,
                phone = selected_shipping_address.phone,
                landmark = selected_shipping_address.landmark
            )
        except Address.DoesNotExist:
            messages.error('Invalid address selected')
            return redirect('checkoutPage')
        

        if payment_method == 'COD':
            shipping_address.save()
            order = Order.objects.create(user=request.user, total_amount=cartSubTotal,discount_amount=discount_amount, delivery_charge=deliveryCharge, final_amount=final_amount, payment_method=payment_method,shipping_address=shipping_address)
            for cartItem in cartItems:
                product_discount = product_discounts.get(str(cartItem.id), 0)
                print(product_discount)
                discounted_price = (cartItem.product.selling_price * cartItem.quantity) - Decimal(product_discount)

                OrderItem.objects.create(
                    order = order,
                    product = cartItem.product,
                    price = cartItem.product.selling_price,
                    final_amount = cartItem.product.selling_price * cartItem.quantity,
                    quantity = cartItem.quantity,
                    discounted_amount = discounted_price
                )

                product = cartItem.product
                if product.quantity >=cartItem.quantity:
                    product.quantity -=cartItem.quantity
                    product.save()

            cartItems.delete()
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']
            messages.success(request, 'Order placed successfully ')
            return redirect('myOrder')
        

        if payment_method == 'ONLINE':
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            order_amount = int(float(final_amount * 100))
            razorpay_order = client.order.create(data={
                'amount':order_amount,
                'currency':'INR',
                'receipt':f'order_rcptid_{request.user.id}',
            })

            shipping_address.save()
            order = Order.objects.create(
                user=request.user, 
                total_amount=cartSubTotal,
                discount_amount=discount_amount, 
                delivery_charge=deliveryCharge, 
                final_amount=final_amount, 
                payment_method=payment_method,
                shipping_address=shipping_address,
                razorpay_order_id=razorpay_order['id'],
                )
            
            for cartItem in cartItems:
                product_discount = product_discounts.get(str(cartItem.id), 0)
                print(product_discount)
                discounted_price = (cartItem.product.selling_price * cartItem.quantity) - Decimal(product_discount)

                OrderItem.objects.create(
                    order = order,
                    product = cartItem.product,
                    price = cartItem.product.selling_price,
                    final_amount = cartItem.product.selling_price * cartItem.quantity,
                    quantity = cartItem.quantity,
                    discounted_amount = discounted_price
                )

                product = cartItem.product
                if product.quantity >=cartItem.quantity:
                    product.quantity -=cartItem.quantity
                    product.save()

            cartItems.delete()
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']

            return render(request, 'useribadi/paymentPage.html', {
                'order_id' : razorpay_order['id'],
                'razorpay_key' : settings.RAZORPAY_KEY_ID,
                'amount' : order_amount,
                'currency' : 'INR',
            })

    return render(request,'useribadi/checkout.html', {
        'cartItems':cartItemWithSubTotal,
        'cartSubTotal':cartSubTotal,
        'deliveryCharge':deliveryCharge,
        'cartTotal':cartTotal,
        'final_amount':final_amount,
        'discount_amount':discount_amount,
        'userAddresses':userAddress,
        'availableCoupons':availableCoupons,
        'payment_methods':payment_method
    }) 




@csrf_exempt
def verifyPayment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print('success aan')

            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_signature = data.get('razorpay_signature')

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            client.utility.verify_payment_signature({
                'razorpay_order_id' : razorpay_order_id,
                'razorpay_payment_id' : razorpay_payment_id,
                'razorpay_signature' : razorpay_signature,
            })
            print('shahal')
            order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()
            print('problemmmmmm')
            if not order:
                return JsonResponse({'message':'Order not found'}, status=404)
            order.payment_status = 'PAID'
            order.save()

            Payment.objects.create(
                user=request.user,
                order=order,
                transaction_id=razorpay_payment_id,
                amount_paid=order.final_amount,
            )

            Cart.objects.filter(user=request.user).delete()
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']

            return JsonResponse({"message": "Payment verified and order created successfully!"}, status=200)    
        except Exception as e:
            print('failed aan')  
            order = Order.objects.filter(razorpay_order_id=data.get('razorpay_order_id')).first()
            if order:
                order.payment_status = 'PENDING'
                order.save()

            return JsonResponse({
                "message": "Payment verification failed!",
                "error": str(e),
                "redirect_url":"/myOrder"
            }, status=400)




def retryPayment(request,order_id):
    order = Order.objects.get(order_id=order_id)
    if not order or order.payment_status != 'PENDING':
        messages.error(request, 'This order is not allowed for Retrying payment')
        return redirect('myOrder')
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order_amount = int(order.final_amount * 100)

    razorpay_order = client.order.create(data={
        'amount':order_amount,
        'currency':'INR',
        'receipt': f'order_rcptid_{order.order_id}'
    })

    order.razorpay_order_id = razorpay_order['id']
    order.save()
    return render(request,'useribadi/paymentPage.html',{
        'order_id': razorpay_order['id'],
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount': order_amount,
        'currency': 'INR',
    })





def myOrder(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    
    orders = Order.objects.filter(user=request.user).order_by('-order_id')
    orderWithItems = []

    for order in orders:
        items = OrderItem.objects.filter(order=order)

        for item in items:
            item.main_image = item.product.product_images.filter(is_main=True).first()
        orderWithItems.append({
            'order':order,
            'items':items,
            'order_status':order.get_order_status_display(),
            'payment_status':order.get_payment_status_display()
        })

    return render(request,'useribadi/myOrder.html',{'orders':orderWithItems})





# def removeProductFromOrder(request,order_item_id):
#     if not request.user.is_authenticated:
#         return redirect('userLogin')
    
#     orderItem = get_object_or_404(OrderItem, order_item_id=order_item_id)

#     if orderItem.is_cancelled:
#         messages.error(request, 'This product is already cancelled')

#     product = orderItem.product
#     product.quantity += orderItem.quantity
#     product.save()

#     orderItem.is_cancelled = True
#     orderItem.save()

#     order = orderItem.order

#     allItems = OrderItem.objects.filter(order=order)
#     remainingItems = [item for item in allItems if not item.is_cancelled]
#     if remainingItems:
#         order.final_amount -=orderItem.price
#     else:
#         order.order_status = 'Cancelled'
#         order.final_amount = order.original_amount

#     order.save()
#     messages.success(request, f'The Product {orderItem.product.product_name} has been removed from your order!')
#     return redirect('myOrder')





def cancelOrder(request,order_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    if request.method == 'POST':
        order = get_object_or_404(Order,order_id=order_id, user=request.user)
        if order.order_status in ['PENDING','SHIPPED']:
            orderItems = OrderItem.objects.filter(order=order)
            for orderItem in orderItems:
                if not orderItem.is_cancelled:
                    product = orderItem.product
                    product.quantity += orderItem.quantity
                    product.save()
                    orderItem.is_cancelled = True
                    orderItem.save()

            order.order_status = 'Cancelled'
            order.final_amount = order.original_amount
            order.save()
            
            if order.payment_method == 'ONLINE':
                try:
                    latestWalletEntry =Wallet.objects.filter(user=request.user).order_by('-created_at').first()
                    currentBalance = latestWalletEntry.current_balance if latestWalletEntry else Decimal(0)
                    updatedBalance = currentBalance + order.final_amount
                    order.payment_status = 'REFUNDED'
                    order.save()

                    print(latestWalletEntry)
                    print(currentBalance)
                    print(updatedBalance)
                    print(order.payment_status)


                    Wallet.objects.create(
                        user=request.user,
                        transaction_type = 'CREDITED',
                        order = order,
                        amount = order.final_amount,
                        current_balance = updatedBalance,
                        reason = f'Refund for cancelled order {order.order_id}'
                    )
                    messages.success(request,f'The amount ₹{order.final_amount} has been refunded to your wallet')
                except ObjectDoesNotExist:
                    messages.error(request, 'No wallet found for this user. Please contact support.')
            else:
                messages.error(request,'Your order has been cancelled successfully.')
        else:
            messages.error(request, 'This order cannot be cancelled.')
        return redirect('myOrder')
    


def returnProduct(request,order_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    
    if request.method == 'POST':
        order = get_object_or_404(Order, order_id=order_id, user=request.user)

        if order.order_status == 'DELIVERED':
            reason = request.POST.get('return_reason')
            order.return_reason = reason
            order.order_status = 'Return Requested'
            order.save()
            messages.success(request, 'Your return request has been submitted succeffully')
        else:
            messages.error(request, 'This order cannot be returned')
    return redirect('myOrder')


    

def addToWishlist(request,product_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    
    product =get_object_or_404(Product,product_id=product_id)

    existingItem = Wishlist.objects.filter(user=request.user, product__product_name=product.product_name).first()

    if existingItem:
        messages.error(request,f'{product.product_name} is already in your wishlist')
    else:
        wishlistItem , created = Wishlist.objects.get_or_create(user=request.user, product_id=product_id)

        if created:
            messages.success(request,f'{product.product_name} has beed added to your wishlist')
    return redirect('productPage', product_id=product_id,variant_id=product.variant.variant_id)




def wishlist(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    
    wishlistItems = Wishlist.objects.filter(user=request.user)
    wishlistProducts = []
    for item in wishlistItems:
        mainImage = item.product.product_images.filter(is_main=True).first()
        wishlistProducts.append({
            'id':item.product.product_id,
            'image':mainImage.images.url,
            'name':item.product.product_name,
            'price':item.product.selling_price,
            'variant_id':item.product.variant.variant_id
            })
    return render(request,'useribadi/wishlist.html',{'wishlistProducts':wishlistProducts})



def removeFromWishlist(request,product_id):
    product = get_object_or_404(Wishlist,product_id=product_id, user=request.user)
    product.delete()
    messages.error(request,'Prouct removed from your wishlist')
    return redirect('wishlist')



def wallet(request):
    walletTransactions = Wallet.objects.filter(user=request.user).order_by('-created_at')
    currentBalance = walletTransactions.first().current_balance if walletTransactions.exists() else 0.00
    return render(request,'useribadi/wallet.html', {'current_balance' : currentBalance, 'wallet_transactions': walletTransactions})



def invoicePdf(request,order_id):
    order = Order.objects.get(order_id=order_id)
    html = render_to_string('useribadi/invoicePdf.html',{'order':order})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{order.order_id}.pdf"'
    
    pisa_status = pisa.CreatePDF(html,dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response





    















