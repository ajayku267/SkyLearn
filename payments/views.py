import stripe
import uuid
import json
from decimal import Decimal

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db.models import Sum, Q

from django.http import JsonResponse

import gopay
from gopay.enums import Recurrence, PaymentInstrument, BankSwiftCode, Currency, Language
from .models import Invoice, TuitionFee, StudentTuitionPayment
from accounts.models import Student
from course.models import Program
from result.models import TakenCourse


def payment_paypal(request):
    return render(request, "payments/paypal.html", context={})


def payment_stripe(request):
    return render(request, "payments/stripe.html", context={})


def payment_coinbase(request):
    return render(request, "payments/coinbase.html", context={})


def payment_paylike(request):
    return render(request, "payments/paylike.html", context={})


def payment_succeed(request):
    return render(request, "payments/payment_succeed.html", context={})


@method_decorator(login_required, name='dispatch')
class TuitionPaymentView(TemplateView):
    template_name = "payments/tuition_payment.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the current student
        try:
            student = Student.objects.get(student=self.request.user)
        except Student.DoesNotExist:
            student = None
            
        if student:
            # Get student's program and level
            program = student.program
            level = student.level
            
            # Get current semester and year from settings or defaults
            # In a real implementation, this would come from the current academic session
            current_year = settings.YEARS[0][0] if settings.YEARS else 1
            current_semester = settings.SEMESTER_CHOICES[0][0] if settings.SEMESTER_CHOICES else "First"
            
            # Get tuition fee for student's program, level, semester, and year
            try:
                tuition_fee = TuitionFee.objects.get(
                    program=program,
                    level=level,
                    semester=current_semester,
                    year=current_year
                )
                context['tuition_fee'] = tuition_fee
            except TuitionFee.DoesNotExist:
                tuition_fee = None
                context['tuition_fee'] = None
            
            # Get student's tuition payment record
            try:
                student_payment = StudentTuitionPayment.objects.get(
                    student=student,
                    program=program,
                    level=level,
                    semester=current_semester,
                    year=current_year
                )
                context['student_payment'] = student_payment
            except StudentTuitionPayment.DoesNotExist:
                student_payment = None
                context['student_payment'] = None
                
                # Create a new payment record if it doesn't exist
                if tuition_fee:
                    student_payment = StudentTuitionPayment.objects.create(
                        student=student,
                        program=program,
                        level=level,
                        semester=current_semester,
                        year=current_year,
                        tuition_fee=tuition_fee,
                        balance=tuition_fee.amount
                    )
                    context['student_payment'] = student_payment
            
            # Get all payment history for the student
            payment_history = StudentTuitionPayment.objects.filter(student=student).order_by('-created_at')
            context['payment_history'] = payment_history
            
        context['student'] = student
        return context


def tuition_payment_history(request):
    """View to show all tuition payment history for a student"""
    try:
        student = Student.objects.get(student=request.user)
        payments = StudentTuitionPayment.objects.filter(student=student).order_by('-created_at')
    except Student.DoesNotExist:
        student = None
        payments = []
    
    context = {
        'student': student,
        'payments': payments
    }
    return render(request, "payments/payment_history.html", context)


def admin_tuition_management(request):
    """Admin view to manage tuition fees and student payments"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get all programs
    programs = Program.objects.all()
    
    # Get all tuition fees
    tuition_fees = TuitionFee.objects.all().order_by('program', 'level', 'year', 'semester')
    
    # Get all student payments
    student_payments = StudentTuitionPayment.objects.all().order_by('-created_at')
    
    context = {
        'programs': programs,
        'tuition_fees': tuition_fees,
        'student_payments': student_payments
    }
    return render(request, "payments/admin_tuition_management.html", context)


def create_tuition_fee(request):
    """Admin view to create a new tuition fee"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    if request.method == 'POST':
        program_id = request.POST.get('program')
        level = request.POST.get('level')
        semester = request.POST.get('semester')
        year = request.POST.get('year')
        amount = request.POST.get('amount')
        
        try:
            program = Program.objects.get(id=program_id)
            tuition_fee = TuitionFee.objects.create(
                program=program,
                level=level,
                semester=semester,
                year=int(year),
                amount=Decimal(amount)
            )
            messages.success(request, f"Tuition fee for {program.title} created successfully!")
        except Exception as e:
            messages.error(request, f"Error creating tuition fee: {str(e)}")
    
    return redirect('admin_tuition_management')


class PaymentGetwaysView(TemplateView):
    template_name = "payments/payment_gateways.html"

    def get_context_data(self, **kwargs):
        context = super(PaymentGetwaysView, self).get_context_data(**kwargs)
        context["key"] = settings.STRIPE_PUBLISHABLE_KEY
        context["amount"] = 500
        context["description"] = "Stripe Payment"
        context["invoice_session"] = self.request.session["invoice_session"]
        print(context["invoice_session"])
        return context


