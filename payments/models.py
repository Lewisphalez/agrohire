from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
from bookings.models import Booking


class Payment(models.Model):
    """
    Model for payment transactions
    """
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Basic payment information
    payment_number = models.CharField(max_length=50, unique=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    
    # Amount and method
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='mpesa')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # M-Pesa specific fields
    mpesa_phone_number = models.CharField(max_length=15, blank=True)
    mpesa_transaction_id = models.CharField(max_length=50, blank=True)
    mpesa_merchant_request_id = models.CharField(max_length=50, blank=True)
    mpesa_checkout_request_id = models.CharField(max_length=50, blank=True)
    mpesa_result_code = models.CharField(max_length=10, blank=True)
    mpesa_result_desc = models.TextField(blank=True)
    
    # Payment details
    currency = models.CharField(max_length=3, default='KES')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, default=1.000000)
    
    # Fees and charges
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    payment_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.payment_number} - {self.booking.booking_number}"
    
    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = self.generate_payment_number()
        if not self.total_amount:
            self.total_amount = self.amount + self.processing_fee + self.platform_fee
        super().save(*args, **kwargs)
    
    def generate_payment_number(self):
        """Generate unique payment number"""
        import random
        import string
        from django.utils import timezone
        
        while True:
            # Format: PAY-YYYYMMDD-XXXX
            date_part = timezone.now().strftime('%Y%m%d')
            random_part = ''.join(random.choices(string.digits, k=4))
            payment_number = f"PAY-{date_part}-{random_part}"
            
            if not Payment.objects.filter(payment_number=payment_number).exists():
                return payment_number
    
    @property
    def is_successful(self):
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        return self.status in ['pending', 'processing']
    
    @property
    def is_failed(self):
        return self.status in ['failed', 'cancelled']
    
    def process_mpesa_payment(self, phone_number):
        """Initiate M-Pesa payment"""
        from .api import MPesaAPI
        
        self.mpesa_phone_number = phone_number
        self.save()
        
        mpesa_api = MPesaAPI()
        result = mpesa_api.initiate_payment(
            phone_number=phone_number,
            amount=self.amount,
            payment_number=self.payment_number,
            booking_number=self.booking.booking_number
        )
        
        if result.get('success'):
            self.mpesa_merchant_request_id = result.get('MerchantRequestID', '')
            self.mpesa_checkout_request_id = result.get('CheckoutRequestID', '')
            self.status = 'processing'
            self.save()
            return True
        else:
            self.status = 'failed'
            self.mpesa_result_desc = result.get('error', 'Payment initiation failed')
            self.save()
            return False
    
    def confirm_mpesa_payment(self, transaction_data):
        """Confirm M-Pesa payment callback"""
        self.mpesa_transaction_id = transaction_data.get('TransID', '')
        self.mpesa_result_code = transaction_data.get('ResultCode', '')
        self.mpesa_result_desc = transaction_data.get('ResultDesc', '')
        
        if self.mpesa_result_code == '0':  # Success
            self.status = 'completed'
            self.payment_date = timezone.now()
        else:
            self.status = 'failed'
        
        self.save()
        
        # Update booking status if payment is successful
        if self.is_successful:
            self.booking.status = 'confirmed'
            self.booking.save()


class PaymentMethod(models.Model):
    """
    Model for storing user payment methods
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=Payment.PAYMENT_METHOD_CHOICES)
    
    # M-Pesa details
    mpesa_phone_number = models.CharField(max_length=15, blank=True)
    
    # Card details (encrypted)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_type = models.CharField(max_length=20, blank=True)
    card_expiry_month = models.PositiveIntegerField(blank=True, null=True)
    card_expiry_year = models.PositiveIntegerField(blank=True, null=True)
    
    # Bank details
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    account_name = models.CharField(max_length=100, blank=True)
    
    # Status
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        if self.payment_type == 'mpesa':
            return f"M-Pesa: {self.mpesa_phone_number}"
        elif self.payment_type == 'card':
            return f"Card: ****{self.card_last_four}"
        else:
            return f"{self.get_payment_type_display()}"


class Refund(models.Model):
    """
    Model for payment refunds
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    reason = models.TextField()
    
    # M-Pesa refund details
    mpesa_transaction_id = models.CharField(max_length=50, blank=True)
    mpesa_result_code = models.CharField(max_length=10, blank=True)
    mpesa_result_desc = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='processed_refunds', 
        blank=True, 
        null=True
    )
    
    # Timestamps
    refund_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund for {self.payment.payment_number} - {self.amount}"
    
    def process_refund(self, processed_by):
        """Process the refund"""
        from .api import MPesaAPI
        
        if self.payment.payment_method == 'mpesa':
            mpesa_api = MPesaAPI()
            result = mpesa_api.process_refund(
                transaction_id=self.payment.mpesa_transaction_id,
                amount=self.amount,
                phone_number=self.payment.mpesa_phone_number
            )
            
            if result.get('success'):
                self.status = 'completed'
                self.mpesa_transaction_id = result.get('TransID', '')
                self.mpesa_result_code = result.get('ResultCode', '')
                self.mpesa_result_desc = result.get('ResultDesc', '')
            else:
                self.status = 'failed'
                self.mpesa_result_desc = result.get('error', 'Refund failed')
        else:
            # Handle other payment methods
            self.status = 'completed'
        
        self.processed_by = processed_by
        self.refund_date = timezone.now()
        self.save()


class TransactionLog(models.Model):
    """
    Model for logging all payment transactions
    """
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='transaction_logs')
    action = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Transaction Log'
        verbose_name_plural = 'Transaction Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.payment.payment_number}"
