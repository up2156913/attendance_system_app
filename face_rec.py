import cv2
import numpy as np
import pandas as pd
import redis



from insightface.app import FaceAnalysis
from sklearn.metrics import pairwise

import time
from datetime import datetime

import os

# Connect to Redis Client
hostname = 'redis-19487.c8.us-east-1-4.ec2.redns.redis-cloud.com'
portnumber = 19487
password = 'ee3x3qAQ7yPMws3P5vHquvbE8o6LY84d'


r = redis.StrictRedis(host=hostname,
                     port=portnumber,
                     password=password)




#Retrive Data from database
def retrive_data(name):
    """
    Retrieve and process data from Redis database
    """
    try:
        # Create Redis connection with retry mechanism
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                retrive_dict = r.hgetall(name)
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise
        
        print(f"Retrieved {len(retrive_dict)} entries from Redis")
        
        # Convert bytes to string for keys
        retrive_dict = {k.decode('utf-8'): v for k, v in retrive_dict.items()}
        
        # Create DataFrame
        retrive_series = pd.Series(retrive_dict)
        
        # Convert the binary data to numpy arrays and ensure 512 dimensions
        def process_embedding(x):
            arr = np.frombuffer(x, dtype=np.float32)
            # If the array is 1024-dimensional, reshape it to 512
            if len(arr) == 1024:
                return arr[:512]  # Take first 512 dimensions
            return arr
            
        retrive_series = retrive_series.apply(process_embedding)
        
        # Verify embedding dimensions
        first_embedding = retrive_series.iloc[0] if len(retrive_series) > 0 else None
        if first_embedding is not None:
            print(f"Embedding dimension after processing: {len(first_embedding)}")
        
        # Split the name_role into separate columns
        retrive_df = retrive_series.to_frame().reset_index()
        retrive_df.columns = ['name_role', 'Facial_features']
        retrive_df[['Name', 'Role']] = retrive_df['name_role'].str.split('@', expand=True)
        
        return retrive_df[['Name', 'Role', 'Facial_features']]
        
    except Exception as e:
        print(f"Error retrieving data from Redis: {e}")
        return pd.DataFrame(columns=['Name', 'Role', 'Facial_features'])

# configure face analysis
faceapp = FaceAnalysis(name='buffalo_sc', root='insightface_model', providers = ['CPUExecutionProvider'])
faceapp.prepare(ctx_id = 0, det_size=(640,640), det_thresh = 0.5)


# ML Search Algorithm


def ml_search_algorithm(dataframe, feature_column, test_vector,
                       name_role=['Name', 'Role'], thresh=0.3):
    """
    Cosine similarity based search algorithm with improved debugging
    """
    try:
        # Convert test_vector to numpy array and ensure it's float32
        test_vector = np.array(test_vector, dtype=np.float32)
        print(f"Test vector shape: {test_vector.shape}")
        
        # Get embeddings from dataframe and ensure they're all 512-dimensional
        X_list = dataframe[feature_column].tolist()
        x = np.vstack([embedding[:512] if len(embedding) > 512 else embedding for embedding in X_list])
        print(f"Database embeddings shape after processing: {x.shape}")
        
        # Normalize vectors
        test_vector_norm = test_vector / np.linalg.norm(test_vector)
        x_norm = x / np.linalg.norm(x, axis=1)[:, np.newaxis]
        
        # Calculate cosine similarity
        similar = np.dot(x_norm, test_vector_norm)
        
        # Find best match
        max_similarity = np.max(similar)
        best_match_idx = np.argmax(similar)
        
        print(f"\nSimilarity scores for each person:")
        for idx, score in enumerate(similar):
            print(f"{dataframe.iloc[idx]['Name']}: {score:.3f}")
        
        print(f"\nBest match score: {max_similarity:.3f} (threshold: {thresh})")
        
        if max_similarity >= thresh:
            person_name = dataframe.iloc[best_match_idx]['Name']
            person_role = dataframe.iloc[best_match_idx]['Role']
            print(f"Match found: {person_name}")
        else:
            person_name = 'Unknown'
            person_role = 'Unknown'
            print("No match found above threshold")
            
    except Exception as e:
        print(f"Error in ml_search_algorithm: {e}")
        person_name = 'Unknown'
        person_role = 'Unknown'
        
    return person_name, person_role

##Real Time Predidction
# we need to save logs for every 1 mins

