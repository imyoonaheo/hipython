from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

res = client.responses.create(
    model = 'gpt-4o-mini', #파라미터 파라미터는 comma로 연결
    input = [
        {"role" : "system", "content":"너는 컨설팅 전문가야"},
        {"role" : "user", "content":"컨설팅 전략을 작성"}
        
    ],
    temperature=2
)
print(res.output_text)