from django import forms
from django.utils import timezone
from datetime import date
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import (
    Payment, Product, StockAdjustment, Sale, PurchaseOrder, 
    SupplierBill, UserProfile, ProductBatch, PurchaseReturn, 
    PurchaseReturnItem, PurchaseOrderItem, Category, Supplier, SaleReturn, SaleReturnItem, ViewPermission
)
from django.contrib.auth.models import User


class ProductForm(forms.ModelForm):
    # Add barcode field with scanning support
    barcode = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Scan or type barcode number',
            'id': 'id_barcode',
            'autocomplete': 'off'  # Important for barcode scanners
        }),
        help_text="Scan barcode or enter manually. Leave empty to auto-generate."
    )
    
    # Remove category and supplier from fields since we handle them via custom dropdowns
    class Meta:
        model = Product
        exclude = ['category', 'supplier']  # Remove these from automatic handling
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter SKU or generate automatically'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter product description (max 500 characters)',
                'maxlength': '500'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'current_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'min_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '10',
                'placeholder': '10'
            }),
            'has_expiry': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_has_expiry'
            }),
            'expiry_warning_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '30',
                'placeholder': '30'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value for expiry warning days if not set
        if not self.instance.pk and not self.initial.get('expiry_warning_days'):
            self.initial['expiry_warning_days'] = 30

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if not sku:
            raise forms.ValidationError('SKU is required.')
        if Product.objects.filter(sku=sku).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A product with this SKU already exists.')
        return sku

    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            # Check if barcode already exists
            if Product.objects.filter(barcode=barcode).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('A product with this barcode already exists.')
            
            # Validate barcode length
            if len(barcode) < 3:
                raise forms.ValidationError('Barcode must be at least 3 characters long.')
        
        return barcode

    def clean_selling_price(self):
        cost_price = self.cleaned_data.get('cost_price')
        selling_price = self.cleaned_data.get('selling_price')
        if selling_price and cost_price and selling_price < cost_price:
            raise forms.ValidationError('Selling price cannot be less than cost price.')
        return selling_price

    def clean_expiry_warning_days(self):
        has_expiry = self.cleaned_data.get('has_expiry', False)
        expiry_warning_days = self.cleaned_data.get('expiry_warning_days', 30)
        
        if has_expiry and expiry_warning_days < 1:
            raise forms.ValidationError('Expiry warning days must be at least 1 day.')
        
        return expiry_warning_days


class ProductBatchForm(forms.ModelForm):
    class Meta:
        model = ProductBatch
        fields = ['product', 'batch_number', 'manufacture_date', 'expiry_date', 'quantity']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_batch_product'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter batch number'
            }),
            'manufacture_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Enter quantity'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        manufacture_date = cleaned_data.get('manufacture_date')
        expiry_date = cleaned_data.get('expiry_date')
        product = cleaned_data.get('product')

        if product and product.has_expiry:
            if not expiry_date:
                raise forms.ValidationError('Expiry date is required for products with expiry tracking.')
            
            if manufacture_date and expiry_date and manufacture_date >= expiry_date:
                raise forms.ValidationError('Expiry date must be after manufacture date.')
        
        return cleaned_data

