import json
from django.shortcuts import render
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models import Count
from django.db.models.functions import TruncDate

def ebigkas_admin(request):
    # Aggregate users by date joined
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
    
    context = {
        'dates': json.dumps(dates),  # Serialize dates to JSON
        'counts': json.dumps(counts),  # Serialize counts to JSON
    }
    return render(request, 'admin_page.html', context)
