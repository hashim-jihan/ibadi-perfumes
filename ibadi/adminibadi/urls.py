from django.urls import path
from . import views

urlpatterns = [
    path('alogin',views.adminLogin,name='adminLogin'),
    path('adminHome',views.adminHome,name='adminHome'),
    path('adminLogout',views.adminLogout,name='adminLogout'),
    path('customers',views.customers,name='customers'),
    path('blockUser/<int:id>/',views.blockUser,name='blockUser'),
    path('unblockUser/<int:id>/',views.unblockUser,name='unblockUser'),
    path('category',views.category,name='category'),
    path('addCategory',views.addCategory,name='addCategory'),
    path('editCategory/<int:category_id>/',views.editCategory,name='editCategory'),
    path('categoryStatus/<int:category_id>/',views.categoryStatus,name='categoryStatus'),
    path('productsList',views.productsList,name='productsList'),
    path('addProduct',views.addProduct,name='addProduct'),
    path('editProduct/<int:product_id>/',views.editProduct,name='editProduct'),
    path('productStatus/<int:product_id>/',views.productStatus,name='productStatus'),
    path('ordersList',views.ordersList,name='ordersList'),
    path('addProductOffer/<int:product_id>',views.addProductOffer,name='addProductOffer'),
    path('addCategoryOffer/<int:category_id>',views.addCategoryOffer,name='addCategoryOffer'),
]
