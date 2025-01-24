from typing import Optional
import cv2
from os import makedirs, path, listdir
from bitstring import BitStream
from math import floor
from io import BufferedWriter, TextIOWrapper


def download_video(vid_path: str, folder: str, extension: str, params: Optional[tuple[int, int]] = None, *, log: bool = False) -> None:
    video = cv2.VideoCapture(vid_path)

    if not path.exists(folder):
        makedirs(folder)

    counter: int = 0
    while (True):
        ret, frame = video.read()
        if not ret:
            break
        
        name: str = f"{folder}frame{counter}{extension}"
        if params:
            cv2.imwrite(name, frame, params)
        else:
            cv2.imwrite(name, frame)
        if log:
            print(f"Created {folder}frame{counter}{extension}")
        counter += 1
    if log:
        print("Finished!")


def encode_video(vid_path: str, colour_depth: int = 8, monochrome: bool = False, size_x: Optional[int] = None, size_y: Optional[int] = None, *, log: bool = False):
    video = cv2.VideoCapture(vid_path)
    
    with open("vidbuff.evf", "wb+", 0) as file:
        ret, frame = video.read()
        file.write((ord('E')).to_bytes(length=1, byteorder="big"))
        file.write((ord('V')).to_bytes(length=1, byteorder="big"))
        height: int = len(frame)
        width: int = len(frame[0])
        if not size_x and not size_y:
            size_y = height
            size_x = width
        elif not size_x and size_y:
            size_x = width // (height // size_y)
        elif size_x and not size_y:
            size_y = height // (width // size_x)
        
        file.write(size_x.to_bytes(length=4, byteorder="big"))
        file.write(size_y.to_bytes(length=4, byteorder="big"))
        file.write((0).to_bytes(length=3, byteorder="big"))
        file.flush()
        
        with BufferedWriter(file, (size_x * size_y * colour_depth * (3 - 2 * monochrome) + 7) // 8) as buff:
            counter: int = 0
            while True:
                if counter:
                    ret, frame = video.read()
                if not ret:
                    break
                    

                buffer: int = 0
                bufflen: int = 0
                #pxtable = [[0 for _ in size_x] for _ in size_y]
                for i in range(height * width):
                    buffer <<= colour_depth
                    buffer |= floor(frame[i // width][i % width][0] ** (colour_depth / 8))
                    bufflen += colour_depth
                    if not monochrome:
                        buffer <<= colour_depth
                        buffer |= floor(frame[i // width][i % width][1] ** (colour_depth / 8))
                        buffer <<= colour_depth
                        buffer |= floor(frame[i // width][i % width][2] ** (colour_depth / 8))
                        bufflen += 2 * colour_depth
                    if not bufflen % 8:
                        buff.write(buffer.to_bytes(length=(bufflen // 8), byteorder="big"))
                        buffer = 0
                        bufflen = 0
                
                if bufflen:
                    buffer <<= bufflen % 8
                    buff.write(size_x.to_bytes(length=((bufflen + 7) // 8), byteorder="big"))

                if log:
                    print(f"Encoded Frame {counter}")
                counter += 1
        
        buffer: int = counter
        buffer <<= 2
        buffer |= 3 - 2 * monochrome
        buffer <<= 4
        buffer |= colour_depth
        file.seek(10)
        file.write(buffer.to_bytes(length=3, byteorder="big"))

    if log:
        print("Finished!")


if __name__ == "__main__":
    encode_video("badapple.mp4", 1, True, log=True)