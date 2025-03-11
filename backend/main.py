from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from lexer import tokenize
from parser import parse_expression
import json

app = FastAPI()

# Allow CORS for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/tokenize")
async def analyze_code(data: dict):
    cpp_code = data.get("code", "")
    if not cpp_code:
        raise HTTPException(status_code=400, detail="No C++ code provided")

    tokens = tokenize(cpp_code)
    return {"tokens": tokens}

@app.post("/parse")
async def parse_code(data: dict):
    cpp_code = data.get("code", "")
    if not cpp_code:
        raise HTTPException(status_code=400, detail="No C++ code provided")

    parse_tree = parse_expression(cpp_code)
    print(parse_tree)
    return {"parse_tree": parse_tree}
    

# Run with: uvicorn main:app --reload