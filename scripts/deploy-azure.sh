#!/bin/bash

cd ..

# Build and deploy on master branch, only if not a pull request
if [[ ($BUILD_SOURCEBRANCHNAME == 'master') && ($SYSTEM_PULLREQUEST_PULLREQUESTID == '') ]]; then
    echo "Building image"
    docker build -t pythondiscord/seasonalbot:latest -f docker/Dockerfile .

    echo "Pushing image to Docker Hub"
    docker push pythondiscord/seasonalbot:latest
else
    echo "Skipping deploy"
fi
