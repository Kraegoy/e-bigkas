import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import Slideshow, Feedback
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from geopy.geocoders import Nominatim
from ebigkasAPP .models import UserProfile
import folium
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse


def get_coordinates(location):
    geolocator = Nominatim(user_agent="MyGeocoderApp/1.0/ebigkas/fsl-recognition-system")
    try:
        print(f"Attempting to geocode location: {location}")  # Debugging line
        location = geolocator.geocode(location)
        if location:
            print(f"Coordinates found: Latitude={location.latitude}, Longitude={location.longitude}")  # Debugging line
            return location.latitude, location.longitude
        print("No location found for the given query.")  # Debugging line
        return None, None
    except Exception as e:
        print(f"Error retrieving coordinates: {e}")  # Log error details
        return None, None


@login_required
def ebigkas_admin(request):
    if not request.user.is_staff:
        return redirect('home')
    
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
    
    # Retrieve active and inactive slideshows
    slideshows = Slideshow.objects.filter(is_active=True).order_by('-created_at')
    inactive_slideshows = Slideshow.objects.filter(is_active=False).order_by('-created_at')
    combined_slideshows = list(slideshows) + list(inactive_slideshows)
    
    username = request.user.username
    
    # Center of the map (Philippines)
    map_center = [12.8797, 121.7740]

    # Create a Folium map
    foli_map = folium.Map(location=map_center, zoom_start=6)

    # Retrieve all unique locations from UserProfile
    locations = UserProfile.objects.values_list('location', flat=True).distinct()

    for location in locations:
        if location:
            try:
                latitude, longitude = get_coordinates(location)
                if latitude and longitude:
                    folium.Marker(
                        location=[latitude, longitude],
                        popup=f"{location}",
                        icon=folium.Icon(icon='info-sign')
                    ).add_to(foli_map)
            except Exception as e:
                print(f"Error processing location '{location}': {e}")


    # Get the HTML representation of the map
    map_html = foli_map._repr_html_()

    context = {
        'dates': json.dumps(dates),  
        'counts': json.dumps(counts), 
        'slideshows': combined_slideshows,
        'username': username,
        'map_html': map_html,  # Pass the map HTML to the context
    }
    return render(request, 'admin_page.html', context)

    

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


@login_required
def admin_feedbacks(request):
    # Fetch feedbacks with and without responses directly from the database
    username = request.user.username
    has_response = Feedback.objects.exclude(response__isnull=True).exclude(response__exact='')
    no_response = Feedback.objects.filter(response__isnull=True) | Feedback.objects.filter(response__exact='')

    # Render the data in the template
    return render(request, 'admin_feedbacks.html', {
        'username': username,
        'has_response': has_response, 
        'no_response': no_response
    })
    
@login_required
def edit_slideshow(request, id):
    slideshow = get_object_or_404(Slideshow, id=id)
    if request.method == "POST":
        is_active = request.POST.get('is_active') == 'True'
        slideshow.is_active = is_active
        slideshow.save()
        messages.success(request, "Slideshow updated successfully.")
        return redirect('ebigkas_admin') 
    

@login_required   
@csrf_exempt
@require_POST
def submit_response(request, feedback_id):
    try:
        feedback = Feedback.objects.get(id=feedback_id)
        response_message = request.body.decode('utf-8')  # Get the response data

        # You may want to parse the JSON data if you're using a JSON request
        import json
        data = json.loads(response_message)
        response_text = data.get('response', '')

        # Save the response in your model (you can create a Response model for this)
        feedback.response = response_text  # Assuming you have a response field in your Feedback model
        feedback.save()

        return JsonResponse({'status': 'success', 'message': 'Response submitted successfully.'})
    
    except Feedback.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Feedback not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)