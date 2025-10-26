from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Category, Supplier, Product, ProductBatch, PurchaseOrder, PurchaseOrderItem,
    PurchaseReturn, PurchaseReturnItem, StockAdjustment, Customer, Sale, SaleItem,
    UserProfile, PurchaseOrderCancellation, SupplierBill, Payment, StockMovement,
    SaleReturn, SaleReturnItem, DuePayment, ViewPermission, UserViewPermission
)

# Inline Admin Classes
class ProductBatchInline(admin.TabularInline):
    model = ProductBatch
    extra = 0
    fields = ['batch_number', 'manufacture_date', 'expiry_date', 'quantity', 'current_quantity']
    readonly_fields = ['current_quantity']

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_cost', 'total_cost', 'batch_number', 'expiry_date']
    readonly_fields = ['total_cost']

class PurchaseReturnItemInline(admin.TabularInline):
    model = PurchaseReturnItem
    extra = 0
    fields = ['purchase_order_item', 'batch', 'quantity', 'unit_cost', 'total_cost', 'reason']
    readonly_fields = ['total_cost']

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    fields = ['product', 'batch', 'quantity', 'unit_price', 'total_price']
    readonly_fields = ['total_price']

class SaleReturnItemInline(admin.TabularInline):
    model = SaleReturnItem
    extra = 0
    fields = ['sale_item', 'batch', 'quantity', 'unit_price', 'total_price', 'reason']
    readonly_fields = ['total_price']

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['payment_date', 'amount', 'payment_method', 'reference_number']
    readonly_fields = ['payment_date']

class DuePaymentInline(admin.TabularInline):
    model = DuePayment
    extra = 0
    fields = ['payment_date', 'amount', 'payment_method', 'reference_number']
    readonly_fields = ['payment_date']

# Main Admin Classes
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    ordering = ['name']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'contact_person', 'email']
    ordering = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'sku', 'barcode', 'cost_price', 'selling_price', 
        'current_stock', 'stock_status', 'has_expiry', 'created_at'
    ]
    list_filter = ['category', 'has_expiry', 'created_at']
    search_fields = ['name', 'sku', 'barcode']
    readonly_fields = ['current_stock', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'supplier', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('cost_price', 'selling_price', 'current_stock', 'min_stock_level')
        }),
        ('Product Identification', {
            'fields': ('sku', 'barcode')
        }),
        ('Expiry Management', {
            'fields': ('has_expiry', 'expiry_warning_days')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [ProductBatchInline]

@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'batch_number', 'manufacture_date', 'expiry_date', 
        'quantity', 'current_quantity', 'is_expired', 'is_near_expiry'
    ]
    list_filter = ['product', 'manufacture_date', 'expiry_date']
    search_fields = ['product__name', 'batch_number']
    readonly_fields = ['current_quantity', 'is_expired', 'is_near_expiry', 'days_until_expiry']
    fieldsets = (
        ('Batch Information', {
            'fields': ('product', 'batch_number', 'purchase_order_item')
        }),
        ('Dates', {
            'fields': ('manufacture_date', 'expiry_date')
        }),
        ('Quantities', {
            'fields': ('quantity', 'current_quantity')
        }),
        ('Status', {
            'fields': ('is_expired', 'is_near_expiry', 'days_until_expiry')
        })
    )

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number', 'supplier', 'order_date', 'expected_date', 'status', 
        'total_amount', 'is_overdue', 'created_by'
    ]
    list_filter = ['status', 'order_date', 'supplier']
    search_fields = ['po_number', 'supplier__name']
    readonly_fields = ['po_number', 'total_amount', 'created_at', 'is_overdue']
    inlines = [PurchaseOrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('po_number', 'supplier', 'status')
        }),
        ('Dates', {
            'fields': ('order_date', 'expected_date')
        }),
        ('Financial', {
            'fields': ('total_amount',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at')
        })
    )

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'product', 'quantity', 'unit_cost', 'total_cost']
    list_filter = ['purchase_order__supplier']
    search_fields = ['product__name', 'purchase_order__po_number']
    readonly_fields = ['total_cost']

@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(admin.ModelAdmin):
    list_display = ['return_number', 'purchase_order', 'return_date', 'reason', 'status', 'return_amount']
    list_filter = ['status', 'reason', 'return_date']
    search_fields = ['return_number', 'purchase_order__po_number']
    readonly_fields = ['return_number', 'created_at']
    inlines = [PurchaseReturnItemInline]

