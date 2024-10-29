import fastapi
import random

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/random")
def read_random():
    r = random.randint(1, 100)
    print(f"Generated random number: {r}")
    return {"random": r}