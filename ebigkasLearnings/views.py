from django.shortcuts import render
from django.contrib.auth.decorators import login_required



@login_required
def learnings_view(request):
    return render(request, 'learnings.html')