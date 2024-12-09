# WebcamGPT Autonomous Robot

## Prerequisites

### Hardware
- Raspberry Pi 4
- Raspberry Pi Camera or USB Webcam
- 4-wheel Robot Chassis with Motor Drivers
- Motor HAT or L298N Motor Driver

### Software Dependencies
- Python 3.7+
- OpenCV (`python3 -m pip install opencv-python`)
- OpenAI Python Library (`python3 -m pip install openai`)
- RPi.GPIO

## Installation Steps

1. **Install Dependencies**
```bash
sudo apt-get update
sudo apt-get install python3-pip python3-opencv
python3 -m pip install RPi.GPIO openai
```

2. **OpenAI API Setup**
- Sign up for an OpenAI account
- Generate an API key
- Set the API key in the script or as an environment variable

3. **GPIO and Camera Configuration**
- Ensure your GPIO pins match the script
- Connect motors to the specified GPIO pins
- Mount the camera on your robot

## Usage

### Running Autonomous Navigation
```bash
python3 autonomous_robot.py
```

## Safety Considerations
- Always supervise the robot during autonomous navigation
- Ensure clear, obstacle-free testing environment
- Have an emergency stop mechanism

## Troubleshooting
- Check GPIO pin connections
- Verify camera is working (`raspistill -o test.jpg`)
- Ensure stable power supply to Raspberry Pi and motors

## Customization
- Adjust GPIO pins in the script to match your specific hardware
- Modify `autonomous_navigate()` duration as needed
- Fine-tune GPT prompt for better navigation decisions

## Known Limitations
- Requires stable internet connection
- GPT vision API calls have associated costs
- Navigation accuracy depends on image processing and GPT interpretation
