// websocket.js
//const socket = new WebSocket('ws://ebigkas.com/ws/video_call/');
const socket = new WebSocket('ws://localhost:8000/ws/video_call/');



let sentStatus = sessionStorage.getItem('sentStatus') || 0;

let inactivityTimeout;
let isOnline = false; // Flag to track if the status is online

// Function to handle status updates
function handleStatusUpdate(status) {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: 'friend_status',
            loggedInUserID: sessionStorage.getItem('loggedInUserId'),
            loggedInUsername: sessionStorage.getItem('loggedInUsername'),
            status: status
        }));
    }
}

 // WebRTC configuration
 const configuration = { 
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] // Public STUN server
};

function createPeerConnection() {
  peerConnection = new RTCPeerConnection(configuration);

  peerConnection.onicecandidate = function(event) {
      if (event.candidate) {
          //console.log('ICE Candidate:', event.candidate);
          socket.send(JSON.stringify({
              type: 'ice_candidate',
              candidate: event.candidate,
              sender_id: loggedInUserId,
              room_id: roomID
          }));
      }
  };

  peerConnection.ontrack = function(event) {
      //console.log('Remote stream added:', event.streams[0]);
      const remoteAudio = document.getElementById('remoteAudio');
      const remoteVideo = document.getElementById('remoteVideo'); 
  
      if (remoteAudio && event.track.kind === 'audio') {
          remoteAudio.srcObject = event.streams[0]; // Assign audio stream
      }
      
      if (remoteVideo && event.track.kind === 'video') {
          remoteVideo.srcObject = event.streams[0]; // Assign video stream
      }
  };
  
}



// Function to reset inactivity timer and update status
function resetInactivityTimer() {
    clearTimeout(inactivityTimeout);

    // Send online status if not already set
    if (!isOnline) {
        handleStatusUpdate('online');
        isOnline = true;
    }

    // Set the timeout to notify the server of inactivity
    inactivityTimeout = setTimeout(() => {
        handleStatusUpdate('offline');
        isOnline = false; // Update flag when going offline
    }, 2 * 60 * 1000); // 2 minutes
}

// Initialize the inactivity timer
resetInactivityTimer();


// Reset the inactivity timer on user activity
window.addEventListener('mousemove', resetInactivityTimer);
window.addEventListener('keydown', resetInactivityTimer);
window.addEventListener('scroll', resetInactivityTimer);



socket.onopen = function(event) {
    const conversationName1 = sessionStorage.getItem('ConversationName');
    if (conversationName1) {
        socket.send(JSON.stringify({
            type: 'load_messages',
            conversationName: conversationName1
        }));
    }

    if (sentStatus == 0) {
        socket.send(JSON.stringify({
            type: 'friend_status',
            loggedInUserID: sessionStorage.getItem('loggedInUserId'),
            loggedInUsername: sessionStorage.getItem('loggedInUsername'),
            status : 'online'
        }));

        // Update sent status in sessionStorage
        sessionStorage.setItem('sentStatus', 1);
        sentStatus = 1;

        console.log("sent status: " + sentStatus);
    }

    console.log("WebSocket connection established with room id");
};
socket.onclose = function(event) {
    console.log('WebSocket closed with code:', event.code);
    console.log('Reason for closing:', event.reason);
    if (socket.readyState === WebSocket.OPEN) {
        try {
            socket.send(JSON.stringify({
                type: 'friend_status',
                loggedInUserID: sessionStorage.getItem('loggedInUserId'),
                loggedInUsername: sessionStorage.getItem('loggedInUsername'),
                status: 'offline'
            }));
        } catch (error) {
            console.error('Error sending message on WebSocket close:', error);
        }
    } else {
        console.warn('WebSocket is not open. Cannot send message.');
    }
};












let isHandlingAnswer = false;
let iceCandidatesQueue = [];


