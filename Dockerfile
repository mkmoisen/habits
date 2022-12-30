FROM amazonlinux:latest

USER 0

WORKDIR /app

# Necessary to scroll up and down in the python interpreter
RUN yum install readline-devel -y
# Necessary for bzip compression - we don't use this but could
RUN yum install wget gcc make zlib-devel openssl-devel -y
# Necessary for UUID - I think this is a C implementation of UUID instead of a python implementation
RUN yum install -y uuid libuuid libuuid-devel

# Necessary for psql
RUN yum install -y postgresql

# For psycopg2
RUN yum install postgresql-devel -y

# Amazon Linux activities to install python from source
RUN yum remove openssl openssl-devel -y
RUN yum install tar gzip openssl11 openssl11-devel bzip2-devel libffi-devel -y

ARG DOCKER_PYTHON_VERSION="3.11.1"

# Install Python
RUN wget https://www.python.org/ftp/python/$DOCKER_PYTHON_VERSION/Python-$DOCKER_PYTHON_VERSION.tgz

CMD sleep 5000
RUN tar xzf Python-$DOCKER_PYTHON_VERSION.tgz && \
    cd Python-$DOCKER_PYTHON_VERSION && \
    ./configure --enable-optimizations
RUN cd Python-$DOCKER_PYTHON_VERSION && make altinstall

# Create the Python venv
RUN Python-$DOCKER_PYTHON_VERSION/python -m venv /app/habits && \
    chown -R 1001:0 /app/habits


# Active the virtualenv
ENV PATH=/app/habits/bin:$PATH
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt


WORKDIR /app/habits/habits

COPY . .

CMD ["gunicorn", "habits.app:create_app()", "--workers=1", "--threads=4", "--bind", "0.0.0.0:80"]
# CMD python wsgi.py