from os import system, path, listdir
from typing import Optional
from sys import stdout
import download_vid
from cursor import hide, show
from fpstimer import FPSTimer


class BMPvid_renderer:
    def render_frames(self, folder: str, size_x: int, size_y: Optional[int] = None, *, ask: bool = False):
        with open(f"{folder}frame0.bmp", "rb") as file:
            file.seek(18)
            width: int = int.from_bytes(file.read(4), "little")
            height: int = int.from_bytes(file.read(4), "little")
            if not size_y:
                size_y = height // (width // size_x)
            num_frames = len([name for name in listdir(folder) if path.isfile(name)])

        system(f"mode {size_x * 2}, {size_y}")
        if ask:
            input("start?")
        timer = FPSTimer(30)
        for i in range(0, 6572, 1):
            self.__parse_frame__(f"{folder}frame{i}.bmp", width, height, size_x, size_y)
            timer.sleep()


    def __parse_frame__(self, frame_path: str, width: int, height: int, size_x: int, size_y: int):
        secxw: int = width // size_x
        secyh: int = height // size_y

        with open(frame_path, "rb") as file:
            file.seek(54)
            file_tbl = [[0 for _ in range(size_x)] for _ in range(size_y)]
            for i in range(width * height):
                file_tbl[(i // width) // secyh][(i % width) // secxw] += int.from_bytes(file.read(1), "little") - 127
                file.read(2)
        
        file_tbl = file_tbl[::-1]
        stdout.write('\r' + "".join(["".join(["##" if square > 0 else "  " for square in row]) for row in file_tbl]))            


def main() -> None:
    if not path.exists("frames/"):
        download_vid.download_video("badapple.mp4", "frames/", ".bmp", log=True)
    system("cls")
    try:
        hide()
        renderer = BMPvid_renderer()
        renderer.render_frames("frames/", 80)
    except KeyboardInterrupt:
        pass
    finally:
        show()
        stdout.write("\x1b[39m\x1b[49m")


if __name__ == "__main__":
    main()