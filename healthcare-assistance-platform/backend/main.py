
from fastapi import FastAPI

# Initialize FastAPI application
app = FastAPI(
    title="AI-Driven Healthcare Assistance Platform",
    description="A multilingual healthcare assistance platform "
                "for rural communities.",
    version="1.0.0"
)


# Root API endpoint
@app.get("/")
def home():
    return {
        "message": "Healthcare Assistance Platform API is running",
        "status": "success"
    }


# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "Healthcare Assistance Platform"
    }
