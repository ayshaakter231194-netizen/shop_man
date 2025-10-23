from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F, Avg, Max, Case, When, FloatField, Value, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from datetime import date
from .models import *
from .forms import *
from django.db.models.functions import Coalesce
from decimal import Decimal, InvalidOperation
from .pdf_utils import generate_sales_report_pdf, create_pdf_response
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .decorators import admin_required, view_permission_required



def role_required(role):
    return user_passes_test(lambda u: hasattr(u, 'userprofile') and getattr(u.userprofile, 'role', None) == role)

@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # FIXED: Use total_amount instead of net_amount for database queries
    daily_stats = Sale.objects.filter(sale_date__date=today).aggregate(
        total_sales=Sum('total_amount'),  # Use total_amount, not net_amount
        total_transactions=Count('id')
    )
    
    # Calculate net sales manually
    daily_net_sales = Sale.objects.filter(sale_date__date=today).aggregate(
        net_sales=Sum(F('total_amount') - F('returned_amount'))
    )['net_sales'] or 0

    total_products = Product.objects.count()

    low_stock_products = Product.objects.filter(current_stock__lte=F('min_stock_level'))
    low_stock_count = low_stock_products.count()

    # Recent sales (last 10)
    recent_sales = Sale.objects.select_related('sold_by').prefetch_related('items__product').all().order_by('-sale_date')[:10]

    # Supplier bill statistics
    bill_stats = SupplierBill.objects.aggregate(
        total_bills=Count('id'),
        total_amount=Sum('total_amount'),
        total_paid=Sum('paid_amount'),
        total_due=Sum('due_amount')
    )
    
    # Overdue bills
    overdue_bills = SupplierBill.objects.filter(
        status='overdue', 
        due_date__lt=today
    )
    overdue_amount = overdue_bills.aggregate(Sum('due_amount'))['due_amount__sum'] or 0

    context = {
        'daily_sales': daily_stats['total_sales'] or 0,
        'daily_net_sales': daily_net_sales,  # Add net sales
        'total_transactions': daily_stats['total_transactions'] or 0,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'low_stock_count': low_stock_count,
        'recent_sales': recent_sales,
        'total_bills': bill_stats['total_bills'] or 0,
        'total_bill_amount': bill_stats['total_amount'] or 0,
        'total_paid': bill_stats['total_paid'] or 0,
        'total_due': bill_stats['total_due'] or 0,
        'overdue_bills_count': overdue_bills.count(),
        'overdue_amount': overdue_amount,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
@view_permission_required('product_list')
def product_list(request):
    products = Product.objects.all().select_related('category', 'supplier')  # Added supplier
    categories = Category.objects.all()

    # Search - now includes barcode
    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(barcode__icontains=search_query) |  # NEW: Search by barcode
            Q(description__icontains=search_query)
        )

    # Category filter
    category_filter = request.GET.get('category')
    if category_filter:
        products = products.filter(category_id=category_filter)

    # Supplier filter (NEW)
    supplier_filter = request.GET.get('supplier')
    if supplier_filter:
        products = products.filter(supplier_id=supplier_filter)

    # Stock status filter
    stock_status = request.GET.get('stock_status', '')
    if stock_status == 'low':
        products = products.filter(current_stock__lte=F('min_stock_level'), current_stock__gt=0)
    elif stock_status == 'out':
        products = products.filter(current_stock=0)
    elif stock_status == 'available':
        products = products.filter(current_stock__gt=0)

    # Stock statistics
    total_products = products.count()
    in_stock_count = products.filter(current_stock__gt=F('min_stock_level')).count()
    low_stock_count = products.filter(current_stock__lte=F('min_stock_level'), current_stock__gt=0).count()
    out_of_stock_count = products.filter(current_stock=0).count()

    # Get suppliers for filter dropdown
    suppliers = Supplier.objects.all()

    # Pagination
    paginator = Paginator(products.order_by('name'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': categories,
        'suppliers': suppliers,  # NEW
        'total_products': total_products,
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    return render(request, 'core/product_list.html', context)

@login_required
@view_permission_required('product_create')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                
                # Handle the custom category and supplier fields
                category_id = request.POST.get('category')
                supplier_id = request.POST.get('supplier')
                
                # Validate and set category (required)
                if category_id:
                    try:
                        product.category = Category.objects.get(id=category_id)
                    except Category.DoesNotExist:
                        messages.error(request, 'Selected category does not exist')
                        return render(request, 'core/product_form.html', {'form': form})
                else:
                    messages.error(request, 'Category is required')
                    return render(request, 'core/product_form.html', {'form': form})
                
                # Set supplier (optional)
                if supplier_id:
                    try:
                        product.supplier = Supplier.objects.get(id=supplier_id)
                    except Supplier.DoesNotExist:
                        # Supplier not found, but it's optional so we can continue
                        product.supplier = None
                
                # Handle barcode generation if not provided
                if not product.barcode and product.sku:
                    product.generate_barcode()
                
                product.save()
                messages.success(request, 'Product created successfully')
                return redirect('product_list')
                
            except Exception as e:
                messages.error(request, f'Error creating product: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
    
    return render(request, 'core/product_form.html', {'form': form})

@login_required
@view_permission_required('product_edit')
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                
                # Handle the custom category and supplier fields
                category_id = request.POST.get('category')
                supplier_id = request.POST.get('supplier')
                
                # Validate and set category (required)
                if category_id:
                    try:
                        product.category = Category.objects.get(id=category_id)
                    except Category.DoesNotExist:
                        messages.error(request, 'Selected category does not exist')
                        return render(request, 'core/product_form.html', {'form': form})
                else:
                    messages.error(request, 'Category is required')
                    return render(request, 'core/product_form.html', {'form': form})
                
                # Set supplier (optional)
                if supplier_id:
                    try:
                        product.supplier = Supplier.objects.get(id=supplier_id)
                    except Supplier.DoesNotExist:
                        # Supplier not found, but it's optional so we can continue
                        product.supplier = None
                else:
                    product.supplier = None
                
                # Handle barcode generation if not provided
                if not product.barcode and product.sku:
                    product.generate_barcode()
                
                product.save()
                messages.success(request, 'Product updated successfully')
                return redirect('product_list')
                
            except Exception as e:
                messages.error(request, f'Error updating product: {str(e)}')
                return render(request, 'core/product_form.html', {'form': form})
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'core/product_form.html', {'form': form})

@login_required
@view_permission_required('stock_adjustment')
def stock_adjustment(request):
    products = Product.objects.prefetch_related('batches').all()
    recent_adjustments = StockAdjustment.objects.select_related('adjusted_by', 'product').order_by('-adjusted_at')[:5]

    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.adjusted_by = request.user
            product = adjustment.product
            adjustment_type = adjustment.adjustment_type
            quantity = adjustment.quantity

            try:
                with transaction.atomic():
                    # ✅ ADD STOCK
                    if adjustment_type == 'add':
                        new_batch_number = form.cleaned_data.get('new_batch_number')
                        batch = adjustment.batch

                        # If user provided a new batch number — create new batch
                        if new_batch_number:
                            batch = ProductBatch.objects.create(
                                product=product,
                                batch_number=new_batch_number,
                                manufacture_date=form.cleaned_data.get('new_manufacture_date'),
                                expiry_date=form.cleaned_data.get('new_expiry_date'),
                                quantity=quantity,
                                current_quantity=quantity,
                            )
                        # If user selected an existing batch — add to it
                        elif batch:
                            batch.current_quantity += quantity
                            batch.quantity += quantity
                            batch.save()
                        else:
                            raise ValidationError("Select a batch or provide a new batch number to add stock.")

                        # Update total product stock
                        product.current_stock += quantity
                        product.save()
                        adjustment.batch = batch

                    # ✅ REMOVE STOCK
                    elif adjustment_type in ['remove', 'expiry_writeoff', 'damage_writeoff']:
                        batch = adjustment.batch
                        if not batch:
                            raise ValidationError("You must select a batch to remove stock from.")

                        if batch.current_quantity < quantity:
                            raise ValidationError(f"Not enough stock in batch {batch.batch_number}.")

                        batch.current_quantity -= quantity
                        batch.save()

                        product.current_stock -= quantity
                        product.save()

                    # ✅ STOCK CORRECTION
                    elif adjustment_type == 'correction':
                        product.current_stock = quantity
                        product.save()

                    # ✅ Save adjustment record
                    adjustment.save()
                    messages.success(request, f"Stock adjusted successfully for {product.name} (New stock: {product.current_stock}).")
                    return redirect('stock_adjustment')

            except Exception as e:
                messages.error(request, f"Error adjusting stock: {e}")

    else:
        form = StockAdjustmentForm()

    return render(request, 'core/stock_adjustment.html', {
        'form': form,
        'products': products,
        'recent_adjustments': recent_adjustments,
    })

@login_required
def pos_sale(request):
    products = Product.objects.filter(current_stock__gt=0).select_related('category')
    categories = Category.objects.all()

    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            sale_data = data.get('sale_data', [])
            if not sale_data:
                return JsonResponse({'success': False, 'error': 'No sale_data provided'})

            customer_name = data.get('customer_name', 'Walk-in Customer')
            customer_phone = data.get('customer_phone', '')
            customer_id = data.get('customer_id')  # Get customer_id from request
            
            subtotal = Decimal(data.get('subtotal', 0))
            discount_amount = Decimal(data.get('discount_amount', 0))
            tax_amount = Decimal(data.get('tax_amount', 0))
            total_amount = Decimal(data.get('total_amount', 0))
            paid_amount = Decimal(data.get('paid_amount', 0))
            change_amount = Decimal(data.get('change_amount', 0))
            tax_percentage = Decimal(data.get('tax_percentage', 0))
            discount_percentage = Decimal(data.get('discount_percentage', 0))

            with transaction.atomic():
                # Get customer instance if customer_id is provided
                customer = None
                if customer_id:
                    try:
                        customer = Customer.objects.get(id=customer_id)
                        # Use customer's actual name and phone
                        customer_name = customer.name
                        customer_phone = customer.phone
                    except Customer.DoesNotExist:
                        # Customer not found, proceed without customer link
                        pass

                # CRITICAL FIX: Validate due sale for unregistered customers
                if paid_amount < total_amount and not customer:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Due sales are only allowed for registered customers. Please register customer first.'
                    })

                # Create sale record with customer
                sale = Sale.objects.create(
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    customer=customer,  # Link the customer (can be None for walk-in)
                    subtotal=subtotal,
                    discount_amount=discount_amount,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    paid_amount=paid_amount,
                    change_amount=change_amount,
                    tax_percentage=tax_percentage,
                    discount_percentage=discount_percentage,
                    sold_by=request.user,
                    sale_date=timezone.now()
                )

                # Payment status is automatically handled in Sale.save() method
                # No need to manually set it here

                # Preload products used in this sale to avoid N+1
                product_ids = [int(item['product_id']) for item in sale_data if 'product_id' in item]
                products_map = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

                for item in sale_data:
                    product = products_map.get(int(item['product_id']))
                    if not product:
                        raise ValueError(f"Product with id {item.get('product_id')} not found")

                    quantity = int(item.get('quantity', 0))
                    unit_price = Decimal(item.get('price', 0))
                    total_price = quantity * unit_price

                    # Create sale item
                    sale_item = SaleItem(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price
                    )

                    # Handle batch tracking for products with expiry
                    if product.has_expiry:
                        # Find the oldest batch that has stock (FIFO)
                        batch = ProductBatch.objects.filter(
                            product=product,
                            current_quantity__gt=0
                        ).exclude(
                            expiry_date__lt=timezone.now().date()  # Exclude expired
                        ).order_by('expiry_date').first()
                        
                        if batch:
                            # Use the minimum of requested quantity and available batch quantity
                            batch_quantity = min(quantity, batch.current_quantity)
                            sale_item.batch = batch
                            batch.current_quantity -= batch_quantity
                            batch.save()

                    sale_item.save()

                    # Update product stock
                    product.current_stock = F('current_stock') - quantity
                    product.save()

                return JsonResponse({
                    'success': True, 
                    'invoice_number': sale.invoice_number, 
                    'sale_id': sale.id,
                    'payment_status': sale.payment_status
                })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    context = {'products': products, 'categories': categories}
    return render(request, 'core/pos_sale.html', context)

@login_required
def generate_invoice(request, invoice_number):
    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), invoice_number=invoice_number)

    total_items = sale.items.aggregate(total_items=Sum('quantity'))['total_items'] or 0

    # Calculate profit for this sale
    total_cost = sum([item.quantity * item.product.cost_price for item in sale.items.all()])
    profit = (sale.total_amount or 0) - total_cost

    context = {
        'sale': sale,
        'total_items': total_items,
        'profit': profit,
    }
    return render(request, 'core/invoice.html', context)

