import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import Slideshow
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

@login_required
def ebigkas_admin(request):
    # Aggregate users by date joined
    if request.user.is_staff:
        user_counts = (
            User.objects
            .annotate(date=TruncDate('date_joined'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        # Prepare data for the chart
        dates = [entry['date'].strftime('%Y-%m-%d') for entry in user_counts]
        counts = [entry['count'] for entry in user_counts]
        
        # Retrieve active slideshows first, ordered by most recent
        slideshows = Slideshow.objects.filter(is_active=True).order_by('-created_at')

        # Retrieve inactive slideshows, ordered by most recent
        inactive_slideshows = Slideshow.objects.filter(is_active=False).order_by('-created_at')

        # Combine active and inactive slideshows
        combined_slideshows = list(slideshows) + list(inactive_slideshows)
        
        context = {
            'dates': json.dumps(dates),  # Serialize dates to JSON
            'counts': json.dumps(counts),  # Serialize counts to JSON
            'slideshows': combined_slideshows,
        }
        return render(request, 'admin_page.html', context)
    else:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    

@login_required
def add_slideshow(request):
    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'  # Boolean field
        image = request.FILES.get('image')
        
        # Basic validation
        if not image:
            messages.error(request, 'Image is required.')
        else:
            slideshow = Slideshow(
                description=description,
                is_active=is_active,
                image=image,
                added_by=request.user,
                updated_by=request.user
            )
            slideshow.save()
            messages.success(request, 'Slideshow added successfully!')
            return redirect('ebigkas_admin')  
    
    return render(request, 'admin_page.html')