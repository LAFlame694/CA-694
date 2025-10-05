from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.db import models
from decimal import Decimal
import uuid

# Create your models here.
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
    ]

    chama = models.ForeignKey("app.Chama", on_delete=models.CASCADE, related_name='transactions')
    member = models.ForeignKey(
        "app.Member", 
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = 'transactions'
    )
    initiated_by = models.CharField(
        max_length = 100,
        blank = True,
        null = True,
        help_text = "Name or identifier of the transaction initiator",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    checkout_id = models.CharField(max_length=100, unique=True)
    mpesa_code = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        default="deposit"
    )

    def __str__(self):
        who = self.member.user.username if self.member else (self.initiated_by or "Unknown")
        return f"{who} - {self.amount} KES ({self.transaction_type})"

class AuditLog(models.Model):
    ACTION_TYPES = [
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
    ]

    transaction = models.OneToOneField(
        "Transaction",
        on_delete = models.CASCADE,
        related_name = 'audit_log'
    )

    chama = models.ForeignKey("app.Chama", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    reference_no = models.CharField(max_length=100, unique=True)

    # prevent deletion of audit logs
    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Audit logs cannot be edited once created.")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError("Audit logs cannot be deleted.")
    
    def __str__(self):
        return f"[{self.action_type.upper()}] {self.chama.name} - {self.amount} KES"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    @receiver(post_save, sender=Transaction)
    def create_audit_log(sender, instance, created, **kwargs):
        if created:
            try:
                AuditLog.objects.create(
                    transaction = instance,
                    chama = instance.chama,
                    user = None,  # User info not available here
                    action_type = instance.transaction_type,
                    amount = instance.amount,
                    reference_no = f"TXN-{uuid.uuid4().hex[:8].upper()}",
                )
            
            except Exception as e:
                print(f"Audit log creation failed: {e}")