@admin.register(PurchaseReturnItem)
class PurchaseReturnItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_return', 'purchase_order_item', 'quantity', 'unit_cost', 'total_cost']
    search_fields = ['purchase_return__return_number', 'purchase_order_item__product__name']

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['product', 'batch', 'adjustment_type', 'quantity', 'adjusted_by', 'adjusted_at']
    list_filter = ['adjustment_type', 'adjusted_at']
    search_fields = ['product__name', 'batch__batch_number']
    readonly_fields = ['adjusted_at']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'phone', 'email', 'total_due', 'credit_limit', 
        'has_due', 'can_make_credit_sale', 'is_active'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['total_due', 'has_due', 'can_make_credit_sale', 'created_at', 'updated_at']
    inlines = [DuePaymentInline]
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'phone', 'email', 'address')
        }),
        ('Credit Information', {
            'fields': ('total_due', 'credit_limit', 'has_due', 'can_make_credit_sale')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'customer_name', 'customer_phone', 'sale_date', 
        'total_amount', 'paid_amount', 'payment_status', 'remaining_due', 'sold_by'
    ]
    list_filter = ['payment_status', 'sale_date', 'sold_by']
    search_fields = ['invoice_number', 'customer_name', 'customer_phone']
    readonly_fields = [
        'invoice_number', 'subtotal', 'tax_amount', 'discount_amount', 
        'total_amount', 'created_at', 'remaining_due', 'paid_display'
    ]
    inlines = [SaleItemInline]
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'sale_date', 'sold_by')
        }),
        ('Customer Information', {
            'fields': ('customer', 'customer_name', 'customer_phone')
        }),
        ('Payment Details', {
            'fields': ('payment_status', 'paid_amount', 'change_amount', 'paid_display', 'remaining_due')
        }),
        ('Financial Breakdown', {
            'fields': ('subtotal', 'tax_amount', 'tax_percentage', 'discount_amount', 'discount_percentage', 'total_amount')
        }),
        ('Returns', {
            'fields': ('returned_amount',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def paid_display(self, obj):
        return obj.paid_display()
    paid_display.short_description = 'Actual Paid Amount'

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'batch', 'quantity', 'unit_price', 'total_price', 'profit']
    list_filter = ['sale__sale_date']
    search_fields = ['sale__invoice_number', 'product__name']
    readonly_fields = ['total_price', 'profit']

    def profit(self, obj):
        return f"${obj.profit:.2f}"
    profit.short_description = 'Profit'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'is_system_admin', 'can_access_admin']
    list_filter = ['role', 'is_system_admin']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['can_access_admin', 'created_at', 'updated_at']

    def can_access_admin(self, obj):
        return obj.can_access_admin
    can_access_admin.boolean = True
    can_access_admin.short_description = 'Can Access Admin'

@admin.register(PurchaseOrderCancellation)
class PurchaseOrderCancellationAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'cancelled_by', 'cancelled_at']
    list_filter = ['cancelled_at']
    search_fields = ['purchase_order__po_number', 'cancelled_by__username']
    readonly_fields = ['cancelled_at']

@admin.register(SupplierBill)
class SupplierBillAdmin(admin.ModelAdmin):
    list_display = [
        'bill_number', 'purchase_order', 'supplier', 'bill_date', 'due_date',
        'total_amount', 'paid_amount', 'due_amount', 'status', 'is_overdue'
    ]
    list_filter = ['status', 'bill_date', 'supplier']
    search_fields = ['bill_number', 'purchase_order__po_number', 'supplier__name']
    readonly_fields = ['bill_number', 'due_amount', 'is_overdue', 'days_overdue', 'paid_percentage']
    inlines = [PaymentInline]
    fieldsets = (
        ('Bill Information', {
            'fields': ('bill_number', 'purchase_order', 'supplier', 'status')
        }),
        ('Dates', {
            'fields': ('bill_date', 'due_date')
        }),
        ('Financial', {
            'fields': ('total_amount', 'paid_amount', 'due_amount', 'paid_percentage')
        }),
        ('Status', {
            'fields': ('is_overdue', 'days_overdue')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['bill', 'payment_date', 'amount', 'payment_method', 'reference_number', 'received_by']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['bill__bill_number', 'reference_number']
    readonly_fields = ['created_at']

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'batch_number', 'movement_date']
    list_filter = ['movement_type', 'movement_date']
    search_fields = ['product__name', 'batch_number']
    readonly_fields = ['created_at']

@admin.register(SaleReturn)
class SaleReturnAdmin(admin.ModelAdmin):
    list_display = [
        'return_number', 'sale', 'return_date', 'reason', 'return_type', 
        'refund_amount', 'status', 'total_return_quantity'
    ]
    list_filter = ['status', 'return_type', 'reason', 'return_date']
    search_fields = ['return_number', 'sale__invoice_number']
    readonly_fields = ['return_number', 'created_at', 'updated_at', 'total_return_quantity']
    inlines = [SaleReturnItemInline]

    def total_return_quantity(self, obj):
        return obj.total_return_quantity
    total_return_quantity.short_description = 'Total Qty'

@admin.register(SaleReturnItem)
class SaleReturnItemAdmin(admin.ModelAdmin):
    list_display = ['sale_return', 'sale_item', 'quantity', 'unit_price', 'total_price', 'reason']
    search_fields = ['sale_return__return_number', 'sale_item__product__name']
    readonly_fields = ['total_price']

@admin.register(DuePayment)
class DuePaymentAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'payment_date', 'amount', 'payment_method', 
        'reference_number', 'received_by', 'allocated_details_display'
    ]
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['customer__name', 'reference_number']
    readonly_fields = ['created_at', 'allocated_details_display']

    def allocated_details_display(self, obj):
        return obj.allocated_details_display
    allocated_details_display.short_description = 'Allocation Details'

@admin.register(ViewPermission)
class ViewPermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'view_code', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'view_code']
    readonly_fields = ['created_at']

@admin.register(UserViewPermission)
class UserViewPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission', 'granted_by', 'granted_at']
    list_filter = ['granted_at', 'permission']
    search_fields = ['user__username', 'permission__name']
    readonly_fields = ['granted_at']

# User Admin customization to show UserProfile inline
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role']
    list_filter = ['is_staff', 'is_superuser', 'is_active']

    def get_role(self, obj):
        try:
            return obj.userprofile.role
        except UserProfile.DoesNotExist:
            return "No role"
    get_role.short_description = 'Role'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Admin site customization
admin.site.site_header = "Inventory Management System"
admin.site.site_title = "IMS Admin"
admin.site.index_title = "Inventory Management System Administration"