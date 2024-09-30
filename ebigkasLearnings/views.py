from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Learning, UserLearning


@login_required
def learn_action(request, id):
    return render(request, 'learnings_recognition.html')


@login_required
def learnings_view(request):
     # Retrieve all learnings
    all_learnings = Learning.objects.all()
    
    # Retrieve UserLearning records for the current user
    learned_learnings = UserLearning.objects.filter(user=request.user).select_related('learning')
    
    # Calculate learned and not learned
    learned_ids = set(learning.learning.id for learning in learned_learnings)
    total_learnings = all_learnings.count()
    learned_count = len(learned_ids)
    not_learned_count = total_learnings - learned_count
    
    # Calculate percentage
    percentage_learned = (learned_count / total_learnings * 100) if total_learnings > 0 else 0

    # Get not learned learnings
    not_learned_learnings = all_learnings.exclude(id__in=learned_ids)

    # Pass the learning data to the template
    return render(request, 'learnings.html', {
   
        'learned_count': learned_count,
        'not_learned_count': not_learned_count,
        'percentage_learned': percentage_learned,
        'not_learned_learnings': not_learned_learnings,
        'learned_learnings' : learned_learnings,
    })

