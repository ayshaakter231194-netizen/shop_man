from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import SupplierBill
from django.db.models import Q
import datetime

class Command(BaseCommand):
    help = 'Check for due bills and update their status to overdue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        today = timezone.now().date()
        
        # Find bills that are due and should be marked as overdue
        due_bills = SupplierBill.objects.filter(
            Q(status='pending') | Q(status='partial'),
            due_amount__gt=0
        ).select_related('supplier', 'purchase_order')
        
        # Filter in Python using the is_overdue property
        overdue_bills = [bill for bill in due_bills if bill.is_overdue]
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Found {len(overdue_bills)} bills that are overdue and need status update"
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN - No changes will be made")
            )
        
        updated_count = 0
        for bill in overdue_bills:
            if dry_run:
                self.stdout.write(
                    f"Would update: BILL-{bill.bill_number} "
                    f"(Due: {bill.due_date.date() if hasattr(bill.due_date, 'date') else bill.due_date}, "
                    f"Amount: ৳{bill.effective_due_amount:.2f}, "
                    f"Supplier: {bill.supplier.name})"
                )
            else:
                # Update the status to overdue
                bill.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated: BILL-{bill.bill_number} to overdue status"
                    )
                )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {updated_count} bills to overdue status"
                )
            )
        
        # Show current overdue statistics
        overdue_bills_all = SupplierBill.objects.filter(status='overdue')
        total_overdue_amount = 0
        overdue_bills_list = list(overdue_bills_all)
        
        for bill in overdue_bills_list:
            total_overdue_amount += bill.effective_due_amount
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("OVERDUE BILLS SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Total overdue bills: {len(overdue_bills_list)}")
        self.stdout.write(f"Total overdue amount: ৳{total_overdue_amount:.2f}")
        
        # Show top overdue suppliers
        from collections import defaultdict
        supplier_totals = defaultdict(lambda: {'amount': 0, 'count': 0})
        
        for bill in overdue_bills_list:
            supplier_totals[bill.supplier.name]['amount'] += bill.effective_due_amount
            supplier_totals[bill.supplier.name]['count'] += 1
        
        # Sort suppliers by total overdue amount
        sorted_suppliers = sorted(
            supplier_totals.items(), 
            key=lambda x: x[1]['amount'], 
            reverse=True
        )[:5]
        
        if sorted_suppliers:
            self.stdout.write("\nTop overdue suppliers:")
            for supplier_name, data in sorted_suppliers:
                self.stdout.write(
                    f"  {supplier_name}: "
                    f"৳{data['amount']:.2f} "
                    f"({data['count']} bills)"
                )