from django.shortcuts import render,redirect,get_object_or_404
from .forms import SignupForm,userLoginForm
from django.contrib import messages
from .models import User
from adminibadi.models import Product,ProductImage,ProductVariants
from django.core.mail import send_mail
from django.contrib.auth import authenticate,login,logout
from django.views.decorators.cache import cache_control
from datetime import datetime,timedelta
from django.utils.timezone import now,localtime
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Address,Cart






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
        messages.error(request,'Something went wrong, Please try again')
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
        messages.success(request,'A new OTP has been sent to your email')
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




@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def userHome(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')

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
                'imageUrl':imageUrl   
                }

            )        
    return render(request,'useribadi/''userHome.html', {'featured_products' : featured_products})




@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def userLogout(request):
    logout(request)
    messages.success(request,'You have been successfuly Logout')
    return redirect('userLogin')



def shop(request):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    products = Product.objects.filter(is_active=True,variant_id=1).prefetch_related('product_images')
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
    return render(request,'useribadi/shopPage.html',{'product_list' : product_list})



@csrf_exempt
def productPage(request,product_id,variant_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    
    product = get_object_or_404(Product, product_id=product_id,variant_id=variant_id)
    images = product.product_images.all()
    mainImage = images.first()

    variants = ProductVariants.objects.filter(is_active=True)

    products = Product.objects.filter(is_active=True,category=product.category).exclude(product_id=product_id).exclude(product_name=product.product_name)
    related_products = []
    seenProductsName = set()

    for related_product in products:
        if related_product.product_name not in seenProductsName:
            seenProductsName.add(related_product.product_name)  
            relatedMainImage = related_product.product_images.filter(is_main=True).first()
            relatedImageUrl = relatedMainImage.images.url if mainImage else None
            related_products.append({
                'id':related_product.product_id,
                'name' :related_product.product_name,
                'price' : related_product.selling_price,
                'relatedImageUrl':relatedImageUrl,
                'variant_id':1
            })
    return render(request,'useribadi/productPage.html',{'product' : product, 'images' : images, 'mainImage' : mainImage, 'variants':variants, 'related_products' : related_products})



@login_required
def userProfile(request):
    return render(request, 'useribadi/userProfile.html', {'user':request.user})




def userAddress(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request,'useribadi/userAddress.html', {'addresses':addresses})




def addAddress(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')
        landmark = request.POST.get('landmark')

        user = request.user
        newAddress = Address(user=user, name=name, phone=phone, address=address, city=city, pincode=pincode, landmark=landmark)
        newAddress.save()
        messages.success(request, 'Address successfully Added')
        return redirect('userAddress')
    return render(request,'useribadi/addAddress.html')




def editAddress(request,address_id):
    currentAddress = get_object_or_404(Address, address_id=address_id)

    if request.method == 'POST':
        if 'update' in request.POST:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            city = request.POST.get('city')
            pincode = request.POST.get('pincode')
            landmark = request.POST.get('landmark')

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
    currentAddess = get_object_or_404(Address,address_id=address_id)
    currentAddess.delete()
    messages.error(request,'Address Succesfully Deleted! ')
    return redirect('userAddress')


@csrf_exempt
def addToCart(request, product_id):
    product = get_object_or_404(Product,product_id=product_id)
 
    cartItem, created = Cart.objects.get_or_create(user=request.user,product_id=product_id)

    if not created:
        cartItem.quantity +=1
        cartItem.save()
        messages.success(request,f'updated the quantity of {product.product_name} in your cart')
    else:
        messages.success(request,f'Added {product.product_name} to your cart')
    return redirect('productPage',product_id=product_id)




def myCart(request):
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




def removeFromCart(request, product_id):
    product = get_object_or_404(Cart,product_id=product_id, user=request.user)
    product.delete()
    messages.error(request,'Item Removed from cart!')
    return redirect('myCart')