class StockAdjustmentForm(forms.ModelForm):
    batch = forms.ModelChoiceField(
        queryset=ProductBatch.objects.none(),  # will be filtered dynamically by JS
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_batch'
        })
    )
    
    # Fields for creating a new batch (when adding stock)
    new_batch_number = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new batch number',
            'id': 'id_new_batch_number'
        })
    )

    new_expiry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_new_expiry_date'
        })
    )

    new_manufacture_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_new_manufacture_date'
        })
    )

    class Meta:
        model = StockAdjustment
        fields = [
            'product', 'batch', 'adjustment_type', 'quantity', 'reason',
            'new_batch_number', 'new_expiry_date', 'new_manufacture_date'
        ]
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_product'
            }),
            'adjustment_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_adjustment_type'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'id': 'id_quantity'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explain the reason for this stock adjustment...',
                'id': 'id_reason'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pre-filter batches if product is already selected (for editing cases)
        if 'product' in self.data:
            try:
                product_id = int(self.data.get('product'))
                self.fields['batch'].queryset = ProductBatch.objects.filter(product_id=product_id)
            except (ValueError, TypeError):
                self.fields['batch'].queryset = ProductBatch.objects.none()
        elif self.instance.pk and self.instance.product:
            self.fields['batch'].queryset = ProductBatch.objects.filter(product=self.instance.product)
        else:
            self.fields['batch'].queryset = ProductBatch.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        adjustment_type = cleaned_data.get('adjustment_type')
        quantity = cleaned_data.get('quantity')
        batch = cleaned_data.get('batch')
        new_batch_number = cleaned_data.get('new_batch_number')
        new_expiry_date = cleaned_data.get('new_expiry_date')
        new_manufacture_date = cleaned_data.get('new_manufacture_date')

        # 🔸 Basic validations
        if not product:
            raise ValidationError("Product selection is required.")
        if not adjustment_type:
            raise ValidationError("Adjustment type selection is required.")
        if not quantity or quantity <= 0:
            raise ValidationError("Valid quantity greater than zero is required.")

        # 🔸 Removal operations must have a batch selected
        if adjustment_type in ['remove', 'expiry_writeoff', 'damage_writeoff']:
            if not batch:
                raise ValidationError({'batch': 'Please select a batch for stock removal operations.'})
            
            # Check if batch belongs to the selected product
            if batch.product != product:
                raise ValidationError({'batch': 'Selected batch does not belong to this product.'})
            
            # Ensure batch has enough stock
            if quantity > batch.current_quantity:
                raise ValidationError({
                    'quantity': f'Cannot remove {quantity} units from batch {batch.batch_number}. '
                                f'Only {batch.current_quantity} units available.'
                })

        # 🔸 Addition operation
        elif adjustment_type == 'add':
            # If new batch number provided → validate batch creation
            if new_batch_number:
                # Check expiry if product has expiry tracking
                if getattr(product, 'has_expiry', False) and not new_expiry_date:
                    raise ValidationError({
                        'new_expiry_date': 'Expiry date is required when creating a new batch for this product.'
                    })

                # Check date order
                if new_manufacture_date and new_expiry_date and new_manufacture_date >= new_expiry_date:
                    raise ValidationError({'new_expiry_date': 'Expiry date must be after manufacture date.'})

                # Ensure batch number doesn’t already exist
                if ProductBatch.objects.filter(product=product, batch_number=new_batch_number).exists():
                    raise ValidationError({'new_batch_number': f'Batch "{new_batch_number}" already exists.'})
            
            # If *no* new batch number and *no* existing batch selected — invalid
            elif not batch:
                raise ValidationError({
                    'batch': 'Select an existing batch or enter a new batch number when adding stock.'
                })

        return cleaned_data

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer_name', 'customer_phone']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'expected_date']
        widgets = {
            'supplier': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_supplier'
            }),
            'expected_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_expected_date'
            }, format='%Y-%m-%d'),
        }

    def clean_expected_date(self):
        expected_date = self.cleaned_data.get('expected_date')
        if expected_date:
            # normalize to date if datetime
            if hasattr(expected_date, "date"):
                expected_date = expected_date.date()
            if expected_date < timezone.now().date():
                raise forms.ValidationError("Expected date cannot be in the past.")
        return expected_date


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'unit_cost', 'batch_number', 'expiry_date']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select product-select',
                'onchange': 'updateProductInfo(this)'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'min': '1'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control cost-input',
                'step': '0.01',
                'min': '0'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control batch-number-input',
                'placeholder': 'Enter batch number (optional)',
                'id': 'batch_number_field'  # Added ID for easier JavaScript targeting
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control expiry-date-input',
                'type': 'date',
                'id': 'expiry_date_field'  # Added ID for easier JavaScript targeting
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make expiry date required only for products with expiry tracking
        self.fields['expiry_date'].required = False

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        expiry_date = cleaned_data.get('expiry_date')
        
        if product and product.has_expiry and not expiry_date:
            raise forms.ValidationError({
                'expiry_date': 'Expiry date is required for products with expiry tracking.'
            })
        
        return cleaned_data



class PurchaseReturnForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturn
        fields = ['purchase_order', 'reason', 'description']
        widgets = {
            'purchase_order': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_purchase_order'
            }),
            'reason': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_reason'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Provide detailed reason for the return...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter purchase orders that have items with remaining quantity > 0
        from django.db.models import OuterRef, Exists, F, Sum, Value
        from django.db.models.functions import Coalesce
        
        # Subquery to find items with remaining quantity
        items_with_remaining = PurchaseOrderItem.objects.filter(
            purchase_order=OuterRef('pk')
        ).annotate(
            returned_qty=Coalesce(Sum('returns__quantity'), Value(0)),
            remaining_qty=F('quantity') - F('returned_qty')
        ).filter(
            remaining_qty__gt=0
        )
        
        self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
            status='completed',
        ).filter(
            Exists(items_with_remaining)
        ).distinct()


