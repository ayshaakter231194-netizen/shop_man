from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    
    # Stock Management
    path('stock-adjustment/', views.stock_adjustment, name='stock_adjustment'),
    
    # POS & Sales
    path('pos/', views.pos_sale, name='pos_sale'),
    path('invoice/<str:invoice_number>/', views.generate_invoice, name='generate_invoice'),
    
    # Purchase Orders
    path('purchase-order/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-order/<int:purchase_id>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-order/<int:purchase_id>/complete/', views.mark_purchase_order_completed, name='mark_purchase_order_completed'),
    path('purchase-order/<int:purchase_id>/process-batches/', views.process_batch_creation, name='process_batch_creation'),
    path('purchase-order/<int:purchase_id>/cancel/', views.cancel_purchase_order, name='cancel_purchase_order'),
    path('purchase-order/<int:purchase_id>/quick-complete/', views.quick_complete_purchase_order, name='quick_complete_purchase_order'),
    
    # Reports
    path('reports/daily-sales/', views.daily_sale_report, name='daily_sale_report'),
    path('reports/stock/', views.stock_report, name='stock_report'),
    path('reports/purchase/', views.purchase_report, name='purchase_report'),
    path('reports/profit/', views.profit_report, name='profit_report'),
    
    # Supplier Billing System
    path('supplier-bills/', views.supplier_bills, name='supplier_bills'),
    path('supplier-bills/<int:pk>/', views.supplier_bill_detail, name='supplier_bill_detail'),
    path('supplier-bills/<int:bill_id>/create-payment/', views.create_payment, name='create_payment'),
    path('bill-dashboard/', views.bill_dashboard, name='bill_dashboard'),
    path('api/bill-summary/', views.bill_summary_api, name='bill_summary_api'),
    


    # Expiry and Returns Management
    path('expiry-report/', views.expiry_report, name='expiry_report'),
    path('batch-management/', views.batch_management, name='batch_management'),
    path('write-off-expired/', views.write_off_expired, name='write_off_expired'),
    path('purchase-returns/', views.purchase_return_list, name='purchase_return_list'),
    path('purchase-returns/create/', views.create_purchase_return, name='create_purchase_return'),
    path('purchase-returns/<int:return_id>/', views.purchase_return_detail, name='purchase_return_detail'),
    path('purchase-returns/<int:return_id>/add-item/', views.add_return_item, name='add_return_item'),
    path('purchase-returns/<int:return_id>/update-status/', views.update_return_status, name='update_return_status'),
    
    # API endpoints
    path('api/po-items/<int:po_id>/', views.get_po_items, name='get_po_items'),
    path('api/batches/<int:product_id>/', views.get_batches_for_product, name='get_batches_for_product'),
    path('get-batches-for-po-item/<int:po_item_id>/', views.get_batches_for_po_item, name='get_batches_for_po_item'),
    # Sale Return URLs
    path('sale-returns/', views.sale_return_list, name='sale_return_list'),
    path('sale-returns/create/', views.sale_return_create, name='sale_return_create'),
    path('sale-returns/add-items/<int:sale_id>/', views.add_sale_return_items, name='add_sale_return_items'),
    path('sale-returns/<int:return_id>/', views.sale_return_detail, name='sale_return_detail'),
    path('sale-returns/<int:return_id>/process/', views.process_sale_return, name='process_sale_return'),
    path('api/search-invoice/', views.search_invoice_for_return, name='search_invoice_for_return'),
    path('sale-returns/<int:return_id>/delete/', views.sale_return_delete, name='sale_return_delete'),
    path('daily-sales-report/', views.daily_sale_report, name='daily_sales_report'),
    path('generate-sales-report/', views.generate_sales_report, name='generate_sales_report'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('api/search-product/', views.search_product_by_barcode, name='search_product_by_barcode'),
    path('search-customer/', views.search_customer, name='search_customer'),
    path('get-customer-due-details/<int:customer_id>/', views.get_customer_due_details, name='get_customer_due_details'),
    path('make-due-payment/', views.make_due_payment, name='make_due_payment'),
     # Customer Due Reports
    path('customer-due-report/', views.customer_due_report, name='customer_due_report'),
    path('due-collection-report/', views.due_collection_report, name='due_collection_report'),
    path('process-due-payment/', views.process_due_payment, name='process_due_payment'),
    path('get-customer-due-details/<int:customer_id>/', views.get_customer_due_details, name='get_customer_due_details'),
    path('debug-customer-due/<int:customer_id>/', views.debug_customer_due, name='debug_customer_due'),
    path('force-update-customer-due/<int:customer_id>/', views.force_update_customer_due, name='force_update_customer_due'),
    path('refresh-all-due-amounts/', views.refresh_all_due_amounts, name='refresh_all_due_amounts'),
    path('force-update-all-due-amounts/', views.force_update_all_due_amounts, name='force_update_all_due_amounts'),
    path('get-product-details/', views.get_product_details, name='get_product_details'),
    path('api/categories/search/', views.search_categories, name='search_categories'),
    path('api/categories/create/', views.create_category, name='create_category'),
    path('api/suppliers/search/', views.search_suppliers, name='search_suppliers'),
    path('api/suppliers/create/', views.create_supplier, name='create_supplier'),
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),

]