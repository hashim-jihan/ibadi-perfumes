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

    products = Product.objects.filter(is_active=True).prefetch_related('product_images')[:9]
    featured_products = []

    for product in products:
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
    products = Product.objects.filter(is_active=True).prefetch_related('product_images')
    product_list = []

    for product in products:
        mainImage = product.product_images.filter(is_main=True).first()
        imageUrl = mainImage.images.url if mainImage else None
        product_list.append({
            'id' : product.product_id,
            'name' : product.product_name,
            'price' : product.selling_price,
            'imageUrl' : imageUrl
        })
    return render(request,'useribadi/shopPage.html',{'product_list' : product_list})



def productPage(request,product_id):
    if not request.user.is_authenticated:
        return redirect('userLogin')
    product = get_object_or_404(Product, product_id=product_id)
    images = product.product_images.all()
    mainImage = images.first()


    related_products = Product.objects.filter(is_active=True,category=product.category).exclude(product_id=product_id)
    return render(request,'useribadi/productPage.html',{'product' : product, 'images' : images, 'mainImage' : mainImage, 'related_products' : related_products})
