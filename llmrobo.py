import RPi.GPIO as GPIO
import cv2
import numpy as np
import time
import openai
import base64
import io
import json

# OpenAI API configuration
openai.api_key = 'your_openai_api_key_here'

# GPIO pin setup for Motor 1 (Left wheels)
in1 = 24
in2 = 23
en1 = 25

# GPIO pin setup for Motor 2 (Right wheels)
in3 = 17
in4 = 27
en2 = 22

class RobotController:
    def __init__(self):
        # Set GPIO mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(in1, GPIO.OUT)
        GPIO.setup(in2, GPIO.OUT)
        GPIO.setup(en1, GPIO.OUT)
        GPIO.setup(in3, GPIO.OUT)
        GPIO.setup(in4, GPIO.OUT)
        GPIO.setup(en2, GPIO.OUT)

        # Setup PWM for motor speed control
        self.pwm1 = GPIO.PWM(en1, 1000)  # 1000 Hz frequency for Motor 1
        self.pwm2 = GPIO.PWM(en2, 1000)  # 1000 Hz frequency for Motor 2
        self.pwm1.start(0)  # Start with motor off (0% duty cycle)
        self.pwm2.start(0)  # Start with motor off (0% duty cycle)

        # Camera setup
        self.camera = cv2.VideoCapture(0)
        
        # Decision tracking
        self.decision_history = []
        
    def capture_image(self):
        """Capture an image from the webcam."""
        ret, frame = self.camera.read()
        if not ret:
            raise Exception("Failed to capture image")
        
        # Convert image to base64 for GPT vision
        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return frame, image_base64

    def move_forward(self):
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)
        self.pwm1.ChangeDutyCycle(75)
        self.pwm2.ChangeDutyCycle(75)
        print("Moving Forward")
        return "Forward"

    def move_backward(self):
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
        self.pwm1.ChangeDutyCycle(75)
        self.pwm2.ChangeDutyCycle(75)
        print("Moving Backward")
        return "Backward"

    def turn_left(self):
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)
        self.pwm1.ChangeDutyCycle(75)
        self.pwm2.ChangeDutyCycle(75)
        print("Turning Left")
        return "Left"

    def turn_right(self):
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
        self.pwm1.ChangeDutyCycle(75)
        self.pwm2.ChangeDutyCycle(75)
        print("Turning Right")
        return "Right"

    def stop_motors(self):
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.LOW)
        self.pwm1.ChangeDutyCycle(0)
        self.pwm2.ChangeDutyCycle(0)
        print("Motors Stopped")
        return "Stop"

    def get_gpt_description(self, image_base64):
        """Get detailed description from GPT Vision API."""
        try:
            # Detailed scene understanding
            scene_response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this image comprehensively. Provide a JSON response with the following keys:
                                - navigation_command: A single word (forward/backward/left/right/stop)
                                - obstacles: List of potential obstacles
                                - path_description: Brief description of the navigation environment
                                - confidence_level: Your confidence in the navigation command (0-100)
                                - reasoning: Brief explanation of why you chose this command"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            scene_data = json.loads(scene_response.choices[0].message.content)
            
            # Validate and clean up the command
            valid_commands = ['forward', 'backward', 'left', 'right', 'stop']
            command = scene_data.get('navigation_command', 'stop').lower()
            if command not in valid_commands:
                print(f"Invalid command received: {command}. Defaulting to stop.")
                command = "stop"
            
            # Return comprehensive scene data
            return command, scene_data
        
        except Exception as e:
            print(f"Error getting GPT analysis: {e}")
            return "stop", {
                "navigation_command": "stop",
                "obstacles": ["Error analyzing scene"],
                "path_description": "Unable to process image",
                "confidence_level": 0,
                "reasoning": str(e)
            }

    def create_decision_visualization(self, frame, scene_data, command):
        """Create a comprehensive visualization of the robot's decision-making."""
        # Create a copy of the frame to annotate
        viz_frame = frame.copy()
        
        # Create a sidebar for decision details
        sidebar_width = 400
        sidebar = np.zeros((frame.shape[0], sidebar_width, 3), dtype=np.uint8)
        sidebar.fill(50)  # Dark background
        
        # Overlay sidebar on the main frame
        full_frame = np.hstack((viz_frame, sidebar))
        
        # Draw navigation command
        cv2.putText(full_frame, f"Command: {command.upper()}", 
                    (viz_frame.shape[1] + 10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw confidence level
        confidence = scene_data.get('confidence_level', 0)
        confidence_color = (0, 255, 0) if confidence > 70 else (0, 165, 255) if confidence > 40 else (0, 0, 255)
        cv2.putText(full_frame, f"Confidence: {confidence}%", 
                    (viz_frame.shape[1] + 10, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, confidence_color, 2)
        
        # Draw obstacles
        obstacles = scene_data.get('obstacles', [])
        cv2.putText(full_frame, "Obstacles:", 
                    (viz_frame.shape[1] + 10, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        for i, obstacle in enumerate(obstacles[:5]):
            cv2.putText(full_frame, f"- {obstacle}", 
                        (viz_frame.shape[1] + 30, 190 + i*40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Draw path description
        cv2.putText(full_frame, "Path Description:", 
                    (viz_frame.shape[1] + 10, 350), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        path_desc = scene_data.get('path_description', 'No description')
        self.draw_wrapped_text(full_frame, path_desc, 
                               (viz_frame.shape[1] + 30, 390), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, 
                               max_width=380)
        
        # Draw reasoning
        cv2.putText(full_frame, "Reasoning:", 
                    (viz_frame.shape[1] + 10, 500), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        reasoning = scene_data.get('reasoning', 'No specific reasoning')
        self.draw_wrapped_text(full_frame, reasoning, 
                               (viz_frame.shape[1] + 30, 540), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, 
                               max_width=380)
        
        return full_frame

    def draw_wrapped_text(self, image, text, pos, font, font_scale, color, thickness, max_width=300):
        """Draw text that wraps to multiple lines."""
        words = text.split()
        lines = []
        current_line = words[0]
        
        for word in words[1:]:
            test_line = current_line + " " + word
            (test_width, _) = cv2.getTextSize(test_line, font, font_scale, thickness)[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)
        
        for i, line in enumerate(lines):
            cv2.putText(image, line, 
                        (pos[0], pos[1] + i*30), 
                        font, font_scale, color, thickness)

    def autonomous_navigate(self, duration=60):
        """Autonomously navigate using GPT vision for 'duration' seconds."""
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                # Capture image
                frame, image_base64 = self.capture_image()
                
                # Get navigation command and scene details from GPT
                command, scene_data = self.get_gpt_description(image_base64)
                
                # Create decision visualization
                full_frame = self.create_decision_visualization(frame, scene_data, command)
                
                # Display the frame
                cv2.imshow("Robot Vision & Decision Making", full_frame)
                
                # Execute corresponding movement
                movement = {
                    "forward": self.move_forward,
                    "backward": self.move_backward,
                    "left": self.turn_left,
                    "right": self.turn_right
                }.get(command, self.stop_motors)()
                
                # Store decision in history
                self.decision_history.append({
                    "timestamp": time.time(),
                    "command": movement,
                    "scene_data": scene_data
                })
                
                # Wait for key press or 1 second
                key = cv2.waitKey(1000)
                
                # Break loop if 'q' is pressed
                if key & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            print("Autonomous navigation stopped by user.")
        
        except Exception as e:
            print(f"An error occurred during navigation: {e}")
        
        finally:
            self.stop_motors()
            self.camera.release()
            cv2.destroyAllWindows()
            GPIO.cleanup()
            
            # Print decision history
            print("\n--- Decision History ---")
            for decision in self.decision_history:
                print(f"Time: {decision['timestamp']}, Command: {decision['command']}")

def main():
    robot = RobotController()
    
    try:
        # Start autonomous navigation for 60 seconds
        robot.autonomous_navigate(duration=60)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