socket.onmessage = function(event) {
    const message = JSON.parse(event.data);


    // Handle offer
if (message.type === 'offer' && message.sender_id != loggedInUserId) {
    if (!peerConnection) createPeerConnection();
    peerConnection.setRemoteDescription(new RTCSessionDescription({ type: 'offer', sdp: message.sdp }))
        .then(() => peerConnection.createAnswer())
        .then(answer => peerConnection.setLocalDescription(answer))
        .then(() => {
            socket.send(JSON.stringify({
                type: 'answer',
                sdp: peerConnection.localDescription.sdp,
                sender_id: loggedInUserId,
                room_id: roomID
            }));
        })
        .catch(error => console.error('Error handling offer:', error));
}

// Handle answer
if (message.type === 'answer' && message.sender_id != loggedInUserId) {
    if (!peerConnection) {
        console.log('No peer connection, ignoring answer.');
        return;
    }
    if (isHandlingAnswer) {
        console.log('Already handling an answer, ignoring new answer.');
        return;
    }
    isHandlingAnswer = true;
    peerConnection.setRemoteDescription(new RTCSessionDescription({ type: 'answer', sdp: message.sdp }))
        .then(() => {
            isHandlingAnswer = false;
            iceCandidatesQueue.forEach(candidate => peerConnection.addIceCandidate(candidate));
            iceCandidatesQueue = [];
        })
        .catch(error => {
            console.error('Error handling answer:', error);
            isHandlingAnswer = false;
        });
}

// Handle ICE candidates
if (message.type === 'ice_candidate' && message.sender_id != loggedInUserId) {
    if (!peerConnection) {
        console.log('No peer connection, ignoring ICE candidate.');
        return;
    }
    const candidate = new RTCIceCandidate(message.candidate);
    if (peerConnection.remoteDescription) {
        peerConnection.addIceCandidate(candidate)
            .catch(error => console.error('Error adding ICE candidate:', error));
    } else {
        iceCandidatesQueue.push(candidate);
    }
}


    if(message.type === 'friend_request_accepted'){
        if(message.user == loggedInUserID){
            friends_list();
        }
        else{
            console.log("not for u" +message.user)
        }
    }
 
        

    if (message.type === 'predicted_action' && message.room_id === roomID) {
        console.log('Received data with room ID:', message); 
        const outputText = message.predicted_action ? message.predicted_action : "blank";
        
        const sanitizedOutputText = removeDuplicates(outputText);
        
        // Create a new div element
        const newDiv = document.createElement('div');
        
        // Set class based on sender_id
        if (message.sender_id === loggedInUserId) {
            newDiv.classList.add('your-sent-action');
        } else {
            newDiv.classList.add('friend-sent-action');
        }

        
        // Clear and speak the output text
        const outputTextElement = document.getElementById('translatedText');
        outputTextElement.textContent = ''; 
        typeText(outputTextElement, sanitizedOutputText); 
        if(sanitizedOutputText != 'blank'){
            speakText(sanitizedOutputText)
        }
  
        setTimeout(() => {
            newDiv.textContent = sanitizedOutputText;
    
          // Append the new div element to the parent container
          const sentActionsContainer = document.querySelector('.sent-actions');
          sentActionsContainer.appendChild(newDiv);
        }, 2000); 

    }
    

    if (message.type === 'output_text1') {
        console.log('Received data with room ID:', message); 
        const outputText1 = message.output_text1;
        
        socket.send(JSON.stringify({
            'type': 'output_text_send',
            'output_text1': outputText1,
            'sender_id': loggedInUserId,
            'room_id': roomID
        }));
    }

    


    if (message.type === 'video-frame' && message.room_id == roomID) {
        const localVideo = document.getElementById('localVideo');
        const remoteVIdeo = document.getElementById('remoteVideo');
        if( message.sender_id == loggedInUserId){
            localVideo.src = message.frame;
        }
        else{
            remoteVIdeo.src = message.frame;
        }
    }

  
    
if (message.type === 'update_profile') {
    // Update the profile content with the received data
    const profileElement = document.getElementById("profile");
    profileElement.textContent = message.content;
}



if (message.type === 'message') {
    const messagesAlert1 = document.getElementById('message-alert');
    if(message.receiver_id == loggedInUserID){
        messagesAlert1.style.display = "flex";
    }
    const message_convoName = message.conversation_name;
    loadFriendsConversations();


    if(conversationName == message_convoName ){
        handleIncomingMessage(message.message);
        scrollToBottom();
        console.log("loaded friends messages")
    }
}

if (message.type === 'messages_loaded') { 
    const message_convoName = message.conversation_name;
        if(conversationName == message_convoName){
            handleMessagesLoaded(message);
                loadFriendsConversations();
        
                } 
 } 
    
    if (message.type === 'video_call_invitation') {
        const invitedUserId = message.invited_user_id; // Corrected key name
        const roomId = message.room_id; // Replace this with the actual room ID

        const invitingUserID = message.inviting_user_id; // Extract inviting user ID from the message

        // Save inviting user ID to session storage
        sessionStorage.setItem('invitingUserID', invitingUserID);
        
        const modal = document.getElementById('confirmationModal');
        // Get the buttons
        const confirmBtn = document.getElementById('confirmBtn');
        const cancelBtn = document.getElementById('cancelBtn');
        
        // Function to show the modal
        function showModal() {
            modal.style.display = 'block';
        }
        
        // Function to hide the modal
        function hideModal() {
            modal.style.display = 'none';
        }
    
        // Function to play ringtone sound
        function playRingtone() {
            const ringtone = new Audio("static\\images\\notif.wav"); 
            ringtone.play();
        }
        
        // Event listener for confirm button
        confirmBtn.addEventListener('click', function() {
            sessionStorage.setItem('invited', 'true');
            const loggedInUserID12 = sessionStorage.getItem('loggedInUserId');
            sessionStorage.setItem('invitedUserID', loggedInUserID12);

            // Retrieve call start time from session storage
            const callStartTime = new Date(sessionStorage.getItem('callStartTime'));
            const callEndTime = new Date();
            const duration = new Date(callEndTime - callStartTime); // Duration in milliseconds

            // Format duration in HH:MM:SS
            const hours = String(duration.getUTCHours()).padStart(2, '0');
            const minutes = String(duration.getUTCMinutes()).padStart(2, '0');
            const seconds = String(duration.getUTCSeconds()).padStart(2, '0');
            const formattedDuration = `${hours}:${minutes}:${seconds}`;

            // Send AJAX request to update the room status
            fetch(`/update-room-status/${roomId}/accepted/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') // Add CSRF token for POST requests
                },
                body: JSON.stringify({
                    room_id: roomId,
                    status: 'accepted'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = `${window.location.protocol}//${window.location.host}/room/${roomId}/`;
                    playRingtone(); // Call function to play ringtone
                }
            })
            .catch(error => console.error('Error:', error));
        });

        cancelBtn.addEventListener('click', function() {

            fetch(`/update-room-status/${roomId}/missed/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') 
                },
                body: JSON.stringify({
                    room_id: roomId,
                    status: 'missed'
                })
            })
            .then(response => response.json())
            .catch(error => console.error('Error:', error));
                    
            socket.send(JSON.stringify({
                type: 'hang_up',
                receiver_id: invitingUserID,
            }));
            hideModal();
        });
        
        // Show the modal when receiving video call invitation
        if (invitedUserId === sessionStorage.getItem('loggedInUserId')) {
            showModal();
            playRingtone(); // Play the ringtone
            setTimeout(function() {
                hideModal();
            }, 30000); // 30 seconds
        } else {
           // console.log('This invitation is not for the logged-in user.');
        }
    }
    
    if (message.type === 'friend_status') {
        loadFriendsConversations()
        const friend_id = message.recent_loggedInUserID;
        const friend_username = message.recent_loggedInUsername;
        
        // Construct the classname based on friend_username and friend_id
        const classname = `${friend_username}${friend_id}`;
        //console.log('Constructed classname:', classname);
    
        // Find the friend container based on classname
        const friendsListDiv = document.querySelector(`.${classname}`);
    
        if (friendsListDiv) {
            // Update the text content of the usernameDiv
            const usernameDiv = friendsListDiv.querySelector('.friend-username-div');
            if (usernameDiv && message.status == 'online') {
                usernameDiv.textContent = friend_username;
                usernameDiv.style.color = '#01d601'; 
                usernameDiv.style.fontWeight = 'bold'; 
            }
            else if (usernameDiv && message.status == 'offline') {
                usernameDiv.textContent = friend_username;
                usernameDiv.style.color = 'white'; 
                usernameDiv.style.fontWeight = 'normal'; 
            }
                
            // Move the friend container to the top of its siblings
            const friendsList = document.getElementById('friends-list');
            friendsList.insertBefore(friendsListDiv, friendsList.firstChild); // Insert at the top
        } else {
            console.error(`Friend container with classname ${classname} not found.`);
        }
    }

    if(message.type === 'hang_up'){

        if(loggedInUserId == message.receiver_id){
            const hangup_overlay = document.getElementById('hangup_overlay');
            const hangup_remind = document.getElementById('hangup_remind');
            const call_ended_okay = document.getElementById('call_ended_okay');

            hangup_overlay.style.display = 'block';
            hangup_remind.style.display = 'block';
        }
    }
    
}
