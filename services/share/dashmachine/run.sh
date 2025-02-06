docker run \
  --name=dashmachine \
  -p 5245:5245 \
  #-e CONTEXT_PATH=/dash
  -v ./data:/dashmachine/dashmachine/user_data \
  --restart unless-stopped \
  rmountjoy/dashmachine:latest