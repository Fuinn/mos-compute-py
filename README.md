# mos-compute

MOS compute workers.

## Pre-requisites

### Services

* rabbitmq

### Python dependencies

```sudo pip install -r requirements.txt``

### Dependencies Julia

```
    import Pkg
    Pkg.activate(".")
    Pkg.instantiate()
```

### Environment variables

* MOS_BACKEND_HOST
* MOS_BACKEND_PORT
* MOS_RABBIT_PORT
* MOS_RABBIT_USR
* MOS_RABBIT_PWD
* MOS_RABBIT_HOST

## Local Deployment

* Launch a Python worker by executing ``./workers/worker.py``.
* Launch a Julia worker by executing ``./workers/worker.jl``.
