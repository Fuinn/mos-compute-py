# mos-compute-py

MOS Python compute worker.

## Pre-requisites

### Services

* rabbitmq
* mos-backend

### Dependencies

```sudo pip install -r requirements.txt```

### Environment variables

The following environment variables can be specified. They can be provided via a .env file.

* MOS_BACKEND_HOST:
* MOS_BACKEND_PORT:
* MOS_ADMIN_USR:
* MOS_ADMIN_PWD:
* MOS_RABBIT_PORT:
* MOS_RABBIT_USR:
* MOS_RABBIT_PWD:
* MOS_RABBIT_HOST:
* MOS_COMPUTE_CONN_RETRIES_INT:
* MOS_COMPUTE_CONN_RETRIES_MAX:

### Configuration for MOS Demo

To enable a compute worker to work with the [MOS demo](https://github.com/Fuinn/mos-demo) on the same machine, specify the following values:

* MOS_BACKEND_HOST=localhost
* MOS_BACKEND_PORT=8000
* MOS_ADMIN_USR=mos
* MOS_ADMIN_PWD=demo
* MOS_RABBIT_PORT=5672  
* MOS_RABBIT_USR=guest
* MOS_RABBIT_PWD=guest
* MOS_RABBIT_HOST=localhost

## Local Deployment

Launch a Python worker by executing ``./workers/worker.py``.

## Docker Deployment

The following scripts are available for building the image, running the container, and for pushing the image to Docker Hub:

* ``./scripts/docker_build.sh``
* ``./scripts/docker_run.sh``
* ``./scripts/docker_push.sh``
