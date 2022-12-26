FROM redhat/ubi8:latest

USER 0

WORKDIR /app

# Necessary to scroll up and down in the python interpreter
# RUN yum install readline-devel -y
# Necessary for bzip compression - we don't use this but could
RUN yum install wget gcc make zlib-devel openssl-devel -y
# Necessary for UUID - I think this is a C implementation of UUID instead of a python implementation
RUN yum install -y uuid libuuid libuuid-devel

ARG DOCKER_PYTHON_VERSION="3.9.16"

# Install Python
RUN wget https://www.python.org/ftp/python/$DOCKER_PYTHON_VERSION/Python-$DOCKER_PYTHON_VERSION.tgz
RUN tar xzf Python-$DOCKER_PYTHON_VERSION.tgz && \
    cd Python-$DOCKER_PYTHON_VERSION && \
    ./configure --enable-optimizations
RUN cd Python-$DOCKER_PYTHON_VERSION && make altinstall

# Create the Python venv
RUN Python-$DOCKER_PYTHON_VERSION/python -m venv /app/habits && \
    chown -R 1001:0 /app/habits


RUN yum install postgresql-devel -y

# Active the virtualenv
ENV PATH=/app/habits/bin:$PATH
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt



# RUN yum install python39 -y



WORKDIR /app/habits/habits

COPY . .


EXPOSE 8000

#CMD ["gunicorn", "habits.app:create_app()"]
CMD python wsgi.py
# 'gunicorn', '--workers=1', '--threads=4', 'habits.app:create_app()', '--reload']