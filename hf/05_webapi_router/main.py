from fastapi import FastAPI
from routers.items import router as items_router
from routers.login import router as login_router
from routers.file_upload import router as file_upload


app = FastAPI()
app.include_router(items_router)
app.include_router(login_router)
app.include_router(file_upload)

#uvicorn main:app --reload
#get /items/
#get /items/1
#get /items/5
#post auth/login

#formed data로 입력하세요
#{
# "username": "alice"
# "password": "1234"
#}

# post /analysis/sentiment