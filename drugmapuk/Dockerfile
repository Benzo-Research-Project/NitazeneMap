FROM python:3.12

WORKDIR /drugmapuk

COPY ./requirements.txt /drugmapuk/requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /drugmapuk/requirements.txt

RUN pip uninstall --yes werkzeug
RUN pip install -v https://github.com/pallets/werkzeug/archive/refs/tags/2.0.3.tar.gz
RUN pip install --upgrade flask werkzeug

COPY ./app.py /drugmapuk/app.py
COPY ./assets /drugmapuk/assets
COPY ./data /drugmapuk/data
COPY ./utils /drugmapuk/utils
COPY ./changelog.md /drugmapuk/changelog.md
COPY ./config.yaml /drugmapuk/config.yaml

CMD ["python","app.py"]