class PurchaseReturnItemForm(forms.ModelForm):
    # Use CharField instead of ModelChoiceField to bypass validation
    batch_selection = forms.CharField(
        required=False,
        widget=forms.HiddenInput()  # We'll use a hidden field for the batch ID
    )

    class Meta:
        model = PurchaseReturnItem
        fields = ['purchase_order_item', 'quantity', 'unit_cost', 'reason', 'notes']
        # Remove 'batch' from fields since we're handling it separately
        widgets = {
            'purchase_order_item': forms.Select(attrs={
                'class': 'form-select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1000'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Additional notes about this return...'
            }),
        }

    def __init__(self, *args, **kwargs):
        purchase_order = kwargs.pop('purchase_order', None)
        super().__init__(*args, **kwargs)
        
        if purchase_order:
            # Get all purchase order items for this order
            all_items = PurchaseOrderItem.objects.filter(purchase_order=purchase_order)
            
            # Filter items that have remaining quantity (quantity > returned_quantity)
            valid_items = []
            for item in all_items:
                if item.remaining_quantity > 0:
                    valid_items.append(item.id)
            
            # Filter the queryset to only valid items
            self.fields['purchase_order_item'].queryset = PurchaseOrderItem.objects.filter(
                id__in=valid_items
            )

    def clean(self):
        cleaned_data = super().clean()
        purchase_order_item = cleaned_data.get('purchase_order_item')
        quantity = cleaned_data.get('quantity')
        batch_id = cleaned_data.get('batch_selection')

        if purchase_order_item and quantity:
            # Validate quantity doesn't exceed remaining quantity
            if quantity > purchase_order_item.remaining_quantity:
                raise forms.ValidationError({
                    'quantity': f'Cannot return more than available quantity ({purchase_order_item.remaining_quantity})'
                })

            # Validate batch if provided
            if batch_id and batch_id != '':
                try:
                    batch = ProductBatch.objects.get(id=batch_id)
                    # Check if batch belongs to the purchase order item
                    if batch.purchase_order_item != purchase_order_item:
                        raise forms.ValidationError('Selected batch does not belong to the chosen product.')
                    
                    # Validate batch quantity
                    if quantity > batch.current_quantity:
                        raise forms.ValidationError({
                            'quantity': f'Cannot return more than available batch quantity ({batch.current_quantity})'
                        })
                    
                    # Store the valid batch instance for later use
                    cleaned_data['batch'] = batch
                    
                except ProductBatch.DoesNotExist:
                    raise forms.ValidationError('Selected batch does not exist.')
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set the batch from the cleaned data if it exists
        batch = self.cleaned_data.get('batch')
        if batch:
            instance.batch = batch
        
        if commit:
            instance.save()
        
        return instance
    
class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=UserProfile.USER_ROLES, required=True)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    is_system_admin = forms.BooleanField(
        required=False,
        help_text="User can access Django admin and manage other users"
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role', 'phone', 
                 'address', 'is_system_admin', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make password fields required for new users
        self.fields['password1'].required = True
        self.fields['password2'].required = True
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

class CustomUserChangeForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.USER_ROLES, required=True)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    is_system_admin = forms.BooleanField(
        required=False,
        help_text="User can access Django admin and manage other users"
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 
                 'address', 'is_system_admin', 'is_active')
    

