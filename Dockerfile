from python:3

RUN python3 -m pip install poetry
RUN mkdir /app

WORKDIR /app 
COPY pyproject.toml /app
RUN poetry install

COPY pcrud /app/pcrud
COPY scripts /app/scripts
COPY alembic.ini /app

CMD poetry run pytest && poetry run alembic upgrade head && poetry run uvicorn pcrud:app --host 0.0.0.0 --port 80
