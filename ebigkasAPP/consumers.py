import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import threading
from django.http import JsonResponse
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
                     
    
    async def process_extracted_keypoints(self, sender_id, room_id, sequences):
        threshold = 0.6
        action_names = []  # Use a list to store action names
        confidences = []  # Store confidences for each action

        for sequence in sequences:
            try:
                # Predict action for the current sequence
                res = model.predict(np.expand_dims(sequence, axis=0))[0]
                action = np.argmax(res)
                confidence = res[action]

                if confidence > threshold:
                    action_names.append(str(actions[action]))  # Collect action names
                    confidences.append(confidence)  # Collect corresponding confidence values

            except Exception as e:
                print(f"Error during model prediction: {e}")
                continue  # Continue to the next sequence

        # If any action names were predicted, send them to the group
        if action_names:
            combined_action_names = " ".join(action_names)  # Combine actions into a single string
            try:
                await self.send_prediction_to_group(sender_id, room_id, combined_action_names)
                print(f"Sent predicted actions: {combined_action_names} with confidences: {confidences}")

            except Exception as send_error:
                print(f"Error sending predicted actions: {send_error}")
        else:
            print("No action predicted.")

    async def send_prediction_to_group(self, sender_id, room_id, predicted_action):
        try:
            await self.channel_layer.group_send(
                'video_call_group',
                {
                    'type': 'predicted_action_back',
                    'predicted_action': predicted_action,
                    'sender_id': sender_id,
                    'room_id': room_id
                }
            )
            print(f"Sent prediction to group: {predicted_action}")
        except Exception as e:
            print(f"Error sending prediction to group: {e}")

    async def predicted_action_back(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'predicted_action',
            'predicted_action': event['predicted_action'],
            'sender_id': event['sender_id'],
            'room_id': event['room_id']
        }))
        
    async def friend_request_accepted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'friend_request_accepted',
            'user': event['user']
        }))

            

            

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
                        "conversation_name" : conversation_name,
                        "sender_id": sender_id,
                        "receiver_id" : receiver_id,
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
                
            elif data['type'] == 'predict_actions_taken':
                sender_id = data.get('sender_id')
                room_id = data.get('room_id')
                sequences = data.get('data')
                await self.process_extracted_keypoints(sender_id, room_id, sequences)
                
                
                
            elif data['type'] == 'predicted_action':
                predicted_action = data.get('predicted_action')
                sender_id = data.get('sender_id')
                room_id = data.get('room_id')
                # Send predicted actions to room group
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        'type': 'predicted_action',
                        'predicted_action': predicted_action,
                        'sender_id': sender_id,
                        'room_id': room_id
                    }
                )
                
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
                
            elif data['type'] == 'friend_request_accepted':
                user = data.get('user')
                await self.channel_layer.group_send(
                    "video_call_group",
                    {
                        'type': 'friend_request_accepted',
                        'user': user,
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
        sender_id = event['sender_id']
        receiver_id = event['receiver_id']
        conversation_name = event['conversation_name']
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": message,
            "conversation_name": conversation_name,
            "sender_id": sender_id,
            "receiver_id": receiver_id,

        }))