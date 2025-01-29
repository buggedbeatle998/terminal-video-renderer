from os import system
from typing import Optional
from sys import stdout
from cursor import hide, show
from fpstimer import FPSTimer
from io import BufferedReader


class EVF_renderer:
    def render_frames(self, path: str, size_x: int, size_y: Optional[int] = None, *,render_fps: Optional[int] = None, video_spd: int = 1, ask: bool = False) -> None:
        # Check that the file is a proper evf
        assert path[-4:] == ".evf", f"Wrong file type (should be .evf was .{path.split('.')[-1]})!"
        with open(path, "rb") as file:
            assert (magic_num := chr(int.from_bytes(file.read(1))) + chr(int.from_bytes(file.read(1)))) == "EV", f"Wrong magic number (should be EV was {magic_num})!"

            # Reading in the metadata
            width: int = int.from_bytes(file.read(4), "big")
            height: int = int.from_bytes(file.read(4), "big")
            if not size_y:
                size_y = height // (width // size_x)
            secxw: int = width // size_x
            secyh: int = height // size_y
            frame_rate: int = int.from_bytes(file.read(2), "big")
            if not render_fps:
                render_fps = frame_rate
            buffer: int = int.from_bytes(file.read(3), "big")
            colour_depth = buffer & ((1 << 4) - 1)
            buffer >>= 4
            monochrome: bool = (buffer & ((1 << 2) - 1)) == 1
            buffer >>= 2
            num_frames: int = buffer & ((1 << 18) - 1)

            # Calculating the byte step size as each pixel does not necessarily line up with a byte
            num_bytes: int = (width * height * (pxl_size := colour_depth * (3 - 2 * monochrome)) + 7) // 8
            if pxl_size % 8 == 0:
                step: int = (pxl_size * 1) // 8
            elif pxl_size % 8 == 4:
                step: int = (pxl_size * 2) // 8
            elif pxl_size % 8 == 2:
                step: int = (pxl_size * 4) // 8
            else:
                step: int = pxl_size

            # Sets cmd size to width * 2 by height because characters are 8 by 16
            system(f"mode {size_x * 2}, {size_y}")
            # Allows timed starts for comparisons
            if ask:
                input("start?")

            # Buffers the reads
            with BufferedReader(file, ((width * height * colour_depth * (3 - 2 * monochrome) + 7) // 8) * num_frames) as buffile:
                # Sorting out the fps
                timer: FPSTimer = FPSTimer(render_fps * video_spd)
                skips: int = frame_rate // render_fps - 1
                for _ in range(0, num_frames, 1):
                    # Skipping frames
                    if skips:
                        buffile.seek(num_bytes * skips, 1)
                    # Parsing the frame and writing it into a list[list[int]]
                    # Although this is not as efficient as it could be, it doesn't need to be as it isn't the bottleneck
                    image: list[list[int]] = self.__parse_frame__(buffile, width, height, colour_depth, monochrome, size_x, size_y, num_bytes, step, pxl_size, secxw, secyh)
                    # THIS is the main bottleneck of the program
                    # I couldn't find any better solutions than using stdout and carriage returns and word wrapping
                    stdout.write('\r' + ''.join(["".join(["##" if square > 0 else "  " for square in row]) for row in image]))
                    # Sleep any time that's left in the frame
                    timer.sleep()


    def __parse_frame__(self, file: str, width: int, height: int, colour_depth: int, monochrome: bool, size_x: int, size_y: int, num_bytes: int, step: int, pxl_size: int, secxw: int, secyh: int) -> list[list[int]]:
        # Initialising the frame
        file_tbl: list[list[int]] = [[0 for _ in range(size_x)] for _ in range(size_y)]
        # This is very weird, so let me explain.
        # This is the pixel number and so it's used to keep track of where everything will map to.
        # Suppose my step size is a byte.
        # Normal:
        # 00010001 000101101
        #      <-^       <-^
        # ----------------->
        # The pointer normally would read a step from right to left as the right is the least significant bit.
        # My system:
        #          00010001 000101101
        # ^        ^->      ^->
        # -------------------------->
        # However my system starts off the beginning and jumps two steps and then reads iterates and reads backwards a step,
        # ending up in the bits being read in the correct order. Again, not optimal but makes everything less confusing to me.
        pxl: int = -step * 8 // pxl_size

        # cnum records the chunk(byte in this case) the point is at
        cnum: int = 0
        for cnum in range(0, num_bytes, step):
            pxl += 2 * step * 8 // pxl_size
            chunk: int = int.from_bytes(file.read(step), "big")
            for _ in range((step * 8) // pxl_size):
                # I have no implemented colour
                if monochrome:
                    pxl -= 1
                    # Negetive is darker, positive in brighter
                    file_tbl[(pxl // width) // secyh][(pxl % width) // secxw] += (chunk & ((1 << colour_depth) - 1)) - ((1 << colour_depth) - 1) / 2
                    chunk >>= colour_depth
        
        # Each frame often has trailing bits as the each frame does not map to a whole number of bytes
        if num_bytes - (cnum + 1):
            pxl += 2 * step * 8 // pxl_size
            chunk: int = int.from_bytes(file.read(num_bytes - cnum), "big")
            for _ in range(pxl - width * height):
                if monochrome:
                    pxl -= 1
                    file_tbl[(pxl // width) // secyh][(pxl % width) // secxw] += (chunk & ((1 << colour_depth) - 1)) - ((1 << colour_depth) - 1) / 2
                    chunk >>= colour_depth
        
        # Return a reference to the frame
        return file_tbl


def main(*, debug: bool = False) -> None:
    # IMPORTANT INFO:
    # * PLEASE RUN IN CMD as that is what this program's made for:
    #   py render_EVF.py

    # * PLEASE USE A 8 x 16 FONT.
    #   This can be done by right clicking on the top bar of cmd then properties -> Font -> Font

    # * This only renders in monochrome because ANSI causing flickers issues.
    #   This is likely because cmd makes space for characters before realising that's they're not.
    #   Such are the flaws of trying to do it in cmd.

    # * This only renders at 1 colour depth because I haven't been bothered to implement any others yet.

    # * Render fps is capped at 60 total fps(render_fps * video_spd).

    # * .evf is my own custom uncompressed file format.
    
    #   It is supposed to take up as little space as possible without compressing.

    try:
        system("cls")
        hide()
        renderer: EVF_renderer = EVF_renderer()
        # Feel free to change the render fps to lower than and a factor of the video fps, default for both videos in 30 fps
        # Feel free to mess around with the video speed although it won't run more than x2 at 30 fps (that's 60 fps total) because of the output bottleneck
        renderer.render_frames("temp.evf", 80, render_fps=30, video_spd=1, ask=True)
        # Current Video Options:
        # * badapple.evf
        #       https://www.youtube.com/watch?v=FtutLA63Cp8
        #       Good monochrome music video
        #       Would also be the first choice for most coders
        # * OnceInALifetime.evf
        #       https://www.youtube.com/watch?v=5IsSpAOD6K8
        #       Very good for testing Faces

    except KeyboardInterrupt:
        pass
    # Resets even after keyboard interupts
    finally:
        show()
        # ANSI clearing for if and when I implement colour
        stdout.write("\x1b[39m\x1b[49m")
        if not debug:
            system("cls")


if __name__ == "__main__":
    main()