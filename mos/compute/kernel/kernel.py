import io
import traceback
from contextlib import redirect_stderr, redirect_stdout

from .. import utils

class ComputeKernel:

    system = None

    def __init__(self, model, caller_id):

        self.model = model
        self.caller_id = caller_id

        self.pusher = utils.PusherClient(caller_id)

    def run_model(self): 

        # Running
        self.model.__set_status__('running')
        self.pusher.send(
            {
                'model_id': self.model.get_id(),
                'model_name': self.model.get_name(),
                'status': 'running',
            }
        )

        # Run
        s = io.StringIO()
        try:

            # Execute custom kernel code
            with redirect_stdout(s), redirect_stderr(s):
                self.__run_model__()
        
            # Log
            self.model.__set_execution_log__(s.getvalue())

            # Success
            self.model.__set_status__('success')
            self.pusher.send(
                {
                    'model_id': self.model.get_id(),
                    'model_name': self.model.get_name(),
                    'status': 'success'
                }
            )

        except Exception:

            s.write('\n')
            s.write('Kernel traceback:\n')
            traceback.print_exc(file=s)
            
            # Log
            self.model.__set_execution_log__(s.getvalue())

            # Error
            self.model.__set_status__('error')
            self.pusher.send(
                {
                    'model_id': self.model.get_id(),
                    'model_name': self.model.get_name(),
                    'status': 'error'
                }
            )

        finally:

            print(s.getvalue())

    def __run_model__(self):

        raise NotImplementedError()
