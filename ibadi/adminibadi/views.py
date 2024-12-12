from django.shortcuts import render,redirect,get_object_or_404
from .forms import aloginForm
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from useribadi.models import User
from django.db.models import Q
from adminibadi.models import Category,Product,ProductImage,ProductVariants
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required


# Create your views here.

@cache_control(no_store=True, must_revalidate=True, no_cache=True)
def adminLogin(request):
    if request.user.is_authenticated:
         if hasattr(request.user, 'is_admin') and request.user.is_admin:
            return redirect('adminHome') 

    if request.method == 'POST':
        form = aloginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.is_admin:
                    login(request,user)
                    messages.success(request,'Admin LoggedIn')
                    return redirect('adminHome')
                else:
                    messages.error(request, 'Invalid email or Password')
            else:
                messages.error(request,'Invalid email or Password')
            
    else:
        form = aloginForm()

    return render(request,'adminibadi/alogin.html', {'form' : form})


@cache_control(no_store=True, must_revalidate=True, no_cache=True)
@login_required
def adminHome(request):
    if not request.user.is_authenticated:
            return redirect('adminLogin')
    return render(request,'adminibadi/adminHome.html')


def adminLogout(request):
    logout(request)
    messages.success(request,'Admin logged out successfully')
    return redirect('adminLogin')


def customers(request):
    users = User.objects.filter(is_admin=False)
    return render(request,'adminibadi/customers.html',{'users' : users })
    


def blockUser(request,id):
     user = get_object_or_404(User,id=id)
     if request.user.is_authenticated:
            user.is_active = False
            user.save()
            messages.error(request,f'{user.full_name} has been blocked!')
     return redirect('customers')

def unblockUser(request,id):
    user = get_object_or_404(User,id=id)
    if request.user.is_authenticated:
        user.is_active = True
        user.save()
        messages.success(request,f'{user.full_name} has been unblocked!')
    return redirect('customers')




def category(request):
    categories = Category.objects.filter(is_deleted = False)
    return render(request,'adminibadi/categories.html', {'categories' : categories})



