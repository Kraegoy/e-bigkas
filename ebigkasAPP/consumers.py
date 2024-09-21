import cv2
import numpy as np
import mediapipe as mp
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import threading
from django.http import JsonResponse
from happytransformer import HappyTextToText, TTSettings
import base64
import asyncio
from .models import Message, Conversation
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.core.serializers.json import DjangoJSONEncoder
import time
from asgiref.sync import async_to_sync




import logging

logger = logging.getLogger(__name__)

mp_holistic = mp.solutions.holistic  # Holistic model
mp_drawing = mp.solutions.drawing_utils  # Drawing utilities

def mediapipe_detection(image, model):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # COLOR CONVERSION BGR 2 RGB
    image.flags.writeable = False  # Image is no longer writeable
    results = model.process(image)  # Make prediction
    image.flags.writeable = True  # Image is now writeable
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # COLOR COVERSION RGB 2 BGR
    return image, results

def draw_styled_landmarks(image, results):
    # Draw face outlines
    mp_drawing.draw_landmarks(image, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS,
                               mp_drawing.DrawingSpec(color=(80, 110, 10), thickness=1, circle_radius=0),
                               mp_drawing.DrawingSpec(color=(80, 256, 121), thickness=1, circle_radius=0)
                               )
    # Draw pose connections
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                               mp_drawing.DrawingSpec(color=(80, 22, 10), thickness=1, circle_radius=0),
                               mp_drawing.DrawingSpec(color=(80, 44, 121), thickness=1, circle_radius=0)
                               )
    # Draw left hand connections
    mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                               mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=1, circle_radius=0),
                               mp_drawing.DrawingSpec(color=(121, 44, 250), thickness=1, circle_radius=0)
                               )
    # Draw right hand connections
    mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                               mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=1, circle_radius=0),
                               mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=1, circle_radius=0)
                               )


def extract_keypoints(results):
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33 * 4)
    face = np.array([[res.x, res.y, res.z] for res in results.face_landmarks.landmark]).flatten() if results.face_landmarks else np.zeros(468 * 3)
    lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21 * 3)
    rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21 * 3)
    return np.concatenate([pose, face, lh, rh])


# Actions that we try to detect
# actions = np.array(['blank','maybe','no','sorry','take care','thank you','understand','welcome','what','when','where','yes','hello', 'thank you', 'how are you', 'I\'m fine', 'I love you', "I'm not fine"])
actions = np.array(['hello', 'thank you', 'I love you','how are you', "I'm fine", "I'm not fine", "yes"])


from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

model = Sequential()
model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(23, 1662)))
model.add(LSTM(128, return_sequences=True, activation='relu'))
model.add(LSTM(64, return_sequences=False, activation='relu'))
model.add(Dense(64, activation='relu'))
model.add(Dense(32, activation='relu'))
model.add(Dense(actions.shape[0], activation='softmax'))

model.load_weights('MyModels/seven.h5')

colors = [(245, 117, 16), (117, 245, 16), (16, 117, 245), (245, 125, 16), (16, 117, 100)]
colors = [(245, 117, 16), (117, 245, 16), (16, 117, 245), (245, 125, 16), (16, 117, 100)]

