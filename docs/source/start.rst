.. _start:

.. role:: bash(code)
	  :language: bash


********
Getting Started
********


^^^^^^^^^^^^^^^  
 Pre-requisites
^^^^^^^^^^^^^^^   

* `MOS Compute` is currently configured for systems with `Ubuntu 18.04` as a local environment.
* Install Python 3.6.8 or greater
* Install Julia 1.0.4 or greater
* Install `rabbitmq-server` from the package manager and make sure you have `rabbitmq-server` service running. 

^^^^^^^^^^^^^^^  
 Dependencies
^^^^^^^^^^^^^^^  

---------------  
 Python
---------------   

Install dependencies with `sudo pip3 install -r requirements.txt`.

---------------  
 Julia
---------------   


Enter the Julia interpreter and type the following

* :bash:`import Pkg`
* :bash:`Pkg.activate(".")`
* :bash:`Pkg.instantiate()`

^^^^^^^^^^^^^^^
 Launching
^^^^^^^^^^^^^^^

* Launch the Python worker by executing :bash:`./workers/worker.py`.
* Launch the Julia worker by executing :bash:`./workers/worker.jl`.
