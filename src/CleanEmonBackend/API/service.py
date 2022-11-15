"""Simple entry point for starting the API server programmatically"""

import uvicorn


def run():
    uvicorn.run("CleanEmonBackend.API:api", reload=True)

# Add this for to help test thing quick through an IDE TODO: Remove in release
if __name__ == '__main__':
    run()