def prob_viz(res, input_frame, colors):
    output_frame = input_frame.copy()
    for num, prob in enumerate(res):
        cv2.rectangle(output_frame, (0, 60 + num * 40), (int(prob * 100), 90 + num * 40), colors[num], -1)
        cv2.putText(output_frame, actions[num], (0, 85 + num * 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
                    cv2.LINE_AA)
    return output_frame


happy_tt = HappyTextToText("T5", "prithivida/grammar_error_correcter_v1")
settings = TTSettings(do_sample=True, top_k=10, temperature=0.5, min_length=1, max_length=100)

def paraphrase(text):
    input_text = "gec: " + text  
    result = happy_tt.generate_text(input_text, args=settings)
    return result.text 


    
class VideoCallConsumer(AsyncWebsocketConsumer):
    output_text_f = ""
    cap = None
    recognizing = False
    stop_requested = False
    recognition_thread = None
    recognized_actions = []
    last_sent_message_time = 0

    async def start_recognition(self, sender_id, room_id):
        self.recognized_actions = []

        if not self.recognizing:
            self.recognizing = True
            self.stop_requested = False
            self.recognition_thread = threading.Thread(target=self.recognition_loop, args=(sender_id, room_id,))
            self.recognition_thread.start()
                     
    
    async def process_extracted_keypoints(self, sender_id, room_id, sequence):
        threshold = 0.6
        action_name = ""
        confidence = 0

        # Validate sequence length
        if len(sequence) != 23:
            print("Invalid sequence length.")
            return

        # Attempt to predict the action
        try:
            res = model.predict(np.expand_dims(sequence, axis=0))[0]
            action = np.argmax(res)
            confidence = res[action]

            if confidence > threshold:
                action_name = actions[action]
        except Exception as e:
            print(f"Error during model prediction: {e}")
            return  # Exit early if there's an error

        # If an action name was predicted, send it to the group
        if action_name:
            try:
                print(f"Sent predicted action: {action_name} with confidence: {confidence}")
               # await self.send_prediction(sender_id, room_id, action_name)
                
            except Exception as send_error:
                print(f"Error sending predicted action: {send_error}")
        else:
            print(f"No action predicted. Confidence: {confidence}")


    async def send_prediction(self, sender_id, room_id, predicted_action):
        await self.channel_layer.group_send(
            "video_call_group",
            {
                'type': 'predicted_action',
                'predicted_action': predicted_action,
                'sender_id': sender_id,
                'room_id': room_id
            }
        )
        print(f"sent prediction: {predicted_action}")

            

            

    async def send_frame(self, frame_data, sender_id, room_id):
        await self.channel_layer.group_send(
            "video_call_group",
            {
                'type': 'video_frame',
                'frame': frame_data,
                'sender_id': sender_id,
                'room_id': room_id
            }
        )

    async def video_frame(self, event):
        frame = event['frame']
        sender_id = event['sender_id']
        room_id = event['room_id']

        await self.send(text_data=json.dumps({
            'type': 'video-frame',
            'frame': frame,
            'sender_id': sender_id,
            'room_id': room_id
        }))
        
    

    async def process_frame_and_predict(self, sequence):
        """
        Asynchronously processes the sequence to make predictions.
        """
        if len(sequence) == 23:
            res = model.predict(np.expand_dims(sequence, axis=0))[0]
            print(f"np.argmax(res): {np.argmax(res)}, res[np.argmax(res)]: {res[np.argmax(res)]}")
            return np.argmax(res), res[np.argmax(res)]
        return None, None
    
                
    
                
                  

    def recognition_loop(self, sender_id, room_id):
        # Ensure OpenCV setup is correct
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(3, 640)
            self.cap.set(4, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)

        cap = self.cap
        if cap.isOpened():
            sequence = []
            sentence = []
            predictions = []
            threshold = 0.5

            with mp.solutions.holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.4) as holistic:
                while self.recognizing and cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    frame = cv2.flip(frame, 1)
                    image, results = mediapipe_detection(frame, holistic)
                    if image is None:
                        continue

                    draw_styled_landmarks(image, results)

                    keypoints = extract_keypoints(results)
                    sequence.append(keypoints)
                    sequence = sequence[-23:]

                    # Use async processing for prediction
                    action, confidence = asyncio.run(self.process_frame_and_predict(sequence))

                    if action is not None:
                        predictions.append(action)
                        if np.unique(predictions[-10:])[0] == action and confidence > threshold:
                            action_name = actions[action]
                            if len(sentence) == 0 or action_name != sentence[-1]:
                                sentence.append(action_name)

                    if len(sentence) > 5:
                        sentence = sentence[-5:]

                    self.output_text_f = " ".join(sentence)

                    _, jpeg = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 15])
                    frame_bytes = jpeg.tobytes()
                    frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
                    data_url = 'data:image/jpeg;base64,' + frame_base64

                    # Use async_to_sync to call send_frame from sync context
                    async_to_sync(self.send_frame)(data_url, sender_id, room_id)

        self.stop_recognition()

    async def stop_recognition(self):
        logger.info("Stopping recognition") 
        frame = "{% static '/images/ebigkas-logo.png' %}"
        if self.recognizing:
            self.recognizing = False
            if self.cap is not None:
                self.cap.release()
                cv2.destroyAllWindows()
                if len(self.output_text_f) > 0:
                    paraphrased_text = paraphrase(self.output_text_f)  
                else:
                    paraphrased_text = 'blank'
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        'type': 'output_text1',
                        'output_text1': paraphrased_text,
                        'frame': frame,
                    }
                )
                logger.info("Recognition stopped. Output text: %s", paraphrased_text) 
                self.cap = None
                
    async def output_text1(self, event):
        await self.send(text_data=json.dumps({
            'type': 'output_text1',
            'output_text1': event['output_text1']
        }))
 

    async def connect(self):
        await self.channel_layer.group_add("video_call_group", self.channel_name)
        await self.accept()
        logger.info("WebSocket connection established.")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("video_call_group", self.channel_name)
        logger.info(f"WebSocket connection closed with code: {close_code}")


    async def update_profile(self, event):
   
        await self.channel_layer.group_send(
            "video_call_group",
            {
                "type": "send_updated_profile",
                "content": event["content"]
            }
        )

    async def send_updated_profile(self, event):
        # This function is called to handle the "send_updated_profile" message
        # Send the updated content to the client
        await self.send(text_data=json.dumps({
            "type": "update_profile",
            "content": event["content"]
        }))
        

    async def video_call_invitation(self, event):
        room_id = event.get('room_id')
        invited_user_id = event.get('invited_user_id')
        inviting_user_id = event.get('inviting_user_id')
        #friendshipObjectName = event.get('friendshipObjectName')

        await self.send(text_data=json.dumps({
            'type': 'video_call_invitation',
            'room_id': room_id,
            'invited_user_id': invited_user_id,
            'inviting_user_id': inviting_user_id,
            #'friendshipObjectName': friendshipObjectName

        }))
        
    async def friend_status(self, event):
        loggedInUserID = event.get('loggedInUserID')
        loggedInUsername = event.get('loggedInUsername')
        status = event.get('status')

        # Broadcast friend status update to all connected clients
        await self.channel_layer.group_send(
        "video_call_group",  
            {
                'type': 'send_friend_status',
                'recent_loggedInUserID': loggedInUserID,
                'recent_loggedInUsername': loggedInUsername,
                'status': status,

            }
        )

    async def send_friend_status(self, event):
        loggedInUserID = event['loggedInUserID']
        loggedInUsername = event['loggedInUsername']
        status = event['status']

        # Send friend status update to the client
        await self.send(text_data=json.dumps({
            'type': 'friend_status',
            'recent_loggedInUserID': loggedInUserID,
            'recent_loggedInUsername': loggedInUsername,
            'status': status,

        }))
        
    async def hang_up(self, event):
        receiver_id = event['receiver_id']

        # Send friend status update to the client
        await self.send(text_data=json.dumps({
            'type': 'hang_up',
            'receiver_id': receiver_id,

        }))


    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            if data['type'] == 'load_messages':
                logger.info("Received load_messages message from client")
                conversation_name = data['conversationName']
                messages = await self.load_messages(conversation_name)
                for message in messages:
                    message['timestamp'] = message['timestamp'].isoformat()
                await self.send(text_data=json.dumps({
                    "type": "messages_loaded",
                    "messages": messages,
                    "conversation_name" : conversation_name
                }, cls=DjangoJSONEncoder))
                
            elif data['type'] == 'video-frame':
                frame = data.get('frame')
                sender_id = data.get('sender_id')
                room_id = data.get('room_id')
                # Send video frame to room group
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        'type': 'video_frame',
                        'frame': frame,
                        'sender_id': sender_id,
                        'room_id': room_id
                    }
                )
                
            elif data['type'] == 'message':
                logger.info("Received message from client")
                message_data = data['message']
                sender_id = message_data['sender_id']
                receiver_id = message_data['receiver_id']
                content = message_data['content']
                timestamp = message_data['timestamp']
                conversation_name = message_data['conversationName']

                message = await self.save_message(sender_id, receiver_id, content, timestamp, conversation_name)
                message['timestamp'] = message['timestamp'].isoformat()

                await self.channel_layer.group_send(
                    "video_call_group",
                    {   
                        "type": "chat_message",
                        "message": message,
                        "conversation_name" : conversation_name
                    }
                )
            elif data['type'] == 'start_recognition':
                logger.info("Received start_recognition message from client")
                sender_id = data.get('sender_id')
                room_id = data.get('room_id')
                await self.start_recognition(sender_id, room_id)

            elif data['type'] == 'stop_recognition':
                logger.info("Received stop_recognition message from client")
                await self.stop_recognition()
                logger.info("stop_recognition method called successfully")
                
            elif data['type'] == 'extracted-keypoints':
                sender_id = data.get('sender_id')
                room_id = data.get('room_id')
                sequence = data.get('sequence')
                await self.process_extracted_keypoints(sender_id, room_id, sequence)
                
            elif data['type'] == 'prediction':
                sender_id = data.get('sender_id')
                room_id = data.get('room_id')
                await self.send_prediction(sender_id, room_id)
                
            elif data['type'] == 'friend_status':
                loggedInUserID = data.get('loggedInUserID')
                loggedInUsername = data.get('loggedInUsername')
                status = data.get('status')
   
                # Broadcast friend status update to the group
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        'type': 'send_friend_status',
                        'loggedInUserID': loggedInUserID,
                        'loggedInUsername': loggedInUsername,
                        'status': status,

                    }
                )
            
            elif data['type'] == 'hang_up':
                receiver_id = data.get('receiver_id')
                
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        'type': 'hang_up',
                        'receiver_id': receiver_id,
                        
                    }
                )                
                

            elif data['type'] == 'video_call_invitation':
                logger.info("Received video_call_invitation message from client")
                room_id = data['room_id']
                invited_user_id = data['invited_user_id']
                inviting_user_id = data['inviting_user_id']
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        "type": "video_call_invitation",
                        "room_id": room_id,
                        "invited_user_id": invited_user_id,
                        "inviting_user_id": inviting_user_id,
                        "sender_id": self.scope['user'].id
                    }
                )
            elif data['type'] == 'output_text_send':
                logger.info("Received output text return message from client")
                logger.info("Sending message to group: %s", "video_call_group")
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        "type": "output_text_return1",
                        "output_text1": data['output_text1'],
                        "sender_id": data['sender_id'],
                        "room_id": data['room_id'],
                    }
                )
                
                
                
            if data['type']  == 'offer':
                # Handle offer
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        'type': 'webrtc_offer',
                        'sdp': data['sdp'],
                        'sender_id': data.get('sender_id'),
                        'room_id': data.get('room_id'),
                    }
                )
            elif data['type']  == 'answer':
                # Handle answer
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        'type': 'webrtc_answer',
                        'sdp': data['sdp'],
                        'sender_id': data.get('sender_id'),
                        'room_id': data.get('room_id'),
                    }
                )
            elif data['type']  == 'ice_candidate':
                # Handle ICE candidate
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        'type': 'ice_candidate',
                        'candidate': data['candidate'],
                        'sender_id': data.get('sender_id'),
                        'room_id': data.get('room_id'),
                    }
                )
            else:
                logger.warning("Unknown message type: %s", data['type'])
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON message: %s", e)
        except KeyError as e:
            logger.error("Missing key in received message: %s", e)
        except Exception as e:
            logger.error("Error processing message (consumer): %s", e)
            
    

    async def output_text_return1(self, event):
        logger.info("Handling output_text_return for event: %s", event)
        
        current_time = time.time()
        if current_time - self.last_sent_message_time >= 5:
            await self.send(text_data=json.dumps({
                'type': 'output_text_s',
                'output_text1': event['output_text1'],
                'sender_id': event['sender_id'],
                'room_id': event['room_id'],
            }))
            self.last_sent_message_time = current_time
        else:
            logger.info("Message discarded as it matches the previous message sent within 5 seconds.")



    async def webrtc_offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'offer',
            'sdp': event['sdp'],
            'sender_id': event.get('sender_id'),
            'room_id': event.get('room_id'),
        }))

    # Send WebRTC answer to WebSocket
    async def webrtc_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'answer',
            'sdp': event['sdp'],
            'sender_id': event.get('sender_id'),
            'room_id': event.get('room_id'),
        }))

    # Send ICE candidate to WebSocket
    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ice_candidate',
            'candidate': event['candidate'],
            'sender_id': event.get('sender_id'),
            'room_id': event.get('room_id'),
        }))
    @database_sync_to_async
    def load_messages(self, conversation_name):
        return list(Message.objects.filter(conversation__name=conversation_name).values())

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content, timestamp, conversation_name):
        conversation = Conversation.objects.get(name=conversation_name)
        message = Message.objects.create(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            timestamp=timestamp,
            conversation=conversation
        )
        return {
            'id': message.id,
            'sender_id': message.sender_id,
            'content': message.content,
            'timestamp': message.timestamp,
            'conversation_id': message.conversation_id
        }
    
    async def chat_message(self, event):
        message = event['message']
        conversation_name = event['conversation_name']
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": message,
            "conversation_name": conversation_name 
        }))