from fastapi import FastAPI

app = FastAPI(title="Team Practice C API")


@app.get("/")
def home():
    return {"message": "Team Practice C backend is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}