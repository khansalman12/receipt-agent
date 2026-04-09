"""Management command to display receipt processing statistics.

Usage:
    python manage.py receiptstats
    python manage.py receiptstats --status FLAGGED
    python manage.py receiptstats --days 7
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone

from api.models import ExpenseReport, Receipt


class Command(BaseCommand):
    help = "Display receipt processing statistics and fraud metrics"

    def add_arguments(self, parser):
        parser.add_argument(
            "--status",
            type=str,
            choices=["PENDING", "APPROVED", "REJECTED", "FLAGGED"],
            help="Filter reports by status",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Only include data from the last N days",
        )

    def handle(self, *args, **options):
        reports = ExpenseReport.objects.all()
        receipts = Receipt.objects.all()

        if options["days"]:
            cutoff = timezone.now() - timedelta(days=options["days"])
            reports = reports.filter(created_at__gte=cutoff)
            receipts = receipts.filter(created_at__gte=cutoff)
            self.stdout.write(f"\nShowing data from the last {options['days']} days\n")

        if options["status"]:
            reports = reports.filter(status=options["status"])
            self.stdout.write(f"Filtered by status: {options['status']}\n")

        # Report stats
        report_counts = reports.values("status").annotate(count=Count("id"))
        total_reports = reports.count()
        total_spend = reports.aggregate(total=Sum("total_amount"))["total"] or 0

        self.stdout.write("\n--- Expense Reports ---")
        self.stdout.write(f"  Total reports:  {total_reports}")
        for entry in report_counts:
            self.stdout.write(f"  {entry['status']:12s}  {entry['count']}")
        self.stdout.write(f"  Total spend:    ${total_spend:,.2f}")

        # Receipt stats
        total_receipts = receipts.count()
        processed = receipts.exclude(merchant_name__isnull=True).count()
        avg_fraud = receipts.aggregate(avg=Avg("fraud_score"))["avg"] or 0
        high_risk = receipts.filter(fraud_score__gte=70).count()

        self.stdout.write("\n--- Receipts ---")
        self.stdout.write(f"  Total receipts: {total_receipts}")
        self.stdout.write(f"  Processed:      {processed}")
        self.stdout.write(f"  Unprocessed:    {total_receipts - processed}")
        self.stdout.write(f"  Avg fraud score: {avg_fraud:.1f}/100")
        self.stdout.write(f"  High risk (>=70): {high_risk}")

        # Top merchants
        top_merchants = (
            receipts
            .exclude(merchant_name__isnull=True)
            .values("merchant_name")
            .annotate(count=Count("id"), total=Sum("total_amount"))
            .order_by("-count")[:5]
        )

        if top_merchants:
            self.stdout.write("\n--- Top Merchants ---")
            for m in top_merchants:
                total = m["total"] or 0
                self.stdout.write(
                    f"  {m['merchant_name']:30s}  {m['count']} receipts  ${total:,.2f}"
                )

        self.stdout.write("")
