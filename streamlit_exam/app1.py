import streamlit as st

st.title('안녕하세요')

#브라우저에 텍스트 출력
st.write('Hello Streamlit')

st.divider()

#사용자 입력을 받는 요소
name = st.text_input('이름:')

st.write(name)

#### 버튼 호출보다 정의가 먼저 나와야됌

def bt1_click(): #정의
  st.write('good')

st.write('')
# bnt1 = st.button('눌러봐', on_click = bt1_click) #호출
bnt1 = st.button('눌러봐')
if bnt1 :
  # st.write('정말 눌렀어??')
  bt1_click()
  




import pandas as pd
df = pd.read_csv('./data/pew.csv')
print = df.info()


st.write(df.head())