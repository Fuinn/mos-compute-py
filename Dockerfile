FROM python:3

LABEL "app.name"="MOS Compute Python"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# CBC
RUN mkdir -p /solvers
RUN cd /solvers/ && wget https://ampl.com/dl/open/cbc/cbc-linux64.zip
RUN cd /solvers/ && unzip cbc-linux64.zip

# Path
ENV PATH="$PATH:/solvers"

# MOS interface
ADD ./submodules/mos-interface-py /mos-interface-py
RUN cd /mos-interface-py/ && pip install -r requirements.txt && python setup.py install

# Python dependencies
ADD ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt

# MOS compute files
ADD . /mos-compute

# Entrypoint
WORKDIR /mos-compute
ENTRYPOINT ["./workers/worker.py"]