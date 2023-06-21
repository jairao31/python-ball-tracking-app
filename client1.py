import asyncio
import cv2
import multiprocessing
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling


async def handle_offer(pc, offer, signaling):
    await pc.setRemoteDescription(offer)
    await pc.setLocalDescription(await pc.createAnswer())
    signaling.send(pc.localDescription)


async def handle_answer(pc, answer):
    await pc.setRemoteDescription(answer)


async def start_client():
    signaling = TcpSocketSignaling("localhost", 3000)
    pc = RTCPeerConnection()

    async def send_offer():
        # Add a video track to the RTCPeerConnection
        video_track = pc.addTrack(VideoStreamTrack())
        await pc.setLocalDescription(await pc.createOffer())
        signaling.send(pc.localDescription)

    signaling.on_offer = lambda offer: asyncio.ensure_future(
        handle_offer(pc, offer, signaling))
    signaling.on_answer = lambda answer: asyncio.ensure_future(
        handle_answer(pc, answer))

    await signaling.connect()
    await send_offer()

    video_track = cv2.VideoCapture(0)

    async def send_frame():
        while True:
            ret, frame = video_track.read()
            if ret:
                await pc.video_track.on_frame(frame)

    asyncio.ensure_future(send_frame())

    # Start a new process to handle frame processing and sending coordinates
    queue = multiprocessing.Queue()
    process_a = multiprocessing.Process(
        target=process_frames, args=(queue, signaling,))
    process_a.start()

    while True:
        await asyncio.sleep(1)


def process_frames(queue, signaling):
    while True:
        frame = queue.get()
        # Process the frame and extract coordinates
        coordinates = extract_coordinates(frame)
        # Send the coordinates via signaling
        signaling.send_coordinates(coordinates)


def extract_coordinates(frame):
    # Add your logic to extract coordinates from the frame
    # Replace the following line with your actual code
    coordinates = [10, 20, 30, 40]
    return coordinates


if __name__ == "__main__":
    asyncio.run(start_client())
