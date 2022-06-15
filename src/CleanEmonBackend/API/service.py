"""Simple entry point for starting the API server programmatically"""

import uvicorn


def run():
    uvicorn.run("CleanEmonBackend.API:api", reload=True)
