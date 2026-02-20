import uvicorn

import api

app = api.app

if __name__ == "__main__":
    uvicorn.run(api.app, host="0.0.0.0", port=8002)
