from .optmod import OptmodKernel
from .cvxpy import CvxpyKernel
from .gams import GamsKernel
from .pyomo import PyomoKernel

kernels = [OptmodKernel, CvxpyKernel, GamsKernel, PyomoKernel]

def new_kernel(model, caller_id):

    for kernel in kernels:
        if kernel.system == model.get_system():
            return kernel(model, caller_id)
    else:
        raise ValueError("Unsupported modeling system %s" %model.get_system())
