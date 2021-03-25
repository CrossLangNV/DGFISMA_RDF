#

! Run from base folder

1. Build docker

    `docker build -t dgfisma/rdf/remote -f docker/remote_interpreter/Dockerfile .`
    
2. Run docker

    `docker run -it -p 10002:5000 dgfisma/rdf/remote`