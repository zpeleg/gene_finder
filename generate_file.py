from random import choice, randint

KB = 1024
MB = 1024 * KB
GB = 1024 * MB

OUTPUT_PATH = "bigfile.txt"
FILE_SIZE = 50 * MB


def main():
    with open(OUTPUT_PATH, "w") as f:
        for i in range(FILE_SIZE):
            f.write(choice(["G", "A", "T", "C"]))
            if randint(0, 100) == 0:
                f.write("AAAAAAAAAAA")


if __name__ == "__main__":
    main()
