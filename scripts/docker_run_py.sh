#!/bin/bash
sudo docker run -it \
                --rm \
                --network=host \
                --name mos-compute-py \
                mos-compute-py