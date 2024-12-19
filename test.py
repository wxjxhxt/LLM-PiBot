import RPi.GPIO as GPIO
import cv2
import time
import openai
import base64
import io

# OpenAI API configuration
openai.api_key = 'openaikey'


# GPIO pin setup for Motor 1 (Left wheels)
in1 = 27
in2 = 17
en1 = 18

# GPIO pin setup for Motor 2 (Right wheels)
in3 = 10
in4 = 22
en2 = 19



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
        self.pwm1.ChangeDutyCycle(50)
        self.pwm2.ChangeDutyCycle(50)
        print("Moving Forward")

    def move_backward(self):
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
        self.pwm1.ChangeDutyCycle(50)
        self.pwm2.ChangeDutyCycle(50)
        print("Moving Backward")

    def turn_left(self):
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)
        self.pwm1.ChangeDutyCycle(50)
        self.pwm2.ChangeDutyCycle(50)
        print("Turning Left")

    def turn_right(self):
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
        self.pwm1.ChangeDutyCycle(50)
        self.pwm2.ChangeDutyCycle(50)
        print("Turning Right")

    def stop_motors(self):
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.LOW)
        self.pwm1.ChangeDutyCycle(0)
        self.pwm2.ChangeDutyCycle(0)
        print("Motors Stopped")

    def get_gpt_description(self, image_base64):
        """Get detailed description from GPT Vision API."""
        try:
            # First, get navigation command
            nav_response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and provide a single-word navigation command: forward, backward, left, or right. Consider obstacles, path clarity, and navigation goals. Respond with ONLY the direction word."
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
                max_tokens=10
            )
            
            # Then, get detailed description
            desc_response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Provide a detailed, concise description of what you see in this image. Focus on key objects, environment, potential obstacles, and navigation challenges."
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
                max_tokens=100
            )
            
            # Extract command and description
            command = nav_response.choices[0].message.content.lower().strip()
            description = desc_response.choices[0].message.content.strip()
            
            # Validate command
            valid_commands = ['forward', 'backward', 'left', 'right']
            if command not in valid_commands:
                print(f"Invalid command received: {command}. Defaulting to stop.")
                command = "stop"
            
            return command, description
        
        except Exception as e:
            print(f"Error getting GPT analysis: {e}")
            return "stop", "Unable to analyze the image"

    def autonomous_navigate(self, duration=60):
        """Autonomously navigate using GPT vision for 'duration' seconds."""
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                # Capture image
                frame, image_base64 = self.capture_image()
                
                # Get navigation command and description from GPT
                command, description = self.get_gpt_description(image_base64)
                
                # Overlay GPT description on the frame
                frame_with_text = frame.copy()
                cv2.putText(frame_with_text, f"Command: {command}", 
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                            1, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(frame_with_text, f"Description: {description}", 
                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.7, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Display the frame
                cv2.imshow("Robot Vision", frame_with_text)
                
                # Execute corresponding movement
                if command == "forward":
                    self.move_forward()
                elif command == "backward":
                    self.move_backward()
                elif command == "left":
                    self.turn_left()
                elif command == "right":
                    self.turn_right()
                else:
                    self.stop_motors()
                
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

