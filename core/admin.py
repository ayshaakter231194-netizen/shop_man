from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import (
    Category, Product, ProductBatch, Supplier, PurchaseOrder, 
    PurchaseOrderItem, PurchaseReturn, PurchaseReturnItem,
    StockAdjustment, Sale, SaleItem, UserProfile, 
    PurchaseOrderCancellation, SupplierBill, Payment,
    StockMovement, SaleReturn, SaleReturnItem, Customer, DuePayment
)

# Custom User Admin to show UserProfile inline
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

# Unregister the default User admin and register with custom
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    
    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Products'

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'product_count', 'created_at']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    list_filter = ['created_at']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'barcode', 'category', 'supplier', 
        'current_stock', 'min_stock_level', 'stock_status_display',
        'cost_price', 'selling_price', 'profit_margin_display',
        'has_expiry', 'created_at'
    ]
    list_filter = [
        'category', 'supplier', 'has_expiry', 'created_at'
    ]
    search_fields = [
        'name', 'sku', 'barcode', 'description'
    ]
    readonly_fields = [
        'current_stock', 'created_at', 'updated_at', 
        'near_expiry_stock', 'expired_stock', 'stock_status',
        'profit_margin'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'sku', 'barcode', 'category', 'supplier', 'description'
            )
        }),
        ('Pricing', {
            'fields': (
                'cost_price', 'selling_price', 'profit_margin'
            )
        }),
        ('Stock Management', {
            'fields': (
                'current_stock', 'min_stock_level', 
                'has_expiry', 'expiry_warning_days'
            )
        }),
        ('Read-only Information', {
            'fields': (
                'stock_status', 'near_expiry_stock', 'expired_stock',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def stock_status_display(self, obj):
        status = obj.stock_status
        if status == 'out_of_stock':
            return '🔴 Out of Stock'
        elif status == 'low_stock':
            return '🟡 Low Stock'
        else:
            return '🟢 In Stock'
    stock_status_display.short_description = 'Stock Status'
    
    def profit_margin_display(self, obj):
        return f"{obj.profit_margin:.1f}%"
    profit_margin_display.short_description = 'Margin'

class ProductBatchInline(admin.TabularInline):
    model = ProductBatch
    extra = 0
    readonly_fields = ['current_quantity', 'is_expired', 'is_near_expiry', 'days_until_expiry']
    fields = ['batch_number', 'manufacture_date', 'expiry_date', 'quantity', 'current_quantity', 'is_expired', 'days_until_expiry']

@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = [
        'batch_number', 'product', 'manufacture_date', 'expiry_date',
        'quantity', 'current_quantity', 'is_expired', 'is_near_expiry',
        'days_until_expiry', 'stock_value'
    ]
    list_filter = [
        'product', 'product__category', 'manufacture_date', 'expiry_date'
    ]
    search_fields = [
        'batch_number', 'product__name', 'product__sku'
    ]
    readonly_fields = [
        'current_quantity', 'is_expired', 'is_near_expiry', 
        'days_until_expiry', 'stock_value'
    ]
    date_hierarchy = 'expiry_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_cost', 'total_cost', 'batch_number', 'expiry_date']
    readonly_fields = ['total_cost']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number', 'supplier', 'order_date', 'expected_date',
        'status', 'total_amount', 'net_amount', 'return_status_display',
        'is_overdue', 'created_by'
    ]
    list_filter = [
        'status', 'supplier', 'order_date', 'expected_date'
    ]
    search_fields = [
        'po_number', 'supplier__name'
    ]
    readonly_fields = [
        'po_number', 'total_amount', 'net_amount', 'returned_amount',
        'has_returns', 'is_overdue', 'return_status', 'total_returned_amount'
    ]
    inlines = [PurchaseOrderItemInline]
    date_hierarchy = 'order_date'
    
    def return_status_display(self, obj):
        status = obj.return_status
        if status == 'has_completed_returns':
            return '🟠 Has Returns'
        elif status == 'has_pending_returns':
            return '🟡 Pending Returns'
        elif status == 'no_returns':
            return '🟢 No Returns'
        else:
            return '⚪ No Active Returns'
    return_status_display.short_description = 'Return Status'

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'purchase_order', 'product', 'quantity', 'unit_cost', 
        'total_cost', 'returned_quantity', 'remaining_quantity'
    ]
    list_filter = [
        'purchase_order__supplier', 'product__category'
    ]
    search_fields = [
        'purchase_order__po_number', 'product__name'
    ]
    readonly_fields = ['total_cost', 'returned_quantity', 'remaining_quantity']

