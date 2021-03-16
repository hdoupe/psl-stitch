cd psl-stitch && \
    export TAG=$(echo $GITHUB_SHA | head -c7) REPO=registry.digitalocean.com/$CONTAINER_REPO && \
    docker-compose up -d $CONTAINER_NAME
