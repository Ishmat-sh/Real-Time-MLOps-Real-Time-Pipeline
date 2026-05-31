.PHONY: up down logs train test-predict build

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f inference consumer producer

build:
	docker compose build

train:
	docker compose run --rm train

test-predict:
	curl -s -X POST http://localhost:8000/predict \
		-H "Content-Type: application/json" \
		-d '{"transaction_id":"test-1","user_id":"user_0001","timestamp":"2025-01-01T12:00:00Z","amount":999.99,"merchant_category":"electronics","merchant_category_code":5732,"location":"Tokyo, JP","hour_of_day":3,"is_weekend":0,"distance_from_home_km":500}' | python3 -m json.tool
