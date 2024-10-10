# Smart Light System

**Authors**:  
Evin Bour-Gilson (ebourgil@iu.edu)  
Noran Abdel-Aziz (nabdelaz@iu.edu)

**Date**: April 25, 2024

## Project Overview

This project involves developing a **Smart Light System** using a Raspberry Pi. The system integrates multiple sensors and actuators to intelligently control lighting. It can be controlled via an infrared remote or over a network through a CoAP server running on the Raspberry Pi.

## Key Components

The project utilizes the following hardware components:
- **IR Receiver**: For receiving infrared signals from a remote control.
- **RGB LED**: Provides visual feedback to indicate different system states.
- **PIR Motion Sensor (HC-SR501)**: Detects motion to enable automatic light control.
- **WS2812B Light Strip**: Provides dynamic lighting effects (gradients, blinking, brightness changes).
- **28BYJ-48 Stepper Motor**: Physically toggles the room's light switch.

## Libraries Used
- **aiocoap**: For creating CoAP resources and handling CoAP requests.
- **asyncio**: Used for asynchronous programming, handling multiple tasks simultaneously.
- **RPi.GPIO**: Accesses GPIO pins on the Raspberry Pi to control the hardware.
- **gpiozero**: Simplifies the use of the PIR motion sensor.
- **datetime**: For handling time-related operations.
- **board** and **neopixel**: For controlling the WS2812B light strip (color and brightness).
- **colorsys**: Converts color formats (HSV to RGB) for smooth lighting transitions.

## GPIO Pin Configuration
- **IR Receiver**: 3v3 Power (1), GPIO 17 (11), Ground (9)
- **RGB LED**: GPIO 10 (19), GPIO 9 (21), GPIO 11 (23), Ground (9)
- **PIR Motion Sensor**: GPIO 4 (7), 5v Power (2), Ground (9)
- **WS2812B Light Strip**: GPIO 21 (40), Ground (14)
- **28BYJ-48 Stepper Motor**: GPIO 26 (37), GPIO 19 (35), GPIO 13 (33), GPIO 6 (31), Ground (9)

## System Architecture

The program is divided into the following segments:

1. **GPIO & Sensor Setup**  
   Initializes GPIO pins and sets up the hardware components (IR receiver, PIR sensor, RGB LED, etc.).
   
2. **Remote Control Handling**  
   Handles input from an infrared remote control, allowing users to toggle lights, adjust brightness, and change colors. This involves reading IR signals, converting them to binary, and executing corresponding actions.
   
3. **CoAP Server Setup**  
   The CoAP server allows remote control of the system via network requests. It supports PUT requests for controlling the lights and exposes several resources for communication.
   
4. **Motion Detection & Stepper Motor Control**  
   The PIR sensor monitors room movement to automatically toggle the lights. The stepper motor physically controls the light switch to synchronize with the LED strip.
   
5. **Lighting Effects**  
   Implements various lighting effects, such as color transitions, brightness adjustments, and animation effects, based on remote inputs or network requests.

## WiFi Protocol and Wireshark Analysis

We used the CoAP protocol to handle data transmission over WiFi. The system sends and receives CoAP requests to control the smart light system remotely.

### Wireshark Analysis of CoAP Packets:
- **GET Request**: The client requests the status of the "power" resource (whether lights are on or off).
- **PUT Request**: The client sends a PUT request to toggle the "remote" resource, turning the lights on.

Acknowledgment packets are sent in response to ensure successful data transmission.

## Conclusion

This project demonstrates the integration of various IoT sensors and actuators to create a smart lighting system. By using asynchronous programming and the CoAP protocol, we enabled networked control of the system, making it efficient and scalable for future IoT applications.