@login_required
@view_permission_required('purchase_order_create')
def purchase_order_create(request):
    products = Product.objects.all().select_related('category')
    suppliers = Supplier.objects.all()

    # Quick-add low stock
    quick_products = Product.objects.filter(current_stock__lte=F('min_stock_level'))[:5]

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            purchase_order = form.save(commit=False)
            purchase_order.created_by = request.user
            
            # Set status to draft if draft button was clicked
            if request.POST.get('draft'):
                purchase_order.status = 'draft'
            
            purchase_order.save()

            # Process items with batch numbers and expiry dates
            items_data = []
            i = 0
            while f'items[{i}].product' in request.POST:
                product_id = request.POST.get(f'items[{i}].product')
                quantity = request.POST.get(f'items[{i}].quantity')
                unit_cost = request.POST.get(f'items[{i}].unit_cost')
                batch_number = request.POST.get(f'items[{i}].batch_number', '')
                expiry_date = request.POST.get(f'items[{i}].expiry_date', '')

                if product_id and quantity and unit_cost:
                    items_data.append({
                        'product_id': product_id,
                        'quantity': int(quantity),
                        'unit_cost': float(unit_cost),
                        'batch_number': batch_number,
                        'expiry_date': expiry_date if expiry_date else None,
                    })
                i += 1

            if not items_data:
                messages.error(request, 'Please add at least one item to the purchase order.')
                purchase_order.delete()  # Delete the empty order
                context = {
                    'form': form,
                    'products': products,
                    'suppliers': suppliers,
                    'quick_products': quick_products,
                }
                return render(request, 'core/purchase_order_form.html', context)

            total_amount = 0
            for item_data in items_data:
                product = Product.objects.get(id=item_data['product_id'])
                total_cost = item_data['quantity'] * item_data['unit_cost']
                
                # Convert expiry_date string to date object if provided
                expiry_date = None
                if item_data['expiry_date']:
                    try:
                        expiry_date = datetime.strptime(item_data['expiry_date'], '%Y-%m-%d').date()
                    except ValueError:
                        expiry_date = None
                
                item = PurchaseOrderItem.objects.create(
                    purchase_order=purchase_order,
                    product=product,
                    quantity=item_data['quantity'],
                    unit_cost=item_data['unit_cost'],
                    total_cost=total_cost,
                    batch_number=item_data['batch_number'],
                    expiry_date=expiry_date
                )
                total_amount += total_cost

            purchase_order.total_amount = total_amount
            purchase_order.save()

            if request.POST.get('draft'):
                messages.success(request, f'Purchase order {purchase_order.po_number} saved as draft successfully!')
            else:
                messages.success(request, f'Purchase order {purchase_order.po_number} created successfully!')
            
            return redirect('purchase_report')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseOrderForm()

    context = {
        'form': form,
        'products': products,
        'suppliers': suppliers,
        'quick_products': quick_products,
    }
    return render(request, 'core/purchase_order_form.html', context)

@login_required
@view_permission_required('daily_sale_report')
def daily_sale_report(request):
    selected_date = request.GET.get('date')
    if selected_date:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    else:
        selected_date = timezone.now().date()

    sales = Sale.objects.filter(sale_date__date=selected_date).select_related('sold_by').prefetch_related('items__product')

    sales_person = request.GET.get('sales_person')
    if sales_person:
        sales = sales.filter(sold_by_id=sales_person)

    # FIXED: Use database fields for calculations
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_returns = sales.aggregate(total=Sum('returned_amount'))['total'] or 0
    net_sales = total_sales - total_returns
    
    total_items_sold = SaleItem.objects.filter(sale__in=sales).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Calculate returned items
    total_items_returned = 0
    for sale in sales:
        total_items_returned += sale.total_returned_quantity
    
    net_items_sold = total_items_sold - total_items_returned
    average_sale = (net_sales / sales.count()) if sales.exists() else 0

    subtotal_total = sales.aggregate(total=Sum('subtotal'))['total'] or 0
    tax_total = sales.aggregate(total=Sum('tax_amount'))['total'] or 0
    discount_total = sales.aggregate(total=Sum('discount_amount'))['total'] or 0

    sales_users = User.objects.filter(sale__isnull=False).distinct()

    top_products = SaleItem.objects.filter(sale__sale_date__date=selected_date).values('product__name', 'product__sku').annotate(
        total_quantity=Sum('quantity'),
        total_amount=Sum('total_price')
    ).order_by('-total_quantity')[:5]

    last_7_days = []
    last_7_days_data = []
    for i in range(6, -1, -1):
        date = selected_date - timedelta(days=i)
        # FIXED: Use database fields for daily sales data
        day_sales = Sale.objects.filter(sale_date__date=date).aggregate(
            total=Sum('total_amount') - Sum('returned_amount')
        )['total'] or 0
        last_7_days.append(date.strftime('%b %d'))
        last_7_days_data.append(float(day_sales))

    hourly_sales = []
    hourly_labels = []
    for hour in range(9, 21):
        hour_sales = Sale.objects.filter(
            sale_date__date=selected_date,
            sale_date__hour=hour
        ).aggregate(
            total=Sum('total_amount') - Sum('returned_amount')
        )['total'] or 0
        hourly_sales.append(float(hour_sales))
        hourly_labels.append(f"{hour:02d}:00")

    all_products = Product.objects.all().order_by('name')
    all_categories = Category.objects.all().order_by('name')
    sales_users = User.objects.filter(sale__isnull=False).distinct()
    

    context = {
        'sales': sales,
        'selected_date': selected_date,
        'total_sales': total_sales,  # Gross sales
        'net_sales': net_sales,      # Net sales after returns
        'total_returns': total_returns,  # Total returns
        'total_items_sold': total_items_sold,
        'total_items_returned': total_items_returned,
        'net_items_sold': net_items_sold,
        'average_sale': average_sale,
        'subtotal_total': subtotal_total,
        'tax_total': tax_total,
        'discount_total': discount_total,
        'sales_users': sales_users,
        'top_products': top_products,
        'today': timezone.now().date(),
        'yesterday': timezone.now().date() - timedelta(days=1),
        'week_ago': timezone.now().date() - timedelta(days=7),
        'month_start': timezone.now().replace(day=1).date(),
        'last_7_days_labels': last_7_days,
        'last_7_days_data': last_7_days_data,
        'hourly_sales': hourly_sales,
        'hourly_labels': hourly_labels,
        'hourly_data': hourly_sales,
        'all_products': all_products,
        'all_categories': all_categories,
        'sales_users': sales_users,
    }
    return render(request, 'core/daily_sale_report.html', context)

