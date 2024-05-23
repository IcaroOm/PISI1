from fastapi import FastAPI
from views import router

app = FastAPI()

# Mount the sub-apps
app.include_router(router, prefix='')
