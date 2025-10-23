from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum, F
from core.models import Customer, Sale
from decimal import Decimal

class Command(BaseCommand):
    help = 'Fix customer due amounts by recalculating from sales data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer',
            type=int,
            help='Fix specific customer by ID',
        )

    def handle(self, *args, **options):
        customer_id = options.get('customer')
        
        if customer_id:
            customers = Customer.objects.filter(id=customer_id)
            if not customers.exists():
                self.stdout.write(
                    self.style.ERROR(f'Customer with ID {customer_id} not found')
                )
                return
        else:
            customers = Customer.objects.all()

        fixed_count = 0
        with transaction.atomic():
            for customer in customers:
                old_due = customer.total_due
                
                # Recalculate due amount from sales
                due_sales = Sale.objects.filter(
                    customer=customer,
                    payment_status__in=['due', 'partial']
                )
                
                total_due = due_sales.aggregate(
                    total_due=Sum(F('total_amount') - F('paid_amount'))
                )['total_due'] or Decimal('0')
                
                # Update if different
                if customer.total_due != total_due:
                    customer.total_due = total_due
                    customer.save(update_fields=['total_due', 'updated_at'])
                    fixed_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Fixed {customer.name} (ID: {customer.id}): ৳{old_due} -> ৳{total_due}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'No change needed for {customer.name} (ID: {customer.id}): ৳{old_due}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully fixed {fixed_count} customer due amounts')
        )