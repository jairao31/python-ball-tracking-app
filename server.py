import asyncio
import cv2
import numpy as np
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
        self.queue = asyncio.Queue()

    async def send_coordinates(self, x, y):
        await self.send(json.dumps({"x": x, "y": y}))

    async def receive_coordinates(self):
        data = await self.receive()
        if data:
            coordinates = json.loads(data)
            return coordinates.get("x"), coordinates.get("y")
        return None


class BallBouncingTrack:
    def __init__(self):
        self.frame_counter = 0

    async def recv(self):
        await asyncio.sleep(0.01)  # Introduce a delay to control frame rate
        image = generate_bouncing_ball_image()
        return self.frame_from_image(image)

    def frame_from_image(self, image):
        frame = cv2.resize(image, (FRAME_WIDTH, FRAME_HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return cv2.imencode(".png", frame)[1].tobytes()


def generate_bouncing_ball_image():
    image = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
    radius = 50
    speed_x = 5
    speed_y = 3
    position_x = 100
    position_y = 100

    image_height, image_width, _ = image.shape
    while True:
        image = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        position_x += speed_x
        position_y += speed_y

        if position_x + radius >= image_width or position_x - radius <= 0:
            speed_x *= -1
        if position_y + radius >= image_height or position_y - radius <= 0:
            speed_y *= -1

        cv2.circle(image, (position_x, position_y),
                   radius, (255, 255, 255), -1)
        yield image


async def server_main():
    signaling = AiortcSignaling("localhost", 3001)
    await signaling.connect()

    pc = RTCPeerConnection()

    # Create a data channel
    data_channel = pc.createDataChannel("coordinates")

    # Handler for receiving coordinates from the client
    @data_channel.on("message")
    def receive_coordinates(message):
        print(f"Server: Received coordinates: {message}")
        coordinates = json.loads(message)
        x, y = coordinates.get("x"), coordinates.get("y")
        # Compute error and perform desired operations with coordinates

    await pc.setLocalDescription(await pc.createOffer())
    print("Server: Sending offer to client...")
    await signaling.send(pc.localDescription)

    while True:
        data = await signaling.receive()
        print(f"Received data: {data}")  # Debugging statement
        if data is None:
            break
        if isinstance(data, RTCSessionDescription):
            await pc.setRemoteDescription(data)
            await pc.createAnswer()
            await pc.setLocalDescription(pc.localDescription)
            print("Server: Sending answer to client...")
            await signaling.send(pc.localDescription)
        elif isinstance(data, BYE):
            print("Server: Received bye from client.")
            break

    await signaling.close()
    pc.close()

    print("Server: Connection closed.")


if __name__ == "__main__":
    asyncio.run(server_main())