class PurchaseReturnItemInline(admin.TabularInline):
    model = PurchaseReturnItem
    extra = 0
    fields = ['purchase_order_item', 'batch', 'quantity', 'unit_cost', 'total_cost', 'reason']
    readonly_fields = ['total_cost']

@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(admin.ModelAdmin):
    list_display = [
        'return_number', 'purchase_order', 'return_date', 'reason',
        'status', 'return_amount', 'created_by'
    ]
    list_filter = [
        'status', 'reason', 'return_date'
    ]
    search_fields = [
        'return_number', 'purchase_order__po_number'
    ]
    readonly_fields = ['return_number', 'return_amount']
    inlines = [PurchaseReturnItemInline]
    date_hierarchy = 'return_date'

@admin.register(PurchaseReturnItem)
class PurchaseReturnItemAdmin(admin.ModelAdmin):
    list_display = [
        'purchase_return', 'purchase_order_item', 'batch', 
        'quantity', 'unit_cost', 'total_cost', 'reason'
    ]
    list_filter = [
        'reason', 'purchase_return__status'
    ]
    readonly_fields = ['total_cost']

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'batch', 'adjustment_type', 'quantity',
        'adjusted_by', 'adjusted_at'
    ]
    list_filter = [
        'adjustment_type', 'adjusted_at', 'adjusted_by'
    ]
    search_fields = [
        'product__name', 'batch__batch_number', 'reason'
    ]
    readonly_fields = ['adjusted_at']
    date_hierarchy = 'adjusted_at'

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'phone', 'email', 'total_due', 'credit_limit',
        'has_due_display', 'can_make_credit_sale_display', 'is_active',
        'created_at', 'has_due_invoices_display'
    ]
    list_filter = [
        'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'phone', 'email'
    ]
    readonly_fields = [
        'total_due', 'has_due', 'can_make_credit_sale', 'created_at', 'updated_at',
        'has_due_invoices'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'phone', 'email', 'address', 'is_active'
            )
        }),
        ('Credit Information', {
            'fields': (
                'total_due', 'credit_limit', 'has_due', 'can_make_credit_sale', 'has_due_invoices'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    actions = ['update_due_amounts']
    
    def has_due_display(self, obj):
        return '🔴 Has Due' if obj.has_due else '🟢 No Due'
    has_due_display.short_description = 'Due Status'
    
    def can_make_credit_sale_display(self, obj):
        return '🟢 Allowed' if obj.can_make_credit_sale else '🔴 Not Allowed'
    can_make_credit_sale_display.short_description = 'Credit Sale'
    
    def has_due_invoices_display(self, obj):
        return '🔴 Has Due Invoices' if obj.has_due_invoices else '🟢 No Due Invoices'
    has_due_invoices_display.short_description = 'Due Invoices'
    
    def update_due_amounts(self, request, queryset):
        for customer in queryset:
            customer.update_due_amount()
        self.message_user(request, f"Successfully updated due amounts for {queryset.count()} customers.")
    update_due_amounts.short_description = "Update due amounts for selected customers"

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    fields = ['product', 'batch', 'quantity', 'unit_price', 'total_price']
    readonly_fields = ['total_price']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'customer_display', 'sale_date', 
        'total_amount', 'net_amount', 'returned_amount', 'paid_amount',
        'payment_status_display', 'remaining_due_display',
        'has_returns', 'sold_by', 'get_profit_display', 'get_net_profit_display'
    ]
    list_filter = [
        'sale_date', 'sold_by', 'payment_status'
    ]
    search_fields = [
        'invoice_number', 'customer_name', 'customer_phone', 'customer__name', 'customer__phone'
    ]
    readonly_fields = [
        'invoice_number', 'subtotal', 'tax_amount', 'discount_amount',
        'total_amount', 'net_amount', 'returned_amount', 'has_returns',
        'remaining_due', 'payment_status', 'get_profit', 'get_profit_margin',
        'get_net_profit', 'get_net_profit_margin', 'total_returned_quantity'
    ]
    inlines = [SaleItemInline]
    date_hierarchy = 'sale_date'
    
    def customer_display(self, obj):
        if obj.customer:
            return f"{obj.customer.name} ({obj.customer.phone})"
        return f"{obj.customer_name} ({obj.customer_phone})"
    customer_display.short_description = 'Customer'
    
    def payment_status_display(self, obj):
        status = obj.payment_status
        if status == 'paid':
            return '🟢 Paid'
        elif status == 'due':
            return '🔴 Due'
        elif status == 'partial':
            return '🟡 Partial'
        return status
    payment_status_display.short_description = 'Payment Status'
    
    def remaining_due_display(self, obj):
        return f"${obj.remaining_due:.2f}"
    remaining_due_display.short_description = 'Remaining Due'
    
    def get_profit_display(self, obj):
        profit = obj.get_profit()
        return f"${profit:.2f}" if profit else "-"
    get_profit_display.short_description = 'Gross Profit'
    
    def get_net_profit_display(self, obj):
        net_profit = obj.get_net_profit()
        return f"${net_profit:.2f}" if net_profit else "-"
    get_net_profit_display.short_description = 'Net Profit'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'sold_by')

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = [
        'sale', 'product', 'batch', 'quantity', 
        'unit_price', 'total_price', 'profit', 'returned_quantity', 
        'net_quantity', 'net_profit'
    ]
    list_filter = [
        'sale__sale_date', 'product__category'
    ]
    search_fields = [
        'sale__invoice_number', 'product__name'
    ]
    readonly_fields = ['total_price', 'profit', 'returned_quantity', 'net_quantity', 'net_profit']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sale', 'product', 'batch')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']

