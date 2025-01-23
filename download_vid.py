from typing import Optional
import cv2
from os import makedirs, path, listdir


def download_video(vid_path: str, folder: str, extension: str, params: Optional[tuple[int, int]] = None, log: bool = False) -> None:
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


def imgs_to_buffer():
    def render_frames(self, folder: str, size_x: int, size_y: Optional[int] = None, ask: bool = False):
        with open(f"{folder}frame0.bmp", "rb") as file:
            file.seek(18)
            width: int = int.from_bytes(file.read(4), "little")
            height: int = int.from_bytes(file.read(4), "little")
            if not size_y:
                size_y = height // (width // size_x)
            num_frames = len([name for name in listdir(folder) if path.isfile(name)])
            #open(buff.txt)

        for i in range(0, 6572, 2):
            secxw: int = width // size_x
            secyh: int = height // size_y

            with open(f"{folder}frame{i}.bmp", "rb") as file:
                file.seek(54)
                file_tbl = [[0 for _ in range(size_x)] for _ in range(size_y)]
                for i in range(width * height):
                    file_tbl[(i // width) // secyh][(i % width) // secxw] += int.from_bytes(file.read(1), "little") - 127
                    file.read(2)
            
            file_tbl = file_tbl[::-1]

