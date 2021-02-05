import base64
import binascii
import logging
import os
import time

from cassis import load_typesystem, load_cas_from_xmi
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID
from rdflib.plugins.stores.auditable import AuditableStore
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

from dgfisma_rdf.reporting_obligations.build_rdf import ROUpdate
from .. import cas_parser
from ..build_rdf import ROGraph

app = FastAPI()

ROOT = os.path.join(os.path.dirname(__file__), '../../..')

load_dotenv(os.path.join(ROOT, 'secrets/dgfisma.env'))
SECRET_USER = os.getenv("FUSEKI_ADMIN_USERNAME")
SECRET_PASS = os.getenv("FUSEKI_ADMIN_PASSWORD")

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
                      endpoint: str = Header(...),
                      ) -> cas_parser.CasContent:
    """

    Args:
        file: CAS
        endpoint: URL to Fuseki endpoint. e.g. f'http://fuseki_RO:3030/RO/'
        doc_id: ID to the document

    Returns:
        None
    """

    return create_file_shared(file.file, endpoint, docid)


@app.post("/ro_cas/base64")
async def create_file_base64(cas_base64: CasBase64,
                             docid: str = Header(...),
                             endpoint: str = Header(...),
                             ) -> cas_parser.CasContent:
    """

    Args:
        cas_base64: CAS in base64 string
        endpoint: URL to Fuseki endpoint. e.g. f'http://fuseki_RO:3030/RO/'
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

    return create_file_shared(decoded_cas_content, endpoint, docid)


def create_file_shared(decoded_cas_content,
                       endpoint,
                       doc_id):
    # Get relevant data of reporting obligations out of the CAS:
    cas = load_cas_from_xmi(decoded_cas_content, typesystem=TYPESYSTEM)

    try:
        cas_content = cas_parser.CasContent.from_cassis_cas(cas)
    except ValueError as e:
        raise HTTPException(status_code=406, detail=f"CAS does contain expected annotations:\n{e}")
    except Exception as e:
        raise HTTPException(status_code=406, detail=f"Unable to extract content from CAS.\n{e}")

    return update_rdf_from_cas_content(cas_content, endpoint, doc_id)


def update_rdf_from_cas_content(cas_content: cas_parser.CasContent,
                                endpoint: str,
                                doc_id: str) -> cas_parser.CasContent:
    sparql_update_store = SPARQLUpdateStore(queryEndpoint=endpoint,
                                            update_endpoint=endpoint + '/update',  # Might have to add "/update"
                                            auth=(SECRET_USER, SECRET_PASS)
                                            )

    g_init = ROGraph(sparql_update_store,
                     DATASET_DEFAULT_GRAPH_ID,
                     include_schema=False)  # TODO This causes a serious delay!

    g = ROGraph(AuditableStore(g_init.store),
                g_init.identifier,
                include_schema=False  # Store should already include schema by now.
                )

    try:

        g.add_cas_content(cas_content, doc_id, endpoint=endpoint)

    except Exception as e:

        g.rollback()

        raise HTTPException(status_code=406, detail=f"Unable to add content to RDF.\n{e}")

    else:
        # Not necessary, but to clean up the pool.
        g.commit()

    return cas_content