@login_required
@view_permission_required('stock_report')
def stock_report(request):
    products = Product.objects.select_related('category').all()
    categories = Category.objects.all()

    category_filter = request.GET.get('category')
    if category_filter:
        products = products.filter(category_id=category_filter)

    stock_status = request.GET.get('stock_status')
    if stock_status == 'in_stock':
        products = products.filter(current_stock__gt=F('min_stock_level'))
    elif stock_status == 'low_stock':
        products = products.filter(current_stock__lte=F('min_stock_level'), current_stock__gt=0)
    elif stock_status == 'out_of_stock':
        products = products.filter(current_stock=0)

    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Calculate stock value
    for product in products:
        product.stock_value = (product.current_stock or 0) * (product.cost_price or 0)

    total_products = products.count()
    in_stock_count = products.filter(current_stock__gt=F('min_stock_level')).count()
    low_stock_count = products.filter(current_stock__lte=F('min_stock_level'), current_stock__gt=0).count()
    out_of_stock_count = products.filter(current_stock=0).count()
    total_stock_value = sum(product.stock_value for product in products)
    average_stock = products.aggregate(avg=Avg('current_stock'))['avg'] or 0

    low_stock_products = products.filter(current_stock__lte=F('min_stock_level'), current_stock__gt=0)[:5]
    out_of_stock_products = products.filter(current_stock=0)[:5]

    category_distribution = Category.objects.annotate(product_count=Count('product')).values('name', 'product_count')

    category_labels = [cat['name'] for cat in category_distribution]
    category_data = [cat['product_count'] for cat in category_distribution]

    paginator = Paginator(products.order_by('name'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': categories,
        'total_products': total_products,
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_stock_value': total_stock_value,
        'average_stock': average_stock,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'category_labels': category_labels,
        'category_data': category_data,
    }
    return render(request, 'core/stock_report.html', context)

@login_required
@view_permission_required('purchase_report')
def purchase_report(request):
    purchases = PurchaseOrder.objects.select_related('supplier', 'created_by').prefetch_related('items').all()
    suppliers = Supplier.objects.all()

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    supplier_filter = request.GET.get('supplier')
    status_filter = request.GET.get('status')

    if start_date:
        purchases = purchases.filter(order_date__date__gte=start_date)
    if end_date:
        purchases = purchases.filter(order_date__date__lte=end_date)
    if supplier_filter:
        purchases = purchases.filter(supplier_id=supplier_filter)
    if status_filter:
        purchases = purchases.filter(status=status_filter)

    total_orders = purchases.count()
    completed_orders = purchases.filter(status='completed').count()
    pending_orders = purchases.filter(status='pending').count()
    cancelled_orders = purchases.filter(status='cancelled').count()
    returned_orders = purchases.filter(status='returned').count()  # Add this line
    total_purchase_value = purchases.aggregate(total=Sum('total_amount'))['total'] or 0
    average_order_value = (total_purchase_value / total_orders) if total_orders > 0 else 0

    top_suppliers = Supplier.objects.annotate(
        order_count=Count('purchaseorder'),
        total_value=Sum('purchaseorder__total_amount'),
        last_order=Max('purchaseorder__order_date')
    ).filter(order_count__gt=0).order_by('-total_value')[:5]

    for supplier in top_suppliers:
        supplier.avg_value = (supplier.total_value or 0) / supplier.order_count if supplier.order_count else 0

    today = timezone.now().date()
    trend_data = []
    trend_labels = []
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        day_purchases = PurchaseOrder.objects.filter(order_date__date=date).aggregate(total=Sum('total_amount'))['total'] or 0
        trend_data.append(float(day_purchases))
        trend_labels.append(date.strftime('%b %d'))

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    next_month = month_start.replace(day=28) + timedelta(days=4)
    month_end = next_month - timedelta(days=next_month.day)

    paginator = Paginator(purchases.order_by('-order_date'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'purchases': page_obj,
        'suppliers': suppliers,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'cancelled_orders': cancelled_orders,
        'returned_orders': returned_orders,  # Add this line
        'total_purchase_value': total_purchase_value,
        'average_order_value': average_order_value,
        'top_suppliers': top_suppliers,
        'start_date': start_date,
        'end_date': end_date,
        'today': today,
        'week_start': week_start,
        'week_end': week_end,
        'month_start': month_start,
        'month_end': month_end,
        'trend_data': trend_data,
        'trend_labels': trend_labels,
    }
    return render(request, 'core/purchase_report.html', context)

@login_required
@admin_required
def profit_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category_filter = request.GET.get('category')
    period = request.GET.get('period', 'monthly')

    if not start_date:
        start_date = timezone.now().replace(day=1).date()
    if not end_date:
        end_date = timezone.now().date()

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    sales = Sale.objects.filter(
        sale_date__date__range=[start_date, end_date]
    ).prefetch_related('items__product', 'returns__items')

    if category_filter:
        sales = sales.filter(items__product__category_id=category_filter).distinct()

    # Calculate gross revenue (before returns)
    gross_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Calculate total returns amount
    total_returns_amount = sales.aggregate(total=Sum('returned_amount'))['total'] or 0
    
    # Calculate net revenue (after returns)
    total_revenue = gross_revenue - total_returns_amount

    # Calculate costs and profits PROPERLY accounting for returns
    total_cost = Decimal('0')
    total_profit = Decimal('0')
    sales_data = []
    
    for sale in sales:
        # Use the new method that accounts for returned items
        sale_cost = sale.get_net_cost()
        sale_profit = sale.get_net_profit()
        sale_margin = sale.get_net_profit_margin()
        
        total_cost += sale_cost
        total_profit += sale_profit
        
        sales_data.append({
            'sale': sale,
            'cost': sale_cost,
            'profit': sale_profit,
            'margin': sale_margin
        })

    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0
    total_sales = sales.count()
    avg_profit_per_sale = (total_profit / total_sales) if total_sales > 0 else 0

    categories = Category.objects.all()

    # Generate trend data
    trend_labels, revenue_data, profit_data = [], [], []
    current_date = start_date
    while current_date <= end_date:
        if period == 'daily':
            period_start, period_end = current_date, current_date
            label = current_date.strftime('%b %d')
            current_date += timedelta(days=1)
        elif period == 'weekly':
            period_start = current_date - timedelta(days=current_date.weekday())
            period_end = period_start + timedelta(days=6)
            label = f"Week {current_date.isocalendar()[1]}"
            current_date = period_end + timedelta(days=1)
        elif period == 'monthly':
            month_start = current_date.replace(day=1)
            next_month = month_start.replace(day=28) + timedelta(days=4)
            period_end = next_month - timedelta(days=next_month.day)
            period_start = month_start
            label = month_start.strftime('%b %Y')
            current_date = period_end + timedelta(days=1)
        else: # yearly
            period_start = current_date.replace(month=1, day=1)
            period_end = current_date.replace(month=12, day=31)
            label = str(current_date.year)
            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)

        date_sales = sales.filter(sale_date__date__range=[period_start, period_end])
        
        # Calculate period revenue properly
        period_gross = date_sales.aggregate(total=Sum('total_amount'))['total'] or 0
        period_returns = date_sales.aggregate(total=Sum('returned_amount'))['total'] or 0
        period_revenue = period_gross - period_returns
        
        # Calculate period cost properly
        period_cost = Decimal('0')
        for sale in date_sales:
            period_cost += sale.get_net_cost()

        period_profit = period_revenue - period_cost

        trend_labels.append(label)
        revenue_data.append(float(period_revenue))
        profit_data.append(float(period_profit))

    # Top products by NET profit (after returns)
    top_products = []
    product_sales = SaleItem.objects.filter(
        sale__sale_date__date__range=[start_date, end_date]
    ).select_related('product', 'product__category')
    
    # Calculate net profit for each product
    product_profits = {}
    for sale_item in product_sales:
        product_id = sale_item.product.id
        if product_id not in product_profits:
            product_profits[product_id] = {
                'product__name': sale_item.product.name,
                'product__category__name': sale_item.product.category.name,
                'total_quantity': 0,
                'total_revenue': Decimal('0'),
                'total_cost': Decimal('0'),
                'total_profit': Decimal('0')
            }
        
        # Calculate net quantity (sold - returned)
        net_quantity = sale_item.net_quantity
        if net_quantity > 0:
            product_profits[product_id]['total_quantity'] += net_quantity
            product_profits[product_id]['total_revenue'] += sale_item.unit_price * Decimal(net_quantity)
            product_profits[product_id]['total_cost'] += sale_item.product.cost_price * Decimal(net_quantity)
    
    # Calculate profit for each product
    for product_data in product_profits.values():
        product_data['total_profit'] = product_data['total_revenue'] - product_data['total_cost']
    
    # Sort by profit and take top 5
    top_products = sorted(product_profits.values(), key=lambda x: x['total_profit'], reverse=True)[:5]

    # Category profits with proper net calculation
    category_profits = []
    category_data = {}
    
    for sale in sales:
        for item in sale.items.all():
            category = item.product.category
            if category.id not in category_data:
                category_data[category.id] = {
                    'name': category.name,
                    'total_revenue': Decimal('0'),
                    'total_cost': Decimal('0'),
                    'total_profit': Decimal('0')
                }
            
            # Use net quantity for calculations
            net_quantity = item.net_quantity
            if net_quantity > 0:
                category_data[category.id]['total_revenue'] += item.unit_price * Decimal(net_quantity)
                category_data[category.id]['total_cost'] += item.product.cost_price * Decimal(net_quantity)
    
    # Calculate profit and margin for each category
    for cat_data in category_data.values():
        cat_data['total_profit'] = cat_data['total_revenue'] - cat_data['total_cost']
        cat_data['profit_margin'] = (cat_data['total_profit'] / cat_data['total_revenue'] * 100) if cat_data['total_revenue'] > 0 else 0
    
    category_profits = sorted(category_data.values(), key=lambda x: x['total_profit'], reverse=True)

    # Best performers
    best_day = {'profit': 0, 'date': start_date}
    best_margin = {'margin': 0}
    
    if profit_data:
        max_profit_index = profit_data.index(max(profit_data))
        best_day = {
            'profit': profit_data[max_profit_index],
            'date': trend_labels[max_profit_index]
        }
        
        # Calculate best margin
        margins = []
        for i in range(len(profit_data)):
            if revenue_data[i] > 0:
                margins.append((profit_data[i] / revenue_data[i]) * 100)
            else:
                margins.append(0)
        
        if margins:
            best_margin = {'margin': max(margins)}

    best_product = top_products[0] if top_products else {'product__name': 'N/A', 'total_profit': 0}
    best_category = category_profits[0] if category_profits else {'name': 'N/A', 'total_profit': 0}

    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    next_month = month_start.replace(day=28) + timedelta(days=4)
    month_end = next_month - timedelta(days=next_month.day)
    year_start = today.replace(month=1, day=1)
    year_end = today.replace(month=12, day=31)

    context = {
        'gross_revenue': gross_revenue,
        'total_returns_amount': total_returns_amount,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'total_sales': total_sales,
        'avg_profit_per_sale': avg_profit_per_sale,
        'sales_data': sales_data,
        'categories': categories,
        'start_date': start_date,
        'end_date': end_date,
        'period': period,
        'period_display': period.title(),
        'today': today,
        'week_start': week_start,
        'week_end': week_end,
        'month_start': month_start,
        'month_end': month_end,
        'year_start': year_start,
        'year_end': year_end,
        'trend_labels': json.dumps(trend_labels),
        'revenue_data': json.dumps(revenue_data),
        'profit_data': json.dumps(profit_data),
        'top_products': top_products,
        'category_profits': category_profits,
        'best_day': best_day,
        'best_margin': best_margin,
        'best_product': best_product,
        'best_category': best_category,
    }
    return render(request, 'core/profit_report.html', context)
# --- Supplier Billing System ---

@login_required
@view_permission_required('supplier_bills')
def supplier_bills(request):
    bills = SupplierBill.objects.select_related(
        'supplier', 'purchase_order', 'created_by'
    ).prefetch_related('payments')
    
    # Filters
    status = request.GET.get('status')
    supplier = request.GET.get('supplier')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status:
        bills = bills.filter(status=status)
    if supplier:
        bills = bills.filter(supplier_id=supplier)
    if date_from:
        bills = bills.filter(bill_date__gte=date_from)
    if date_to:
        bills = bills.filter(bill_date__lte=date_to)
        
    bills = bills.order_by('-bill_date')
    
    # Summary statistics
    total_bills = bills.count()
    total_amount = bills.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = bills.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    total_due = bills.aggregate(Sum('due_amount'))['due_amount__sum'] or 0
    
    # Calculate payment rate
    payment_rate = (total_paid / total_amount * 100) if total_amount > 0 else 0
    
    # Overdue bills
    overdue_bills = bills.filter(status='overdue')
    overdue_amount = overdue_bills.aggregate(Sum('due_amount'))['due_amount__sum'] or 0
    
    # Pagination
    paginator = Paginator(bills, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'bills': page_obj,
        'suppliers': Supplier.objects.all(),
        'status_choices': SupplierBill.BILL_STATUS,
        'total_bills': total_bills,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_due': total_due,
        'payment_rate': payment_rate,
        'overdue_bills_count': overdue_bills.count(),
        'overdue_amount': overdue_amount,
        'today': timezone.now().date(),  # Add today for due date comparisons
    }
    return render(request, 'core/supplier_bills.html', context)

@login_required
@view_permission_required('supplier_bill_detail')
def supplier_bill_detail(request, pk):
    bill = get_object_or_404(SupplierBill.objects.select_related(
        'supplier', 'purchase_order', 'created_by'
    ), pk=pk)
    
    payments = bill.payments.all().select_related('received_by').order_by('-payment_date')
    
    context = {
        'bill': bill,
        'payments': payments,
        'today': timezone.now().date(),
    }
    return render(request, 'core/supplier_bill_detail.html', context)

@login_required
@view_permission_required('create_payment')
def create_payment(request, bill_id):
    bill = get_object_or_404(SupplierBill, pk=bill_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, bill=bill)
        if form.is_valid():
            try:
                payment = form.save(commit=False)
                payment.bill = bill
                payment.received_by = request.user
                payment.save()
                
                messages.success(request, f'Payment of ৳{payment.amount} recorded successfully!')
                return redirect('supplier_bill_detail', pk=bill.id)
                
            except ValidationError as e:
                # Handle any remaining validation errors
                for field, errors in e.error_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            except Exception as e:
                messages.error(request, f'Error creating payment: {str(e)}')
    else:
        form = PaymentForm(bill=bill, initial={
            'amount': bill.due_amount,
            'payment_date': timezone.now().date()
        })
    
    context = {
        'form': form,
        'bill': bill,
    }
    return render(request, 'core/create_payment.html', context)

@login_required
def bill_dashboard(request):
    today = timezone.now().date()
    
    # Key metrics
    bills = SupplierBill.objects.all()
    total_bills = bills.count()
    total_amount = bills.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = bills.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    total_due = bills.aggregate(Sum('due_amount'))['due_amount__sum'] or 0
    
    # Overdue bills
    overdue_bills = bills.filter(status='overdue', due_date__lt=today)
    overdue_amount = overdue_bills.aggregate(Sum('due_amount'))['due_amount__sum'] or 0
    
    # Upcoming due bills (next 7 days)
    upcoming_due = bills.filter(
        due_date__range=[today, today + timedelta(days=7)],
        due_amount__gt=0
    )
    
    # Supplier-wise summary
    supplier_summary = Supplier.objects.annotate(
        total_bills=Count('supplierbill'),
        total_amount=Sum('supplierbill__total_amount'),
        total_due=Sum('supplierbill__due_amount')
    ).filter(total_bills__gt=0).order_by('-total_amount')
    
    # Recent bills
    recent_bills = bills.select_related('supplier').order_by('-bill_date')[:10]
    
    context = {
        'total_bills': total_bills,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_due': total_due,
        'overdue_bills_count': overdue_bills.count(),
        'overdue_amount': overdue_amount,
        'upcoming_due_count': upcoming_due.count(),
        'supplier_summary': supplier_summary,
        'recent_bills': recent_bills,
        'today': today,
    }
    return render(request, 'core/bill_dashboard.html', context)

def bill_summary_api(request):
    """API endpoint for bill summary data"""
    today = timezone.now().date()
    last_year = today - timedelta(days=365)
    
    # Monthly bill data
    monthly_data = SupplierBill.objects.filter(
        bill_date__gte=last_year
    ).extra(
        {'month': "strftime('%%Y-%%m', bill_date)"}
    ).values('month').annotate(
        total_amount=Sum('total_amount'),
        paid_amount=Sum('paid_amount')
    ).order_by('month')
    
    # Status distribution
    status_data = SupplierBill.objects.values('status').annotate(
        count=Count('id'),
        amount=Sum('total_amount')
    )
    
    return JsonResponse({
        'monthly_data': list(monthly_data),
        'status_data': list(status_data),
    })

# --- User management ---

@login_required
@admin_required
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    
                    # Create user profile
                    UserProfile.objects.create(
                        user=user,
                        role=form.cleaned_data.get('role', 'staff'),
                        phone=form.cleaned_data.get('phone', ''),
                        address=form.cleaned_data.get('address', ''),
                        is_system_admin=form.cleaned_data.get('is_system_admin', False)
                    )
                    
                    # Handle view permissions
                    view_permissions = request.POST.getlist('view_permissions')
                    for view_code in view_permissions:
                        try:
                            permission = ViewPermission.objects.get(view_code=view_code)
                            UserViewPermission.objects.create(
                                user=user,
                                permission=permission,
                                granted_by=request.user
                            )
                        except ViewPermission.DoesNotExist:
                            continue
                    
                    messages.success(request, f'User {user.username} created successfully with selected permissions!')
                    return redirect('user_management')
                    
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
                # Add debug information
                print(f"Error creating user: {str(e)}")
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()
    
    # Get all view permissions grouped by category
    all_permissions = ViewPermission.objects.all()
    view_categories = [
        ('Dashboard', all_permissions.filter(view_code='dashboard')),
        ('Product Management', all_permissions.filter(view_code__in=[
            'product_list', 'product_create', 'product_edit', 'product_delete'
        ])),
        ('Stock Management', all_permissions.filter(view_code__in=[
            'stock_adjustment', 'stock_report', 'expiry_report', 'batch_management'
        ])),
        ('Sales', all_permissions.filter(view_code__in=[
            'pos_sale', 'daily_sale_report', 'profit_report', 'sale_return_list'
        ])),
        ('Purchases', all_permissions.filter(view_code__in=[
            'purchase_order_create', 'purchase_report', 'purchase_return_list'
        ])),
        ('Supplier & Billing', all_permissions.filter(view_code__in=[
            'supplier_bills', 'bill_dashboard'
        ])),
        ('Customers', all_permissions.filter(view_code__in=[
            'customer_management', 'customer_due_report', 'due_collection_report'
        ])),
        ('Reports', all_permissions.filter(view_code__in=[
            'generate_sales_report'
        ])),
        ('Administration', all_permissions.filter(view_code__in=[
            'user_management'
        ])),
    ]
    
    return render(request, 'core/user_form.html', {
        'form': form,
        'view_categories': view_categories,
        'user_view_permissions': [],
        'user_profile': None
    })

@login_required
@admin_required
def edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user_profile = get_object_or_404(UserProfile, user=user)
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Handle password separately if provided
                    password1 = request.POST.get('password1')
                    password2 = request.POST.get('password2')
                    
                    if password1 and password2:
                        if password1 == password2:
                            user.set_password(password1)
                            user.save()
                            messages.success(request, f'Password updated for {user.username}!')
                        else:
                            messages.error(request, 'Passwords do not match!')
                    
                    user = form.save()
                    
                    # Update user profile
                    user_profile.role = form.cleaned_data.get('role', 'staff')
                    user_profile.phone = form.cleaned_data.get('phone', '')
                    user_profile.address = form.cleaned_data.get('address', '')
                    user_profile.is_system_admin = form.cleaned_data.get('is_system_admin', False)
                    user_profile.save()
                    
                    # Update view permissions
                    selected_permissions = request.POST.getlist('view_permissions')
                    
                    # Remove existing permissions
                    UserViewPermission.objects.filter(user=user).delete()
                    
                    # Add new permissions
                    for view_code in selected_permissions:
                        try:
                            permission = ViewPermission.objects.get(view_code=view_code)
                            UserViewPermission.objects.create(
                                user=user,
                                permission=permission,
                                granted_by=request.user
                            )
                        except ViewPermission.DoesNotExist:
                            continue
                    
                    messages.success(request, f'User {user.username} updated successfully!')
                    return redirect('user_management')
                    
            except Exception as e:
                messages.error(request, f'Error updating user: {str(e)}')
    else:
        form = CustomUserChangeForm(instance=user, initial={
            'role': user_profile.role,
            'phone': user_profile.phone,
            'address': user_profile.address,
            'is_system_admin': user_profile.is_system_admin,
        })
    
    # Get user's current view permissions
    user_view_permissions = ViewPermission.objects.filter(
        userviewpermission__user=user
    )
    
    # Get all view permissions grouped by category
    all_permissions = ViewPermission.objects.all()
    view_categories = [
        ('Dashboard', all_permissions.filter(view_code='dashboard')),
        ('Product Management', all_permissions.filter(view_code__in=[
            'product_list', 'product_create', 'product_edit', 'product_delete'
        ])),
        ('Stock Management', all_permissions.filter(view_code__in=[
            'stock_adjustment', 'stock_report', 'expiry_report', 'batch_management'
        ])),
        ('Sales', all_permissions.filter(view_code__in=[
            'pos_sale', 'daily_sale_report', 'profit_report', 'sale_return_list'
        ])),
        ('Purchases', all_permissions.filter(view_code__in=[
            'purchase_order_create', 'purchase_report', 'purchase_return_list'
        ])),
        ('Supplier & Billing', all_permissions.filter(view_code__in=[
            'supplier_bills', 'bill_dashboard'
        ])),
        ('Customers', all_permissions.filter(view_code__in=[
            'customer_management', 'customer_due_report', 'due_collection_report'
        ])),
        ('Reports', all_permissions.filter(view_code__in=[
            'generate_sales_report'
        ])),
        ('Administration', all_permissions.filter(view_code__in=[
            'user_management'
        ])),
    ]
    
    return render(request, 'core/user_form.html', {
        'form': form,
        'view_categories': view_categories,
        'user_view_permissions': user_view_permissions,
        'user_profile': user_profile
    })

@login_required
@admin_required
def user_management(request):
    """View for managing all users"""
    users = User.objects.select_related('userprofile').prefetch_related('view_permissions__permission').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Statistics
    total_users = users.count()
    admin_users = users.filter(
        Q(userprofile__is_system_admin=True) | Q(is_superuser=True)
    ).count()
    active_users = users.filter(is_active=True).count()
    
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'total_users': total_users,
        'admin_users': admin_users,
        'active_users': active_users,
        'search_query': search_query,
    }
    return render(request, 'core/user_management.html', context)






