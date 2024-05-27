from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render
from .forms import LoginForm  # forms.py 파일에서 LoginForm을 import합니다.

def home(request):
    return render(request, 'home.html')

def login(request):
    form = LoginForm()
    return render(request, 'login.html', {'form': form})
