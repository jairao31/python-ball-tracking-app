import asyncio
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import TcpSocketSignaling
from aiortc import VideoStreamTrack


async def generate_frames():
    width, height = 640, 480
    center_x, center_y = width // 2, height // 2
    radius = 50
    velocity_x, velocity_y = 5, 3

    while True:
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.circle(frame, (center_x, center_y), radius, (0, 0, 255), -1)

        center_x += velocity_x
        center_y += velocity_y

        if center_x <= radius or center_x >= width - radius:
            velocity_x = -velocity_x
        if center_y <= radius or center_y >= height - radius:
            velocity_y = -velocity_y

        yield frame
        await asyncio.sleep(0.02)


async def handle_offer(pc, offer, signaling):
    await pc.setRemoteDescription(offer)

    # Create an answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Send the answer to the client
    signaling.send(pc.localDescription)


async def start_server():
    signaling = TcpSocketSignaling("localhost", 3001)
    pc = RTCPeerConnection()

    connected_clients = []  # List to store connected clients

    signaling.on_offer = lambda offer: asyncio.ensure_future(
        handle_offer(pc, offer, signaling))

    await signaling.connect()

    # Create a video track and add it to the peer connection
    class BouncingBallTrack(VideoStreamTrack):
        def __init__(self):
            super().__init__()
            self.frame_generator = generate_frames()

        async def recv(self):
            frame = await self.frame_generator.__anext__()
            return frame

    video_track = BouncingBallTrack()
    pc.addTrack(video_track)

    # Send frames to the connected clients
    while True:
        frame = await video_track.recv()
        for client in connected_clients:
            client.video_track.on_data(frame, timestamp=0)
        await asyncio.sleep(0.02)


if __name__ == "__main__":
    asyncio.run(start_server())
