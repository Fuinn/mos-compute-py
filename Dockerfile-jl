FROM julia:1.5.3

LABEL "app.name"="MOS Compute Julia"

# MOS compute files
ADD . /mos-compute
WORKDIR /mos-compute

# Julia dependencies
RUN julia -e 'import Pkg; Pkg.activate("."); Pkg.instantiate(); Pkg.status()'

# Entrypoint
ENTRYPOINT ["./workers/worker.jl"]