@admin.register(PurchaseOrderCancellation)
class PurchaseOrderCancellationAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'cancelled_by', 'cancelled_at']
    list_filter = ['cancelled_at']
    search_fields = ['purchase_order__po_number', 'reason']
    readonly_fields = ['cancelled_at']

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['payment_date', 'amount', 'payment_method', 'reference_number', 'received_by']
    readonly_fields = ['received_by']

@admin.register(SupplierBill)
class SupplierBillAdmin(admin.ModelAdmin):
    list_display = [
        'bill_number', 'purchase_order', 'supplier', 'bill_date',
        'due_date', 'total_amount', 'paid_amount', 'due_amount',
        'status', 'paid_percentage_display', 'is_overdue', 'returned_amount_display'
    ]
    list_filter = [
        'status', 'bill_date', 'due_date', 'supplier'
    ]
    search_fields = [
        'bill_number', 'purchase_order__po_number', 'supplier__name'
    ]
    readonly_fields = [
        'bill_number', 'total_amount', 'due_amount', 'paid_amount',
        'returned_amount', 'net_amount', 'paid_percentage', 'is_overdue'
    ]
    inlines = [PaymentInline]
    date_hierarchy = 'bill_date'
    
    def paid_percentage_display(self, obj):
        return f"{obj.paid_percentage:.1f}%"
    paid_percentage_display.short_description = 'Paid %'
    
    def returned_amount_display(self, obj):
        return f"${obj.returned_amount:.2f}"
    returned_amount_display.short_description = 'Returned Amount'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'bill', 'payment_date', 'amount', 'payment_method',
        'reference_number', 'received_by'
    ]
    list_filter = [
        'payment_method', 'payment_date'
    ]
    search_fields = [
        'bill__bill_number', 'reference_number'
    ]
    readonly_fields = ['received_by']
    date_hierarchy = 'payment_date'

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'movement_type', 'quantity', 'batch_number',
        'reference_number', 'movement_date'
    ]
    list_filter = [
        'movement_type', 'movement_date'
    ]
    search_fields = [
        'product__name', 'batch_number', 'reference_number'
    ]
    readonly_fields = ['movement_date']
    date_hierarchy = 'movement_date'

