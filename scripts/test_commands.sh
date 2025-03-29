docker-compose up -d --build


curl -X POST "http://localhost:8000/api/v1/users/" \
-H "Content-Type: application/json" \
-d '{
  "email": "user1@example.com",
  "password": "securepassword123"
}'

TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1@example.com&password=securepassword123" | jq -r '.access_token')

curl -X 'POST' 'http://127.0.0.1:8000/api/v1/audio/upload/' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/Users/tyroneyanaga/Downloads/conversation-in-class-room-66980.mp3;type=audio/mp3'

curl -X POST "http://127.0.0.1:8000/api/v1/transcriptions/transcribe/4" \
  -H "Authorization: Bearer $TOKEN" \
  -H "accept: application/json"


psql -h localhost -p 5432 -U user -d audio_db
SELECT * FROM audio_files;


docker exec -it interview_assist-backend-1 bash
which ffmpeg