@login_required
@role_required('admin')
def mark_purchase_order_completed(request, purchase_id):
    if request.method == 'POST':
        purchase_order = get_object_or_404(PurchaseOrder, id=purchase_id)
        
        if purchase_order.status != 'pending':
            return JsonResponse({
                'success': False, 
                'error': f'Order is already {purchase_order.status}'
            })
        
        try:
            # Update stock for each item in the purchase order
            for item in purchase_order.items.all():
                product = item.product
                product.current_stock = F('current_stock') + item.quantity
                product.save()
                product.refresh_from_db()
            
            # Update purchase order status
            purchase_order.status = 'completed'
            purchase_order.save()
            
            messages.success(request, f'Purchase order #{purchase_order.po_number} marked as completed and stock updated!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                return redirect('purchase_report')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error: {str(e)}')
                return redirect('purchase_report')
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@view_permission_required('cancel_purchase_order')
def cancel_purchase_order(request, purchase_id):
    if request.method == 'POST':
        purchase_order = get_object_or_404(PurchaseOrder, id=purchase_id)
        
        if purchase_order.status != 'pending':
            return JsonResponse({
                'success': False, 
                'error': f'Cannot cancel order with status: {purchase_order.status}'
            })
        
        try:
            reason = request.POST.get('reason', 'No reason provided')
            
            # Update purchase order status
            purchase_order.status = 'cancelled'
            purchase_order.save()
            
            # Create cancellation record
            PurchaseOrderCancellation.objects.create(
                purchase_order=purchase_order,
                cancelled_by=request.user,
                reason=reason
            )
            
            messages.warning(request, f'Purchase order #{purchase_order.po_number} has been cancelled.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                return redirect('purchase_report')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error: {str(e)}')
                return redirect('purchase_report')
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@view_permission_required('purchase_order_detail')
def purchase_order_detail(request, purchase_id):
    """View for displaying purchase order details"""
    purchase_order = get_object_or_404(
        PurchaseOrder.objects.select_related('supplier', 'created_by')
        .prefetch_related('items__product'), 
        id=purchase_id
    )
    
    context = {
        'purchase_order': purchase_order,
    }
    return render(request, 'core/purchase_order_detail.html', context)

@login_required
@view_permission_required('expiry_report')
def expiry_report(request):
    """View for showing products nearing expiry"""
    today = timezone.now().date()
    
    # Get filter parameters
    days_threshold = int(request.GET.get('days', 30))
    category_filter = request.GET.get('category')
    include_expired = request.GET.get('include_expired', False)
    
    # Calculate threshold date
    threshold_date = today + timedelta(days=days_threshold)
    
    # Get ALL batches first (not just nearing expiry)
    batches = ProductBatch.objects.select_related('product', 'product__category').filter(
        current_quantity__gt=0
    )
    
    # Apply category filter to ALL batches
    if category_filter:
        batches = batches.filter(product__category_id=category_filter)
    
    # Create filtered queryset for display
    display_batches = batches.filter(expiry_date__lte=threshold_date)
    
    if not include_expired:
        display_batches = display_batches.filter(expiry_date__gte=today)
    
    # Sort by expiry date (soonest first)
    display_batches = display_batches.order_by('expiry_date')
    
    # Calculate statistics from ALL batches (not just filtered ones)
    total_batches = batches.count()
    expired_batches_count = batches.filter(expiry_date__lt=today).count()
    near_expiry_batches_count = batches.filter(
        expiry_date__gte=today,
        expiry_date__lte=threshold_date
    ).count()
    good_batches_count = batches.filter(
        expiry_date__gt=threshold_date
    ).count()
    
    # Calculate values for display batches
    total_value_near_expiry = sum(
        batch.current_quantity * batch.product.cost_price 
        for batch in display_batches.filter(expiry_date__gte=today)
    )
    total_value_expired = sum(
        batch.current_quantity * batch.product.cost_price 
        for batch in display_batches.filter(expiry_date__lt=today)
    )
    
    categories = Category.objects.all()
    
    context = {
        'batches': display_batches,  # Show filtered batches
        'categories': categories,
        'today': today,
        'days_threshold': days_threshold,
        'total_batches': total_batches,  # But count ALL batches
        'total_near_expiry': near_expiry_batches_count,  # From ALL batches
        'total_expired': expired_batches_count,  # From ALL batches
        'total_good': good_batches_count,  # From ALL batches
        'total_value_near_expiry': total_value_near_expiry,
        'total_value_expired': total_value_expired,
        'include_expired': include_expired,
    }
    return render(request, 'core/expiry_report.html', context)

@login_required
@view_permission_required('create_purchase_return')
def create_purchase_return(request):
    if request.method == 'POST':
        form = PurchaseReturnForm(request.POST)
        if form.is_valid():
            # Process the form
            purchase_return = form.save(commit=False)
            purchase_return.created_by = request.user
            purchase_return.save()
            return redirect('add_return_item', return_id=purchase_return.id)
    else:
        form = PurchaseReturnForm()
    
    # Get recent returnable orders for the sidebar
    returnable_orders = PurchaseOrder.objects.filter(
        status='completed'
    ).annotate(
        total_ordered=Sum('items__quantity'),
        total_returned=Coalesce(Sum('items__returns__quantity'), Value(0)),
        remaining_qty=F('total_ordered') - F('total_returned')
    ).filter(
        remaining_qty__gt=0
    ).order_by('-order_date')[:5]
    
    context = {
        'form': form,
        'returnable_orders': returnable_orders
    }
    
    return render(request, 'core/create_purchase_return.html', context)

@login_required
def purchase_return_list(request):
    """View for listing all purchase returns"""
    returns = PurchaseReturn.objects.select_related(
        'purchase_order', 'purchase_order__supplier', 'created_by'
    ).prefetch_related('items').all().order_by('-return_date')
    
    # Filters
    status_filter = request.GET.get('status')
    supplier_filter = request.GET.get('supplier')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status_filter:
        returns = returns.filter(status=status_filter)
    if supplier_filter:
        returns = returns.filter(purchase_order__supplier_id=supplier_filter)
    if date_from:
        returns = returns.filter(return_date__gte=date_from)
    if date_to:
        returns = returns.filter(return_date__lte=date_to)
    
    # Statistics
    total_returns = returns.count()
    pending_returns = returns.filter(status='pending').count()
    approved_returns = returns.filter(status='approved').count()
    completed_returns = returns.filter(status='completed').count()
    total_return_amount = returns.aggregate(Sum('return_amount'))['return_amount__sum'] or 0
    
    paginator = Paginator(returns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'returns': page_obj,
        'suppliers': Supplier.objects.all(),
        'total_returns': total_returns,
        'pending_returns': pending_returns,
        'approved_returns': approved_returns,
        'completed_returns': completed_returns,
        'total_return_amount': total_return_amount,
    }
    return render(request, 'core/purchase_return_list.html', context)

@login_required
@view_permission_required('purchase_return_detail')
def purchase_return_detail(request, return_id):
    """View for purchase return details"""
    purchase_return = get_object_or_404(
        PurchaseReturn.objects.select_related(
            'purchase_order', 'purchase_order__supplier', 'created_by'
        ).prefetch_related(
            'items__purchase_order_item__product', 
            'items__batch'
        ),
        id=return_id
    )
    
    # Calculate total return amount
    total_amount = sum(item.total_cost for item in purchase_return.items.all())
    
    context = {
        'purchase_return': purchase_return,
        'total_amount': total_amount,
    }
    return render(request, 'core/purchase_return_detail.html', context)

@login_required
@view_permission_required('add_return_item')
def add_return_item(request, return_id):
    """View for adding items to a return"""
    purchase_return = get_object_or_404(PurchaseReturn, id=return_id)
    
    if request.method == 'POST':
        form = PurchaseReturnItemForm(
            request.POST, 
            purchase_order=purchase_return.purchase_order
        )
        
        if form.is_valid():
            return_item = form.save(commit=False)
            return_item.purchase_return = purchase_return
            
            # Set unit cost from purchase order item if not set
            if not return_item.unit_cost and return_item.purchase_order_item:
                return_item.unit_cost = return_item.purchase_order_item.unit_cost
            
            # Calculate total cost
            return_item.total_cost = return_item.quantity * return_item.unit_cost
            
            with transaction.atomic():
                return_item.save()
                
                # Update return amount
                purchase_return.return_amount = purchase_return.items.aggregate(
                    total=Sum('total_cost')
                )['total'] or 0
                purchase_return.save()
                
            messages.success(request, f'Added {return_item.quantity} units to return.')
            return redirect('purchase_return_detail', return_id=purchase_return.id)
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseReturnItemForm(purchase_order=purchase_return.purchase_order)
    
    # Prepare data for JavaScript
    po_items_data = []
    if form.fields['purchase_order_item'].queryset:
        for item in form.fields['purchase_order_item'].queryset:
            po_items_data.append({
                'id': str(item.id),
                'product_id': item.product.id,
                'product_name': item.product.name,
                'remaining_quantity': item.remaining_quantity,
                'unit_cost': float(item.unit_cost),
            })
    
    context = {
        'form': form,
        'purchase_return': purchase_return,
        'po_items_data': json.dumps(po_items_data),
    }
    return render(request, 'core/add_return_item.html', context)

@login_required
@view_permission_required('update_return_status')
def update_return_status(request, return_id):
    """View for updating return status - FIXED VERSION"""
    purchase_return = get_object_or_404(
        PurchaseReturn.objects.select_related(
            'purchase_order', 'purchase_order__supplier', 'created_by'
        ).prefetch_related(
            'items__purchase_order_item__product',
            'items__batch'
        ), 
        id=return_id
    )
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        print(f"DEBUG: POST received - new_status: {new_status}, current_status: {purchase_return.status}")
        
        if new_status in dict(PurchaseReturn.RETURN_STATUS):
            old_status = purchase_return.status
            
            # Don't do anything if status hasn't changed
            if old_status == new_status:
                messages.info(request, 'Return status is already set to {}'.format(new_status))
                return redirect('purchase_return_detail', return_id=purchase_return.id)
            
            try:
                with transaction.atomic():
                    # Handle status change to "Completed" - adjust stock and batch quantities
                    if new_status == 'completed' and old_status != 'completed':
                        print("DEBUG: Processing completion...")
                        batches_to_delete = []  # Track batches that become empty
                        
                        # Process each return item and update stock and batch
                        for return_item in purchase_return.items.all():
                            product = return_item.purchase_order_item.product
                            quantity = return_item.quantity
                            batch = return_item.batch
                            
                            print(f"DEBUG: Processing item - Product: {product.name}, Quantity: {quantity}, Batch: {batch}")
                            
                            if not batch:
                                continue  # Skip if no batch associated
                                
                            # Get current values BEFORE updating
                            old_product_stock = product.current_stock
                            old_batch_quantity = batch.current_quantity
                            
                            # Update product stock using direct calculation
                            product.current_stock = old_product_stock - quantity
                            if product.current_stock < 0:
                                raise ValidationError(f'Cannot return {quantity} units. Only {old_product_stock} available for {product.name}.')
                            product.save()
                            
                            print(f"DEBUG: Product stock updated from {old_product_stock} to {product.current_stock}")
                            
                            # Update batch quantity
                            batch.current_quantity = old_batch_quantity - quantity
                            if batch.current_quantity < 0:
                                raise ValidationError(f'Cannot return {quantity} units from batch {batch.batch_number}. Only {old_batch_quantity} available.')
                            
                            # Check if batch should be deleted (quantity reached zero)
                            if batch.current_quantity == 0:
                                batches_to_delete.append(batch)
                                print(f"DEBUG: Batch {batch.batch_number} will be deleted (quantity reached zero)")
                            else:
                                batch.save()
                                print(f"DEBUG: Batch {batch.batch_number} updated from {old_batch_quantity} to {batch.current_quantity}")
                            
                            # Create stock movement record for return
                            StockMovement.objects.create(
                                product=product,
                                movement_type='return_out',
                                quantity=-quantity,
                                batch_number=batch.batch_number if batch else '',
                                reference_number=purchase_return.return_number,
                                notes=f"Purchase return completed - {purchase_return.return_number}",
                                movement_date=timezone.now()
                            )
                        
                        # Delete batches that reached zero quantity
                        for batch in batches_to_delete:
                            batch.delete()
                            print(f"DEBUG: Batch {batch.batch_number} deleted (quantity reached zero)")
                        
                        # Update Purchase Order status to "returned" if it's not already
                        purchase_order = purchase_return.purchase_order
                        if purchase_order.status != 'returned':
                            purchase_order.status = 'returned'
                            purchase_order.save()
                            print(f"DEBUG: Purchase order status updated to 'returned'")
                        
                        # Update Supplier Bill if exists - FIXED SECTION
                        try:
                            supplier_bill = SupplierBill.objects.get(purchase_order=purchase_order)
                            
                            # Don't change total_amount - keep original for tracking
                            # Just let the save() method handle status based on returns
                            supplier_bill.save()  # This will recalculate status
                            
                            print(f"DEBUG: Supplier bill status updated to: {supplier_bill.status}")
                            
                        except SupplierBill.DoesNotExist:
                            print("DEBUG: No supplier bill found for this purchase order")
                        
                        messages.success(request, f'Return status updated to completed. Stock/batch quantities adjusted, purchase order marked as returned, and supplier bill updated.')
                    
                    # Handle reversal if status changed from "Completed" to something else
                    elif old_status == 'completed' and new_status != 'completed':
                        print("DEBUG: Processing reversal...")
                        # Reverse the stock and batch adjustment
                        for return_item in purchase_return.items.all():
                            product = return_item.purchase_order_item.product
                            quantity = return_item.quantity
                            batch = return_item.batch
                            
                            # Get current values BEFORE updating
                            old_product_stock = product.current_stock
                            
                            # Update product stock using direct calculation
                            product.current_stock = old_product_stock + quantity
                            product.save()
                            
                            print(f"DEBUG: Product stock reversed from {old_product_stock} to {product.current_stock}")
                            
                            # For batch restoration, we need to handle this differently
                            # since the batch might have been deleted
                            if not batch:
                                # Batch was deleted, we need to recreate it
                                po_item = return_item.purchase_order_item
                                batch = ProductBatch.objects.create(
                                    product=product,
                                    batch_number=f"RESTORED-{return_item.id}-{uuid.uuid4().hex[:6].upper()}",
                                    manufacture_date=timezone.now().date(),
                                    expiry_date=po_item.expiry_date if product.has_expiry else None,
                                    quantity=quantity,
                                    current_quantity=quantity,
                                    purchase_order_item=po_item
                                )
                                return_item.batch = batch
                                return_item.save()
                                print(f"DEBUG: Recreated batch {batch.batch_number} with quantity {quantity}")
                            else:
                                # Batch still exists, just update quantity
                                old_batch_quantity = batch.current_quantity
                                batch.current_quantity = old_batch_quantity + quantity
                                batch.save()
                                print(f"DEBUG: Batch {batch.batch_number} reversed from {old_batch_quantity} to {batch.current_quantity}")
                            
                            # Create reverse stock movement record
                            StockMovement.objects.create(
                                product=product,
                                movement_type='return_in',
                                quantity=quantity,
                                batch_number=batch.batch_number if batch else '',
                                reference_number=purchase_return.return_number,
                                notes=f"Return status reversed from completed - {purchase_return.return_number}",
                                movement_date=timezone.now()
                            )
                        
                        # Revert Purchase Order status back to "completed"
                        purchase_order = purchase_return.purchase_order
                        purchase_order.status = 'completed'
                        purchase_order.save()
                        print(f"DEBUG: Purchase order status reverted to 'completed'")
                        
                        # Revert Supplier Bill changes
                        try:
                            supplier_bill = SupplierBill.objects.get(purchase_order=purchase_order)
                            supplier_bill.save()  # This will recalculate status based on current returns
                            print(f"DEBUG: Supplier bill status reverted to: {supplier_bill.status}")
                            
                        except SupplierBill.DoesNotExist:
                            print("DEBUG: No supplier bill found for this purchase order")
                        
                        messages.warning(request, f'Return status updated and all adjustments (stock, batches, purchase order, supplier bill) have been reversed.')
                    
                    # Regular status update (not involving completed status)
                    else:
                        print("DEBUG: Processing regular status update...")
                        messages.success(request, f'Return status updated from {old_status} to {new_status}.')
                    
                    # Update the return status and description
                    purchase_return.status = new_status
                    
                    if notes:
                        if purchase_return.description:
                            purchase_return.description += f"\n\nStatus Update ({timezone.now().strftime('%Y-%m-%d %H:%M')}): {notes}"
                        else:
                            purchase_return.description = f"Status Update ({timezone.now().strftime('%Y-%m-%d %H:%M')}): {notes}"
                    
                    purchase_return.save()
                    print(f"DEBUG: Return status updated to {purchase_return.status}")
                    
            except Exception as e:
                print(f"DEBUG: Error occurred: {str(e)}")
                messages.error(request, f'Error updating return status: {str(e)}')
                return redirect('purchase_return_detail', return_id=purchase_return.id)
        
        return redirect('purchase_return_detail', return_id=purchase_return.id)
    
    context = {
        'purchase_return': purchase_return,
        'status_choices': PurchaseReturn.RETURN_STATUS,
    }
    return render(request, 'core/update_return_status.html', context)

