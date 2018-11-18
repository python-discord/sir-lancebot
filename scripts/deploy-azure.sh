#!/bin/bash

cd ..

# Build and deploy on master branch, only if not a pull request
if [[ ($BUILD_SOURCEBRANCHNAME == 'master') && ($SYSTEM_PULLREQUEST_PULLREQUESTID == '') ]]; then
    echo "Building image"
    docker build -t pythondiscord/seasonalbot:latest -f docker/Dockerfile .

    echo "Pushing image to Docker Hub"
    docker push pythondiscord/seasonalbot:latest

    echo "Deploying on server"
    pepper $1 state.apply docker/hacktoberbot --out=no_out --non-interactive
else
    echo "Skipping deploy"
fi
