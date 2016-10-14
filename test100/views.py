
# Import necessary classes
from django.shortcuts import render
from django.http import HttpResponse
from test100.models import Book, DVD, Libuser, Libitem, Suggestion
from test100.forms import SuggestionForm, SearchlibForm, RegisterForm
from django.conf.urls import patterns, url
from django.http import Http404
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
import random
from PIL import Image
import barcode # barcode generrator! downdloaded from https://bitbucket.org/whitie/python-barcode/
from barcode.writer import ImageWriter # default barcode image generator
import shutil
import os



# Create your views here.


# Index page
def index(request):
    itemlist = Libitem.objects.all().order_by('title')[:10]
    return render(request, "test100/index.html", {'itemlist': itemlist})


# About page
def about(request):
    # counting how many times that about page has been visited by using cookies
    if 'about_visits' in request.COOKIES:
        aboutVisits = int(request.COOKIES['about_visits']) + 1
    else:
        aboutVisits = 1
    response = render(request, 'test100/about.html', {'aboutVisits': aboutVisits})
    response.set_cookie('about_visits', aboutVisits, 300)
    return response


# Detial page; showing detail information about books or dvds
def detail(request, item_id):
    # select targeted item and create its own barcode image when user clicks
    try:
        item = Libitem.objects.get(pk=item_id)
        code = str(item.barcode) # transfer integers into strings
        # targeted item is a book
        if item.itemtype == 'Book':
            items = Book.objects.get(pk=item_id)
            # generate barcode picture
            ean = barcode.get('ean8',code, writer=ImageWriter())
            # moving the picture to static/bar-img/books
            bar_name = item.title
            bar_pic = ean.save(bar_name)
            shutil.copy(bar_pic, 'test100/static/bar-img/book/')
            os.remove(bar_pic)
            # create url for detail page to display the barcode iamge
            bar_url = 'bar-img/book/' + bar_name + '.png'
        # targeted item is a dvd
        else:
            items = DVD.objects.get(pk=item_id)
            # generate barcode picture
            ean = barcode.get('ean8', code, writer=ImageWriter())
            # moving the picture to static/bar-img/books
            bar_name = item.title
            bar_pic = ean.save(bar_name)
            shutil.copy(bar_pic, 'test100/static/bar-img/dvd/')
            os.remove(bar_pic)
            # create url for detail page to display the barcode iamge
            bar_url = 'bar-img/dvd/' + bar_name + '.png'
        return render(request, 'test100/detail.html', {'item': items, 'bar_url':bar_url})
    except:
        raise Http404


# Suggestions page which shows all suggestions that made by the user
def suggestions(request):
    suggestionlist = Suggestion.objects.all()[:10]
    return render(request, 'test100/suggestions.html', {'itemlist': suggestionlist})


# Suggestiondetail page which shows detail information about selected item
def suggestdetail(request, suggest_id):
    try:
        suggestlist = Suggestion.objects.get(pk=suggest_id)
        return render(request, 'test100/suggestdetail.html', {'suggestlist': suggestlist})
    except:
        raise Http404


# Newitem page where an user can make a new suggestion
def newitem(request):
    suggestions = Suggestion.objects.all()
    if request.method == 'POST':
        form = SuggestionForm(request.POST) # check forms.py: SuggestionForm
        if form.is_valid():
            suggestion = form.save(commit=False)
            suggestion.num_interested = 1
            suggestion.save()
            return HttpResponseRedirect(reverse('test100:suggestions'))
        else:
            return render(request, 'test100/newitem.html', {'form': form, 'suggestions': suggestions})
    else:
        form = SuggestionForm()
        return render(request, 'test100/newitem.html', {'form': form, 'suggestions': suggestions})


# Searchlib page; users search for books or dvds
def searchlib(request):
    if request.method == 'GET':
        form = SearchlibForm() # check forms.py: SearchlibForm
        return render(request, 'test100/searchlib.html')
    else:
        return HttpResponseRedirect(reverse('test100:searchlib'))


# Result page; showing the result that searched by user
def result(request):
    # get information from keyboard typing
    if 'title'or 'author' or 'maker' in request.GET:
        title = request.GET['title']
        author = request.GET['author']
        maker = request.GET['maker']
        # rules: a book has title and author, a dvd has title and maker, user can search either or both
        try:
            # an item cannot have both author and maker
            if author and maker:
                message = 'Wow! Please fill in either author or maker '
                return render(request, 'test100/result.html', {'message':message})
            # search title - including books and dvds
            elif title:
                items = DVD.objects.filter(title__icontains=title) or Book.objects.filter(title__icontains=title)
            # search a dvd
            elif title and maker:
                items = DVD.objects.filter(title__icontains=title).filter(maker__icontains=maker)
            elif maker:
                items = DVD.objects.filter(maker__icontains=maker)
            # search a book
            elif title and author:
                items = Book.objects.filter(title__icontains=title).filter(author__icontains=author)
            elif author:
                items = Book.objects.filter(author__icontains=author)
            return render(request, 'test100/result.html', {'items':items, 'title':title, 'author':author, 'maker':maker})
        except:
            message = 'You submitted an empty form' # when user did not type anything and submit an empty form
        return render(request, 'test100/result.html', {'message':message})


# Login page
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        request.session.set_expiry(3600)
        # user status check
        if user:
            if user.is_active:
                # get or set luckynum
                if 'luckynum' in request.session:
                    luckynum = request.session.get('luckynum')
                else:
                    request.session['luckynum'] = str(random.randint(1,9))
                login(request, user)
                return HttpResponseRedirect(reverse('test100:index'))
            else:
                return HttpResponse('Your account is disabled.')
        else:
            return HttpResponse('Invalid login details.')
    else:
        return render(request, 'test100/login.html')


# User logout and return to index
@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse(('test100:index')))


# Myitem page; shows all items that a user borrows, staff and superusers cannot borrow items form library
def myitems(request):
    # check if the user is a library user
    if request.user.is_authenticated():
        try:
            Libuser.objects.get(username=request.user)
        except:
            message = 'You are not a Libuser'
            return render(request, 'test100/myitems.html', {'message':message})
        # show all items borrowed by specific user
        myitem=Libitem.objects.filter(checked_out=True).filter(user=request.user)
        return render(request, 'test100/myitems.html', {'myitem':myitem})
    else:
        message = 'login please'
        return render(request, 'test100/myitems.html', {'message':message})


# Register page; a student can register as a library user here
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST) # check forms.py: RegisterForm
        if form.is_valid():
            username=request.POST['username']
            email=request.POST['email']
            password=request.POST['password']
            firstname=request.POST['first_name']
            lastname=request.POST['last_name']
            user = Libuser.objects.create_user(username, email, password)
            user.last_name=lastname
            user.first_name=firstname
            user.save()
            return HttpResponseRedirect(reverse( 'test100:index'))
        else:
            return render(request, 'test100/register.html', {'form':form})
    else:
        form = RegisterForm()
        return render(request, 'test100/register.html', {'form':form})


# Book page; show all books
def book(request):
    booklist=Book.objects.all()
    return render(request, 'test100/book.html', {'booklist':booklist})


# Dvd page; show all dvds
def dvd(request):
    dvdlist=DVD.objects.all()
    return render(request, 'test100/dvd.html', {'dvdlist':dvdlist})


# Other page; show all other items
def other(request):
    otherlist=Libitem.objects.filter(itemtype='Other')
    return render(request, 'test100/other.html', {'otherlist':otherlist})



