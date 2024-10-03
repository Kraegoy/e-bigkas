document.addEventListener('DOMContentLoaded', function () {
    const leftNav = document.querySelector('.nav-container');
    const checkbox = document.getElementById('checkbox');
    const bottomContent = document.querySelector('.bottom-content');    
    const videoContainer = document.querySelector('.video-container');    
    const videStreams = document.querySelector('#video-streams');  
    const controlsWrapper = document.querySelector('#controls-wrapper');   
    const allfriend = document.querySelector('#allfriend');  
    const profileContainer = document.querySelector('#profile-container');  
    const loggedinUser = document.querySelector('#loggedinUser');  
    const user_profilePic = document.querySelector('#user-profilePic');  
    const navs = document.querySelector('#navs');  




    checkbox.addEventListener('change', function () {

        if (checkbox.checked) {
            if(profileContainer){
                profileContainer.style.marginLeft = '-5em';
            }
            if(allfriend){
                allfriend.style.marginLeft = '-5em';
            }
            if(videoContainer){
                videoContainer.style.marginRight = '1.5em';
                videStreams.style.marginLeft = '74%';
                controlsWrapper.style.marginLeft = '33%';
            }
            if(bottomContent){
                bottomContent.style.marginLeft = '-1%';
            }
            leftNav.classList.add('menu-opened');
            loggedinUser.style.display = 'none';
            user_profilePic.style.marginLeft ="5.5em";
            navs.style.display ="none";


        } else {
            if(profileContainer){
                profileContainer.style.marginLeft = '0';
            }
            if(allfriend){
                allfriend.style.marginLeft = '0';
            }  
            if(videoContainer){
                videoContainer.style.marginRight = '2px';
                videStreams.style.marginLeft = '78.5%'; 
                controlsWrapper.style.marginLeft = '37%';
            }
            if(bottomContent){
                bottomContent.style.marginLeft = '30px';
            }
            leftNav.classList.remove('menu-opened');
            loggedinUser.style.display = 'block';
            user_profilePic.style.marginLeft ="2em"
            navs.style.display ="block";


        }
    });
    

    
});


   

