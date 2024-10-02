from fastapi import FastAPI
from app.router import auth_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


origins = [
     "http://localhost:5173",  # React app running on localhost
   "https://maileyo.com"  # Replace with your production URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
