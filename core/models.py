from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.db.models import Sum
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name
    
class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="Barcode Number")
    description = models.TextField(blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_stock = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=10)
    has_expiry = models.BooleanField(default=False)
    expiry_warning_days = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['sku']),
            models.Index(fields=['supplier']),
        ]

    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate that selling price is not less than cost price"""
        if self.selling_price < self.cost_price:
            raise ValidationError('Selling price cannot be less than cost price.')
        
        if self.barcode and len(self.barcode) < 3:
            raise ValidationError('Barcode must be at least 3 characters long.')
    
    @property
    def near_expiry_stock(self):
        """Get quantity of products nearing expiry"""
        if not self.has_expiry:
            return 0
        warning_date = timezone.now().date() + timedelta(days=self.expiry_warning_days)
        return self.batches.filter(
            expiry_date__lte=warning_date,
            expiry_date__gte=timezone.now().date()
        ).aggregate(total=Sum('current_quantity'))['total'] or 0
    
    @property
    def expired_stock(self):
        """Get quantity of expired products"""
        if not self.has_expiry:
            return 0
        return self.batches.filter(expiry_date__lt=timezone.now().date()).aggregate(
            total=Sum('current_quantity')
        )['total'] or 0
    
    @property
    def stock_status(self):
        """Get stock status for display"""
        if self.current_stock == 0:
            return 'out_of_stock'
        elif self.current_stock <= self.min_stock_level:
            return 'low_stock'
        else:
            return 'in_stock'
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return 0
    
    def generate_barcode(self):
        """Generate a unique barcode if not provided"""
        if not self.barcode:
            base_barcode = self.sku.replace('SKU-', 'BC-')
            counter = 1
            new_barcode = base_barcode
            
            while Product.objects.filter(barcode=new_barcode).exclude(pk=self.pk).exists():
                new_barcode = f"{base_barcode}-{counter}"
                counter += 1
            
            self.barcode = new_barcode
    
    @classmethod
    def find_by_barcode(cls, barcode):
        """Find product by barcode number"""
        try:
            return cls.objects.get(barcode=barcode)
        except cls.DoesNotExist:
            return None
    
    def save(self, *args, **kwargs):
        if not self.barcode and self.sku:
            self.generate_barcode()
        super().save(*args, **kwargs)

class ProductBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    quantity = models.IntegerField(help_text="Original quantity received or created in this batch")
    current_quantity = models.IntegerField(default=0, help_text="Current available quantity in this batch")
    purchase_order_item = models.ForeignKey('PurchaseOrderItem', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Batches"
        ordering = ['expiry_date']
        unique_together = ('product', 'batch_number')

    def __str__(self):
        return f"{self.product.name} - Batch: {self.batch_number}"

    def clean(self):
        """Validate batch data"""
        if self.expiry_date and self.manufacture_date:
            if self.expiry_date <= self.manufacture_date:
                raise ValidationError('Expiry date must be after manufacture date.')
        
        if self.current_quantity > self.quantity:
            raise ValidationError('Current quantity cannot exceed original quantity.')

    def save(self, *args, **kwargs):
        if self.current_quantity is None or self.current_quantity == 0:
            self.current_quantity = self.quantity
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < timezone.now().date())

    @property
    def is_near_expiry(self):
        if not self.expiry_date:
            return False
        warning_days = getattr(self.product, 'expiry_warning_days', 30)
        warning_date = timezone.now().date() + timedelta(days=warning_days)
        return self.expiry_date <= warning_date and not self.is_expired

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - timezone.now().date()).days

    @property
    def stock_value(self):
        return self.current_quantity * self.product.cost_price

    def add_stock(self, quantity):
        """Increase stock for this batch"""
        if quantity < 0:
            raise ValidationError("Cannot add negative stock.")
        self.current_quantity += quantity
        self.quantity += quantity
        self.save(update_fields=['current_quantity', 'quantity'])

    def remove_stock(self, quantity):
        """Reduce stock for this batch safely"""
        if quantity < 0:
            raise ValidationError("Cannot remove negative stock.")
        if self.current_quantity < quantity:
            raise ValidationError(f"Not enough stock in batch {self.batch_number}. Available: {self.current_quantity}")
        self.current_quantity -= quantity
        self.save(update_fields=['current_quantity'])


class PurchaseOrder(models.Model):
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Partially Returned'),
    )

    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order_date = models.DateTimeField(default=timezone.now)
    expected_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"PO-{self.po_number}"
    
    def clean(self):
        if self.expected_date <= self.order_date:
            raise ValidationError('Expected date must be after order date.')
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = self.generate_po_number()
        super().save(*args, **kwargs)
    
    def generate_po_number(self):
        """Generate PO number in format YYMMDDXXX (without PO- prefix)"""
        date_str = timezone.now().strftime('%y%m%d')  # YYMMDD format
        
        # Get the last PO number for today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_pos = PurchaseOrder.objects.filter(created_at__gte=today_start)
        
        if today_pos.exists():
            last_po = today_pos.order_by('-created_at').first()
            # Extract just the numeric part for comparison
            last_po_number = last_po.po_number
            if last_po_number.startswith(date_str):
                try:
                    last_seq = int(last_po_number[6:])  # Extract sequence after YYMMDD
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
        else:
            new_seq = 1
        
        # Format: YYMMDDXXX (9 digits total)
        po_number = f"{date_str}{new_seq:03d}"
        return po_number
    
    @property
    def returned_amount(self):
        return self.returns.aggregate(total=Sum('return_amount'))['total'] or 0
    
    @property
    def is_overdue(self):
        return self.status == 'pending' and timezone.now() > self.expected_date
    
    def create_batches(self):
        """Create batches for all items in the purchase order"""
        batches_created = []
        for item in self.items.all():
            product = item.product
            
            batch_number = item.batch_number
            if not batch_number:
                batch_number = f"BATCH-{timezone.now().strftime('%Y%m%d')}-{item.id}"
            
            batch = ProductBatch.objects.create(
                product=product,
                batch_number=batch_number,
                manufacture_date=timezone.now().date(),
                expiry_date=item.expiry_date if product.has_expiry else None,
                quantity=item.quantity,
                current_quantity=item.quantity,
                purchase_order_item=item
            )
            batches_created.append(batch)
        
        return batches_created
    
    @property
    def has_returns(self):
        return self.returns.exists()
    
    @property 
    def total_returned_amount(self):
        return self.returns.aggregate(total=Sum('return_amount'))['total'] or 0
    
    @property
    def net_amount(self):
        return self.total_amount - self.total_returned_amount
    
    @property
    def return_status(self):
        if not self.has_returns:
            return 'no_returns'
        
        completed_returns = self.returns.filter(status='completed')
        if completed_returns.exists():
            return 'has_completed_returns'
        
        pending_returns = self.returns.filter(status__in=['pending', 'approved'])
        if pending_returns.exists():
            return 'has_pending_returns'
        
        return 'no_active_returns'

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    batch_number = models.CharField(max_length=100, blank=True, verbose_name="Batch Number")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Expiry Date")

    class Meta:
        ordering = ['product__name']

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
    
    @property
    def returned_quantity(self):
        return self.returns.aggregate(total=Sum('quantity'))['total'] or 0
    
    @property
    def remaining_quantity(self):
        return self.quantity - self.returned_quantity
    
    def create_batch(self):
        """Create a batch for this purchase order item"""
        if not self.batch_number:
            self.batch_number = f"BATCH-{timezone.now().strftime('%Y%m%d')}-{self.id}"
            self.save()
        
        batch = ProductBatch.objects.create(
            product=self.product,
            batch_number=self.batch_number,
            manufacture_date=timezone.now().date(),
            expiry_date=self.expiry_date if self.product.has_expiry else None,
            quantity=self.quantity,
            current_quantity=self.quantity,
            purchase_order_item=self
        )
        return batch

class PurchaseReturn(models.Model):
    RETURN_REASONS = (
        ('expired', 'Expired Product'),
        ('damaged', 'Damaged Product'),
        ('defective', 'Defective Product'),
        ('wrong_item', 'Wrong Item Delivered'),
        ('excess_quantity', 'Excess Quantity'),
        ('quality_issue', 'Quality Issue'),
        ('other', 'Other'),
    )
    
    RETURN_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='returns')
    return_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    return_date = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=20, choices=RETURN_REASONS)
    description = models.TextField(blank=True)
    return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=RETURN_STATUS, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-return_date']

    def __str__(self):
        return f"RETURN-{self.return_number}"
    
    def save(self, *args, **kwargs):
        if not self.return_number:
            self.return_number = f"RET-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class PurchaseReturnItem(models.Model):
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name='items')
    purchase_order_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.CASCADE, related_name='returns')
    batch = models.ForeignKey(ProductBatch, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=PurchaseReturn.RETURN_REASONS)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['purchase_order_item__product__name']

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

class StockAdjustment(models.Model):
    ADJUSTMENT_TYPES = (
        ('add', 'Add Stock'),
        ('remove', 'Remove Stock'),
        ('correction', 'Stock Correction'),
        ('expiry_writeoff', 'Expiry Write-off'),
        ('damage_writeoff', 'Damage Write-off'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch = models.ForeignKey(ProductBatch, on_delete=models.CASCADE, null=True, blank=True)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    quantity = models.IntegerField()
    reason = models.TextField()
    adjusted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    adjusted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-adjusted_at']

    def __str__(self):
        return f"{self.adjustment_type} - {self.product.name}"
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError('Quantity must be positive.')
        
        if self.adjustment_type in ['remove', 'expiry_writeoff', 'damage_writeoff']:
            available_stock = self.batch.current_quantity if self.batch else self.product.current_stock
            if self.quantity > available_stock:
                raise ValidationError(f'Cannot remove more than available stock ({available_stock}).')


class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    total_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def has_due(self):
        return self.total_due > 0

    @property
    def can_make_credit_sale(self):
        return self.total_due < self.credit_limit

    def update_due_amount(self):
        """Recalculate total due from unpaid sales"""
        from django.db.models import Sum, F
        from decimal import Decimal
        
        try:
            # Calculate total due from sales where paid_amount < total_amount
            due_sales = Sale.objects.filter(
                customer=self,
                payment_status__in=['due', 'partial']
            )
            
            total_due = due_sales.aggregate(
                total_due=Sum(F('total_amount') - F('paid_amount'))
            )['total_due'] or Decimal('0')
            
            # Update the customer's total_due field
            if self.total_due != total_due:
                self.total_due = total_due
                self.save(update_fields=['total_due', 'updated_at'])
                
        except Exception as e:
            print(f"Error updating customer due amount: {e}")

    @property
    def has_due_invoices(self):
        """Check if customer has any due invoices"""
        return Sale.objects.filter(
            customer=self,
            payment_status__in=['due', 'partial']
        ).exists()

    def get_due_invoices(self):
        """Get all due invoices for this customer"""
        return Sale.objects.filter(
            customer=self,
            payment_status__in=['due', 'partial']
        ).order_by('sale_date')

    def allocate_payment(self, payment_amount, payment_method='cash', notes='', received_by=None):
        """
        Allocate payment to due invoices using FIFO method
        Returns: list of allocated payments with details
        """
        from django.db import transaction
        
        allocated_payments = []
        remaining_amount = payment_amount
        
        # Get due sales ordered by date (oldest first)
        due_sales = Sale.objects.filter(
            customer=self,
            payment_status__in=['due', 'partial']
        ).order_by('sale_date')
        
        with transaction.atomic():
            for sale in due_sales:
                if remaining_amount <= 0:
                    break
                    
                sale_due = sale.remaining_due
                payment_to_apply = min(remaining_amount, sale_due)
                
                # Record allocation
                allocated_payments.append({
                    'invoice_number': sale.invoice_number,
                    'sale_date': sale.sale_date,
                    'due_amount': float(sale_due),
                    'allocated_amount': float(payment_to_apply),
                    'remaining_due_after': float(sale_due - payment_to_apply)
                })
                
                # Update sale
                sale.paid_amount += payment_to_apply
                remaining_amount -= payment_to_apply
                
                # Update sale payment status
                if sale.paid_amount >= sale.total_amount:
                    sale.payment_status = 'paid'
                else:
                    sale.payment_status = 'partial'
                
                sale.save()
            
            # If there's any remaining amount after paying all dues, 
            # it could be treated as advance or refunded
            if remaining_amount > 0:
                allocated_payments.append({
                    'invoice_number': 'ADVANCE',
                    'sale_date': timezone.now(),
                    'due_amount': 0,
                    'allocated_amount': float(remaining_amount),
                    'remaining_due_after': 0,
                    'notes': 'Advance payment for future purchases'
                })
            
            # Create due payment record
            due_payment = DuePayment.objects.create(
                customer=self,
                amount=payment_amount,
                payment_method=payment_method,
                notes=notes,
                received_by=received_by,
                allocated_details=allocated_payments
            )
            
            # Update customer total_due
            self.update_due_amount()
        
        return allocated_payments


class Sale(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    sale_date = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    returned_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    payment_status = models.CharField(
        max_length=20, 
        choices=[('paid', 'Paid'), ('due', 'Due'), ('partial', 'Partial')],
        default='paid'
    )
    
    sold_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ['-sale_date']

    def __str__(self):
        return f"Invoice-{self.invoice_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
            
        # Link to customer if phone number exists
        if self.customer_phone and not self.customer:
            try:
                customer = Customer.objects.get(phone=self.customer_phone)
                self.customer = customer
                # Use customer's name if not set
                if not self.customer_name or self.customer_name == 'Walk-in Customer':
                    self.customer_name = customer.name
            except Customer.DoesNotExist:
                # Only create new customer if name is provided and not generic
                if self.customer_name and self.customer_name != 'Walk-in Customer':
                    customer = Customer.objects.create(
                        name=self.customer_name,
                        phone=self.customer_phone
                    )
                    self.customer = customer

        # Store old values before saving
        old_customer_id = None
        if self.pk:
            try:
                old_sale = Sale.objects.get(pk=self.pk)
                old_customer_id = old_sale.customer_id if old_sale.customer else None
            except Sale.DoesNotExist:
                pass

        # Update payment status based on paid amount
        if self.paid_amount >= self.total_amount:
            self.payment_status = 'paid'
            self.change_amount = self.paid_amount - self.total_amount
        elif self.paid_amount == 0:
            self.payment_status = 'due'
            self.change_amount = 0
        else:
            self.payment_status = 'partial'
            self.change_amount = 0

        super().save(*args, **kwargs)

        # Update customer due amounts
        try:
            # Update current customer
            if self.customer:
                self.customer.update_due_amount()

            # Update old customer if customer changed
            if old_customer_id and old_customer_id != getattr(self.customer, 'id', None):
                try:
                    old_customer = Customer.objects.get(id=old_customer_id)
                    old_customer.update_due_amount()
                except Customer.DoesNotExist:
                    pass
                    
        except Exception as e:
            print(f"Error updating customer due amounts: {e}")

    def generate_invoice_number(self):
        """Generate invoice number in format YYMMDDXXX (without INV- prefix)"""
        date_str = timezone.now().strftime('%y%m%d')  # YYMMDD format
        
        # Get the last invoice number for today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_sales = Sale.objects.filter(created_at__gte=today_start)
        
        if today_sales.exists():
            last_sale = today_sales.order_by('-created_at').first()
            # Extract just the numeric part for comparison
            last_invoice_number = last_sale.invoice_number
            if last_invoice_number.startswith(date_str):
                try:
                    last_seq = int(last_invoice_number[6:])  # Extract sequence after YYMMDD
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
        else:
            new_seq = 1
        
        # Format: YYMMDDXXX (9 digits total)
        invoice_number = f"{date_str}{new_seq:03d}"
        return invoice_number
    
    @property
    def paid(self):
        """Calculate actual amount paid by customer (paid_amount - change_amount)"""
        paid_amount = self.paid_amount
        change_amount = self.change_amount
        
        # Convert to Decimal if they are floats
        if isinstance(paid_amount, float):
            paid_amount = Decimal(str(paid_amount))
        if isinstance(change_amount, float):
            change_amount = Decimal(str(change_amount))
            
        # Calculate actual paid amount (money kept by the business)
        actual_paid = paid_amount - change_amount
        
        # Ensure it's not negative and doesn't exceed total_amount
        return max(Decimal('0'), min(actual_paid, self.total_amount))

    @property
    def remaining_due(self):
        """Get remaining due amount"""
        return max(Decimal('0'), self.total_amount - self.paid)
    
    def get_total_items(self):
        return self.items.aggregate(total_items=Sum('quantity'))['total_items'] or 0

    def get_profit(self):
        """Calculate profit for this sale"""
        total_cost = Decimal('0')
        for item in self.items.all():
            # Ensure both are Decimal for consistent arithmetic
            cost_price = item.product.cost_price
            if isinstance(cost_price, float):
                cost_price = Decimal(str(cost_price))
            total_cost += cost_price * Decimal(str(item.quantity))
        
        # Ensure net_amount is also Decimal
        net_amount = self.net_amount
        if isinstance(net_amount, float):
            net_amount = Decimal(str(net_amount))
            
        return net_amount - total_cost
    
    def get_profit_margin(self):
        """Calculate profit margin percentage"""
        profit = self.get_profit()
        net_amount = self.net_amount
        if isinstance(net_amount, float):
            net_amount = Decimal(str(net_amount))
            
        if net_amount > 0:
            return (profit / net_amount) * 100
        return Decimal('0')

    @property
    def net_amount(self):
        """Get net amount after returns"""
        # Convert both to Decimal for consistent arithmetic
        total_amount = self.total_amount
        returned_amount = self.returned_amount
        
        if isinstance(total_amount, float):
            total_amount = Decimal(str(total_amount))
        if isinstance(returned_amount, float):
            returned_amount = Decimal(str(returned_amount))
            
        return total_amount - returned_amount

    @property
    def has_returns(self):
        """Check if this sale has any returns"""
        return self.returns.exists()

    @property
    def total_returned_quantity(self):
        """Get total quantity returned"""
        total = 0
        for sale_return in self.returns.filter(status='completed'):
            for item in sale_return.items.all():
                total += item.quantity
        return total

    def profit_display(self):
        """Display profit in admin"""
        profit = self.get_profit()
        return f"${profit:.2f}" if profit else "-"
    profit_display.short_description = 'Profit'

    def paid_display(self):
        """Display paid amount in admin"""
        return f"${self.paid:.2f}"
    paid_display.short_description = 'Paid Amount'

    def get_net_cost(self):
        """Calculate total cost after accounting for returns"""
        total_cost = Decimal('0')
        for item in self.items.all():
            quantity_sold = item.quantity
            # Get returned quantity for this item
            returned_quantity = item.returns.aggregate(
                total_returned=Sum('quantity')
            )['total_returned'] or 0
            net_quantity = quantity_sold - returned_quantity
            
            if net_quantity > 0:
                cost_price = item.product.cost_price
                if isinstance(cost_price, float):
                    cost_price = Decimal(str(cost_price))
                total_cost += cost_price * Decimal(net_quantity)
        return total_cost
    
    def get_net_profit(self):
        """Calculate profit after accounting for returns and their costs"""
        net_revenue = self.net_amount
        net_cost = self.get_net_cost()
        return net_revenue - net_cost
    
    def get_net_profit_margin(self):
        """Calculate profit margin after returns"""
        net_profit = self.get_net_profit()
        net_revenue = self.net_amount
        if net_revenue > 0:
            return (net_profit / net_revenue) * 100
        return Decimal('0')
    
    @property
    def remaining_due(self):
        """Get remaining due amount"""
        return max(Decimal('0'), self.total_amount - self.paid_amount)


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch = models.ForeignKey(ProductBatch, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['product__name']

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    @property
    def cost_price(self):
        return self.product.cost_price
    
    @property
    def profit(self):
        unit_price = self.unit_price
        cost_price = self.cost_price
        
        # Ensure both are Decimal
        if isinstance(unit_price, float):
            unit_price = Decimal(str(unit_price))
        if isinstance(cost_price, float):
            cost_price = Decimal(str(cost_price))
            
        return (unit_price - cost_price) * Decimal(str(self.quantity))
    
    @property
    def returned_quantity(self):
        """Get total quantity returned for this sale item"""
        return self.returns.aggregate(total=Sum('quantity'))['total'] or 0
    
    @property
    def net_quantity(self):
        """Get net quantity after returns"""
        return self.quantity - self.returned_quantity
    
    @property
    def net_profit(self):
        """Calculate profit after accounting for returns"""
        unit_price = self.unit_price
        cost_price = self.cost_price
        
        if isinstance(unit_price, float):
            unit_price = Decimal(str(unit_price))
        if isinstance(cost_price, float):
            cost_price = Decimal(str(cost_price))
            
        return (unit_price - cost_price) * Decimal(str(self.net_quantity))

class UserProfile(models.Model):
    USER_ROLES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('sales', 'Sales Person'),
        ('purchase', 'Purchase Manager'),
        ('staff', 'Staff'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='staff')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_system_admin = models.BooleanField(default=False, 
        help_text="User can access Django admin and manage users")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    @property
    def can_access_admin(self):
        """Check if user can access Django admin"""
        return self.is_system_admin or self.user.is_superuser
    
    def has_view_permission(self, view_code):
        """Check if user has permission for a specific view"""
        if self.can_access_admin:
            return True
        
        return self.user.view_permissions.filter(
            permission__view_code=view_code
        ).exists()

class PurchaseOrderCancellation(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    cancelled_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    cancelled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-cancelled_at']

    def __str__(self):
        return f"Cancelled PO-{self.purchase_order.po_number}"

class SupplierBill(models.Model):
    BILL_STATUS = (
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('returned', 'Returned'),
        ('partially_returned', 'Partially Returned'),
    )
    
    bill_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    purchase_order = models.OneToOneField(PurchaseOrder, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    bill_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=BILL_STATUS, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-bill_date']

    def __str__(self):
        return f"BILL-{self.bill_number}"
    
    def clean(self):
        if self.due_date <= self.bill_date:
            raise ValidationError('Due date must be after bill date.')
    
    def save(self, *args, **kwargs):
        # Calculate due amount considering returns
        purchase_order = self.purchase_order
        total_returned = purchase_order.total_returned_amount
        
        # Calculate net amount after returns
        net_amount = self.total_amount - total_returned
        
        # Calculate due amount based on net amount
        self.due_amount = max(Decimal('0'), net_amount - self.paid_amount)
        
        # Update status based on returns and payments
        if total_returned > 0:
            if total_returned >= self.total_amount:
                self.status = 'returned'
                self.due_amount = Decimal('0')
            else:
                self.status = 'partially_returned'
        else:
            # Auto-update status based on payment
            if self.paid_amount >= net_amount:
                self.status = 'paid'
                self.due_amount = Decimal('0')
            elif self.paid_amount > 0:
                self.status = 'partial'
            else:
                self.status = 'pending'
                
            # Check if overdue
            if self.due_amount > 0:
                due_date = self.due_date.date() if hasattr(self.due_date, 'date') else self.due_date
                today = timezone.now().date()
                
                if due_date < today:
                    self.status = 'overdue'
            
        super().save(*args, **kwargs)
    
    @property
    def returned_amount(self):
        """Get total returned amount for this bill"""
        return self.purchase_order.total_returned_amount
    
    @property
    def net_amount(self):
        """Get net amount after returns"""
        return max(Decimal('0'), self.total_amount - self.returned_amount)
    
    @property
    def effective_due_amount(self):
        """Get the actual due amount considering returns"""
        return max(Decimal('0'), self.net_amount - self.paid_amount)
    
    @property
    def paid_percentage(self):
        """Calculate paid percentage based on net amount (after returns)"""
        if self.net_amount > 0:
            return (self.paid_amount / self.net_amount) * 100
        return 0
    
    @property
    def is_overdue(self):
        """Check if bill is overdue (due date passed and has due amount)"""
        if self.effective_due_amount <= 0:
            return False
            
        due_date = self.due_date.date() if hasattr(self.due_date, 'date') else self.due_date
        today = timezone.now().date()
        
        return due_date < today
    
    @property
    def days_overdue(self):
        """Get number of days overdue"""
        if not self.is_overdue:
            return 0
            
        due_date = self.due_date.date() if hasattr(self.due_date, 'date') else self.due_date
        today = timezone.now().date()
        return (today - due_date).days
    
    @property
    def payment_progress(self):
        """Get payment progress information"""
        return {
            'paid': float(self.paid_amount),
            'due': float(self.effective_due_amount),
            'total': float(self.net_amount),
            'percentage': float(self.paid_percentage)
        }
    
    @property
    def can_accept_payment(self):
        """Check if this bill can accept payments"""
        return (self.effective_due_amount > 0 and 
                self.status not in ['returned', 'paid'])
    
    @property
    def payment_status_display(self):
        """Get enhanced status display with overdue info"""
        display = self.get_status_display()
        if self.is_overdue:
            return f"{display} ({self.days_overdue} days overdue)"
        return display

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('digital', 'Digital Payment'),
    )
    
    bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='bank')
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment-{self.id} for BILL-{self.bill.bill_number}"
    
    def clean(self):
        if not self.bill_id:
            return
            
        if self.amount <= 0:
            raise ValidationError('Payment amount must be positive.')
        
        try:
            bill = SupplierBill.objects.get(id=self.bill_id)
            # Use effective due amount for validation
            if self.amount > bill.effective_due_amount:
                raise ValidationError(f'Payment amount cannot exceed due amount (৳{bill.effective_due_amount}).')
        except SupplierBill.DoesNotExist:
            raise ValidationError('Associated bill does not exist.')

    def save(self, *args, **kwargs):
        # Only validate if we have a bill
        if self.bill_id:
            self.full_clean()
        super().save(*args, **kwargs)
        
        # Update bill payment status
        self.update_bill_payment_status()
    
    def update_bill_payment_status(self):
        """Update the bill's payment status after saving payment"""
        try:
            bill = self.bill
            total_paid = sum(payment.amount for payment in bill.payments.all())
            bill.paid_amount = total_paid
            bill.save()
        except SupplierBill.DoesNotExist:
            # Bill was deleted, nothing to update
            pass

