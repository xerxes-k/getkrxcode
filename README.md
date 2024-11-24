# getkrxcode
data.go.kr 공식 API를 사용해 KRX 상장 기업의 종목 코드를 조회하는 프로젝트입니다.

data.go.kr의 공식 API를 사용하여 KRX(한국거래소) 상장 기업의 종목 코드를 손쉽게 조회할 수 있는 프로젝트입니다. 최신 상장 기업 정보를 자동으로 가져와 금융 데이터 분석이나 애플리케이션 개발에 활용할 수 있도록 돕습니다.

Retrieve KRX-listed company stock codes using the official data.go.kr API

This project retrieves stock codes for companies listed on the Korea Exchange (KRX) using the official API provided by data.go.kr. It simplifies accessing financial data by automating the retrieval process, ensuring that users have up-to-date information on KRX-listed companies for further analysis or integration into financial applications.

### 사용법 use guide

1. 먼저 https://www.data.go.kr/data/15094775/openapi.do 에서 서비스 키를 발급 받으세요
- first, get your service key from https://www.data.go.kr/en/data/15094775/openapi.do
2. 발급 받은 서비스 키를 project.py가 있는 폴더에 serviceKey.txt라는 파일에 저장하세요
- store your service key in a txt file called serviceKey.txt in the same folder as project.py

### 주요 기능 functions

- read_service_key_from_text
- fetch_stock_by_name
- fetch_code_by_name
- fetch_all_listings

#### Video Demo:  <URL [HERE](https://youtu.be/JV72hRNXSDc)>
