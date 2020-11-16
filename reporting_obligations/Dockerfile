FROM tiangolo/uvicorn-gunicorn:python3.8

COPY ./reporting_obligations/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy dependencies
COPY ./reporting_obligations /app/reporting_obligations
# Copy the app/main.py
COPY ./reporting_obligations/app /app

#WORKDIR /app
RUN ls
RUN dir
