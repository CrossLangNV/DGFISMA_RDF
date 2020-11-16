import base64
import logging
import os
import time

import binascii
from SPARQLWrapper import SPARQLWrapper, DIGEST, JSON, POST
from cassis import load_typesystem, load_cas_from_xmi
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rdflib import Literal

from reporting_obligations import cas_parser
from reporting_obligations.build_rdf import ROGraph

app = FastAPI()

ROOT = os.path.join(os.path.dirname(__file__), '../..')
rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'
path_typesystem = os.path.join(ROOT, rel_path_typesystem)
with open(path_typesystem, 'rb') as f:
    TYPESYSTEM = load_typesystem(f)

LOCAL_URL = 'http://fuseki_RO:3030/RO/'


class CasBase64(BaseModel):
    content: str  # Base64 content as string


@app.get("/")
async def root():
    return {"message": "DGFisma reporting obligation RDF connector."}


@app.post("/ro_cas/upload")
async def create_file(file: UploadFile = File(...)) -> cas_parser.CasContent:
    # Get relevant data of reporting obligations out of the CAS:

    cas = load_cas_from_xmi(file.file, typesystem=TYPESYSTEM)
    cas_content = cas_parser.CasContent.from_cassis_cas(cas)

    # Load into an RDF
    return update_rdf_from_cas_content(cas_content)


@app.post("/ro_cas/base64")
async def create_file_base64(cas_base64: CasBase64) -> cas_parser.CasContent:
    # Get relevant data of reporting obligations out of the CAS:

    try:
        decoded_cas_content = base64.b64decode(cas_base64.content).decode('utf-8')
    except binascii.Error:
        logging.info(f"could not decode the 'cas_content' field. Make sure it is in base64 encoding.")
        end = time.time()
        logging.info(end)
        return JSONResponse(cas_base64)

    cas = load_cas_from_xmi(decoded_cas_content, typesystem=TYPESYSTEM)
    cas_content = cas_parser.CasContent.from_cassis_cas(cas)

    return update_rdf_from_cas_content(cas_content)


def update_rdf_from_cas_content(cas_content) -> cas_parser.CasContent:
    # Load into an RDF
    g = ROGraph()
    # # g = PersistentROGraph()
    g.add_cas_content(cas_content)

    # Store in Fuseki
    sparql = SPARQLWrapper(LOCAL_URL)
    sparql.setHTTPAuth(DIGEST)
    if 0:  # doesn't seem to be necessary!
        sparql.setCredentials("", "")  # get from secret
    sparql.setReturnFormat(JSON)
    sparql.setMethod(POST)

    def get_string_repr(n):
        if isinstance(n, Literal):
            return f"""\"{n.toPython()}\""""
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
    ret = sparql.query()

    results = ret.convert()
    logging.info(results)

    return cas_content
