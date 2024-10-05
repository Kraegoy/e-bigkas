from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Learning, UserLearning
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import numpy as np
from django.http import JsonResponse
import json
import logging
from django.conf import settings




logger = logging.getLogger(__name__)

# Global model variable
global_model = None
global_belongs_to_array = None

def create_model(action_id):
    """Create and compile the LSTM model."""
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(23, 1662)))
    model.add(LSTM(128, return_sequences=True, activation='relu'))
    model.add(LSTM(64, return_sequences=False, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))

    # Retrieve the Learning object with the given id
    action = Learning.objects.get(id=action_id)

    # Convert the belongs_to string to a list
    belongs_to_string = action.belongs_to
    belongs_to_list = [item.strip().strip('"') for item in belongs_to_string.split(',')]
    
    global_belongs_to_array = np.array(belongs_to_list)

    model.add(Dense(global_belongs_to_array.shape[0], activation='softmax'))
    model.load_weights(action.model_file_path)
    
    return model, global_belongs_to_array

@login_required
def recognize_action(request, id):
    global global_model
    global global_belongs_to_array

    if request.method == 'POST':
        try:
            # Load JSON data from the request body
            data = json.loads(request.body)
            sequence = np.array(data['sequence'])

            threshold = 0.7

            # Check if the model is already created
            if global_model is None:
                global_model, global_belongs_to_array = create_model(id)

            # Ensure sequence is in the correct shape
            sequence = sequence.reshape(1, 23, 1662)

            # Predict using the model
            res = global_model.predict(sequence)[0]
            action_index = np.argmax(res)
            confidence = float(res[action_index])  # Keep confidence as a float

            predicted_action = str(global_belongs_to_array[action_index])  # Use action_index

            if confidence > threshold:  # Compare confidence as a float
                return JsonResponse({'predicted_action': predicted_action, 'confidence': confidence})

            return JsonResponse({'predicted_action': None, 'confidence': confidence})

        except Learning.DoesNotExist:
            logger.error(f"Learning object with id {id} does not exist.")
            return render(request, '404.html')
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")  # Log the exception
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)



@login_required
def learn_action(request, id):
   
    action = Learning.objects.get(id=id)
    action_id = action.id
    action_title = action.title
    return render(request, 'learnings_recognition.html', {'action': action, 'action_id': action_id, 'action_title': action_title})  



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
        'AWS_S3_CUSTOM_DOMAIN': settings.AWS_S3_CUSTOM_DOMAIN,
    })



@login_required
def save_user_learning(request, learning_id):
    if request.method == 'POST':
        # Get the Learning object by ID
        learning = get_object_or_404(Learning, id=learning_id)
        
        # Create or get the UserLearning object
        user_learning, created = UserLearning.objects.get_or_create(
            user=request.user,
            learning=learning
        )

        if created:
            # Learning saved successfully
            return JsonResponse({'message': 'Learning saved successfully!'}, status=201)
        else:
            # The user has already learned this subject
            return JsonResponse({'message': 'You have already learned this subject.'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)