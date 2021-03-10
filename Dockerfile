FROM continuumio/miniconda3

RUN conda config --append channels conda-forge && \
    conda install taxcalc paramtools && \
    pip install fastapi uvicorn python-jose[cryptography]

RUN pip install "git+https://github.com/compute-tooling/compute-studio-kit.git@async#egg=cs_kit"

COPY ./setup.py /setup.py
COPY ./psl_stitch /psl_stitch

RUN pip install -e .

EXPOSE 80

COPY ./api /api

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]