@login_required

def batch_management(request):
    """View for managing product batches"""
    batches = ProductBatch.objects.select_related('product', 'product__category').all()
    
    # Filters
    product_filter = request.GET.get('product')
    expiry_status = request.GET.get('expiry_status')
    category_filter = request.GET.get('category')
    
    if product_filter:
        batches = batches.filter(product_id=product_filter)
    if category_filter:
        batches = batches.filter(product__category_id=category_filter)
    if expiry_status == 'expired':
        batches = batches.filter(expiry_date__lt=timezone.now().date())
    elif expiry_status == 'near_expiry':
        warning_date = timezone.now().date() + timedelta(days=30)
        batches = batches.filter(
            expiry_date__lte=warning_date,
            expiry_date__gte=timezone.now().date()
        )
    elif expiry_status == 'good':
        warning_date = timezone.now().date() + timedelta(days=30)
        batches = batches.filter(expiry_date__gt=warning_date)
    
    # Statistics
    total_batches = batches.count()
    expired_batches = batches.filter(expiry_date__lt=timezone.now().date()).count()
    near_expiry_batches = batches.filter(
        expiry_date__lte=timezone.now().date() + timedelta(days=30),
        expiry_date__gte=timezone.now().date()
    ).count()
    
    # Sort by expiry date
    batches = batches.order_by('expiry_date', 'product__name')
    
    products = Product.objects.filter(has_expiry=True)
    categories = Category.objects.all()
    
    paginator = Paginator(batches, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'batches': page_obj,
        'products': products,
        'categories': categories,
        'total_batches': total_batches,
        'expired_batches': expired_batches,
        'near_expiry_batches': near_expiry_batches,
        'today': timezone.now().date(),
    }
    return render(request, 'core/batch_management.html', context)

@login_required
@view_permission_required('write_off_expired')
def write_off_expired(request):
    """View for writing off expired products"""
    if request.method == 'POST':
        batch_id = request.POST.get('batch_id')
        quantity = int(request.POST.get('quantity', 0))
        reason = request.POST.get('reason', 'Expired')
        
        batch = get_object_or_404(ProductBatch, id=batch_id)
        
        if quantity <= 0 or quantity > batch.current_quantity:
            messages.error(request, 'Invalid quantity specified.')
        else:
            with transaction.atomic():
                # Create stock adjustment
                StockAdjustment.objects.create(
                    product=batch.product,
                    batch=batch,
                    adjustment_type='expiry_writeoff',
                    quantity=quantity,
                    reason=f'Expiry write-off: {reason}',
                    adjusted_by=request.user
                )
                
                # Update batch quantity
                batch.current_quantity = F('current_quantity') - quantity
                batch.save()
                batch.refresh_from_db()
                
                # Update product stock
                batch.product.current_stock = F('current_stock') - quantity
                batch.product.save()
                batch.product.refresh_from_db()
                
                messages.success(request, f'Written off {quantity} units of {batch.product.name} (Batch: {batch.batch_number})')
        
        return redirect('batch_management')
    
    # GET request - show expired batches
    expired_batches = ProductBatch.objects.filter(
        expiry_date__lt=timezone.now().date(),
        current_quantity__gt=0
    ).select_related('product').order_by('expiry_date')
    
    context = {
        'expired_batches': expired_batches,
    }
    return render(request, 'core/write_off_expired.html', context)

# API views for AJAX calls
@login_required
def get_po_items(request, po_id):
    """API endpoint to get purchase order items for returns"""
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    items = purchase_order.items.filter(remaining_quantity__gt=0).values(
        'id', 'product__name', 'quantity', 'remaining_quantity', 'unit_cost'
    )
    
    return JsonResponse(list(items), safe=False)

@login_required
def get_batches_for_product(request, product_id):
    """API endpoint to get batches for a product"""
    batches = ProductBatch.objects.filter(
        product_id=product_id,
        current_quantity__gt=0
    ).values('id', 'batch_number', 'expiry_date', 'current_quantity').order_by('expiry_date')
    
    batches_list = list(batches)
    for batch in batches_list:
        batch['expiry_date'] = batch['expiry_date'].strftime('%Y-%m-%d') if batch['expiry_date'] else None
    
    return JsonResponse(batches_list, safe=False)

@login_required
def get_batches_for_po_item(request, po_item_id):
    """API endpoint to get batches for a purchase order item"""
    po_item = get_object_or_404(PurchaseOrderItem, id=po_item_id)
    
    # Get batches that were created from this specific purchase order item
    batches = ProductBatch.objects.filter(
        purchase_order_item=po_item,
        current_quantity__gt=0
    ).values('id', 'batch_number', 'expiry_date', 'current_quantity').order_by('expiry_date')
    
    batches_list = list(batches)
    for batch in batches_list:
        batch['expiry_date'] = batch['expiry_date'].strftime('%Y-%m-%d') if batch['expiry_date'] else None
    
    return JsonResponse(batches_list, safe=False)

@login_required
@admin_required
def mark_purchase_order_completed(request, purchase_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_id)
    
    if purchase_order.status != 'pending':
        messages.error(request, f'Order is already {purchase_order.status}')
        return redirect('purchase_report')
    
    # Check if we're in batch creation mode
    if request.method == 'POST' and 'create_batches' in request.POST:
        # Show the batch creation form
        form = BatchCreationForm(purchase_order)
        context = {
            'purchase_order': purchase_order,
            'form': form,
        }
        return render(request, 'core/create_batches.html', context)
    
    # If auto-create batches is requested
    elif request.method == 'POST' and 'auto_create_batches' in request.POST:
        try:
            with transaction.atomic():
                # Auto-create batches without showing form
                batches = purchase_order.create_batches()
                
                # Update stock
                for item in purchase_order.items.all():
                    product = item.product
                    product.current_stock = F('current_stock') + item.quantity
                    product.save()
                
                # Update purchase order status
                purchase_order.status = 'completed'
                purchase_order.save()
                
                messages.success(request, 
                    f'Purchase order #{purchase_order.po_number} completed! '
                    f'Auto-created {len(batches)} batches.'
                )
                
                return redirect('purchase_report')
                    
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('purchase_report')
    
    # Show confirmation page for GET requests
    context = {
        'purchase_order': purchase_order,
    }
    
    return render(request, 'core/confirm_purchase_completion.html', context)

@login_required
def process_batch_creation(request, purchase_id):
    """Process the batch creation form"""
    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_id)
    
    if purchase_order.status != 'pending':
        messages.error(request, f'Order is already {purchase_order.status}')
        return redirect('purchase_report')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Process batch creation from form data
                batches_created = []
                for item in purchase_order.items.all():
                    # Get batch number from form
                    batch_number = request.POST.get(f'batch_number_{item.id}')
                    expiry_date_str = request.POST.get(f'expiry_date_{item.id}')
                    
                    # If no batch number provided, generate one
                    if not batch_number:
                        batch_number = f"BATCH-{timezone.now().strftime('%Y%m%d')}-{item.id}"
                    
                    # Parse expiry date
                    expiry_date = None
                    if expiry_date_str and item.product.has_expiry:
                        try:
                            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            expiry_date = None
                    
                    # Create batch
                    batch = ProductBatch.objects.create(
                        product=item.product,
                        batch_number=batch_number,
                        manufacture_date=timezone.now().date(),
                        expiry_date=expiry_date,
                        quantity=item.quantity,
                        current_quantity=item.quantity,
                        purchase_order_item=item
                    )
                    batches_created.append(batch)
                    
                    # Update product stock
                    item.product.current_stock = F('current_stock') + item.quantity
                    item.product.save()
                
                # Update purchase order status
                purchase_order.status = 'completed'
                purchase_order.save()
                
                messages.success(request, 
                    f'Purchase order #{purchase_order.po_number} completed! '
                    f'Created {len(batches_created)} batches with custom settings.'
                )
                
                return redirect('purchase_report')
                        
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('purchase_report')
    
    # If not POST, redirect to confirmation
    return redirect('mark_purchase_order_completed', purchase_id=purchase_id)

@login_required
@admin_required
def quick_complete_purchase_order(request, purchase_id):
    """Quick complete without batch form - auto-generate batches"""
    if request.method == 'POST':
        purchase_order = get_object_or_404(PurchaseOrder, id=purchase_id)
        
        if purchase_order.status != 'pending':
            return JsonResponse({
                'success': False, 
                'error': f'Order is already {purchase_order.status}'
            })
        
        try:
            with transaction.atomic():
                # Auto-create batches
                batches = purchase_order.create_batches()
                
                # Update stock for each item
                for item in purchase_order.items.all():
                    product = item.product
                    product.current_stock = F('current_stock') + item.quantity
                    product.save()
                    product.refresh_from_db()
                
                # Update purchase order status
                purchase_order.status = 'completed'
                purchase_order.save()
                
                messages.success(request, 
                    f'Purchase order #{purchase_order.po_number} completed! '
                    f'Auto-created {len(batches)} batches.'
                )
                
                return JsonResponse({'success': True})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@admin_required
def sale_return_create(request):
    """Create a new sale return - UPDATED VERSION"""
    if request.method == 'POST':
        invoice_number = request.POST.get('invoice_number')
        
        if invoice_number:
            try:
                sale = Sale.objects.get(invoice_number=invoice_number)
                return redirect('add_sale_return_items', sale_id=sale.id)
            except Sale.DoesNotExist:
                messages.error(request, 'Invoice number not found!')
        
    # Get recent sales for quick access
    recent_sales = Sale.objects.select_related('sold_by').prefetch_related('items__product').all().order_by('-sale_date')[:10]
    
    # Get today's sales for stats
    today_sales = Sale.objects.filter(sale_date__date=timezone.now().date())
    
    context = {
        'recent_sales': recent_sales,
        'today_sales': today_sales,
    }
    return render(request, 'core/sale_return_create.html', context)

