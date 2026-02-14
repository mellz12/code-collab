from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
async def root():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Code collab</title>
        </head>
            <body>
            <h1> хелоу хелоу хелоу</h1>
            <p>Сервер работает</p>
            </body>
    </html>
            """
    return HTMLResponse(content=html_content)

