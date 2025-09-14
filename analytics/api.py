# analytics/api.py
from fastapi import FastAPI

app = FastAPI(title="Medical Pipeline Analytics")

@app.get("/")
def root():
    return {"message": "Analytics API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}