from os import system, path, listdir
from typing import Optional
from sys import stdout
import download_vid
from cursor import hide, show
from fpstimer import FPSTimer
from time import time, sleep
from io import BufferedReader


class EVF_renderer:
    def render_frames(self, path: str, size_x: int, size_y: Optional[int] = None, *,render_fps: Optional[int] = None, ask: bool = False) -> None:
        assert path[-4:] == ".evf", f"Wrong file type (should be .evf was .{path.split('.')[-1]})!"
        with open(path, "rb") as file:
            assert (magic_num := chr(int.from_bytes(file.read(1))) + chr(int.from_bytes(file.read(1)))) == "EV", f"Wrong magic number (should be EV was {magic_num})!"

            width: int = int.from_bytes(file.read(4), "big")
            height: int = int.from_bytes(file.read(4), "big")
            if not size_y:
                size_y = height // (width // size_x)
            secxw: int = width // size_x
            secyh: int = height // size_y
            frame_rate: int = int.from_bytes(file.read(2), "big")
            buffer: int = int.from_bytes(file.read(3), "big")
            colour_depth = buffer & ((1 << 4) - 1)
            buffer >>= 4
            monochrome = (buffer & ((1 << 2) - 1)) == 1
            buffer >>= 2
            num_frames = buffer & ((1 << 18) - 1)

            num_bytes: int = (width * height * (pxl_size := colour_depth * (3 - 2 * monochrome)) + 7) // 8
            if pxl_size % 8 == 0:
                step = (pxl_size * 1) // 8
            elif pxl_size % 8 == 4:
                step = (pxl_size * 2) // 8
            elif pxl_size % 8 == 2:
                step = (pxl_size * 4) // 8
            else:
                step = pxl_size
            
            frame_step: int = frame_rate // render_fps
            spf = 1 / render_fps

            system(f"mode {size_x * 2}, {size_y}")
            if ask:
                input("start?")

            with BufferedReader(file, ((width * height * colour_depth * (3 - 2 * monochrome) + 7) // 8) * num_frames) as buffile:
                timer = FPSTimer(30)
                for i in range(0, num_frames, 1):
                    image: list[list[int]] = self.__parse_frame__(file, width, height, colour_depth, monochrome, size_x, size_y, num_bytes, step, pxl_size, secxw, secyh)
                    stdout.write('\r' + ''.join(["".join(["##" if square > 0 else "  " for square in row]) for row in image]))
                    timer.sleep()


    def __parse_frame__(self, file: str, width: int, height: int, colour_depth: int, monochrome: bool, size_x: int, size_y: int, num_bytes: int, step: int, pxl_size: int, secxw: int, secyh: int) -> list[list[int]]:
        secxw: int = width // size_x
        secyh: int = height // size_y
        file_tbl: list[list[int]] = [[0 for _ in range(size_x)] for _ in range(size_y)]
        pxl: int = -step * 8 // pxl_size

        cnum: int = 0
        for cnum in range(0, num_bytes, step):
            pxl += 2 * step * 8 // pxl_size
            chunk: int = int.from_bytes(file.read(step), "big")
            for _ in range((step * 8) // pxl_size):
                if monochrome:
                    pxl -= 1
                    file_tbl[(pxl // width) // secyh][(pxl % width) // secxw] += (chunk & ((1 << colour_depth) - 1)) - ((1 << colour_depth) - 1) / 2
                    chunk >>= colour_depth
        
        if num_bytes - (cnum + 1):
            pxl += 2 * step * 8 // pxl_size
            chunk: int = int.from_bytes(file.read(num_bytes - cnum), "big")
            for _ in range(pxl - width * height):
                if monochrome:
                    pxl -= 1
                    file_tbl[(pxl // width) // secyh][(pxl % width) // secxw] += (chunk & ((1 << colour_depth) - 1)) - ((1 << colour_depth) - 1) / 2
                    chunk >>= colour_depth
        
        return file_tbl


def main() -> None:
    system("cls")
    debug = False
    try:
        hide()
        renderer = EVF_renderer()
        renderer.render_frames("OnceInALifetime.evf", 80, render_fps=15, ask=True)
    except KeyboardInterrupt:
        pass
    finally:
        show()
        stdout.write("\x1b[39m\x1b[49m")
        if not debug:
            system("cls")


if __name__ == "__main__":
    main()