@login_required
def add_sale_return_items(request, sale_id):
    """Add items to a sale return - COMPLETE UPDATED VERSION"""
    sale = get_object_or_404(
        Sale.objects.select_related('sold_by').prefetch_related('items__product', 'items__batch'),
        id=sale_id
    )
    
    if request.method == 'POST':
        form = SaleReturnForm(request.POST)
        if form.is_valid():
            sale_return = form.save(commit=False)
            sale_return.sale = sale
            sale_return.created_by = request.user
            
            # Get balance amount from form
            balance_amount = Decimal(request.POST.get('balance_amount', 0))
            sale_return.balance_amount = balance_amount
            
            # Save the return first to get an ID
            sale_return.save()
            
            # Process return items
            items_data = []
            i = 0
            while f'items[{i}].sale_item' in request.POST:
                sale_item_id = request.POST.get(f'items[{i}].sale_item')
                quantity = request.POST.get(f'items[{i}].quantity')
                reason = request.POST.get(f'items[{i}].reason')
                notes = request.POST.get(f'items[{i}].notes')
                
                if sale_item_id and quantity and int(quantity) > 0:
                    items_data.append({
                        'sale_item_id': sale_item_id,
                        'quantity': int(quantity),
                        'reason': reason,
                        'notes': notes,
                    })
                i += 1
            
            if not items_data:
                messages.error(request, 'Please add at least one item to return.')
                sale_return.delete()
                return redirect('add_sale_return_items', sale_id=sale.id)
            
            total_refund = 0
            for item_data in items_data:
                try:
                    sale_item = SaleItem.objects.get(id=item_data['sale_item_id'])
                    
                    # Validate quantity doesn't exceed available
                    total_returned = SaleReturnItem.objects.filter(
                        sale_item=sale_item
                    ).aggregate(total=Sum('quantity'))['total'] or 0
                    
                    remaining_qty = sale_item.quantity - total_returned
                    
                    if item_data['quantity'] > remaining_qty:
                        messages.error(request, f'Return quantity for {sale_item.product.name} exceeds available quantity.')
                        sale_return.delete()
                        return redirect('add_sale_return_items', sale_id=sale.id)
                    
                    total_price = item_data['quantity'] * sale_item.unit_price
                    
                    return_item = SaleReturnItem.objects.create(
                        sale_return=sale_return,
                        sale_item=sale_item,
                        quantity=item_data['quantity'],
                        unit_price=sale_item.unit_price,
                        total_price=total_price,
                        reason=item_data['reason'],
                        notes=item_data['notes'],
                        batch=sale_item.batch
                    )
                    total_refund += total_price
                    
                except SaleItem.DoesNotExist:
                    messages.error(request, f'Sale item not found: {item_data["sale_item_id"]}')
                    sale_return.delete()
                    return redirect('add_sale_return_items', sale_id=sale.id)
            
            # Update refund amount
            sale_return.refund_amount = total_refund
            
            # Handle exchange product validation
            if sale_return.return_type == 'product':
                if not sale_return.exchange_product:
                    messages.error(request, 'Exchange product is required for product exchange.')
                    sale_return.delete()
                    return redirect('add_sale_return_items', sale_id=sale.id)
                
                if not sale_return.exchange_quantity or sale_return.exchange_quantity <= 0:
                    messages.error(request, 'Valid exchange quantity is required.')
                    sale_return.delete()
                    return redirect('add_sale_return_items', sale_id=sale.id)
                
                # Check if exchange product has sufficient stock
                if sale_return.exchange_product.current_stock < sale_return.exchange_quantity:
                    messages.error(request, f'Insufficient stock for {sale_return.exchange_product.name}. Available: {sale_return.exchange_product.current_stock}')
                    sale_return.delete()
                    return redirect('add_sale_return_items', sale_id=sale.id)
            
            sale_return.save()
            
            messages.success(request, f'Sale return {sale_return.return_number} created successfully!')
            
            # Add balance information to message
            if sale_return.return_type == 'product':
                if balance_amount > 0:
                    messages.info(request, f'Customer will receive ৳{balance_amount:.2f} refund.')
                elif balance_amount < 0:
                    messages.info(request, f'Customer needs to pay ৳{abs(balance_amount):.2f} extra.')
                else:
                    messages.info(request, 'Equal exchange - no balance amount.')
            
            return redirect('sale_return_detail', return_id=sale_return.id)
        else:
            # Form validation failed
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SaleReturnForm()
    
    # Get sale items with return information
    sale_items = []
    for item in sale.items.all():
        total_returned = SaleReturnItem.objects.filter(
            sale_item=item
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        remaining_qty = item.quantity - total_returned
        
        sale_items.append({
            'id': item.id,
            'product': item.product,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total_price': item.total_price,
            'batch': item.batch,
            'returned_quantity': total_returned,
            'remaining_quantity': remaining_qty,
        })
    
    # Get products for the template (for price data)
    products = Product.objects.filter(current_stock__gt=0)
    
    context = {
        'sale': sale,
        'form': form,
        'sale_items': sale_items,
        'products': products,  # Add products for price data
    }
    return render(request, 'core/add_sale_return_items.html', context)

@login_required
@view_permission_required('sale_return_list')
def sale_return_list(request):
    """List all sale returns"""
    returns = SaleReturn.objects.select_related(
        'sale', 'processed_by', 'exchange_product'
    ).prefetch_related('items').all().order_by('-return_date')
    
    # Filters
    status_filter = request.GET.get('status')
    return_type_filter = request.GET.get('return_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status_filter:
        returns = returns.filter(status=status_filter)
    if return_type_filter:
        returns = returns.filter(return_type=return_type_filter)
    if date_from:
        returns = returns.filter(return_date__gte=date_from)
    if date_to:
        returns = returns.filter(return_date__lte=date_to)
    
    # Statistics
    total_returns = returns.count()
    pending_returns = returns.filter(status='pending').count()
    completed_returns = returns.filter(status='completed').count()
    total_refund_amount = returns.aggregate(Sum('refund_amount'))['refund_amount__sum'] or 0
    
    paginator = Paginator(returns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'returns': page_obj,
        'total_returns': total_returns,
        'pending_returns': pending_returns,
        'completed_returns': completed_returns,
        'total_refund_amount': total_refund_amount,
    }
    return render(request, 'core/sale_return_list.html', context)

@login_required
def sale_return_detail(request, return_id):
    """View sale return details"""
    sale_return = get_object_or_404(
        SaleReturn.objects.select_related(
            'sale', 'sale__sold_by', 'processed_by', 'exchange_product'
        ).prefetch_related(
            'items__sale_item__product',
            'items__batch'
        ),
        id=return_id
    )
    
    context = {
        'sale_return': sale_return,
    }
    return render(request, 'core/sale_return_detail.html', context)

@login_required
def process_sale_return(request, return_id):
    """Process sale return (approve/complete) - UPDATED WITH BALANCE HANDLING"""
    sale_return = get_object_or_404(
        SaleReturn.objects.select_related(
            'sale', 'exchange_product'
        ).prefetch_related(
            'items__sale_item__product',
            'items__batch'
        ),
        id=return_id
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        print(f"DEBUG: Processing action: {action}, current status: {sale_return.status}")
        
        try:
            with transaction.atomic():
                if action == 'approve' and sale_return.status == 'pending':
                    sale_return.status = 'approved'
                    sale_return.processed_by = request.user
                    
                    if notes:
                        if sale_return.description:
                            sale_return.description += f"\n\nApproval Notes ({timezone.now().strftime('%Y-%m-%d %H:%M')}): {notes}"
                        else:
                            sale_return.description = f"Approval Notes ({timezone.now().strftime('%Y-%m-%d %H:%M')}): {notes}"
                    
                    sale_return.save()
                    messages.success(request, f'Sale return {sale_return.return_number} approved successfully!')
                
                elif action == 'complete' and sale_return.status == 'approved':
                    print("DEBUG: Starting completion process...")
                    
                    # Process the return based on type
                    if sale_return.return_type == 'money':
                        print("DEBUG: Processing money refund...")
                        
                        # Update the original sale's returned amount
                        original_sale = sale_return.sale
                        original_sale.returned_amount += sale_return.refund_amount
                        original_sale.save()
                        print(f"DEBUG: Updated sale returned_amount to {original_sale.returned_amount}")
                        
                        # Update stock for returned items
                        for return_item in sale_return.items.all():
                            product = return_item.sale_item.product
                            quantity = return_item.quantity
                            batch = return_item.batch
                            
                            print(f"DEBUG: Processing item - {product.name}, Qty: {quantity}")
                            
                            # Update product stock
                            old_product_stock = product.current_stock
                            product.current_stock = old_product_stock + quantity
                            product.save()
                            product.refresh_from_db()
                            
                            print(f"DEBUG: Product {product.name} stock updated from {old_product_stock} to {product.current_stock}")
                            
                            # Update batch quantity if batch exists
                            if batch:
                                old_batch_quantity = batch.current_quantity
                                batch.current_quantity = old_batch_quantity + quantity
                                batch.save()
                                batch.refresh_from_db()
                                print(f"DEBUG: Batch {batch.batch_number} updated from {old_batch_quantity} to {batch.current_quantity}")
                            
                            # Create stock movement record
                            StockMovement.objects.create(
                                product=product,
                                movement_type='return_in',
                                quantity=quantity,
                                batch_number=batch.batch_number if batch else '',
                                reference_number=sale_return.return_number,
                                notes=f"Sale return completed - {sale_return.return_number}",
                                movement_date=timezone.now()
                            )
                        
                        # Handle balance amount for money returns
                        if sale_return.balance_amount != 0:
                            balance_info = f"Balance amount: ৳{abs(sale_return.balance_amount):.2f}"
                            if sale_return.balance_amount > 0:
                                balance_info += " (Refund to customer)"
                            else:
                                balance_info += " (Payment from customer)"
                            messages.info(request, balance_info)
                        
                        messages.success(request, f'Money refund processed. Stock updated and refund recorded.')
                    
                    elif sale_return.return_type == 'product':
                        print("DEBUG: Processing product exchange...")
                        
                        if not sale_return.exchange_product or sale_return.exchange_quantity <= 0:
                            messages.error(request, 'Exchange product and quantity are required for product exchange!')
                            return redirect('sale_return_detail', return_id=sale_return.id)
                        
                        if not sale_return.can_process_exchange:
                            messages.error(request, f'Insufficient stock for exchange product! Available: {sale_return.exchange_product.current_stock}')
                            return redirect('sale_return_detail', return_id=sale_return.id)
                        
                        # Process returned items (add back to stock)
                        for return_item in sale_return.items.all():
                            product = return_item.sale_item.product
                            quantity = return_item.quantity
                            batch = return_item.batch
                            
                            # Update returned product stock
                            old_product_stock = product.current_stock
                            product.current_stock = old_product_stock + quantity
                            product.save()
                            product.refresh_from_db()
                            
                            print(f"DEBUG: Returned product {product.name} stock updated from {old_product_stock} to {product.current_stock}")
                            
                            # Update batch quantity if batch exists
                            if batch:
                                old_batch_quantity = batch.current_quantity
                                batch.current_quantity = old_batch_quantity + quantity
                                batch.save()
                                batch.refresh_from_db()
                                print(f"DEBUG: Batch {batch.batch_number} updated from {old_batch_quantity} to {batch.current_quantity}")
                            
                            # Create stock movement record for return
                            StockMovement.objects.create(
                                product=product,
                                movement_type='return_in',
                                quantity=quantity,
                                batch_number=batch.batch_number if batch else '',
                                reference_number=sale_return.return_number,
                                notes=f"Sale return exchange - {sale_return.return_number}",
                                movement_date=timezone.now()
                            )
                        
                        # Process exchange product (reduce stock)
                        exchange_product = sale_return.exchange_product
                        exchange_quantity = sale_return.exchange_quantity
                        
                        old_exchange_stock = exchange_product.current_stock
                        exchange_product.current_stock = old_exchange_stock - exchange_quantity
                        exchange_product.save()
                        exchange_product.refresh_from_db()
                        
                        print(f"DEBUG: Exchange product {exchange_product.name} stock updated from {old_exchange_stock} to {exchange_product.current_stock}")
                        
                        # Create stock movement for exchange out
                        StockMovement.objects.create(
                            product=exchange_product,
                            movement_type='sale_out',
                            quantity=exchange_quantity,
                            reference_number=sale_return.return_number,
                            notes=f"Exchange for return - {sale_return.return_number}",
                            movement_date=timezone.now()
                        )
                        
                        # Handle balance amount for product exchange
                        if sale_return.balance_amount != 0:
                            balance_info = f"Balance amount: ৳{abs(sale_return.balance_amount):.2f}"
                            if sale_return.balance_amount > 0:
                                balance_info += " (Refund to customer)"
                            else:
                                balance_info += " (Payment from customer)"
                            messages.info(request, balance_info)
                        
                        messages.success(request, f'Product exchange processed. {exchange_quantity} units of {exchange_product.name} issued.')
                    
                    # Update return status
                    sale_return.status = 'completed'
                    sale_return.processed_by = request.user
                    sale_return.processed_at = timezone.now()
                    
                    if notes:
                        if sale_return.description:
                            sale_return.description += f"\n\nCompletion Notes ({timezone.now().strftime('%Y-%m-%d %H:%M')}): {notes}"
                        else:
                            sale_return.description = f"Completion Notes ({timezone.now().strftime('%Y-%m-%d %H:%M')}): {notes}"
                    
                    sale_return.save()
                    print(f"DEBUG: Sale return status updated to: {sale_return.status}")
                    messages.success(request, f'Sale return {sale_return.return_number} completed successfully!')
                
                elif action == 'reject':
                    sale_return.status = 'rejected'
                    sale_return.processed_by = request.user
                    sale_return.processed_at = timezone.now()
                    
                    if notes:
                        if sale_return.description:
                            sale_return.description += f"\n\nRejection Notes ({timezone.now().strftime('%Y-%m-%d %H:%M')}): {notes}"
                        else:
                            sale_return.description = f"Rejection Notes ({timezone.now().strftime('%Y-%m-%d %H:%M')}): {notes}"
                    
                    sale_return.save()
                    messages.warning(request, f'Sale return {sale_return.return_number} rejected.')
                else:
                    messages.error(request, f'Invalid action or status transition: {action} from {sale_return.status}')
                
        except Exception as e:
            print(f"DEBUG: Error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error processing return: {str(e)}')
        
        return redirect('sale_return_detail', return_id=sale_return.id)
    
    context = {
        'sale_return': sale_return,
    }
    return render(request, 'core/process_sale_return.html', context)


@login_required
def search_invoice_for_return(request):
    """Search invoice for return processing - ENHANCED VERSION"""
    query = request.GET.get('q', '').strip()
    
    if query:
        sales = Sale.objects.filter(
            Q(invoice_number__icontains=query) |
            Q(customer_name__icontains=query) |
            Q(customer_phone__icontains=query)
        ).select_related('sold_by').prefetch_related('items__product')[:10]
        
        results = []
        for sale in sales:
            # Calculate total returned amount for this sale
            total_returned = SaleReturn.objects.filter(
                sale=sale, 
                status='completed'
            ).aggregate(total=Sum('refund_amount'))['total'] or 0
            
            results.append({
                'id': sale.id,
                'invoice_number': sale.invoice_number,
                'customer_name': sale.customer_name,
                'customer_phone': sale.customer_phone or 'N/A',
                'sale_date': sale.sale_date.strftime('%Y-%m-%d %H:%M'),
                'total_amount': float(sale.total_amount),
                'total_returned': float(total_returned),
                'sold_by': sale.sold_by.get_full_name() or sale.sold_by.username,
                'remaining_amount': float(sale.total_amount - total_returned),
            })
        
        return JsonResponse(results, safe=False)
    
    return JsonResponse([], safe=False)


@login_required
def sale_return_delete(request, return_id):
    """Delete a sale return (admin only)"""
    sale_return = get_object_or_404(SaleReturn, id=return_id)
    
    if request.method == 'POST':
        return_number = sale_return.return_number
        sale_return.delete()
        
        messages.success(request, f'Sale return {return_number} has been deleted successfully.')
        return redirect('sale_return_list')
    
    return redirect('sale_return_detail', return_id=return_id)



@login_required
@view_permission_required('generate_sales_report')

def generate_sales_report(request):
    """Generate sales report based on filters"""
    print("DEBUG: generate_sales_report view called")
    
    if request.method == 'POST':
        try:
            print("DEBUG: Processing POST request for report generation")
            
            # Get form data
            report_type = request.POST.get('report_type', 'daily')
            date_range = request.POST.get('date_range', 'today')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            product_id = request.POST.get('product')
            category_id = request.POST.get('category')
            user_id = request.POST.get('user')
            company = request.POST.get('company')
            report_format = request.POST.get('report_format', 'detailed')
            include_returns = request.POST.get('include_returns') == 'on'
            action = request.POST.get('action', 'print')
            language = request.GET.get('lang', 'en')
            currency_symbol = request.GET.get('currency', '৳')
            multilingual_context = get_multilingual_context(language)

            print(f"DEBUG: Form data - report_type: {report_type}, date_range: {date_range}, format: {report_format}, action: {action}")

            # Build filters
            filters = Q()
            today = timezone.now().date()
            
            # Date range filtering
            if date_range == 'custom' and start_date and end_date:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                filters &= Q(sale_date__date__range=[start_date_obj, end_date_obj])
                print(f"DEBUG: Custom date range: {start_date} to {end_date}")
            elif date_range == 'today':
                filters &= Q(sale_date__date=today)
                print(f"DEBUG: Today's date: {today}")
            elif date_range == 'yesterday':
                yesterday = today - timedelta(days=1)
                filters &= Q(sale_date__date=yesterday)
                print(f"DEBUG: Yesterday's date: {yesterday}")
            elif date_range == 'this_week':
                start_of_week = today - timedelta(days=today.weekday())
                filters &= Q(sale_date__date__gte=start_of_week)
                print(f"DEBUG: This week from: {start_of_week}")
            elif date_range == 'last_week':
                start_of_week = today - timedelta(days=today.weekday() + 7)
                end_of_week = start_of_week + timedelta(days=6)
                filters &= Q(sale_date__date__range=[start_of_week, end_of_week])
                print(f"DEBUG: Last week: {start_of_week} to {end_of_week}")
            elif date_range == 'this_month':
                start_of_month = today.replace(day=1)
                filters &= Q(sale_date__date__gte=start_of_month)
                print(f"DEBUG: This month from: {start_of_month}")
            elif date_range == 'last_month':
                start_of_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
                end_of_month = today.replace(day=1) - timedelta(days=1)
                filters &= Q(sale_date__date__range=[start_of_month, end_of_month])
                print(f"DEBUG: Last month: {start_of_month} to {end_of_month}")
            else:
                # Default to today
                filters &= Q(sale_date__date=today)
                print(f"DEBUG: Default to today: {today}")

            # Additional filters based on report type
            if report_type == 'product_wise' and product_id:
                filters &= Q(items__product_id=product_id)
                print(f"DEBUG: Product filter: {product_id}")
            elif report_type == 'category_wise' and category_id:
                filters &= Q(items__product__category_id=category_id)
                print(f"DEBUG: Category filter: {category_id}")
            elif report_type == 'user_wise' and user_id:
                filters &= Q(sold_by_id=user_id)
                print(f"DEBUG: User filter: {user_id}")

            # Apply filters to sales
            print("DEBUG: Querying sales data...")
            sales = Sale.objects.filter(filters).select_related('sold_by').prefetch_related('items__product', 'items__batch').distinct()
            sales_count = sales.count()
            print(f"DEBUG: Found {sales_count} sales records")

            # Calculate report statistics
            total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
            total_returns = sales.aggregate(total=Sum('returned_amount'))['total'] or 0
            net_sales = total_sales - total_returns
            total_transactions = sales.count()
            
            # Calculate items sold
            total_items_sold = SaleItem.objects.filter(sale__in=sales).aggregate(total=Sum('quantity'))['total'] or 0
            
            # Calculate returned items
            total_items_returned = 0
            for sale in sales:
                total_items_returned += sale.total_returned_quantity
            
            net_items_sold = total_items_sold - total_items_returned
            average_sale = (net_sales / sales.count()) if sales.exists() else 0

            print(f"DEBUG: Statistics - Gross: {total_sales}, Net: {net_sales}, Transactions: {total_transactions}")

            # Get top products for this report
            top_products = SaleItem.objects.filter(sale__in=sales).values(
                'product__name', 'product__sku'
            ).annotate(
                total_quantity=Sum('quantity'),
                total_amount=Sum('total_price')
            ).order_by('-total_quantity')[:5]

            # Prepare context
            context = {
                'sales': sales,
                'report_type': report_type,
                'date_range': date_range,
                'start_date': start_date,
                'end_date': end_date,
                'product_id': product_id,
                'category_id': category_id,
                'user_id': user_id,
                'company': company,
                'report_format': report_format,
                'include_returns': include_returns,
                'request_user': request.user.get_full_name() or request.user.username,
                
                # Statistics
                'gross_sales': total_sales,
                'net_sales': net_sales,
                'total_returns': total_returns,
                'total_items_sold': total_items_sold,
                'total_items_returned': total_items_returned,
                'net_items_sold': net_items_sold,
                'average_sale': average_sale,
                'total_transactions': total_transactions,
                'top_products': top_products,

                'company_name': multilingual_context['company_name'],
                'report_title': multilingual_context['report_title'],
                'footer_text': multilingual_context['footer_text'],
                'currency_symbol': currency_symbol,
                
                # Additional data
                'today': today,
                'selected_date': today,
                'generated_at': timezone.now(),
            }

            # Add specific product/category/user info if filtered
            if product_id:
                try:
                    product = Product.objects.get(id=product_id)
                    context['selected_product'] = product
                    print(f"DEBUG: Added product: {product.name}")
                except Product.DoesNotExist:
                    print(f"DEBUG: Product not found: {product_id}")

            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    context['selected_category'] = category
                    print(f"DEBUG: Added category: {category.name}")
                except Category.DoesNotExist:
                    print(f"DEBUG: Category not found: {category_id}")

            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    context['selected_user'] = user
                    print(f"DEBUG: Added user: {user.username}")
                except User.DoesNotExist:
                    print(f"DEBUG: User not found: {user_id}")

            # Handle PDF download
            if action == 'download_pdf':
                print("DEBUG: Generating PDF download...")
                # Generate PDF using ReportLab
                try:
                    pdf_content = generate_sales_report_pdf(context)
                    
                    if pdf_content and len(pdf_content) > 100:  # Basic validation that PDF has content
                        # Create filename
                        filename = f"sales_report_{report_type}_{today}.pdf"
                        
                        # Return PDF response
                        response = HttpResponse(pdf_content, content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{filename}"'
                        print("DEBUG: PDF response created successfully")
                        return response
                    else:
                        error_msg = "Generated PDF is empty or too small"
                        print(f"DEBUG: {error_msg}, PDF size: {len(pdf_content) if pdf_content else 0}")
                        messages.error(request, "Failed to generate PDF. The generated file was empty.")
                        return redirect('daily_sale_report')
                        
                except Exception as pdf_error:
                    error_msg = f'PDF generation failed: {str(pdf_error)}'
                    print(f"DEBUG: {error_msg}")
                    messages.error(request, "Failed to generate PDF. Please check the server logs.")
                    return redirect('daily_sale_report')
                    
            else:
                # For HTML display, show success message and render template
                print("DEBUG: Rendering HTML template")
                messages.success(request, f"Report generated successfully! Found {total_transactions} transactions totaling {currency_symbol}{net_sales:,.2f}.")
                return render(request, 'core/print_report_template.html', context)

        except Exception as e:
            error_msg = f'Error generating report: {str(e)}'
            print(f"DEBUG: {error_msg}")
            import traceback
            traceback.print_exc()
            
            messages.error(request, "An error occurred while generating the report. Please try again.")
            
            # Return empty context on error
            context = {
                'error': error_msg,
                'sales': [],
                'gross_sales': 0,
                'net_sales': 0,
                'total_returns': 0,
                'total_items_sold': 0,
                'total_items_returned': 0,
                'net_items_sold': 0,
                'average_sale': 0,
                'total_transactions': 0,
                'top_products': [],
                'today': timezone.now().date(),
                'company_name': 'Shop Management System',
                'report_title': 'Sales Report',
                'footer_text': 'Shop Management System - Confidential Report',
                'currency_symbol': '৳',
            }
            return render(request, 'core/print_report_template.html', context)

    # If GET request, redirect to report form
    print("DEBUG: GET request redirected to daily_sale_report")
    messages.info(request, 'Please use the report form to generate sales reports.')
    return redirect('daily_sale_report')

def get_multilingual_context(language='en'):
    """Get multilingual text based on language"""
    contexts = {
        'en': {  # English
            'company_name': 'SHOP MANAGEMENT SYSTEM',
            'report_title': 'SALES REPORT',
            'footer_text': 'Shop Management System - Confidential Report'
        },
        'bn': {  # Bengali
            'company_name': 'দোকান ব্যবস্থাপনা সিস্টেম',
            'report_title': 'বিক্রয় রিপোর্ট',
            'footer_text': 'দোকান ব্যবস্থাপনা সিস্টেম - গোপনীয় রিপোর্ট'
        },
        'ar': {  # Arabic
            'company_name': 'نظام إدارة المتجر',
            'report_title': 'تقرير المبيعات',
            'footer_text': 'نظام إدارة المتجر - تقرير سري'
        },
        'es': {  # Spanish
            'company_name': 'SISTEMA DE GESTIÓN DE TIENDA',
            'report_title': 'INFORME DE VENTAS',
            'footer_text': 'Sistema de Gestión de Tienda - Informe Confidencial'
        },
        'fr': {  # French
            'company_name': 'SYSTÈME DE GESTION DE BOUTIQUE',
            'report_title': 'RAPPORT DE VENTES',
            'footer_text': 'Système de Gestion de Boutique - Rapport Confidentiel'
        },
        'hi': {  # Hindi
            'company_name': 'दुकान प्रबंधन प्रणाली',
            'report_title': 'बिक्री रिपोर्ट',
            'footer_text': 'दुकान प्रबंधन प्रणाली - गोपनीय रिपोर्ट'
        }
    }
    
    return contexts.get(language, contexts['en'])


@login_required
@view_permission_required('product_edit')
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            
            # Handle barcode generation if not provided
            if not product.barcode and product.sku:
                product.generate_barcode()
            
            product.save()
            messages.success(request, 'Product updated successfully')
            return redirect('product_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'core/product_form.html', {'form': form})


@login_required
@view_permission_required('product_delete')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully')
        return redirect('product_list')
    
    return render(request, 'core/product_confirm_delete.html', {'product': product})

@login_required
def search_product_by_barcode(request):
    """API endpoint to search product by barcode or name"""
    query = request.GET.get('barcode', '').strip()
    
    if query:
        try:
            # First try exact barcode match (maintains existing functionality)
            product = Product.objects.get(barcode=query)
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'barcode': product.barcode,
                    'selling_price': str(product.selling_price),
                    'current_stock': product.current_stock,
                    'has_expiry': product.has_expiry,
                }
            })
        except Product.DoesNotExist:
            # NEW: If no exact barcode match, search by name or partial barcode
            products = Product.objects.filter(
                Q(name__icontains=query) | 
                Q(barcode__icontains=query) |
                Q(sku__icontains=query)
            )[:10]  # Limit results for performance
            
            if products.exists():
                product_list = []
                for product in products:
                    product_list.append({
                        'id': product.id,
                        'name': product.name,
                        'sku': product.sku,
                        'barcode': product.barcode,
                        'selling_price': str(product.selling_price),
                        'current_stock': product.current_stock,
                        'has_expiry': product.has_expiry,
                    })
                
                return JsonResponse({
                    'success': True,
                    'products': product_list,
                    'multiple': True  # Flag to indicate multiple results
                })
            
            return JsonResponse({
                'success': False,
                'error': 'No products found with that name or barcode'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'No search query provided'
    })


def search_customer(request):
    """Search customers by name or phone"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'success': False, 'message': 'Please enter at least 2 characters'})
    
    customers = Customer.objects.filter(
        Q(name__icontains=query) | Q(phone__icontains=query),
        is_active=True
    ).values('id', 'name', 'phone', 'total_due', 'credit_limit')[:10]
    
    return JsonResponse({
        'success': True,
        'customers': list(customers)
    })

def get_customer_due_details(request, customer_id):
    """Get customer due details and due sales"""
    try:
        customer = Customer.objects.get(id=customer_id)
        due_sales = Sale.objects.filter(
            customer=customer,
            payment_status__in=['due', 'partial']
        ).values('invoice_number', 'sale_date', 'total_amount', 'paid_amount')
        
        # Calculate remaining due for each sale
        for sale in due_sales:
            sale['remaining_due'] = sale['total_amount'] - sale['paid_amount']
        
        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'total_due': float(customer.total_due),
                'credit_limit': float(customer.credit_limit),
            },
            'due_sales': list(due_sales)
        })
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Customer not found'})

def make_due_payment(request):
    """Process due payment for customer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_id = data.get('customer_id')
            amount = Decimal(data.get('amount', 0))
            payment_method = data.get('payment_method', 'cash')
            notes = data.get('notes', '')
            
            customer = Customer.objects.get(id=customer_id)
            
            if amount <= 0:
                return JsonResponse({'success': False, 'message': 'Invalid payment amount'})
            
            if amount > customer.total_due:
                return JsonResponse({'success': False, 'message': 'Payment amount exceeds total due'})
            
            # Create due payment
            due_payment = DuePayment.objects.create(
                customer=customer,
                amount=amount,
                payment_method=payment_method,
                notes=notes,
                received_by=request.user
            )
            
            # Update corresponding sales (FIFO method)
            remaining_payment = amount
            due_sales = Sale.objects.filter(
                customer=customer,
                payment_status__in=['due', 'partial']
            ).order_by('sale_date')
            
            for sale in due_sales:
                if remaining_payment <= 0:
                    break
                    
                sale_due = sale.total_amount - sale.paid_amount
                payment_to_apply = min(remaining_payment, sale_due)
                
                sale.paid_amount += payment_to_apply
                remaining_payment -= payment_to_apply
                
                # Update sale payment status
                if sale.paid_amount >= sale.total_amount:
                    sale.payment_status = 'paid'
                else:
                    sale.payment_status = 'partial'
                
                sale.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Payment of ৳{amount} received successfully',
                'new_due': float(customer.total_due)
            })
            
        except Customer.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Customer not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error processing payment: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})



