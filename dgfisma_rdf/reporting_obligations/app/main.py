import base64
import binascii
import logging
import os
import time

from SPARQLWrapper import SPARQLWrapper, DIGEST, JSON, POST
from cassis import load_typesystem, load_cas_from_xmi
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rdflib import Literal

from .. import cas_parser
from ..build_rdf import ROGraph

app = FastAPI()

ROOT = os.path.join(os.path.dirname(__file__), '../..')
rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'
path_typesystem = os.path.join(ROOT, rel_path_typesystem)
with open(path_typesystem, 'rb') as f:
    TYPESYSTEM = load_typesystem(f)


class CasBase64(BaseModel):
    content: str  # Base64 content as string


@app.get("/")
async def root():
    return {"message": "DGFisma reporting obligation RDF connector."}


@app.post("/ro_cas/upload")
async def create_file(file: UploadFile = File(...), endpoint: str = Header(...)) -> cas_parser.CasContent:
    """

    Args:
        file: CAS
        endpoint: URL to Fuseki endpoint. e.g. f'http://fuseki_RO:3030/RO/'

    Returns:
        None
    """

    return create_file_shared(file.file, endpoint)


@app.post("/ro_cas/base64")
async def create_file_base64(cas_base64: CasBase64,
                             endpoint: str = Header(...)
                             ) -> cas_parser.CasContent:
    """

    Args:
        cas_base64: CAS in base64 string
        endpoint: URL to Fuseki endpoint. e.g. f'http://fuseki_RO:3030/RO/'

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

    return create_file_shared(decoded_cas_content, endpoint)


def create_file_shared(decoded_cas_content, endpoint):
    # Get relevant data of reporting obligations out of the CAS:
    cas = load_cas_from_xmi(decoded_cas_content, typesystem=TYPESYSTEM)

    try:
        cas_content = cas_parser.CasContent.from_cassis_cas(cas)
    except ValueError as e:
        raise HTTPException(status_code=406, detail=f"CAS does contain expected annotations:\n{e}")
    except Exception as e:
        raise HTTPException(status_code=406, detail=f"Unable to extract content from CAS.\n{e}")

    return update_rdf_from_cas_content(cas_content, endpoint)


def update_rdf_from_cas_content(cas_content, endpoint) -> cas_parser.CasContent:
    # Load into an RDF
    g = ROGraph()
    # # g = PersistentROGraph()

    try:
        g.add_cas_content(cas_content)
    except Exception as e:
        raise HTTPException(status_code=406, detail=f"Unable to add content to RDF.\n{e}")

    # Store in Fuseki
    sparql = SPARQLWrapper(endpoint)

    sparql.setHTTPAuth(DIGEST)
    if 0:  # doesn't seem to be necessary!
        sparql.setCredentials("", "")  # get from secret
    sparql.setReturnFormat(JSON)
    sparql.setMethod(POST)

    def get_string_repr(n):
        if isinstance(n, Literal):
            # If you want to include line breaks on your ttl files you need to use long literals,
            # ie three double quotes (""")
            # https://github.com/ckan/ckanext-dcat/issues/63
            return f"""\"\"\"{n.toPython()}\"\"\""""
        else:
            return f"""<{n.toPython()}>"""

    def get_q(g: ROGraph):
        """
        Based on  q = "INSERT DATA { <http://foo> <http://bar> <http://baz> . }"
        """

        q = """INSERT DATA {\n"""

        for row in g:
            q_i = " ".join(map(get_string_repr, row)) + ' . \n'
            q += q_i

        q += '}'
        return q

    q = get_q(g)

    sparql.setQuery(q)
    try:
        sparql.query()
    except ValueError as e:
        raise HTTPException(status_code=406, detail=f"Unable to query to fuseki with endpoint = '{endpoint}'.\n{e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to query due to following exception:\n{e}")

    return cas_content
