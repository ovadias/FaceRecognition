# attendance.py
import cv2
#import numpy as np
import pandas as pd
#from deepface import DeepFace
#from mtcnn.mtcnn import MTCNN
import pickle
import os
#from PIL import Image
#import random
import face_recognition
from retinaface import RetinaFace
import matplotlib.pyplot as plt
#from tqdm import tqdm
#import tensorflow as tf

def take_attendance(image_path, embeddings_path, class_list_csv, output_directory):
    # Load embeddings
    with open(embeddings_path, 'rb') as file:
            known_faces_encodings, known_face_names = pickle.load(file)
    


    print(f"Opening image: {image_path}")

    img = cv2.imread(image_path)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
   
    # Detect faces using RetinaFace
    print('Performing detection')
    face_locations = RetinaFace.detect_faces(img)

        # Convert face_locations to the format expected by face_recognition library
    face_locations = [(face['facial_area'][1], face['facial_area'][2], face['facial_area'][3], face['facial_area'][0]) for face in face_locations.values()]

    print('performing recognition')
        # Recognize faces using face_recognition library
    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

    detected_names = []

        # Loop through detected faces and their encodings
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Compare face encodings with known face encodings
        distances = face_recognition.face_distance(known_faces_encodings, face_encoding)

            # Find the index of the closest match
        min_distance_index = distances.argmin()

        # Draw a rectangle around the face
        cv2.rectangle(img, (left, top), (right, bottom), (0, 0, 255), 3)

        # Add text label with the identity
        name = known_face_names[min_distance_index]
        detected_names.append(name)
        cv2.putText(img, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)


    output_image_path = os.path.join(output_directory, 'processed_image.jpg')
    print(f"Saving processed image to {output_image_path}")
    cv2.imwrite(output_image_path, img)

    class_list_df = pd.read_csv(class_list_csv)
    print(f"Reading class list from {class_list_csv}")
    class_list = class_list_df['Student Name'].tolist()
    print(f"Total students in class list: {len(class_list)}")

    attendance_records = [{'Student Name': name, 'Present': 'Yes' if name in detected_names else 'No'} for name in class_list]
    attendance_df = pd.DataFrame(attendance_records)

    attendance_csv_path = os.path.join(output_directory, 'attendance.csv')
    print(f"Saving attendance to {attendance_csv_path}")
    attendance_df.to_csv(attendance_csv_path, index=False)

    print("Attendance processing completed.")
    return output_image_path, attendance_csv_path