from django.core.management.base import BaseCommand
from core.models import ViewPermission

class Command(BaseCommand):
    help = 'Populate view permissions'
    
    def handle(self, *args, **options):
        permissions_data = [
            # Dashboard
            {'name': 'Dashboard Access', 'view_code': 'dashboard', 'description': 'Access to main dashboard'},
            
            # Products
            {'name': 'View Products', 'view_code': 'product_list', 'description': 'View product list'},
            {'name': 'Create Products', 'view_code': 'product_create', 'description': 'Create new products'},
            {'name': 'Edit Products', 'view_code': 'product_edit', 'description': 'Edit existing products'},
            {'name': 'Delete Products', 'view_code': 'product_delete', 'description': 'Delete products'},
            
            # Stock
            {'name': 'Stock Adjustment', 'view_code': 'stock_adjustment', 'description': 'Adjust stock levels'},
            {'name': 'Stock Reports', 'view_code': 'stock_report', 'description': 'View stock reports'},
            {'name': 'Expiry Reports', 'view_code': 'expiry_report', 'description': 'View expiry reports'},
            {'name': 'Batch Management', 'view_code': 'batch_management', 'description': 'Manage product batches'},
            
            # Sales
            {'name': 'POS Sales', 'view_code': 'pos_sale', 'description': 'Access Point of Sale'},
            {'name': 'Daily Sales Report', 'view_code': 'daily_sale_report', 'description': 'View daily sales reports'},
            {'name': 'Profit Reports', 'view_code': 'profit_report', 'description': 'View profit reports'},
            {'name': 'Sale Returns', 'view_code': 'sale_return_list', 'description': 'Manage sale returns'},
            
            # Purchases
            {'name': 'Create Purchase Orders', 'view_code': 'purchase_order_create', 'description': 'Create purchase orders'},
            {'name': 'Purchase Reports', 'view_code': 'purchase_report', 'description': 'View purchase reports'},
            {'name': 'Purchase Returns', 'view_code': 'purchase_return_list', 'description': 'Manage purchase returns'},
            
            # Supplier & Billing
            {'name': 'Supplier Bills', 'view_code': 'supplier_bills', 'description': 'Manage supplier bills'},
            {'name': 'Bill Dashboard', 'view_code': 'bill_dashboard', 'description': 'Access bill dashboard'},
            
            # Customers
            {'name': 'Customer Management', 'view_code': 'customer_management', 'description': 'Manage customers'},
            {'name': 'Customer Due Reports', 'view_code': 'customer_due_report', 'description': 'View customer due reports'},
            {'name': 'Due Collection Reports', 'view_code': 'due_collection_report', 'description': 'View due collection reports'},
            
            # Reports
            {'name': 'Generate Sales Reports', 'view_code': 'generate_sales_report', 'description': 'Generate sales reports'},
            
            # Administration
            {'name': 'User Management', 'view_code': 'user_management', 'description': 'Manage system users'},
        ]
        
        created_count = 0
        for perm_data in permissions_data:
            permission, created = ViewPermission.objects.get_or_create(
                view_code=perm_data['view_code'],
                defaults=perm_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created permission: {perm_data["name"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} view permissions')
        )