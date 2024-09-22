from fastapi import FastAPI
from app.router import auth_router

app = FastAPI()

app.include_router(auth_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
