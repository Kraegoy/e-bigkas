const loggedInUserID = sessionStorage.getItem('loggedInUserId');
const loggedInUsername = sessionStorage.getItem('loggedInUsername');
sessionStorage.setItem('loggedInUserId', '{{ request.user.id }}');
sessionStorage.setItem('loggedInUsername', '{{ request.user.username }}');


// Function to send a video call invitation
function sendVideoCallInvitation(roomID, invitedUserID) {
    const message = {
        type: 'video_call_invitation',
        room_id: roomID,
        invited_user_id: invitedUserID
    };
    socket.send(JSON.stringify(message)); // Send the message object
}




// Function to generate a random room ID
function generateRoomID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

 
 sessionStorage.setItem('roomID', roomID);

//-------------------------------------------------Detection----------------------------------------------------------

var toggleButton = document.getElementById('toggleButton');
var speakButton = document.getElementById('speakButton');

const cameraBtn =  document.getElementById('camera-btn');
const leftNav = document.querySelector('.nav-container');
const checkbox = document.getElementById('checkbox');
const bottomContent = document.querySelector('.bottom-content');    
const videoContainer = document.querySelector('.video-container');    
const videStreams = document.querySelector('#video-streams');  
const controlsWrapper = document.querySelector('#controls-wrapper');    
var video = document.getElementById('video');


cameraBtn.addEventListener('click', function() {
let videoElement = document.getElementById('video-video');

if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    if (!videoElement.srcObject) {
        // Camera is currently off, turn it on
        cameraBtn.style.backgroundColor = 'rgba(245, 222, 179, 0.886)';
        video.src = '';
        leftNav.classList.add('menu-opened');
        videoContainer.style.marginRight = '1.5em';
        videStreams.style.marginLeft = '74%';
        bottomContent.style.marginLeft = '-1%'
        controlsWrapper.style.marginLeft = '33%'
        
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                videoElement.srcObject = stream;
                videoElement.style.transform = 'translateY(-100.75%) scaleX(-1)'; // Apply both translations
            })
            .catch(function(error) {
                console.error('Error accessing camera:', error);
            });
    } else {
        leftNav.classList.remove('menu-opened');
        videoContainer.style.marginRight = '2px';
        videStreams.style.marginLeft = '78.5%'; 
        bottomContent.style.marginLeft = '30px'
        controlsWrapper.style.marginLeft = '37%'
        cameraBtn.style.backgroundColor = 'rgb(255, 80, 80, 1)';

        let stream = videoElement.srcObject;
        let tracks = stream.getTracks();
        
        tracks.forEach(function(track) {
            track.stop();
        });
        
        videoElement.srcObject = null;
    }
} else {
    console.error('getUserMedia not supported on this browser');
}
});



var streaming = false;
function toggleStream() {

// currently at stop recognition
if (streaming) {
    socket.send(JSON.stringify({ 'type': 'stop_recognition' }));
    video.src = '';
    toggleButton.innerText = 'Start Recognition';
    toggleButton.classList.remove('stopButton');
    toggleButton.classList.add('startButton');

    leftNav.classList.remove('menu-opened');
    videoContainer.style.marginRight = '2px';
    videStreams.style.marginLeft = '78.5%'; 
    bottomContent.style.marginLeft = '30px';
    controlsWrapper.style.marginLeft = '37%';
} else {
        // Turn off camera first
    let videoElement = document.getElementById('video-video');
    let stream = videoElement.srcObject;
    if (stream) {
        let tracks = stream.getTracks();
        tracks.forEach(function(track) {
            track.stop();
        });
        videoElement.srcObject = null;
    }
    socket.send(JSON.stringify({ 'type': 'start_recognition' }));

    toggleButton.innerText = 'Stop Recognition';
    toggleButton.classList.remove('startButton');
    toggleButton.classList.add('stopButton');

    leftNav.classList.add('menu-opened');
    videoContainer.style.marginRight = '1.5em';
    videStreams.style.marginLeft = '74%';
    bottomContent.style.marginLeft = '-1%';
    controlsWrapper.style.marginLeft = '33%';
}
streaming = !streaming;
}


function simulateCameraBtnClick() {
cameraBtn.click();
}

// Add an event listener to send a message to the server when Enter key is pressed
document.addEventListener('keypress', function(event) {
if (event.key === 'Enter') {
    const message = {
        type: 'stop_recognition'
    };
    // Send WebSocket message to server
    socket.send(JSON.stringify(message));
    // Simulate click on cameraBtn
    simulateCameraBtnClick();
}
});

function typeText(element, text, index = 0) {
if (index < text.length) {
    element.textContent += text.charAt(index);
    index++;
    setTimeout(() => typeText(element, text, index), 100); 
}
}


function speakText(textToSpeak) {
 var synth = window.speechSynthesis;
 var utterance = new SpeechSynthesisUtterance(textToSpeak);

 // Set the language
 utterance.lang = 'en-IE'; // English (Ireland)

 // Set the voice directly without relying on onvoiceschanged event
 var voices = synth.getVoices();
 for (var i = 0; i < voices.length; i++) {
     if (voices[i].name === 'Microsoft Emily Online (Natural) - English (Ireland)') {
         utterance.voice = voices[i];
         break;
     }
 }
 // Speak the utterance
 synth.speak(utterance);
}

document.addEventListener('DOMContentLoaded', function () {
 const addFriendForms = document.querySelectorAll('.add-friend-form');
 addFriendForms.forEach(form => {
     form.addEventListener('submit', function (event) {
         event.preventDefault();
         const formData = new FormData(form);
         const friendId = formData.get('friend_id');
         fetch(form.action, {
             method: 'POST',
             body: formData,
             headers: {
                 'X-CSRFToken': '{{ csrf_token }}'
             }
         })
         .then(response => response.json())
         .then(data => {
             if (data.success) {
                 // Reload the page
                 location.reload();
             } else {
                 // Handle error
                 console.error(data.error);
             }
         })
         .catch(error => {
             console.error('Error:', error);
         });
     });
 });
});



const micBtn = document.getElementById('mic-btn');
let x = true; 

micBtn.addEventListener('click', function onClick() {
if (x === true) {
    micBtn.style.backgroundColor = 'rgb(255, 80, 80, 1)';
    x = false;
} else {
    micBtn.style.backgroundColor = 'rgba(245, 222, 179, 0.886)';
    x = true;
}
});

