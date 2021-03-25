!Run from parent directory!

# app

An api is provided through fast api that extracts the *reporting obligations* from the *cas+*.

To build the Docker image:

`docker build . -t ro-rdf --no-cache -f dgfisma_rdf/reporting_obligations/Dockerfile`

To run the app:

`docker run -d --name ro_rdf_container -p 10080:80 --network ROnetwork -e MODULE_NAME="dgfisma_rdf.reporting_obligations.app.main" ro-rdf`

To post a request use:
http://localhost:10080/

## Useful commands

* Logs

      docker logs -f ro_rdf_container

* Docs

  [http://localhost:10080/docs](http://localhost:10080/docs)

* Tunnel host port to local.

      ssh -L localhost:10080:localhost:10080 <username>@<server>

  e.g. `ssh -L localhost:10080:localhost:10080 laurens@192.168.105.41
  `

* Remove container:

      docker stop ro_rdf_container; docker rm ro_rdf_container 

# RDF ontology

## TODO's

* [build_rdf.py](./build_rdf.py)
    * [ ] Decide on Namespace for DGFISMA reporting obligations.
    * [ ] index documents and reporting obligations. They are saved as *blank nodes*.
    * [x] catch if sentence segment (e.g. Report, Frequency, RegulatoryBody) has no known representation.        
      e.g. ARGM-PRP, ARGM-PRD.

      This is now solved by linking directly to a SKOS:Concept through hasEntity predicate. 