#customer Due payment views

@login_required
@view_permission_required('customer_due_report')
def customer_due_report(request):
    """Customer Due Report with accurate due calculation - FIXED VERSION"""
    # Get all active customers
    customers = Customer.objects.filter(is_active=True).order_by('-total_due')
    
    # Apply filters
    customer_filter = request.GET.get('customer', '')
    due_status = request.GET.get('due_status', 'all')
    min_due = request.GET.get('min_due', '')
    max_due = request.GET.get('max_due', '')
    
    if customer_filter:
        customers = customers.filter(
            Q(name__icontains=customer_filter) | 
            Q(phone__icontains=customer_filter)
        )
    
    # Force update due amounts for all filtered customers to ensure accuracy
    for customer in customers:
        customer.update_due_amount()
        customer.refresh_from_db()  # Refresh to get updated values
    
    # Re-apply filters after updating due amounts
    if due_status == 'with_due':
        customers = customers.filter(total_due__gt=0)
    elif due_status == 'without_due':
        customers = customers.filter(total_due=0)
    
    if min_due:
        try:
            min_due_decimal = Decimal(min_due)
            customers = customers.filter(total_due__gte=min_due_decimal)
        except (ValueError, InvalidOperation):
            pass
    
    if max_due:
        try:
            max_due_decimal = Decimal(max_due)
            customers = customers.filter(total_due__lte=max_due_decimal)
        except (ValueError, InvalidOperation):
            pass
    
    # Get due invoices for each customer
    for customer in customers:
        customer.due_invoices = Sale.objects.filter(
            customer=customer,
            payment_status__in=['due', 'partial']
        ).order_by('sale_date')
        customer.due_invoices_count = customer.due_invoices.count()
        customer.actual_due_amount = sum(invoice.remaining_due for invoice in customer.due_invoices)
    
    # Calculate summary statistics
    total_customers = customers.count()
    customers_with_due = customers.filter(total_due__gt=0).count()
    total_due_amount = customers.aggregate(
        total_due=Sum('total_due')
    )['total_due'] or Decimal('0')
    
    # Calculate average due per customer with due
    avg_due_per_customer = total_due_amount / customers_with_due if customers_with_due > 0 else Decimal('0')
    
    paginator = Paginator(customers, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'total_customers': total_customers,
        'customers_with_due': customers_with_due,
        'total_due_amount': total_due_amount,
        'avg_due_per_customer': avg_due_per_customer,
        'today': timezone.now().date(),
        'filters': {
            'customer': customer_filter,
            'due_status': due_status,
            'min_due': min_due,
            'max_due': max_due,
        }
    }
    return render(request, 'core/customer_due_report.html', context)

