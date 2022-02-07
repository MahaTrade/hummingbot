#!/bin/bash
aws ecr-public get-login-password --region us-east-1 --profile scallop | docker login --username AWS --password-stdin public.ecr.aws/g2z2e8i7
docker buildx build --platform linux/amd64 -t mahatrade/hummingbot . -f Dockerfile.arm
docker tag mahatrade/hummingbot:latestpublic.ecr.aws/g2z2e8i7/mahatrade/hummingbot:latest
docker pushpublic.ecr.aws/g2z2e8i7/mahatrade/hummingbot:latest

# docker tag mahatrade/hummingbot:latest enamakel/hummingbot:latest
# docker push enamakel/hummingbot:latest