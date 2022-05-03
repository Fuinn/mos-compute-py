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

## Local Deployment

Launch a Python worker by executing ``./workers/worker.py``.

## Docker Deployment

The following scripts are available for building the image, running the container, and for pushing the image to Docker Hub:

* ``./scripts/docker_build.sh``
* ``./scripts/docker_run.sh``
* ``./scripts/docker_push.sh``
