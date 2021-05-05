import asyncio
import base64
import binascii
import logging
import os
import time
from typing import Optional

from cassis import load_typesystem, load_cas_from_xmi
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

from .. import cas_parser
from ..build_rdf import ROGraph

app = FastAPI()

ROOT = os.path.join(os.path.dirname(__file__), '../../..')

load_dotenv(os.path.join(ROOT, 'secrets/dgfisma.env'))

SECRET_USER = os.environ["FUSEKI_ADMIN_USERNAME"]
SECRET_PASS = os.environ["FUSEKI_ADMIN_PASSWORD"]

rel_path_typesystem = 'dgfisma_rdf/reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'
path_typesystem = os.path.join(ROOT, rel_path_typesystem)
with open(path_typesystem, 'rb') as f:
    TYPESYSTEM = load_typesystem(f)


class CasBase64(BaseModel):
    content: str  # Base64 content as string


@app.get("/")
async def root():
    return {"message": "DGFisma reporting obligation RDF connector."}


@app.post("/ro_cas/upload")
async def create_file(file: UploadFile = File(...),
                      docid: str = Header(...),
                      source_name: Optional[str] = Header(None),
                      source_url: Optional[str] = Header(None),
                      endpoint: str = Header(...),
                      updateendpoint: str = Header(...),
                      ) -> cas_parser.CasContent:
    """

    Args:
        file: CAS
        endpoint: URL to Fuseki endpoint. e.g. f'http://fuseki_RO:3030/RO/query'
        updateendpoint: URL to the Fuseki update endpoint. e.g. f'http://fuseki_RO:3030/RO/update'
        doc_id: ID to the document

    Returns:
        None
    """

    return create_file_shared(file.file, endpoint, updateendpoint, docid,
                              source_name=source_name,
                              source_url=source_url,
                              )


@app.post("/ro_cas/base64")
async def create_file_base64(cas_base64: CasBase64,
                             docid: str = Header(...),
                             source_name: Optional[str] = Header(None),
                             source_url: Optional[str] = Header(None),
                             endpoint: str = Header(...),
                             updateendpoint: str = Header(...),
                             ) -> cas_parser.CasContent:
    """

    Args:
        cas_base64: CAS in base64 string
        endpoint: URL to Fuseki endpoint. e.g. 'http://fuseki_RO:3030/RO/query'
        updateendpoint: URL to the Fuseki update endpoint. e.g. 'http://fuseki_RO:3030/RO/update'
        doc_id: ID to the document

    Returns:
        None
    """
    # Get relevant data of reporting obligations out of the CAS:

    try:
        decoded_cas_content = base64.b64decode(cas_base64.content).decode('utf-8')
    except binascii.Error:
        logging.info(f"could not decode the 'cas_content' field. Make sure it is in base64 encoding.")
        end = time.time()
        logging.info(end)
        return JSONResponse(cas_base64)

    return create_file_shared(decoded_cas_content, endpoint, updateendpoint, docid,
                              source_name=source_name,
                              source_url=source_url)


@app.post("/ro_cas/init")
async def init_file_base64(endpoint: str = Header(...),
                           updateendpoint: str = Header(...),
                           ):
    """ Initialise the RDF with the reporting obligation schema

    Args:
        endpoint: URL to Fuseki endpoint. e.g. 'http://fuseki_RO:3030/RO/query'
        updateendpoint: URL to the Fuseki update endpoint. e.g. 'http://fuseki_RO:3030/RO/update'

    Returns:
        None
    """

    sparql_update_store = SPARQLUpdateStore(queryEndpoint=endpoint,
                                            update_endpoint=updateendpoint,
                                            auth=(SECRET_USER, SECRET_PASS),  # needed
                                            context_aware=False,
                                            )

    g = ROGraph(sparql_update_store,
                DATASET_DEFAULT_GRAPH_ID,
                include_schema=True)

    g.commit()

    return JSONResponse(content={"message": "RDF model initialised succesfully"})


@app.post("/doc_source/add")
async def add_doc_source(docid: str = Header(...),
                         source_name: str = Header(...),
                         source_url: str = Header(None),
                         endpoint: str = Header(...),
                         updateendpoint: str = Header(...),
                         ):
    if source_url is None:
        # Give same name as source name and convert to URI.
        source_url = source_name

    g = get_sparql_update_graph(endpoint,
                                updateendpoint)

    g.add_doc_source(doc_id=docid,
                     source_id=source_url,
                     source_name=source_name)

    g.commit()
    g.close(False)
    return


def create_file_shared(decoded_cas_content,
                       endpoint,
                       update_endpoint,
                       doc_id,
                       source_name=None,
                       source_url=None,
                       ):
    # Get relevant data of reporting obligations out of the CAS:
    cas = load_cas_from_xmi(decoded_cas_content, typesystem=TYPESYSTEM)

    try:
        cas_content = cas_parser.CasContent.from_cassis_cas(cas)
    except ValueError as e:
        raise HTTPException(status_code=406, detail=f"CAS does contain expected annotations:\n{e}")
    except Exception as e:
        raise HTTPException(status_code=406, detail=f"Unable to extract content from CAS.\n{e}")

    return update_rdf_from_cas_content(cas_content, endpoint, update_endpoint, doc_id,
                                       source_name=None,
                                       source_url=None,
                                       )


def update_rdf_from_cas_content(cas_content: cas_parser.CasContent,
                                query_endpoint: str,
                                update_endpoint: str,
                                doc_id: str,
                                source_name=None,
                                source_url=None,
                                ) -> cas_parser.CasContent:
    g = get_sparql_update_graph(query_endpoint,
                                update_endpoint)

    try:

        g.add_cas_content(cas_content, doc_id, query_endpoint=query_endpoint)

    except Exception as e:

        g.rollback()

        raise HTTPException(status_code=406, detail=f"Unable to add content to RDF.\n{e}")

    else:
        # Push all updates to fuseki
        g.commit()

    g.close(False)  # commit_pending_transaction flag shouldn't matter, but just to be safe

    if source_name is not None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(add_doc_source(doc_id, source_url=source_url,
                                                        source_name=source_name,
                                                        endpoint=query_endpoint,
                                                        updateendpoint=update_endpoint, ))

    return cas_content


def get_sparql_update_graph(query_endpoint,
                            update_endpoint):
    # Context-aware has to be set to false to allow querying from the Graph object
    sparql_update_store = SPARQLUpdateStore(queryEndpoint=query_endpoint,
                                            update_endpoint=update_endpoint,
                                            auth=(SECRET_USER, SECRET_PASS),  # needed
                                            context_aware=False,
                                            autocommit=False
                                            )

    g = ROGraph(sparql_update_store,
                DATASET_DEFAULT_GRAPH_ID,
                include_schema=False)

    return g
