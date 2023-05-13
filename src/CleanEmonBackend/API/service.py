"""Simple entry point for starting the API server programmatically"""

import uvicorn


def run():
    uvicorn.run("CleanEmonBackend.API:api", reload=True, host = "0.0.0.0")


# Add this to help testing and debugging quickly through an IDE. TODO: Remove in release
if __name__ == '__main__':
    run()
