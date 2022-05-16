import sys

import uvicorn

if __name__ == "__main__":
    if "--api" in sys.argv:
        uvicorn.run("CleanEmonBackend.API:api")

