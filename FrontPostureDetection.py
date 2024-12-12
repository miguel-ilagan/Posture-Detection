import cv2
import time
import math as m
import mediapipe as mp
from pygame import mixer
import time

# Reference is made to https://learnopencv.com/building-a-body-posture-analysis-system-using-mediapipe/

# Define function which will compute the angle between left point and right point.
# (x1, y1) are the coordinates of the left point
# (x2, y2) are the coordinates of the right point
# Note that the x-coordinate of the right side is less than the left side.
def compute_angle(x1, y1, x2, y2):
    angle = m.atan((abs(y1-y2))/(x1-x2)) # output in radians
    angle = int(180/m.pi)*angle
    return int(angle)

# Define function to send alert when bad posture is detected
# https://stackoverflow.com/questions/20021457/playing-mp3-song-on-python
mixer.init()
def play_sound(filename):
    mixer.music.load(filename)
    mixer.music.play()

    # Wait for the sound to finish
    while mixer.music.get_busy():
        time.sleep(1)

# Variables to count number of frames with good and bad posture
good_frames = 0
bad_frames  = 0
 
# Font type.
font = cv2.FONT_HERSHEY_SIMPLEX
 
# Colors.
colour1 = (50, 50, 255)
colour2 = (0, 255, 255)
colour3 = (255, 0, 255)
 
# Initialize mediapipe pose class.
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialise webcam
cap = cv2.VideoCapture(0)

# Set webcam properties
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)  # Set width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Set height

print("Press 'q' to exit the webcam")

while cap.isOpened():

    # Capture frames
    success, image = cap.read()

    if not success:
        continue

    # Get fps.
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Get height and width of the frame.
    h, w = image.shape[:2]
    
    # Convert the BGR image to RGB.
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Process the image (requires RGB input).
    keypoints = pose.process(image)

    # Visualise keypoints 
    # Use lm and lmPose as representative of the following methods.
    lm = keypoints.pose_landmarks

    if lm:
        lmPose  = mp_pose.PoseLandmark
        
        # Coordinates of landmarks
        # Left shoulder.
        left_shoulder_x = int(lm.landmark[lmPose.LEFT_SHOULDER].x * w)
        left_shoulder_y = int(lm.landmark[lmPose.LEFT_SHOULDER].y * h)
        
        # Right shoulder.
        right_shoulder_x = int(lm.landmark[lmPose.RIGHT_SHOULDER].x * w)
        right_shoulder_y = int(lm.landmark[lmPose.RIGHT_SHOULDER].y * h)
        
        # Left ear.
        left_ear_x = int(lm.landmark[lmPose.LEFT_EAR].x * w)
        left_ear_y = int(lm.landmark[lmPose.LEFT_EAR].y * h)
        
        # Right ear.
        right_ear_x = int(lm.landmark[lmPose.RIGHT_EAR].x * w)
        right_ear_y = int(lm.landmark[lmPose.RIGHT_EAR].y * h)
        
        # Left elbow
        left_elbow_x = int(lm.landmark[lmPose.LEFT_ELBOW].x * w)
        left_elbow_y = int(lm.landmark[lmPose.LEFT_ELBOW].y * h)

        # Right elbow
        right_elbow_x = int(lm.landmark[lmPose.RIGHT_ELBOW].x * w)
        right_elbow_y = int(lm.landmark[lmPose.RIGHT_ELBOW].y * h)

        # Draw landmarks
        cv2.circle(image, (left_shoulder_x, left_shoulder_y), 7, colour2, -1) # Draw left shoulder
        cv2.circle(image, (right_shoulder_x, right_shoulder_y), 7, colour2, -1) # Draw right shoulder
        cv2.circle(image, (left_ear_x, left_ear_y), 7, colour3, -1)  # Draw left ear
        cv2.circle(image, (right_ear_x, right_ear_y), 7, colour3, -1) # Draw right ear
        cv2.circle(image, (left_elbow_x, left_elbow_y), 7, colour1, -1) # Draw left elbow
        cv2.circle(image, (right_elbow_x, right_elbow_y), 7, colour1, -1) # Draw right elbow

        # Draw lines connecting the the left and right landmarks
        cv2.line(image, (left_shoulder_x, left_shoulder_y), (right_shoulder_x, right_shoulder_y), colour2, 2)
        cv2.line(image, (left_ear_x, left_ear_y), (right_ear_x, right_ear_y), colour3, 2)

        # Put text of the angle between left and right landmarks
        ear_angle = compute_angle(left_ear_x, left_ear_y, right_ear_x, right_ear_y)
        shoulder_angle = compute_angle(left_shoulder_x, left_shoulder_y, right_shoulder_x, right_shoulder_y)
    
        # Display angles
        cv2.putText(image, f'Ear angle: {ear_angle:} degrees', (left_ear_x, left_ear_y - 10), font, 0.8, colour3, 2)
        cv2.putText(image, f'Shoulder angle: {shoulder_angle} degrees', (left_shoulder_x, left_shoulder_y - 10), font, 0.8, colour2, 2)
        
        # Track duration of poor and good posture
        # Thresholds (selected based on personal experimentation)
        angle_threshold = 3
        elbow_threshold = 535 # Case where elbows are on the table
        if ear_angle >= 3 or shoulder_angle >= 3 or left_elbow_y > 535 or right_elbow_y > 535:
            good_frames = 0
            bad_frames += 1
        
        else:
            good_frames += 1
            bad_frames = 0

        good_posture_duration = (1/fps) * good_frames
        bad_posture_duration = (1/fps) * bad_frames

        # Pose time.
        if good_posture_duration > 0:
            time_string_good = 'Good Posture Time : ' + str(round(good_posture_duration, 1)) + 's'
            cv2.putText(image, time_string_good, (10, h - 20), font, 0.9, colour2, 2)
        else:
            time_string_bad = 'Bad Posture Time : ' + str(round(bad_posture_duration, 1)) + 's'
            cv2.putText(image, time_string_bad, (10, h - 20), font, 0.9, colour1, 2)
        
        # If you stay in bad posture for more than threshold (seconds) send an alert.
        BAD_POSTURE_THRESHOLD = 10
        if bad_posture_duration > BAD_POSTURE_THRESHOLD:
            play_sound('posture.mp3')

    # Convert the image back to BGR.
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Display the live webcam feed (required BGR input)
    cv2.imshow('Webcam Feed', image)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break