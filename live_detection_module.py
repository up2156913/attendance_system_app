import cv2
import numpy as np
import time

class LivenessDetection:
    def __init__(self):
        self.blink_threshold = 0.3  # Threshold for eye aspect ratio to detect blinks
        self.movement_threshold = 5.0  # Threshold for movement detection
        self.face_movement_frames = 10  # Number of frames to check for facial movement
        self.previous_landmarks = None
        self.movement_count = 0
        self.blink_detected = False
        self.frame_count = 0
        self.previous_frame = None
        self.movement_scores = []
        self.last_reset_time = time.time()

    def reset(self):
        """Reset detection state"""
        self.previous_landmarks = None
        self.movement_count = 0
        self.blink_detected = False
        self.frame_count = 0
        self.previous_frame = None
        self.movement_scores = []
        self.last_reset_time = time.time()

    def detect_movement(self, current_face_roi):
        """Detect facial movement between frames using simple frame differencing"""
        if self.previous_frame is None or current_face_roi is None:
            if current_face_roi is not None:
                self.previous_frame = current_face_roi.copy()
            return False
        
        # Make sure frames are the same size
        if self.previous_frame.shape != current_face_roi.shape:
            try:
                self.previous_frame = cv2.resize(self.previous_frame, 
                                               (current_face_roi.shape[1], current_face_roi.shape[0]))
            except:
                self.previous_frame = current_face_roi.copy()
                return False
        
        # Calculate absolute difference between frames
        try:
            frame_diff = cv2.absdiff(self.previous_frame, current_face_roi)
            mean_diff = np.mean(frame_diff)
            
            # Update previous frame
            self.previous_frame = current_face_roi.copy()
            
            # Check if movement is significant
            if mean_diff > 10:  # Threshold for movement
                self.movement_count += 1
                self.movement_scores.append(mean_diff)
                return True
            
            return False
        except Exception as e:
            print(f"Error in movement detection: {e}")
            self.previous_frame = current_face_roi.copy()
            return False

    def detect_texture_variance(self, face_roi):
        """Detect texture variance in face region to differentiate real faces from prints"""
        if face_roi is None or face_roi.size == 0:
            return 0
            
        # Convert to grayscale
        if len(face_roi.shape) == 3:
            gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        else:
            gray_roi = face_roi
            
        # Apply Laplacian to detect edges/textures
        laplacian = cv2.Laplacian(gray_roi, cv2.CV_64F)
        
        # Calculate variance
        return laplacian.var()

    def detect_liveness(self, frame, face_bbox):
        """
        Main liveness detection function
        Returns: (is_live, confidence, status_message)
        """
        # Auto-reset if it's been a while
        if time.time() - self.last_reset_time > 60:  # Reset every minute
            self.reset()
            
        self.frame_count += 1
        status = "Checking liveness..."
        
        # Extract face region
        if face_bbox is not None:
            x1, y1, x2, y2 = map(int, face_bbox)
            # Make sure coordinates are valid
            height, width = frame.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(width, x2), min(height, y2)
            
            # Check if face region is valid
            if x1 >= x2 or y1 >= y2:
                return False, 0.0, "Invalid face region"
                
            face_roi = frame[y1:y2, x1:x2]
            
            # Ensure face_roi is not empty
            if face_roi.size == 0:
                return False, 0.0, "Empty face region"
            
            # Check for texture variance (real faces have more variance than printed photos)
            texture_score = self.detect_texture_variance(face_roi)
            
            # Track facial movement
            movement_detected = self.detect_movement(face_roi)
            
            # Decision making
            is_live = False
            confidence = 0.0
            
            # Texture-based confidence (higher variance suggests real face)
            texture_confidence = min(texture_score / 500.0, 1.0)  # Normalize
            
            # Movement-based confidence
            movement_confidence = min(self.movement_count / 3.0, 1.0)  # Normalize
            
            # Combined confidence score with more weight on texture
            confidence = 0.7 * texture_confidence + 0.3 * movement_confidence
            
            # Decision threshold
            if confidence > 0.5:
                is_live = True
                status = f"Live Person  ({confidence:.2f})"
            else:
                status = f"Checking... ({confidence:.2f})"
                if self.frame_count > 30:  # After 30 frames, make final decision
                    status = f"Liveness Failed  ({confidence:.2f})"
            
            # If we've been checking for a while and still no good signal, adjust messaging
            if self.frame_count > 150:  # Reset after 150 frames (about 5 seconds at 30fps)
                self.reset()  # Reset and start over
                
            return is_live, confidence, status
        
        return False, 0.0, "No face detected"
