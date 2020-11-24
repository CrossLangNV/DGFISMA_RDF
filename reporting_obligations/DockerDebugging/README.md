## Build

    docker build . -t ro-rdf/remote

## Run

    docker run --name ro_rdf_remote -it -p 15000:5000 --network ROnetwork ro-rdf/remote
    
### Legacy solution:

    docker run --name ro_rdf_remote -it -p 15000:5000 --link fuseki_RO --network ROnetwork ro-rdf/remote 
 
    
## Interpreter
    
[/usr/local/bin/python](/usr/local/bin/python)

## Tunnel to inside docker

local address; address in docker; address on server.

    ssh -L localhost:15080:127.0.0.1:8080 neuro@192.168.105.41 -p 15000
    
Make sure to run this locally.