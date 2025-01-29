from typing import Optional
from cv2 import VideoCapture, CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH, CAP_PROP_FPS, CAP_PROP_FRAME_COUNT
from io import BufferedWriter
from sys import stdout
from numpy import array, ndarray, uint8


def encode_video(vid_path: str, colour_depth: int = 8, monochrome: bool = False, size_x: Optional[int] = None, size_y: Optional[int] = None, *, log: bool = False) -> None:
    # Load the video
    video: VideoCapture = VideoCapture(vid_path)
    
    # Open the wrtiting file
    with open("temps.evf", "wb", 0) as file:
        # Write the metadata
        file.write((ord('E')).to_bytes(length=1, byteorder="big"))
        file.write((ord('V')).to_bytes(length=1, byteorder="big"))
        height: int = int(video.get(CAP_PROP_FRAME_HEIGHT))
        width: int = int(video.get(CAP_PROP_FRAME_WIDTH))
        if not size_x and not size_y:
            size_y = height
            size_x = width
        elif not size_x and size_y:
            size_x = width // (height // size_y)
        elif size_x and not size_y:
            size_y = height // (width // size_x)
        
        file.write(size_x.to_bytes(length=4, byteorder="big"))
        file.write(size_y.to_bytes(length=4, byteorder="big"))
        file.write(round(video.get(CAP_PROP_FPS)).to_bytes(length=2, byteorder="big"))
        framec: int = int(video.get(CAP_PROP_FRAME_COUNT))
        buffer: int = framec
        buffer <<= 2
        buffer |= 3 - 2 * monochrome
        buffer <<= 4
        buffer |= colour_depth
        file.write(buffer.to_bytes(length=3, byteorder="big"))
        # Clear the buffer
        file.flush()

        cd: int = 8 - colour_depth
        # Buffer the entire length of the file
        with BufferedWriter(file, ((size_x * size_y * colour_depth * (3 - 2 * monochrome) + 7) // 8) * framec) as buff:
            for counter in range(framec):
                # Checking the next frame exists then reading the frame into an ndarray
                ret, frame = video.read()
                if not ret:
                    break
                frame: ndarray[ndarray[uint8]] = array(frame, ndarray, copy=False)

                buffer: int = 0
                bufflen: int = 0
                # Loop over every pixel
                for row in frame:
                    for pxl in row:
                        buffer <<= colour_depth
                        if monochrome:
                            # Finding the average bightness of the pixel
                            if pxl[0] or pxl[1] or pxl[2]:
                                buffer |= ((pxl[0] + pxl[1] + pxl[2]) >> cd) // 3
                            bufflen += colour_depth
                        else:
                            # Write each colour contiguously to the buffer
                            buffer <<= colour_depth
                            if pxl[0]:
                                buffer |= int(pxl[0] >> cd)
                            buffer <<= colour_depth
                            if pxl[1]:
                                buffer |= int(pxl[1] >> cd)
                            buffer <<= colour_depth
                            if pxl[2]:
                                buffer |= int(pxl[2] >> cd)
                            bufflen += 3 * colour_depth
                        # When the buffer is a whole number of bytes, write them to the file
                        if not bufflen % 8:
                            buff.write(buffer.to_bytes(length=(bufflen // 8), byteorder="big"))
                            buffer = 0
                            bufflen = 0
                
                # Write any remaining pixels to the file with trailing bits
                if bufflen:
                    buffer <<= bufflen % 8
                    buff.write(size_x.to_bytes(length=((bufflen + 7) // 8), byteorder="big"))

                if log:
                    stdout.write(f"\rEncoded Frame {counter + 1} of {framec}")
    if log:
        stdout.write("\nFinished!\n")


def main() -> None:
    # IMPORTANT INFO
    # * This currently does not support resizing.

    # * Two .evf files are already included.

    # * By default, the file is saved to temp.evf.

    # * Cobalt video downloader was used at 240p.
    #   https://cobalt.tools/

    encode_video("OnceInALifeTime.mp4", 1, True, log=True)


if __name__ == "__main__":
    main()