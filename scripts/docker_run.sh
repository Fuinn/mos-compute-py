#!/bin/bash
sudo docker run -it \
                --rm \
                --network=host \
                --env-file=.env \
                --name=mos-compute-py \
                tomastinoco/mos-compute-py