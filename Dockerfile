FROM continuumio/miniconda3

COPY ./requirements.txt ./requirements.txt
COPY ./conda-requirements.txt ./conda-requirements.txt

RUN conda config --append channels conda-forge && \
    conda install -r ./conda-requirements.txt && \
    pip install -r ./requirements.txt

COPY ./setup.py /setup.py
COPY ./psl_stitch /psl_stitch

RUN pip install -e .

EXPOSE 80

COPY ./api /api

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]