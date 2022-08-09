import os
from mos.interface import Interface

from . import utils
from .kernel import new_kernel

def model_run(model_id, model_name, caller_id):

    backend_host = os.getenv('MOS_BACKEND_HOST', 'localhost')
    backend_port = os.getenv('MOS_BACKEND_PORT', '8000')
    
    # Get kernel
    try:
        if backend_port == '443':
            protocol = 'https'
        else:
            protocol = 'http'
            
        interface = Interface('%s://%s:%s/api/' %(
            protocol, 
            backend_host, 
            backend_port))

        if os.getenv('MOS_ADMIN_TKN') == None:
            token = interface.get_user_token(
                os.getenv('MOS_ADMIN_USR'),
                os.getenv('MOS_ADMIN_PWD'),
            )
        else:
            token = os.getenv('MOS_ADMIN_TKN')
            
        interface.set_token(token)

        model = interface.get_model_with_id(model_id)
        kernel = new_kernel(model, caller_id)

    except Exception as e:
        pusher = utils.PusherClient(caller_id)
        pusher.send(
            {
                'model_id': model_id,
                'model_name': model_name,
                'status': 'error'
            }
        )
        raise e

    # Run model
    kernel.run_model()