class StockMovement(models.Model):
    MOVEMENT_TYPES = (
        ('purchase_in', 'Purchase In'),
        ('sale_out', 'Sale Out'),
        ('return_in', 'Return In'),
        ('return_out', 'Return Out'),
        ('adjustment_in', 'Adjustment In'),
        ('adjustment_out', 'Adjustment Out'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    batch_number = models.CharField(max_length=100, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    movement_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.movement_type} - {self.product.name}"

class SaleReturn(models.Model):
    RETURN_REASONS = [
        ('defective', 'Defective Product'),
        ('wrong_item', 'Wrong Item Delivered'),
        ('changed_mind', 'Changed Mind'),
        ('quality_issue', 'Quality Issue'),
        ('expired', 'Expired Product'),
        ('damaged', 'Damaged in Transit'),
        ('other', 'Other'),
    ]
    
    RETURN_TYPES = [
        ('money', 'Money Refund'),
        ('product', 'Product Exchange'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    return_number = models.CharField(max_length=20, unique=True)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    return_date = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=20, choices=RETURN_REASONS)
    return_type = models.CharField(max_length=10, choices=RETURN_TYPES)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Positive: customer gets refund, Negative: customer pays extra"
    )
    exchange_product = models.ForeignKey(
        'Product', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='exchange_returns'
    )
    exchange_quantity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_returns', null=True,blank=True)
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='processed_returns'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-return_date']

    def __str__(self):
        return f"Return {self.return_number} for {self.sale.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.return_number:
            self.return_number = self.generate_return_number()
        super().save(*args, **kwargs)

    def generate_return_number(self):
        prefix = "SR"
        date_str = timezone.now().strftime('%Y%m%d')
        last_return = SaleReturn.objects.filter(
            return_number__startswith=f"{prefix}{date_str}"
        ).order_by('-return_number').first()
        
        if last_return:
            last_num = int(last_return.return_number[-4:])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"{prefix}{date_str}{new_num:04d}"

    def get_total_return_value(self):
        """Calculate total value of returned items"""
        return sum(item.total_price for item in self.items.all())

    def get_exchange_product_value(self):
        """Calculate total value of exchange product"""
        if self.exchange_product and self.exchange_quantity > 0:
            return self.exchange_product.selling_price * self.exchange_quantity
        return Decimal('0')

    def calculate_balance_amount(self):
        """Calculate the balance amount (positive = refund, negative = payment due)"""
        return_value = self.get_total_return_value()
        exchange_value = self.get_exchange_product_value()
        return return_value - exchange_value

    @property
    def can_process_exchange(self):
        """Check if exchange can be processed (sufficient stock)"""
        if self.return_type == 'product' and self.exchange_product:
            return self.exchange_product.current_stock >= self.exchange_quantity
        return True

    def get_status_display_html(self):
        status_colors = {
            'pending': 'warning',
            'approved': 'info',
            'completed': 'success',
            'rejected': 'danger',
        }
        color = status_colors.get(self.status, 'secondary')
        return f'<span class="badge bg-{color}">{self.get_status_display()}</span>'
    
    @property
    def total_return_quantity(self):
        """Calculate total quantity of returned items"""
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0

    def get_total_return_quantity(self):
        """Admin-compatible method for total return quantity"""
        return self.total_return_quantity
    get_total_return_quantity.short_description = 'Total Qty'

    @property
    def exchange_product_value(self):
        """Calculate total value of exchange product"""
        if self.exchange_product and self.exchange_quantity > 0:
            return self.exchange_product.selling_price * self.exchange_quantity
        return Decimal('0')


class SaleReturnItem(models.Model):
    sale_return = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name='items')
    sale_item = models.ForeignKey(SaleItem, on_delete=models.CASCADE, related_name='returns')
    batch = models.ForeignKey(ProductBatch, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=SaleReturn.RETURN_REASONS)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['sale_item__product__name']

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    @property
    def returned_cost(self):
        cost_price = self.sale_item.product.cost_price
        if isinstance(cost_price, float):
            cost_price = Decimal(str(cost_price))
        return self.quantity * cost_price

class DuePayment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('digital', 'Digital Payment'),
    )
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='due_payments')
    payment_date = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    allocated_details = models.JSONField(default=dict, blank=True, null=True)
    
    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Due Payment-{self.id} for {self.customer.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update customer due amount
        try:
            customer = Customer.objects.get(id=self.customer.id)
            customer.update_due_amount()
        except Exception as e:
            print(f"Error updating customer due amount in DuePayment.save(): {e}")

    def delete(self, *args, **kwargs):
        customer = self.customer
        super().delete(*args, **kwargs)
        # Update customer due amount after deletion
        try:
            customer.refresh_from_db()
            customer.update_due_amount()
        except Exception as e:
            print(f"Error updating customer due amount in DuePayment.delete(): {e}")

    @property
    def allocated_details_display(self):
        """Display allocated details in a readable format"""
        if not self.allocated_details:
            return "No allocation details"
        
        try:
            details = []
            for allocation in self.allocated_details:
                invoice_info = f"Invoice {allocation.get('invoice_number', 'N/A')}: "
                invoice_info += f"৳{allocation.get('allocated_amount', 0):.2f}"
                details.append(invoice_info)
            
            return "; ".join(details)
        except (TypeError, KeyError):
            return "Error parsing allocation details"

class ViewPermission(models.Model):
    """Model to define which views users can access"""
    VIEW_CHOICES = (
        # Dashboard
        ('dashboard', 'Dashboard'),
        
        # Products
        ('product_list', 'Product List'),
        ('product_create', 'Create Product'),
        ('product_edit', 'Edit Product'),
        ('product_delete', 'Delete Product'),
        
        # Stock
        ('stock_adjustment', 'Stock Adjustment'),
        ('stock_report', 'Stock Report'),
        ('expiry_report', 'Expiry Report'),
        ('batch_management', 'Batch Management'),
        
        # Sales
        ('pos_sale', 'POS Sale'),
        ('daily_sale_report', 'Daily Sales Report'),
        ('profit_report', 'Profit Report'),
        ('sale_return_list', 'Sale Returns'),
        
        # Purchases
        ('purchase_order_create', 'Create Purchase Order'),
        ('purchase_report', 'Purchase Report'),
        ('purchase_return_list', 'Purchase Returns'),
        
        # Supplier & Billing
        ('supplier_bills', 'Supplier Bills'),
        ('bill_dashboard', 'Bill Dashboard'),
        
        # Customers
        ('customer_management', 'Customer Management'),
        ('customer_due_report', 'Customer Due Report'),
        ('due_collection_report', 'Due Collection Report'),
        
        # Reports
        ('generate_sales_report', 'Generate Sales Report'),
        
        # User Management (only for admin)
        ('user_management', 'User Management'),
    )
    
    name = models.CharField(max_length=100, unique=True)
    view_code = models.CharField(max_length=50, choices=VIEW_CHOICES, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'View Permission'
        verbose_name_plural = 'View Permissions'
    
    def __str__(self):
        return self.name

class UserViewPermission(models.Model):
    """Model to assign view permissions to users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='view_permissions')
    permission = models.ForeignKey(ViewPermission, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_permissions')
    
    class Meta:
        unique_together = ['user', 'permission']
        ordering = ['permission__name']
        verbose_name = 'User View Permission'
        verbose_name_plural = 'User View Permissions'
    
    def __str__(self):
        return f"{self.user.username} - {self.permission.name}"

# Signals
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=PurchaseOrder)
def create_supplier_bill(sender, instance, created, **kwargs):
    if instance.status == 'completed':
        if not SupplierBill.objects.filter(purchase_order=instance).exists():
            SupplierBill.objects.create(
                purchase_order=instance,
                supplier=instance.supplier,
                total_amount=instance.total_amount,
                due_date=instance.expected_date + timedelta(days=30),
                created_by=instance.created_by
            )

@receiver(post_save, sender=PurchaseOrderItem)
def create_product_batches(sender, instance, created, **kwargs):
    if created and instance.purchase_order.status == 'completed':
        product = instance.product
        batch_number = instance.batch_number or f"BATCH-{uuid.uuid4().hex[:8].upper()}"
        
        ProductBatch.objects.create(
            product=product,
            batch_number=batch_number,
            expiry_date=instance.expiry_date if product.has_expiry else None,
            quantity=instance.quantity,
            current_quantity=instance.quantity,
            purchase_order_item=instance
        )