@login_required
@view_permission_required('due_collection_report')
def due_collection_report(request):
    """Due Collection Report with filtering"""
    payments = DuePayment.objects.select_related('customer', 'received_by').all().order_by('-payment_date')
    
    # Filters
    customer_filter = request.GET.get('customer', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    payment_method = request.GET.get('payment_method', '')
    
    if customer_filter:
        payments = payments.filter(
            Q(customer__name__icontains=customer_filter) | 
            Q(customer__phone__icontains=customer_filter)
        )
    
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    # Summary statistics
    total_payments = payments.count()
    total_collected = payments.aggregate(
        total=Sum('amount', output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total'] or Decimal('0')
    average_payment = total_collected / total_payments if total_payments > 0 else Decimal('0')
    
    # Payment method breakdown
    payment_methods = payments.values('payment_method').annotate(
        total_amount=Sum('amount', output_field=DecimalField(max_digits=10, decimal_places=2)),
        payment_count=Count('id')
    ).order_by('-total_amount')
    
    # Daily collection trend (last 30 days)
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    daily_collections = DuePayment.objects.filter(
        payment_date__date__gte=start_date
    ).values('payment_date__date').annotate(
        total_amount=Sum('amount', output_field=DecimalField(max_digits=10, decimal_places=2)),
        payment_count=Count('id')
    ).order_by('payment_date__date')
    
    daily_labels = [collection['payment_date__date'].strftime('%Y-%m-%d') for collection in daily_collections]
    daily_data = [float(collection['total_amount']) for collection in daily_collections]
    
    # Top customers by collection
    top_customers = payments.values('customer__name', 'customer__phone').annotate(
        total_paid=Sum('amount', output_field=DecimalField(max_digits=10, decimal_places=2)),
        payment_count=Count('id')
    ).order_by('-total_paid')[:5]
    
    # Get customers with current due for quick payment
    customers_with_due = Customer.objects.filter(total_due__gt=0, is_active=True).order_by('-total_due')[:10]
    
    paginator = Paginator(payments, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'payments': page_obj,
        'total_payments': total_payments,
        'total_collected': total_collected,
        'average_payment': average_payment,
        'payment_methods': payment_methods,
        'top_customers': top_customers,
        'customers_with_due': customers_with_due,
        'daily_labels': json.dumps(daily_labels),
        'daily_data': json.dumps(daily_data),
        'today': today,
        'start_date': start_date,
        'filters': {
            'customer': customer_filter,
            'date_from': date_from,
            'date_to': date_to,
            'payment_method': payment_method,
        }
    }
    return render(request, 'core/due_collection_report.html', context)

@login_required

def process_due_payment(request):
    """Process due payment with automatic invoice allocation - FIXED VERSION"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_id = data.get('customer_id')
            amount = Decimal(data.get('amount', 0))
            payment_method = data.get('payment_method', 'cash')
            notes = data.get('notes', '')
            
            customer = Customer.objects.get(id=customer_id)
            
            if amount <= 0:
                return JsonResponse({
                    'success': False, 
                    'message': 'Payment amount must be greater than zero'
                })
            
            # Get due invoices ordered by date (oldest first) - FIFO
            due_invoices = Sale.objects.filter(
                customer=customer,
                payment_status__in=['due', 'partial']
            ).order_by('sale_date', 'id')
            
            if not due_invoices.exists():
                return JsonResponse({
                    'success': False, 
                    'message': 'Customer has no due invoices'
                })
            
            total_due = sum(invoice.remaining_due for invoice in due_invoices)
            
            if amount > total_due:
                return JsonResponse({
                    'success': False, 
                    'message': f'Payment amount (৳{amount}) exceeds total due (৳{total_due})'
                })
            
            # Allocate payment to invoices using FIFO
            allocated_payments = []
            remaining_amount = amount
            
            with transaction.atomic():
                for invoice in due_invoices:
                    if remaining_amount <= 0:
                        break
                        
                    invoice_due = invoice.remaining_due
                    payment_to_apply = min(remaining_amount, invoice_due)
                    
                    # Record allocation details
                    allocated_payments.append({
                        'invoice_number': invoice.invoice_number,
                        'sale_date': invoice.sale_date.strftime('%Y-%m-%d'),
                        'due_amount': float(invoice_due),
                        'allocated_amount': float(payment_to_apply),
                        'remaining_due_after': float(invoice_due - payment_to_apply)
                    })
                    
                    # Update sale
                    invoice.paid_amount += payment_to_apply
                    remaining_amount -= payment_to_apply
                    
                    # Update sale payment status
                    if invoice.paid_amount >= invoice.total_amount:
                        invoice.payment_status = 'paid'
                    else:
                        invoice.payment_status = 'partial'
                    
                    invoice.save()
                
                # Create due payment record
                due_payment = DuePayment.objects.create(
                    customer=customer,
                    amount=amount,
                    payment_method=payment_method,
                    notes=notes,
                    received_by=request.user,
                    allocated_details=allocated_payments
                )
                
                # CRITICAL FIX: Force update customer due amount
                customer.refresh_from_db()
                customer.update_due_amount()
                customer.refresh_from_db()  # Refresh again to get updated total_due
            
            return JsonResponse({
                'success': True,
                'message': f'Payment of ৳{amount} processed successfully',
                'allocated_payments': allocated_payments,
                'new_total_due': float(customer.total_due)
            })
            
        except Customer.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Customer not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error processing payment: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_customer_due_details(request, customer_id):
    """Get detailed due information for a customer"""
    try:
        customer = Customer.objects.get(id=customer_id)
        
        # Get due invoices with details
        due_invoices = Sale.objects.filter(
            customer=customer,
            payment_status__in=['due', 'partial']
        ).order_by('sale_date').values(
            'id', 'invoice_number', 'sale_date', 'total_amount', 
            'paid_amount', 'payment_status'
        )
        
        # Calculate remaining due for each invoice
        for invoice in due_invoices:
            invoice['remaining_due'] = invoice['total_amount'] - invoice['paid_amount']
            invoice['sale_date'] = invoice['sale_date'].strftime('%Y-%m-%d %H:%M')
        
        total_due = sum(invoice['remaining_due'] for invoice in due_invoices)
        
        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'total_due': float(total_due),
                'credit_limit': float(customer.credit_limit),
            },
            'due_invoices': list(due_invoices),
            'total_due_amount': float(total_due),
            'due_invoice_count': len(due_invoices)
        })
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Customer not found'})
    


@login_required
def debug_customer_due(request, customer_id):
    """Debug view to check customer due calculation"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Get all sales for this customer
    sales = Sale.objects.filter(customer=customer).order_by('sale_date')
    
    due_sales = sales.filter(payment_status__in=['due', 'partial'])
    
    # Calculate manually
    manual_total_due = sum(sale.remaining_due for sale in due_sales)
    
    context = {
        'customer': customer,
        'sales': sales,
        'due_sales': due_sales,
        'manual_total_due': manual_total_due,
        'customer_total_due': customer.total_due,
        'is_consistent': manual_total_due == customer.total_due,
    }
    
    return render(request, 'core/debug_customer_due.html', context)

@login_required
def force_update_customer_due(request, customer_id):
    """Force update customer due amount"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        old_due = customer.total_due
        customer.update_due_amount()
        customer.refresh_from_db()
        
        messages.success(
            request, 
            f'Force updated due amount for {customer.name}: ৳{old_due} → ৳{customer.total_due}'
        )
        
        return redirect('debug_customer_due', customer_id=customer_id)
    
    return redirect('debug_customer_due', customer_id=customer_id)

@login_required
def refresh_all_due_amounts(request):
    """Refresh due amounts for all customers on the current page"""
    try:
        updated_count = 0
        customers = Customer.objects.filter(is_active=True)
        
        for customer in customers:
            old_due = customer.total_due
            customer.update_due_amount()
            customer.refresh_from_db()
            if customer.total_due != old_due:
                updated_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Refreshed due amounts for {customers.count()} customers. {updated_count} updated.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error refreshing due amounts: {str(e)}'
        })

@login_required
def force_update_all_due_amounts(request):
    """Force update due amounts for ALL customers"""
    try:
        from django.db import transaction
        
        with transaction.atomic():
            customers = Customer.objects.all()
            updated_count = 0
            
            for customer in customers:
                old_due = customer.total_due
                
                # Recalculate from scratch
                due_sales = Sale.objects.filter(
                    customer=customer,
                    payment_status__in=['due', 'partial']
                )
                
                total_due = due_sales.aggregate(
                    total_due=Sum(F('total_amount') - F('paid_amount'))
                )['total_due'] or Decimal('0')
                
                if customer.total_due != total_due:
                    customer.total_due = total_due
                    customer.save(update_fields=['total_due', 'updated_at'])
                    updated_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Force updated due amounts for {customers.count()} customers. {updated_count} records changed.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error force updating due amounts: {str(e)}'
        })
    



@login_required
def get_product_details(request):
    """API endpoint to get product details for exchange"""
    product_id = request.GET.get('product_id')
    
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'selling_price': str(product.selling_price),
                    'current_stock': product.current_stock,
                    'cost_price': str(product.cost_price),
                }
            })
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
    
    return JsonResponse({'success': False, 'error': 'No product ID provided'})



#category & Supplier

@require_http_methods(["GET"])
def search_categories(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    categories = Category.objects.filter(name__icontains=query)[:10]
    results = []
    for category in categories:
        results.append({
            'id': category.id,
            'name': category.name,
            'description': category.description
        })
    
    return JsonResponse(results, safe=False)

@require_http_methods(["GET"])
def search_suppliers(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    suppliers = Supplier.objects.filter(name__icontains=query)[:10]
    results = []
    for supplier in suppliers:
        results.append({
            'id': supplier.id,
            'name': supplier.name,
            'contact_person': supplier.contact_person,
            'phone': supplier.phone
        })
    
    return JsonResponse(results, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def create_category(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Category name is required'})
        
        # Check if category already exists
        if Category.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'Category already exists'})
        
        category = Category.objects.create(
            name=name,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def create_supplier(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        contact_person = data.get('contact_person', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        address = data.get('address', '').strip()
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Supplier name is required'})
        
        # Check if supplier already exists
        if Supplier.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'Supplier already exists'})
        
        supplier = Supplier.objects.create(
            name=name,
            contact_person=contact_person,
            email=email,
            phone=phone,
            address=address
        )
        
        return JsonResponse({
            'success': True,
            'supplier': {
                'id': supplier.id,
                'name': supplier.name,
                'contact_person': supplier.contact_person,
                'phone': supplier.phone
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    


