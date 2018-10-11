#!/bin/bash

# Build and deploy on master branch
if [[ $TRAVIS_BRANCH == 'master' && $TRAVIS_PULL_REQUEST == 'false' ]]; then
    echo "Connecting to docker hub"
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

    echo "Building image"
    docker build -t pythondiscord/hacktober-bot:latest -f docker/Dockerfile .

    echo "Pushing image"
    docker push pythondiscord/hacktober-bot:latest
    
    echo "Deploying on server"
    pepper ${SALTAPI_TARGET} state.apply docker/hacktoberbot --out=no_out --non-interactive &> /dev/null
else
    echo "Skipping deploy"
fi
