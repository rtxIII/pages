#!/bin/bash

# Uptime Kuma Push URL
PUSH_URL="https://kuma.we2.xyz/api/push/KEY?status=up&msg=OK&ping="

# Status code: 0 for up, 1 for down
STATUS=0

# Optional: Message to include in the push
MESSAGE="Service is up and running"

# Send the push request
curl -X GET  "$PUSH_URL"

# Check if the request was successful
if [ $? -eq 0 ]; then
    echo "Push notification sent successfully."
else
    echo "Failed to send push notification."
fi