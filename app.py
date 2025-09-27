from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/generatePartNumber")
def generate_part_number():
    # Example logic to generate a part number
    part_number = "PART-12345"
    return {"partNumber": part_number}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9095)