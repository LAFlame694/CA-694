from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid

# Create your models here.
class VirtualAccount(models.Model):
    chama = models.ForeignKey("Chama", on_delete=models.CASCADE, related_name="virtual_accounts")
    member = models.ForeignKey("Member", on_delete=models.CASCADE, related_name="virtual_accounts", null=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # use chama.account_number
    account_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        if self.member:
            return f"{self.chama.name} - {self.member.user.username} {self.account_number}"
        return f"{self.chama.name} Main Account ({self.account_number})"

class Contribution(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
    ]

    member = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])
    date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)

    def __str__(self):
        return f"{self.member.user.username} - {self.amount} via {self.payment_method}"


class Member(models.Model):
    ROLE_CHOICES = [
        ('leader', 'Leader'),
        ('member', 'Member'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chama = models.ForeignKey('Chama', on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'chama') # prevents duplicate membership

    def __str__(self):
        return f"{self.user.username} -> {self.chama.name} ({self.role})"

    """
    How Member Management Works:
    
    1. When someone creates a Chama, they are automatically assigned as Leader in the Member table.
    2. The Leader can later invite/add members by selecting existing users or entering their email/username.
    3. Each user can belong to multiple Chamas.
    """

class Chama(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chamas_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    account_number = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            # generate a unique account number
            self.account_number = str(uuid.uuid4().int)[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username