class RealTimePred:
    def __init__(self):
        self.logs = dict(name=[],role=[],current_time=[])
        
    def reset_dict(self):
        self.logs = dict(name=[],role=[],current_time=[])
    
    def saveLogs_redis(self):
        # step-1: create a logs dataframe
        dataframe = pd.DataFrame(self.logs)        
        # step-2: drop the duplicate information (distinct name)
        dataframe.drop_duplicates('name',inplace=True) 
        # step-3: push data to redis database (list)
        # encode the data
        name_list = dataframe['name'].tolist()
        role_list = dataframe['role'].tolist()
        ctime_list = dataframe['current_time'].tolist()
        encoded_data = []

        for name, role, ctime in zip(name_list, role_list, ctime_list):
            if name != 'Unknown':
                concat_string = f"{name}@{role}@{ctime}"
                encoded_data.append(concat_string)
                
        if len(encoded_data) >0:
            r.lpush('attendance:logs',*encoded_data)
        
                    
        self.reset_dict()     



    def face_prediction(self,test_image, dataframe, feature_column,
                    name_role=['Name', 'Role'], thresh=0.3):
        try:
            current_time = str(datetime.now())
            results = faceapp.get(test_image)
            test_copy = test_image.copy()
            
            print(f"\nProcessing image with {len(results)} faces detected")
            print(f"Database contains {len(dataframe)} registered faces")
            
            if len(results) == 0:
                return test_copy
            
            for res in results:
                try:
                    # Get bbox coordinates
                    x1, y1, x2, y2 = map(int, res['bbox'])
                    
                    # Get embeddings and identify person
                    embeddings = res['embedding']
                    print(f"\nProcessing face at ({x1}, {y1})")
                    
                    person_name, person_role = ml_search_algorithm(dataframe,
                                                                feature_column,
                                                                test_vector=embeddings,
                                                                name_role=name_role,
                                                                thresh=thresh)
                    
                    # Set color based on recognition result
                    color = (0, 255, 0) if person_name != 'Unknown' else (0, 0, 255)
                    
                    # Draw rectangle and text
                    cv2.rectangle(test_copy, (x1, y1), (x2, y2), color, 2)
                    
                    # Add text with background
                    text = f"{person_name}"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.7
                    thickness = 2
                    
                    # Get text size
                    (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
                    
                    # Draw background rectangle for text
                    cv2.rectangle(test_copy, 
                                (x1, y1 - text_height - 10), 
                                (x1 + text_width, y1), 
                                color, 
                                -1)
                    
                    # Add text
                    cv2.putText(test_copy, 
                            text,
                            (x1, y1 - 5), 
                            font,
                            font_scale,
                            (255, 255, 255),
                            thickness)
                    
                    cv2.putText(test_copy, current_time, (x1, y1 - 30), font, font_scale, (255, 255, 255), thickness)

                    # Save logs
                    self.logs['name'].append(person_name)
                    self.logs['role'].append(person_role)
                    self.logs['current_time'].append(current_time)

                    
                except Exception as e:
                    print(f"Error processing individual face: {e}")
                    continue
            
            return test_copy
            
        except Exception as e:
            print(f"Error in face_prediction: {e}")
            return test_image
        


### Face Registration Form

class RegistrationForm:
    def __init__(self):
        self.sample = 0
    def reset(self):
        self.sample = 0
        
    def get_embedding(self,frame):
        # get results from insightface model
        results = faceapp.get(frame,max_num=1)
        embeddings = None
        for res in results:
            self.sample += 1
            x1, y1, x2, y2 = res['bbox'].astype(int)
            cv2.rectangle(frame, (x1,y1),(x2,y2),(0,255,0),1)
            # put text samples info
            text = f"samples = {self.sample}"
            cv2.putText(frame,text,(x1,y1),cv2.FONT_HERSHEY_DUPLEX,0.6,(255,255,0),2)
            
            # facial features
            embeddings = res['embedding']
            
        return frame, embeddings
    
    def save_data_in_redis_db(self,name,role):
        #validation name
        if name is not None:
            if name.strip() != '':
                key = f'{name}@{role}'
            else:
                return 'name_false'
        else:
            return 'name_false'
        
        #if face_embedding.txt exists

        if 'face_embedding.txt' not in os.listdir():
            return 'file_false'
        
        #step-1 load "face_embedding.txt"
        x_array = np.loadtxt('face_embedding.txt',dtype=np.float32)

        #step-2: convert into array
        received_samples = int(x_array.size/512)
        x_array = x_array.reshape(received_samples,512)
        x_array = np.asarray(x_array)   


        #step-3: cal. mean of embeddings

        x_mean = x_array.mean(axis = 0)
        x_mean = x_mean.astype(np.float32)
        x_mean_bytes = x_mean.tobytes()

        #step-4: save data into redis db
        #redis database
        r.hset(name = 'academy:register',key =key, value = x_mean_bytes)
        # 
        os.remove('face_embedding.txt')
        self.reset()
        
        return True