def stripe_charge(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if request.method == "POST":
        charge = stripe.Charge.create(
            amount=500,
            currency="eur",
            description="A Django charge",
            source=request.POST["stripeToken"],
        )
        invoice_code = request.session["invoice_session"]
        invoice = Invoice.objects.get(invoice_code=invoice_code)
        invoice.payment_complete = True
        invoice.save()
        return redirect("completed")
        # return JsonResponse({"invoice_code": invoice.invoice_code}, status=201)
        # return render(request, 'payments/charge.html')


def gopay_charge(request):
    if request.method == "POST":
        user = request.user

        payments = gopay.payments(
            {
                "goid": "[PAYMENT_ID]",
                "clientId": "[GOPAY_CLIENT_ID]",
                "clientSecret": "[GOPAY_CLIENT_SECRET]",
                "isProductionMode": False,
                "scope": gopay.TokenScope.ALL,
                "language": gopay.Language.ENGLISH,
                "timeout": 30,
            }
        )

        # recurrent payment must have field ''
        recurrentPayment = {
            "recurrence": {
                "recurrence_cycle": Recurrence.DAILY,
                "recurrence_period": "7",
                "recurrence_date_to": "2015-12-31",
            }
        }

        # pre-authorized payment must have field 'preauthorization'
        preauthorizedPayment = {"preauthorization": True}

        response = payments.create_payment(
            {
                "payer": {
                    "default_payment_instrument": PaymentInstrument.BANK_ACCOUNT,
                    "allowed_payment_instruments": [PaymentInstrument.BANK_ACCOUNT],
                    "default_swift": BankSwiftCode.FIO_BANKA,
                    "allowed_swifts": [BankSwiftCode.FIO_BANKA, BankSwiftCode.MBANK],
                    "contact": {
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone_number": user.phone,
                        "city": "example city",
                        "street": "Plana 67",
                        "postal_code": "373 01",
                        "country_code": "CZE",
                    },
                },
                "amount": 150,
                "currency": Currency.CZECH_CROWNS,
                "order_number": "001",
                "order_description": "pojisteni01",
                "items": [
                    {"name": "item01", "amount": 50},
                    {"name": "item02", "amount": 100},
                ],
                "additional_params": [{"name": "invoicenumber", "value": "2015001003"}],
                "callback": {
                    "return_url": "http://www.your-url.tld/return",
                    "notification_url": "http://www.your-url.tld/notify",
                },
                "lang": Language.CZECH,  # if lang is not specified, then default lang is used
            }
        )

        if response.has_succeed():
            print("\nPayment Succeed\n")
            print("hooray, API returned " + str(response))
        else:
            print("\nPayment Fail\n")
            print(
                "oops, API returned " + str(response.status_code) + ": " + str(response)
            )
        return JsonResponse({"message": str(response)})

    return JsonResponse({"message": "GET requested"})


def paymentComplete(request):
    print(request.is_ajax())
    if request.is_ajax() or request.method == "POST":
        invoice_id = request.session["invoice_session"]
        invoice = Invoice.objects.get(id=invoice_id)
        invoice.payment_complete = True
        invoice.save()
        
        # If this is a tuition payment, update the student's payment record
        try:
            student_payment = StudentTuitionPayment.objects.get(invoice=invoice)
            student_payment.make_payment(invoice.amount)
            messages.success(request, "Tuition payment completed successfully!")
        except StudentTuitionPayment.DoesNotExist:
            pass  # Not a tuition payment
        
        # return redirect('invoice', invoice.invoice_code)
    body = json.loads(request.body)
    print("BODY:", body)
    return JsonResponse("Payment completed!", safe=False)


def create_invoice(request):
    print(request.is_ajax())
    if request.method == "POST":
        amount = request.POST.get("amount")
        
        # Check if this is a tuition payment
        student_payment_id = request.POST.get("student_payment_id")
        
        invoice = Invoice.objects.create(
            user=request.user,
            amount=float(amount),
            total=float(amount),
            invoice_code=str(uuid.uuid4()),
        )
        
        # If this is a tuition payment, link it to the student payment record
        if student_payment_id:
            try:
                student_payment = StudentTuitionPayment.objects.get(id=student_payment_id)
                student_payment.invoice = invoice
                student_payment.save()
            except StudentTuitionPayment.DoesNotExist:
                pass
        
        request.session["invoice_session"] = invoice.invoice_code
        return redirect("payment_gateways")
    # if request.is_ajax():
    #     invoice = Invoice.objects.create(
    #         user = request.user,
    #         amount = 15,
    #         total=26,
    #     )
    #     return JsonResponse({'invoice': invoice}, status=201) # created

    return render(
        request,
        "invoices.html",
        context={"invoices": Invoice.objects.filter(user=request.user)},
    )


def invoice_detail(request, slug):
    return render(
        request,
        "invoice_detail.html",
        context={"invoice": Invoice.objects.get(invoice_code=slug)},
    )