class SupplierBillForm(forms.ModelForm):
    class Meta:
        model = SupplierBill
        fields = ['purchase_order', 'supplier', 'bill_date', 'due_date', 'total_amount', 'notes']
        widgets = {
            'bill_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_date', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Enter payment amount'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional reference number'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional payment notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.bill = kwargs.pop('bill', None)
        super().__init__(*args, **kwargs)
        
        # Set initial payment date to today if not provided
        if not self.instance.pk and 'payment_date' not in self.data:
            self.fields['payment_date'].initial = timezone.now().date()
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than zero.")
        
        # If we have a bill instance, validate against due amount
        if self.bill and amount > self.bill.due_amount:
            raise forms.ValidationError(
                f"Payment amount cannot exceed due amount (৳{self.bill.due_amount:.2f})."
            )
        
        return amount
    
    def clean_payment_date(self):
        payment_date = self.cleaned_data.get('payment_date')
        if payment_date:
            # Ensure both are date objects for comparison
            today = timezone.now().date()
            
            # If payment_date is a datetime, extract the date part
            if hasattr(payment_date, 'date'):
                payment_date = payment_date.date()
            
            if payment_date > today:
                raise forms.ValidationError("Payment date cannot be in the future.")
        
        return payment_date
    


class ExpiryReportFilterForm(forms.Form):
    DATE_RANGE_CHOICES = [
        ('7', 'Next 7 Days'),
        ('15', 'Next 15 Days'),
        ('30', 'Next 30 Days'),
        ('60', 'Next 60 Days'),
        ('90', 'Next 90 Days'),
        ('custom', 'Custom Range'),
    ]
    
    date_range = forms.ChoiceField(
        choices=DATE_RANGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    include_expired = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),  # Now Category is imported
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get('date_range')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if date_range == 'custom' and (not start_date or not end_date):
            raise forms.ValidationError('Both start date and end date are required for custom range.')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('Start date cannot be after end date.')
        
        return cleaned_data
    


class BatchCreationForm(forms.Form):
    def __init__(self, purchase_order, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.purchase_order = purchase_order
        
        for item in purchase_order.items.all():
            product = item.product
            
            # Batch number field
            self.fields[f'batch_number_{item.id}'] = forms.CharField(
                label=f'Batch Number for {product.name}',
                initial=item.batch_number or f"BATCH-{timezone.now().strftime('%Y%m%d')}-{item.id}",
                required=True,
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
            
            # Expiry date field (only for products with expiry)
            if product.has_expiry:
                self.fields[f'expiry_date_{item.id}'] = forms.DateField(
                    label=f'Expiry Date for {product.name}',
                    required=True,
                    widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    initial=timezone.now().date() + timedelta(days=365)  # Default 1 year
                )
            else:
                self.fields[f'expiry_date_{item.id}'] = forms.DateField(
                    label=f'Expiry Date for {product.name}',
                    required=False,
                    widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    initial=None
                )

    def save_batches(self):
        batches = []
        for item in self.purchase_order.items.all():
            batch_number = self.cleaned_data[f'batch_number_{item.id}']
            expiry_date = self.cleaned_data.get(f'expiry_date_{item.id}')
            
            # Only set expiry date for products that track expiry
            if not item.product.has_expiry:
                expiry_date = None
            
            batch = ProductBatch.objects.create(
                product=item.product,
                batch_number=batch_number,
                manufacture_date=timezone.now().date(),
                expiry_date=expiry_date,
                quantity=item.quantity,
                current_quantity=item.quantity,
                purchase_order_item=item
            )
            batches.append(batch)
        
        return batches
    
class SaleReturnForm(forms.ModelForm):
    class Meta:
        model = SaleReturn
        fields = ['reason', 'return_type', 'exchange_product', 'exchange_quantity', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'return_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_return_type'}),
            'exchange_product': forms.Select(attrs={'class': 'form-control', 'id': 'id_exchange_product'}),
            'exchange_quantity': forms.NumberInput(attrs={
                'class': 'form-control', 
                'id': 'id_exchange_quantity',
                'min': '1',
                'value': '1'
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add stock information to exchange product choices
        exchange_products = Product.objects.filter(current_stock__gt=0)
        choices = [('', '---------')]
        for product in exchange_products:
            choices.append((
                product.id, 
                f"{product.name} - ৳{product.selling_price} (Stock: {product.current_stock})"
            ))
        
        self.fields['exchange_product'].choices = choices
        
        # Set initial values and required status
        self.fields['exchange_product'].required = False
        self.fields['exchange_quantity'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        return_type = cleaned_data.get('return_type')
        exchange_product = cleaned_data.get('exchange_product')
        exchange_quantity = cleaned_data.get('exchange_quantity')
        
        if return_type == 'product':
            if not exchange_product:
                raise forms.ValidationError("Exchange product is required for product exchange.")
            
            if not exchange_quantity or exchange_quantity <= 0:
                raise forms.ValidationError("Valid exchange quantity is required.")
            
            # Check stock availability
            if exchange_product.current_stock < exchange_quantity:
                raise forms.ValidationError(
                    f"Insufficient stock for {exchange_product.name}. "
                    f"Available: {exchange_product.current_stock}, Requested: {exchange_quantity}"
                )
        
        return cleaned_data
class SaleReturnItemForm(forms.ModelForm):
    class Meta:
        model = SaleReturnItem
        fields = ['sale_item', 'quantity', 'reason', 'notes']
        widgets = {
            'sale_item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.sale = kwargs.pop('sale', None)
        super().__init__(*args, **kwargs)
        
        if self.sale:
            # Only show items from this sale that haven't been fully returned
            returned_items = SaleReturnItem.objects.filter(
                sale_item__sale=self.sale
            ).values('sale_item').annotate(
                total_returned=sum('quantity')
            )
            
            returned_dict = {item['sale_item']: item['total_returned'] for item in returned_items}
            
            sale_items = []
            for item in self.sale.items.all():
                returned_qty = returned_dict.get(item.id, 0)
                remaining_qty = item.quantity - returned_qty
                if remaining_qty > 0:
                    sale_items.append((item.id, f"{item.product.name} - {remaining_qty} available (Sold: {item.quantity})"))
            
            self.fields['sale_item'].choices = sale_items

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        sale_item = self.cleaned_data.get('sale_item')
        
        if sale_item and quantity:
            # Calculate remaining quantity
            total_returned = SaleReturnItem.objects.filter(
                sale_item=sale_item
            ).aggregate(total=sum('quantity'))['total'] or 0
            
            remaining_qty = sale_item.quantity - total_returned
            
            if quantity > remaining_qty:
                raise forms.ValidationError(
                    f'Cannot return more than {remaining_qty} units. '
                    f'Already returned {total_returned} of {sale_item.quantity} units.'
                )
        
        return quantity