def addCategory(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        description = request.POST.get('description')

        if not category_name:
            messages.error(request,'Category name is required! ')
            return render(request,'adminibadi/addCategory.html')
        
        Category.objects.create(category_name=category_name, description= description, is_active=True, is_deleted=False)
        messages.success(request,f'Category {category_name} is addedd successfully')
        return redirect('addCategory')
    
    return render(request,'adminibadi/addCategory.html')



def editCategory(request,category_id):
    category = get_object_or_404(Category, pk=category_id, is_deleted=False)

    if request.method == 'POST':
        if 'update' in request.POST:
            category_name = request.POST.get('category_name')
            description = request.POST.get('description')

            category.category_name = category_name
            category.description = description
            category.save()
            messages.success(request,'Category updated Successfully')
            return redirect('category')
        
        elif 'delete' in request.POST:
            category.is_deleted = True
            category.is_active = False
            category.save()
            messages.error(request,'Category deleted ')
            return redirect('category')
 
    return render(request,'adminibadi/editCategory.html',{'category':category})


def categoryStatus(request, category_id):
    category = get_object_or_404(Category, category_id=category_id, is_deleted=False)
    category.is_active = not category.is_active
    category.save()

    action = 'listed' if category.is_active else 'unlisted'
    messages.success(request,f'Category {category.category_name} has been {action}')
    return redirect('category')


def productsList(request):
    products = Product.objects.filter(is_deleted=False).order_by('-created_at').prefetch_related('product_images').select_related('category','variant')
    return render(request,'adminibadi/products.html',{'products' : products})





def addProduct(request):
    categories = Category.objects.filter(is_active=True)
    variants = ProductVariants.objects.filter(is_active=True)

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        category_id = request.POST.get('category')
        variant_id = request.POST.get('variant')
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')
        regular_price = request.POST.get('regular_price')
        selling_price = request.POST.get('selling_price')

        if not all([ product_name, category_id, variant_id,description, quantity, regular_price, selling_price]):
            messages.error(request,'Fields is required') 
            return render(request,'adminibadi/addProduct.html',{'categories' : categories})

        try:
            category = Category.objects.get(category_id=category_id)
            variant = ProductVariants.objects.get(variant_id=variant_id)
        except Category.DoesNotExist:
            messages.error(request, 'Invalid category selected')
            return render(request,'adminibadi/addProduct.html', {'categories' : categories})
        except ProductVariants.DoesNotExist:
            messages.error(request,'Invalid variant selection')
            return render(request,'adminibadi/addProduct.html',{'categories' : categories})

        product = Product(product_name=product_name, category=category,variant=variant, description=description, regular_price=regular_price, selling_price=selling_price, quantity=quantity)
        product.save()

        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        if image1:
            product_image1 = ProductImage(product=product, images=image1, is_main=True)
            product_image1.save()
        if image2:
            product_image2 = ProductImage(product=product, images=image2)
            product_image2.save()
        if image3:
            product_image3 = ProductImage(product=product, images=image3)
            product_image3.save()

            messages.success(request, 'Product Successfully Added!')
            return redirect('productsList')
    return render(request,'adminibadi/addProduct.html',{'categories' : categories, 'variants':variants})



def editProduct(request,product_id):
    product = get_object_or_404(Product, product_id=product_id)
    categories = Category.objects.filter(is_active=True)
    variants = ProductVariants.objects.filter(is_active=True)
    images = ProductImage.objects.filter(product=product)

    imageMap = {f'image{i+1}': img for i,img in enumerate(images)}
    imageFileName = {key: image.images.name.split('/')[-1] for key, image in imageMap.items()}

    if request.method == 'POST':
        if 'update' in request.POST:
            product_name = request.POST.get('product_name')
            category_id = request.POST.get('category')
            description = request.POST.get('description')
            variant_id = request.POST.get('variant')
            quantity = request.POST.get('quantity')
            regular_price = request.POST.get('regular_price')
            selling_price = request.POST.get('selling_price')

            try: 
                category = Category.objects.get(category_id=category_id)
                variant = ProductVariants.objects.get(variant_id=variant_id)
                product.product_name = product_name
                product.category = category
                product.variant = variant
                product.description = description
                product.quantity = quantity
                product.regular_price = regular_price
                product.selling_price = selling_price
                product.save()

            
            except Category.DoesNotExist():
                messages.error(request,'Invalid category selected')
                return redirect('editProduct', product_id=product_id)

            image1 = request.FILES.get('image1')
            image2 = request.FILES.get('image2')
            image3 = request.FILES.get('image3')

            if image1:
                oldImage1 = ProductImage.objects.filter(product=product,is_main=True).first()
                if oldImage1:
                    oldImage1.delete()
                ProductImage.objects.create(product=product,is_main=True, images=image1)

            if image2:
                oldImage2 = ProductImage.objects.filter(product=product,is_main=False).first()
                if oldImage2:
                    oldImage2.delete()
                ProductImage.objects.create(product=product, is_main=False,images=image2)

            if image3:
                oldImage3 = ProductImage.objects.filter(product=product,is_main=False).last()
                if oldImage3:
                    oldImage3.delete()
                ProductImage.objects.create(product=product,is_main=False,images=image3)


        
            messages.success(request,'Product Uploaded Successfully! ')
            return redirect('productsList')
        
        elif 'delete' in request.POST:
            product.is_active = False
            product.is_deleted = True
            product.save()

            messages.error(request,'Product deleted Successfully')
            return redirect('productsList')

    return render(request,'adminibadi/editProduct.html',{
        'product':product, 
        'categories':categories,
        'variants' : variants,
        'imageFileName' : imageFileName,
        })



def productStatus(request,product_id):
    product = get_object_or_404(Product, product_id=product_id, is_deleted=False)

    product.is_active = not product.is_active
    product.save()
    status = 'listed' if product.is_active else 'unlisted'
    messages.success(request, f'Product "{product.product_name}" { status }')
    return redirect('productsList')

