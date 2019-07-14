from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    #return HttpResponse("Psh Psh")
    return render(request, 'cloud/index.html')
