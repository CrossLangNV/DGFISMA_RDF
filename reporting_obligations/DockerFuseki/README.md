From [https://hub.docker.com/r/stain/jena-fuseki](https://hub.docker.com/r/stain/jena-fuseki)

## First run busybox for data parsistence

    docker run --name fuseki-data-RO -v /fuseki busybox

## Docker network

    docker network create ROnetwork

## 

    docker run -d --name fuseki_RO -p 3030:3030 -e ADMIN_PASSWORD=neuro --volumes-from fuseki-data-RO --network ROnetwork stain/jena-fuseki


* -d: run in background

* add to other runs: `--network ROnetwork`
e.g.

<!---
## TODO check if correct way to do it?

`ssh -L localhost:3030:localhost:3030 laurens@192.168.105.41`
-->
