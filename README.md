# Python-Ball-Tracking-App

A Python-based client-server application that enables real-time transmission and tracking of a bouncing ball across a screen. The server program generates continuous 2D images/frames of a ball's motion and transmits them to the client using aiortc's frame transport. The client program receives the images and displays them using OpenCV. Additionally, the client spawns a separate process (process_a) to analyze the images and determine the current location of the ball in terms of x and y coordinates. These coordinates are then sent to the server via an aiortc data channel.

## To run the application, execute the following commands in separate command line terminals:

#### 1. Start the server:

```
python3 server.py
```

#### 2. Start the client:

```
python3 client.py
```

### Description

The server creates an aiortc offer and sends it to the client. The client receives the offer and generates an aiortc answer. The communication between the server and the client is established using aiortc's built-in TcpSocketSignaling.

Once the transmission begins, the server continuously generates frames of a bouncing ball across the screen. These frames are transmitted to the client using aiortc's frame transport mechanism. The client, using OpenCV, displays the received frames in real-time.

Simultaneously, the client spawns a new process (process_a) to process the received frames. The frames are passed to process_a via a multiprocessing queue. Inside process_a, image processing algorithms are applied to extract the x and y coordinates of the ball's current location. The computed coordinates are stored as multiprocessing values.

The client's main thread establishes an aiortc data channel with the server and sends the computed x and y coordinates to the server. The server program receives the coordinates, displays them, and computes the error between the received coordinates and the actual location of the ball.

This project showcases the integration of aiortc, OpenCV, and multiprocessing to achieve real-time ball tracking with image processing and communication between the client and server.
