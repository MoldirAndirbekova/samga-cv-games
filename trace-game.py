import cv2
import mediapipe as mp
import numpy as np
import time

class LetterTracingGame:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Initialize the camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("Could not open video device")
            
        # Get camera frame dimensions
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Calculate pixel density (assuming standard webcam with 96 DPI)
        self.pixels_per_cm = 96 / 2.54  # pixels per centimeter
        self.target_thickness_cm = 2  # target thickness in centimeters
        self.letter_thickness = int(self.target_thickness_cm * self.pixels_per_cm)
        
        # Current letter to trace
        self.current_letter = 'A'
        self.letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.current_letter_index = 0
        
        # Words for each letter
        self.letter_words = {
            'A': 'Apple',
            'B': 'Ball',
            'C': 'Cat',
            'D': 'Dog',
            'E': 'Elephant',
            'F': 'Fish',
            'G': 'Giraffe',
            'H': 'House',
            'I': 'Ice',
            'J': 'Jump',
            'K': 'Kite',
            'L': 'Lion',
            'M': 'Monkey',
            'N': 'Nest',
            'O': 'Orange',
            'P': 'Panda',
            'Q': 'Queen',
            'R': 'Rainbow',
            'S': 'Sun',
            'T': 'Tree',
            'U': 'Umbrella',
            'V': 'Violin',
            'W': 'Water',
            'X': 'Xylophone',
            'Y': 'Yellow',
            'Z': 'Zebra'
        }
        
        # Drawing canvas
        self.canvas = None
        self.prev_x, self.prev_y = 0, 0
        
        # Letter template and masks
        self.letter_template = None
        self.letter_mask = None
        self.create_letter_template()
        
        # Drawing state
        self.is_drawing = False
        self.drawing_points = []
        self.fill_progress = 0
        self.show_congrats = False
        self.congrats_time = 0
        
    def next_letter(self):
        # Move to the next letter
        self.current_letter_index = (self.current_letter_index + 1) % len(self.letters)
        self.current_letter = self.letters[self.current_letter_index]
        
        # Reset drawing state
        self.drawing_points = []
        self.fill_progress = 0
        self.show_congrats = False
        self.congrats_time = 0
        
        # Create new template for the next letter
        self.create_letter_template()
        
    def create_letter_template(self):
    # Create a blank canvas with the same size as the camera frame
        self.letter_template = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        self.letter_template.fill(255)  # White background

        # Create mask for the letter
        self.letter_mask = np.zeros((self.frame_height, self.frame_width), dtype=np.uint8)

        # Calculate center position
        center_x = self.frame_width // 2
        center_y = self.frame_height // 2

        # Draw the letter with larger size and bolder stroke
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = min(self.frame_width, self.frame_height) / 25

        # Get text size to center it properly
        (text_width, text_height), _ = cv2.getTextSize(self.current_letter, font, font_scale, self.letter_thickness)
        text_x = center_x - text_width // 2
        text_y = center_y + text_height // 2

        # Draw white bold outline (thicker)
        border_thickness = self.letter_thickness + 6
        cv2.putText(self.letter_template, self.current_letter,
                    (text_x, text_y), font, font_scale, (255, 255, 255), border_thickness, cv2.LINE_AA)

        # Draw black inside letter
        cv2.putText(self.letter_template, self.current_letter,
                    (text_x, text_y), font, font_scale, (0, 0, 0), self.letter_thickness, cv2.LINE_AA)

        # Create mask for the letter with black fill
        cv2.putText(self.letter_mask, self.current_letter,
                    (text_x, text_y), font, font_scale, 255, self.letter_thickness, cv2.LINE_AA)

        
    def update_fill_progress(self):
        if len(self.drawing_points) < 2:
            return
            
        # Create a temporary mask for the drawn path
        path_mask = np.zeros((self.frame_height, self.frame_width), dtype=np.uint8)
        
        # Draw the path with the same thickness as the letter
        points = np.array(self.drawing_points, dtype=np.int32)
        cv2.polylines(path_mask, [points], False, 255, self.letter_thickness)
        
        # Find intersection between path and letter
        intersection = cv2.bitwise_and(path_mask, self.letter_mask)
        
        # Calculate fill progress
        total_letter_pixels = np.count_nonzero(self.letter_mask)
        filled_pixels = np.count_nonzero(intersection)
        self.fill_progress = filled_pixels / total_letter_pixels if total_letter_pixels > 0 else 0
        
        # Check if we should show congratulations
        if self.fill_progress >= 0.9 and not self.show_congrats:
            self.show_congrats = True
            self.congrats_time = time.time()
        
    def is_within_bounds(self, x, y):
        return 0 <= x < self.frame_width and 0 <= y < self.frame_height
        
    def run(self):
        # Create a canvas for the traced path
        traced_path = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            # Flip the frame horizontally for a later selfie-view display
            frame = cv2.flip(frame, 1)
            
            # Convert the BGR image to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame and get hand landmarks
            results = self.hands.process(rgb_frame)
            
            # Create a copy of the frame for drawing
            display_frame = frame.copy()
            
            # Draw the letter template with proper alpha blending
            # Create a mask for the letter area
            letter_area = np.zeros_like(display_frame)
            letter_area[self.letter_mask > 0] = self.letter_template[self.letter_mask > 0]
            
            # Blend only the letter area with the frame
            alpha = 0.4  # Reduced from 0.3 to 0.2 for clearer background
            cv2.addWeighted(letter_area, alpha, display_frame, 1 - alpha, 0, display_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Get the index finger tip coordinates
                    index_finger = hand_landmarks.landmark[8]
                    x, y = int(index_finger.x * self.frame_width), int(index_finger.y * self.frame_height)
                    
                    # Ensure coordinates are within bounds
                    x = max(0, min(x, self.frame_width - 1))
                    y = max(0, min(y, self.frame_height - 1))
                    
                    # Draw a circle at the finger tip
                    cv2.circle(display_frame, (x, y), 10, (0, 255, 0), -1)
                    
                    # Check if we should start/continue drawing
                    if self.prev_x != 0 and self.prev_y != 0:
                        # Only draw if within the letter and within bounds
                        if self.is_within_bounds(x, y) and self.letter_mask[y, x] > 0:
                            # Draw the tracing line on the traced path canvas with the same thickness as the letter
                            cv2.line(traced_path, (self.prev_x, self.prev_y), (x, y), (0, 0, 255), self.letter_thickness)
                            self.drawing_points.append((x, y))
                            self.update_fill_progress()
                    
                    self.prev_x, self.prev_y = x, y
            
            # Create a mask of the traced path
            traced_mask = cv2.cvtColor(traced_path, cv2.COLOR_BGR2GRAY)
            
            # Create red overlay for the entire traced path
            red_overlay = np.zeros_like(display_frame)
            red_overlay[:] = (0, 0, 255)  # Red color
            red_overlay = cv2.bitwise_and(red_overlay, red_overlay, mask=traced_mask)
            
            # Combine the red overlay with the display frame
            display_frame = cv2.add(display_frame, red_overlay)
            
            # Add instructions and progress
            cv2.putText(display_frame, "Trace the letter with your finger", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display_frame, f"Progress: {int(self.fill_progress * 100)}%", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display_frame, "Press 'q' to quit", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Show congratulations message when progress reaches 90%
            if self.show_congrats:
                congrats_text = f"Good job! {self.letter_words[self.current_letter]} starts with {self.current_letter}!"
                text_size = cv2.getTextSize(congrats_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                text_x = (self.frame_width - text_size[0]) // 2
                text_y = self.frame_height - 50
                
                # Draw text with black outline
                cv2.putText(display_frame, congrats_text, (text_x, text_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
                cv2.putText(display_frame, congrats_text, (text_x, text_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Move to next letter after 3 seconds
                if time.time() - self.congrats_time > 3:
                    self.next_letter()
                    traced_path = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
            
            # Display the frame
            cv2.imshow('Letter Tracing Game', display_frame)
            
            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Release resources
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    game = LetterTracingGame()
    game.run() 