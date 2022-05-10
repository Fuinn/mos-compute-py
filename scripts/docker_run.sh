#!/bin/bash
sudo docker run -it \
                --rm \
                --network=host \
                --env-file=.env \
                --name=mos-demo-compute-py \
                tomastinoco/mos-demo-compute-py