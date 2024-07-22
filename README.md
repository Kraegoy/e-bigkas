# e-BIGKAS

## Overview
This project aims to create a platform for detecting basic Filipino sign language words using TensorFlow, MediaPipe, RNN, 
and other relevant technologies. It provides video call functionality, catering to the needs of the deaf community and their 
loved ones who may not understand Filipino sign language. The project is developed as a part of our thesis 
and for the "Friendship of Enjoy" community.

## Installation

### Prerequisites
- Python

### Installation Steps
1. Install Python if not already installed.
2. Install the required Python packages:
    ```
    pip install opencv-python
    pip install matplotlib
    pip install mediapipe
    pip install tensorflow==2.12.0rc0
    pip install django
    pip install channels
    pip install happytransformer
    ```

## Usage
1. Clone or download the project repository.
1.2. Paste the folders base, demo, static, and templates to the 	project
2. Navigate to the project directory.
3. Run the Django server:
    ```
    python manage.py runserver
    ```
4. Access the platform through your web browser.

## Troubleshooting
- If there are issues related to the database, especially concerning 'friendship' or 'userProfile', try running the following command:
    ```
    python manage.py migrate base
    ```

## Contributing
Thank you for considering contributing to our project! Feel free to submit bug reports, feature requests, or pull requests via GitHub.


## Contact Information
For any inquiries or support, please contact avilakraeg@gmail.com .

## Credits
This project was made possible with the support of the "Friendship of Enjoy" community and contributions from the following individuals:
- Avila, Kraeg (Lead Programmer / System analyst)
- Esdicul, Ralph David
- Mangguing, Sebastian

