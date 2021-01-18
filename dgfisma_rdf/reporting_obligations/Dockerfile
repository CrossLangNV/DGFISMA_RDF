FROM tiangolo/uvicorn-gunicorn:python3.8

COPY ./dgfisma_rdf/reporting_obligations/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy dependencies
COPY ./dgfisma_rdf /app/dgfisma_rdf

RUN dir
