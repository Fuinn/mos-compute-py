# mos-compute

MOS compute workers.

## Pre-requisites

### Services

* rabbitmq

### Python dependencies

```sudo pip install -r requirements.txt```

### Julia Dependencies

```
import Pkg
Pkg.activate(".")
Pkg.instantiate()
```

### Environment variables

The following environment variables can be specified. They can be provided via a .env file.

* MOS_BACKEND_HOST
* MOS_BACKEND_PORT
* MOS_BACKEND_TOKEN
* MOS_RABBIT_PORT
* MOS_RABBIT_USR
* MOS_RABBIT_PWD
* MOS_RABBIT_HOST

The backend TOKEN shoud be from an admin user.

## Local Deployment

* Launch a Python worker by executing ``./workers/worker.py``.
* Launch a Julia worker by executing ``./workers/worker.jl``.

## Docker Deployment

Launch a dockerized Python worker using
* ``./scripts/docker_build_py.sh``
* ``./scripts/docker_run_py.sh``

Launch a dockerized Julia worker using
* ``./scripts/docker_build_jl.sh``
* ``./scripts/docker_run_jl.sh``
