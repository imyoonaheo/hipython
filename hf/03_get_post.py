from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")   # get은 서버에 있는 데이터 읽기
def say_hello():
  return {"message":"안녕하세요.."}

@app.post("/echo")  # post는 서버에 새로운 데이터를 보내기
def echo(data: dict):
  return {"dict":data}

@app.get("/test1")
def root1():
  return {"name":"길동이"}

@app.get("/test2")
def root2():
  return ["길동이","둘리","또치"]

@app.get("/test3")
def root3():
  return "<h1>안녕?</h1>"

@app.get("/test4")
def root4():
  return 2000

# 경로매개변수, 핸들러
@app.get("/items/{item_id}")
def read_item(item_id:int):
  item_id = item_id*2
  print(f'{item_id}를 받았습니다')

  return {"ID":item_id}

#uvicorn 03_get_post:app --reload --port 8001

#쿼리 매개변수 > ? 뒤에 온다
#http://127.0.01:8001/items/3?discount=true
@app.get("/items/{item_id}")
def get_item(item_id: int, discount:bool ):
  item_msg = f"{discount} 할인여부"
  return item_msg


#http://127.0.01:8001/items/3/orders/2
@app.get("/items/{item_id}/orders/{order_id}")
def get_item_orders(item_id: int, order_id:int ):
  print("get_item_orders")
  return {"item_id" :item_id, "order_id": order_id}

# /stocks/005930/history?days=608market=kospi
@app.get("/stocks/{ticker}/history")
def get_stock_history(
  ticker: str, days: int, market: str
):
  print("get_stock_history > 종목 이력을 조회합니다.")
  return {"ticker" :ticker, "days":days, "histor": "구현예정입니다."}

#post로 바꾸기

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
class StockRequest(BaseModel):
    days: int
    market: str

# /stocks/005930/history?days=608market=kospi
@app.post("/stocks/{ticker}/history")
def get_stock_history(ticker: str, request: StockRequest):
    # request 객체를 통해 데이터를 가져옵니다.
    print(f"종목 이력 조회: {ticker}, 기간: {request.days}, 시장: {request.market}")
    
    return {
        "ticker": ticker,
        "days": request.days,
        "market": request.market,
        "history": "구현 예정입니다."
    }


from pydantic import BaseModel
class News(BaseModel):
  title: str
  content: str
  views: int = 0
  

@app.post("/news")
def anal_news(data: News):
  return {"news":data.title}



from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI('감성분석서비스')

class TextRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    text: str
    label: str
    score: float

@app.post("/sentiment", response_model=SentimentResponse)
def analyze_sentiment(request: TextRequest):
    # 실제 모델 연결 전 더미 응답
    return SentimentResponse(
        text=request.text,
        label="positive",
        score=0.95
    )
  

#uvicorn 03_get_post:app --reload --port 8001
#{
#	"title": "FastAPI와 Pydantic의 만남",
#    "content": "Pydantic을 사용하면 데이터 검증이 매우 쉬워집니다. 타입  힌트를 통해 안전한 코딩이 가능하죠.",
#    "views": 157
#} 