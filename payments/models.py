from django.db import models
from django.conf import settings
from decimal import Decimal

from accounts.models import Student
from course.models import Program, Course
from result.models import TakenCourse


class Invoice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total = models.FloatField(null=True, blank=True)
    amount = models.FloatField(null=True, blank=True)
    payment_complete = models.BooleanField(default=False)
    invoice_code = models.CharField(max_length=200, blank=True, null=True)


class TuitionFee(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    level = models.CharField(max_length=25, choices=settings.LEVEL_CHOICES)
    semester = models.CharField(choices=settings.SEMESTER_CHOICES, max_length=200)
    year = models.IntegerField(choices=settings.YEARS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.program.title} - {self.level} - {self.year} {self.semester}: ${self.amount}"

    class Meta:
        unique_together = ('program', 'level', 'semester', 'year')


class StudentTuitionPayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    level = models.CharField(max_length=25, choices=settings.LEVEL_CHOICES)
    semester = models.CharField(choices=settings.SEMESTER_CHOICES, max_length=200)
    year = models.IntegerField(choices=settings.YEARS)
    tuition_fee = models.ForeignKey(TuitionFee, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PARTIAL', 'Partial Payment'),
            ('PAID', 'Fully Paid'),
            ('OVERPAID', 'Overpaid')
        ],
        default='PENDING'
    )
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.student.get_full_name} - {self.program.title} - {self.year} {self.semester}"

    def calculate_balance(self):
        self.balance = self.tuition_fee.amount - self.amount_paid
        if self.balance < 0:
            self.payment_status = 'OVERPAID'
        elif self.balance == 0:
            self.payment_status = 'PAID'
        elif self.amount_paid > 0:
            self.payment_status = 'PARTIAL'
        else:
            self.payment_status = 'PENDING'
        self.save()
        return self.balance

    def make_payment(self, amount):
        self.amount_paid += amount
        self.calculate_balance()

    class Meta:
        unique_together = ('student', 'program', 'level', 'semester', 'year')
