FROM python:3.9.6-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir poetry 

RUN poetry config virtualenvs.create false
RUN poetry install --no-root

CMD [ "python", "main.py" ]