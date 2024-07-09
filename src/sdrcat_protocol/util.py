def PrintHex(data: bytes):
    i = 0
    print("-----|-------------------------------------------------|-----------------")
    print("     |  0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F | ASCII           ")
    print("-----|-------------------------------------------------|-----------------")
    while i < len(data):
        if i + 16 < len(data):
            chunk = data[i:i+16]
            rem = ""
        else:
            chunk = data[i:]
            rem = " ".join("  " for x in range(i + 16 - len(data))) + " "

        print("{:04X} | ".format(i) + " ".join("{:02X}".format(b) for b in chunk) + rem + " | " + "".join(chr(b if b >= 32 and b < 127 else ord('.')) for b in chunk))
        i += 16