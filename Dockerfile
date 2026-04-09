FROM python:3.14
EXPOSE 8000

ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org -o install_poetry.py
RUN python3 install_poetry.py --version 2.3.2
RUN $POETRY_HOME/bin/poetry --version

WORKDIR /code
COPY . .

RUN ${POETRY_HOME}/bin/poetry install --only main --no-interaction --no-ansi

ENTRYPOINT ${POETRY_HOME}/bin/poetry run fastapi dev
