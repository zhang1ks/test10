from django.db import models
from django.contrib.auth.models import User
import datetime
import django.utils
from PIL import Image


# Create your models here.

class Libuser(User):
    PROVINCE_CHOICES = (
        ('AB', 'Alberta'),  # The first value is actually stored in db, the second is descriptive
        ('MB', 'Manitoba'),
        ('ON', 'Ontario'),
        ('QC', 'Quebec'),
    )
    address = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=20, default='Windsor')
    province = models.CharField(max_length=2, choices=PROVINCE_CHOICES, default='ON')
    phone = models.IntegerField(null=True, blank=True)
    postalcode = models.CharField(max_length=6,null=True, blank=True)

    def __str__(self):
        return self.first_name


class Libitem(models.Model):
    TYPE_CHOICES = (
        ('Book', 'Book'),
        ('DVD', 'DVD'),
        ('Other', 'Other'),
    )
    title = models.CharField(max_length=100)
    itemtype = models.CharField(max_length=6, choices=TYPE_CHOICES, default='Other')
    checked_out = models.BooleanField(default=False)
    user = models.ForeignKey(Libuser, default=None, null=True, blank=True)
    duedate = models.DateField(default=None, null=True, blank=True)
    last_chkout = models.DateField(default=None, null=True, blank=True)
    date_acquired = models.DateField(default=django.utils.timezone.now)
    pubyr = models.IntegerField()
    num_chkout = models.IntegerField(null=False, default=0)
    barcode = models.IntegerField(null=True)

    def __str__(self):
        return self.title

    def overdue(self):
        if self.checked_out == True :
            if self.duedate == None:
                return 'No'
            elif self.duedate < datetime.date.today():
                return  'Yes'
            else:
                return 'No'


class Book(Libitem):
    CATEGORY_CHOICES = (
        (1, 'Fiction'),
        (2, 'Biography'),
        (3, 'Self Help'),
        (4, 'Education'),
        (5, 'Children'),
        (6, 'Teen'),
        (7, 'Other'),
    )
    author = models.CharField(max_length=100)
    category = models.IntegerField(choices=CATEGORY_CHOICES, default=1)

    def __str__(self):
        return self.title + ' by ' + self.author


class DVD(Libitem):
    RATING_CHOICE = (
        (1, 'G'),
        (2, 'PG'),
        (3, 'PG-13'),
        (4, '14A'),
        (5, 'R'),
        (6, 'NR'),
    )
    maker = models.CharField(max_length=100)
    duration = models.IntegerField()
    rating = models.IntegerField(choices=RATING_CHOICE, default=1)

    def __str__(self):
        return self.title + ' by ' + self.maker


# database for suggested items
class Suggestion(models.Model):
    TYPE_CHOICES = (
        ('Book', 'Book'),
        ('DVD','DVD'),
        ('Other', 'Other'),
    )
    title = models.CharField(max_length=100)
    pubyr = models.IntegerField(null=True, blank=True) #limited from 1900 to 2016
    type = models.CharField(max_length=6, default='Other', choices=TYPE_CHOICES)
    cost = models.IntegerField()
    num_interested = models.IntegerField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title




