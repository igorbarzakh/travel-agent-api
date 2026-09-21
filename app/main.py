from fastapi import FastAPI

app = FastAPI(
    title="Travel Agent API",
    description="API туристического AI-ассистента",
    version="0.0.1",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}