from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from accounts.models import Student
from course.models import Program
from payments.models import TuitionFee, StudentTuitionPayment


class TuitionPaymentModelsTest(TestCase):
    def setUp(self):
        # Create a user
        self.user = get_user_model().objects.create_user(
            username='teststudent',
            email='student@test.com',
            password='testpass123',
            is_student=True
        )
        
        # Create a program
        self.program = Program.objects.create(
            title='Computer Science',
            summary='Computer Science Program'
        )
        
        # Create a student
        self.student = Student.objects.create(
            student=self.user,
            level='Bachelor',
            program=self.program
        )
        
        # Create a tuition fee
        self.tuition_fee = TuitionFee.objects.create(
            program=self.program,
            level='Bachelor',
            semester='First',
            year=1,
            amount=Decimal('5000.00')
        )
    
    def test_tuition_fee_creation(self):
        """Test that tuition fee is created correctly"""
        self.assertEqual(self.tuition_fee.program, self.program)
        self.assertEqual(self.tuition_fee.level, 'Bachelor')
        self.assertEqual(self.tuition_fee.semester, 'First')
        self.assertEqual(self.tuition_fee.year, 1)
        self.assertEqual(self.tuition_fee.amount, Decimal('5000.00'))
    
    def test_student_tuition_payment_creation(self):
        """Test that student tuition payment is created correctly"""
        payment = StudentTuitionPayment.objects.create(
            student=self.student,
            program=self.program,
            level='Bachelor',
            semester='First',
            year=1,
            tuition_fee=self.tuition_fee,
            amount_paid=Decimal('0.00'),
            balance=Decimal('5000.00'),
            payment_status='PENDING'
        )
        
        self.assertEqual(payment.student, self.student)
        self.assertEqual(payment.program, self.program)
        self.assertEqual(payment.level, 'Bachelor')
        self.assertEqual(payment.semester, 'First')
        self.assertEqual(payment.year, 1)
        self.assertEqual(payment.tuition_fee, self.tuition_fee)
        self.assertEqual(payment.amount_paid, Decimal('0.00'))
        self.assertEqual(payment.balance, Decimal('5000.00'))
        self.assertEqual(payment.payment_status, 'PENDING')
    
    def test_student_tuition_payment_make_payment(self):
        """Test making a payment updates the balance and status"""
        payment = StudentTuitionPayment.objects.create(
            student=self.student,
            program=self.program,
            level='Bachelor',
            semester='First',
            year=1,
            tuition_fee=self.tuition_fee,
            amount_paid=Decimal('0.00'),
            balance=Decimal('5000.00'),
            payment_status='PENDING'
        )
        
        # Make a partial payment
        payment.make_payment(Decimal('2000.00'))
        
        self.assertEqual(payment.amount_paid, Decimal('2000.00'))
        self.assertEqual(payment.balance, Decimal('3000.00'))
        self.assertEqual(payment.payment_status, 'PARTIAL')
        
        # Make another payment to fully pay
        payment.make_payment(Decimal('3000.00'))
        
        self.assertEqual(payment.amount_paid, Decimal('5000.00'))
        self.assertEqual(payment.balance, Decimal('0.00'))
        self.assertEqual(payment.payment_status, 'PAID')