#!/bin/bash

# Build and deploy on master branch
#if [[ $TRAVIS_BRANCH == 'master' && $TRAVIS_PULL_REQUEST == 'false' ]]; then
    echo "Connecting to docker hub"
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

    echo "Building image"
    docker build -t pythondiscord/hacktober-bot:latest -f docker/Dockerfile .

    echo "Pushing image"
    docker push pythondiscord/hacktober-bot:latest
    
    echo "Deploying on server"
    pepper "glimglam.gserv.me" state.apply docker/hacktoberbot -u ${SALTAPI_URL} -a ${SALTAPI_EAUTH} --username ${SALTAPI_USER} --password ${SALTAPI_PASS} &> /dev/null

#    echo "Deploying container"
#    curl -H "token: $AUTODEPLOY_TOKEN" $AUTODEPLOY_WEBHOOK
#else
#    echo "Skipping deploy"
#fi
