from bitstring import BitStream

with open("test.evf", "wb+") as buff:
    buff.write((2).to_bytes(length=2, byteorder="big"))
    buff.write((3).to_bytes(length=3, byteorder="big"))