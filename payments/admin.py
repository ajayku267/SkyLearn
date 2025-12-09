from django.contrib import admin
from .models import Invoice, TuitionFee, StudentTuitionPayment

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'total', 'payment_complete', 'invoice_code')
    list_filter = ('payment_complete', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'invoice_code')

@admin.register(TuitionFee)
class TuitionFeeAdmin(admin.ModelAdmin):
    list_display = ('program', 'level', 'semester', 'year', 'amount')
    list_filter = ('program', 'level', 'semester', 'year')
    search_fields = ('program__title',)

@admin.register(StudentTuitionPayment)
class StudentTuitionPaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'program', 'level', 'semester', 'year', 'amount_paid', 'balance', 'payment_status')
    list_filter = ('program', 'level', 'semester', 'year', 'payment_status')
    search_fields = ('student__student__username', 'student__student__first_name', 'student__student__last_name', 'program__title')