class SaleReturnItemInline(admin.TabularInline):
    model = SaleReturnItem
    extra = 0
    readonly_fields = ['sale_item', 'quantity', 'unit_price', 'total_price', 'reason', 'notes']
    can_delete = False

@admin.register(SaleReturn)
class SaleReturnAdmin(admin.ModelAdmin):
    list_display = [
        'return_number', 
        'sale', 
        'customer_name',
        'return_type', 
        'refund_amount', 
        'balance_amount',
        'status', 
        'get_total_return_quantity',  # Fixed: using the method
        'return_date',
        'created_by'
    ]
    
    list_filter = [
        'status', 
        'return_type', 
        'reason', 
        'return_date',
        'created_by'
    ]
    
    search_fields = [
        'return_number', 
        'sale__invoice_number',
        'sale__customer_name',
        'sale__customer_phone'
    ]
    
    readonly_fields = [
        'return_number',
        'get_total_return_quantity',  # Fixed: using the method
        'refund_amount',
        'balance_amount',
        'created_by',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Return Information', {
            'fields': (
                'return_number', 
                'sale', 
                'return_date',
                'get_total_return_quantity',
                'refund_amount',
                'balance_amount'
            )
        }),
        ('Return Details', {
            'fields': (
                'reason',
                'return_type',
                'exchange_product',
                'exchange_quantity',
                'description'
            )
        }),
        ('Status & Processing', {
            'fields': (
                'status',
                'created_by',
                'processed_by',
                'processed_at'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [SaleReturnItemInline]
    
    def customer_name(self, obj):
        return obj.sale.customer_name
    customer_name.short_description = 'Customer'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    # Add this method for better display of balance amount
    def balance_amount_display(self, obj):
        if obj.balance_amount > 0:
            return f"৳{obj.balance_amount} (Refund)"
        elif obj.balance_amount < 0:
            return f"৳{abs(obj.balance_amount)} (Payment Due)"
        return "৳0 (Equal)"
    balance_amount_display.short_description = 'Balance Amount'

@admin.register(SaleReturnItem)
class SaleReturnItemAdmin(admin.ModelAdmin):
    list_display = [
        'sale_return', 'sale_item', 'batch', 'quantity',
        'unit_price', 'total_price', 'reason', 'returned_cost'
    ]
    list_filter = [
        'reason', 'sale_return__status'
    ]
    search_fields = [
        'sale_return__return_number', 'sale_item__product__name'
    ]
    readonly_fields = ['total_price', 'returned_cost']

@admin.register(DuePayment)
class DuePaymentAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'payment_date', 'amount', 'payment_method',
        'reference_number', 'received_by', 'created_at', 'allocated_details_display'
    ]
    list_filter = [
        'payment_method', 'payment_date', 'created_at'
    ]
    search_fields = [
        'customer__name', 'customer__phone', 'reference_number'
    ]
    readonly_fields = [
        'received_by', 'created_at', 'allocated_details_display'
    ]
    date_hierarchy = 'payment_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'received_by')
    
    def allocated_details_display(self, obj):
        """Display allocated details in a readable format"""
        if not obj.allocated_details:
            return "No allocation details"
        
        try:
            details = []
            for allocation in obj.allocated_details:
                invoice_info = f"Invoice {allocation.get('invoice_number', 'N/A')}: "
                invoice_info += f"${allocation.get('allocated_amount', 0):.2f}"
                details.append(invoice_info)
            
            return "; ".join(details)
        except (TypeError, KeyError):
            return "Error parsing allocation details"
    allocated_details_display.short_description = 'Allocation Details'

# Custom admin site header and title
admin.site.site_header = 'Shop Management System'
admin.site.site_title = 'Shop Management Admin'
admin.site.index_title = 'Administration Dashboard'