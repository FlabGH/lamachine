import os
import time

DATABASE_URL = os.getenv("DATABASE_URL", "")
QDRANT_URL = os.getenv("QDRANT_URL", "")


def main() -> None:
    print("worker started")
    print(f"DATABASE_URL configured: {bool(DATABASE_URL)}")
    print(f"QDRANT_URL: {QDRANT_URL}")

    while True:
        print("worker heartbeat")
        time.sleep(30)


if __name__ == "__main__":
    main()