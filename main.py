from fastapi import FastAPI

app = FastAPI() # this function creates a FastAPI application instance
@app.get("/") # GET endpoint at the root URL
async def root():
    return {"message": "Hello World"}

