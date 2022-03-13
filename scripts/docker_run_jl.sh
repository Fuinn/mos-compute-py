#!/bin/bash
sudo docker run -it \
                --rm \
                --network=host \
                --name mos-compute-jl \
                mos-compute-jl