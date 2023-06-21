import asyncio
import cv2
import numpy as np
import multiprocessing
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import BYE, TcpSocketSignaling
import json

# Constants for video frame dimensions
FRAME_WIDTH = 640
FRAME_HEIGHT = 480


class AiortcSignaling(TcpSocketSignaling):
    async def connect(self):
        await super().connect()

        self.pc = None
        self.queue = multiprocessing.Queue()

    async def send_coordinates(self, x, y):
        await self.send(f"{x},{y}")

    async def receive_coordinates(self):
        data = await self.receive()
        if data and "," in data:
            x, y = data.split(",")
            return int(x), int(y)
        return None


def display_image(image):
    frame = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
    cv2.imshow("Received Image", frame)
    cv2.waitKey(1)


def process_coordinates(queue):
    while True:
        coordinates = queue.get()
        if coordinates is None:
            break
        x, y = coordinates
        # Process the received coordinates as needed
        print(f"Client: Received coordinates: ({x}, {y})")


async def client_main():
    signaling = AiortcSignaling("localhost", 3000)
    await signaling.connect()

    pc = RTCPeerConnection()

    # Create a data channel
    data_channel = pc.createDataChannel("coordinates")

    # Handler for receiving coordinates from the server
    @data_channel.on("message")
    def receive_coordinates(message):
        print(f"Client: Received coordinates: {message}")
        x, y = message.split(",")
        signaling.queue.put((int(x), int(y)))

    # Start the process to handle received coordinates
    process_a = multiprocessing.Process(
        target=process_coordinates, args=(signaling.queue,))
    process_a.start()

    await pc.setLocalDescription(await pc.createOffer())
    print("Client: Sending offer to server...")
    await signaling.send(pc.localDescription)

    while True:
        try:
            data = await signaling.receive()
            if data is None:
                break
            if isinstance(data, RTCSessionDescription):
                await pc.setRemoteDescription(data)
                await pc.createAnswer()
                await pc.setLocalDescription(pc.localDescription)
                print("Client: Sending answer to server...")
                await signaling.send(pc.localDescription)
            elif isinstance(data, bytes):
                display_image(data)
                # Process the received frame to determine the coordinates
                # and send them to the server
                frame = cv2.imdecode(np.frombuffer(
                    data, np.uint8), cv2.IMREAD_COLOR)
                # Process the frame and get the ball coordinates
                x, y = process_frame(frame)
                # Send the coordinates to the server
                await signaling.send_coordinates(x, y)
            elif data == BYE:
                print("Client: Server disconnected.")
                break
        except json.JSONDecodeError:
            print("Client: Invalid data received.")

    # Cleanup
    await pc.close()
    signaling.queue.put(None)  # Signal the process to exit
    process_a.join()


def process_frame(frame):
    # Implement your logic to process the frame and determine
    # the coordinates of the ball
    # For demonstration purposes, let's assume the ball coordinates
    # are the center of the frame
    height, width, _ = frame.shape
    x = width // 2
    y = height // 2
    return x, y


if __name__ == "__main__":
    asyncio.run(client_main())
