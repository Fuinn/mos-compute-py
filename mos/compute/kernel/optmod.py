import io

from .kernel import ComputeKernel
 
class OptmodKernel(ComputeKernel):

    system = 'optmod'

    def __run_model__(self):

        import optmod

        # Locals
        model = self.model

        try:

            # Get recipe
            print('Getting recipe')
            recipe = io.StringIO()
            model.__write__(recipe)
            
            # Download input files
            print('Downloading input files')
            model.__download_input_files__()

            # Download input object files
            print('Downloading input object files')
            model.__download_input_object_files__()

            # Execute recipe in isolated scope
            print('Executing model')
            scope = {}
            exec(recipe.getvalue(), scope, scope)

            # Extract helper objects
            print('Extracting helper objects') 
            for o in model.__get_helper_objects__():
                o_optmod = scope[o['name']]
                model.__set_helper_object__(o, o_optmod)
 
            # Extract variable states
            print('Extracting variable states')
            var_states = []
            for v in model.__get_variables__():
                
                # Extract optmod var from scope
                v_optmod = scope[v['name']]
                v_labels = scope[v['labels']] if v['labels'] else {}

                # Variable scalar
                #################

                # Variable array
                ################

                # Variable hashmap
                ##################
                if isinstance(v_optmod, optmod.variable.VariableDict):

                    # Type and shape
                    model.__set_var_type_and_shape__(v,  
                                                     'hashmap', 
                                                     [len(v_optmod)])

                    # States
                    for key in v_optmod.keys():
                        vs = v_optmod[key]
                        if vs.type == 'continuous':
                            kind = 'continuous'
                        elif vs.type == 'integer':
                            kind = 'integer'
                        else:
                            kind = 'unknown'
                        var_states.append(dict(
                            variable=v['url'],
                            owner=model.get_owner_id(),
                            index=key,
                            label=v_labels[key] if key in v_labels else '',
                            kind=kind,
                            value=vs.get_value(),
                            upper_bound=0.,
                            lower_bound=0.))

                # Unknown
                #########
                else:
                    raise TypeError('invalid variable type')

            model.__add_variable_states__(var_states)

            # Extract function states
            print('Extracting function states')
            func_states = []
            for f in model.__get_functions__():

                # Extract optmod function from scope
                f_optmod = scope[f['name']]

                # Expression scalar
                ###################
                if isinstance(f_optmod, optmod.expression.Expression):
                    model.__set_func_type_and_shape__(f, 'scalar', None)
                    func_states.append(dict(
                        function=f['url'],
                        owner=model.get_owner_id(),
                        index=None,
                        label=f['name'],
                        value=f_optmod.get_value()))

                # Expression array
                ##################

                # Expression hashmap
                ####################

                # Unknown
                #########
                else:
                    raise TypeError('invalid function type')
            model.__add_function_states__(func_states)

            # Extract constraint states
            print('Extracting constraint states')
            constr_states = []
            for c in model.__get_constraints__():

                # Extract optmod constraint from scope
                c_optmod = scope[c['name']]
                c_labels = scope[c['labels']] if c['labels'] else {}

                # Constraint scalar
                ###################

                # Constraint array
                ##################

                # Constraint hashmap
                ####################

                # Constraint list
                #################
                if isinstance(c_optmod, list):
                    model.__set_constraint_type_and_shape__(c, 
                                                            'array',
                                                            [len(c_optmod)])
                    for i, cc in enumerate(c_optmod):
                        constr_states.append(dict(
                            constraint=c['url'],
                            owner=model.get_owner_id(),
                            index=[i],
                            label=c_labels[i] if i in c_labels else '',
                            kind='equality' if cc.op == '==' else 'inequality',
                            dual=cc.get_dual(),
                            violation=cc.get_violation()))
                else:
                    raise TypeError('invalid constraint type')
            model.__add_constraint_states__(constr_states)

            # Extract solver state
            print('Extracting solver state')
            if model.has_solver():
                s = model.__get_solver__()
                s_optmod = scope[s['name']]
                s_state = dict(solver=s['url'],
                               owner=model.get_owner_id(),
                               name=s_optmod.__class__.__name__,
                               status=s_optmod.get_status(),
                               message='',
                               iterations=s_optmod.get_iterations(),
                               time=0.,
                               parameters=s_optmod.parameters)
                model.__add_solver_state__(s_state)

            # Extract problem state
            print('Extracting problem state')
            if model.has_problem():
                p = model.__get_problem__()
                p_optmod = scope[p['name']]
                p_state = dict(
                    problem=p['url'],
                    owner=model.get_owner_id())
                model.__add_problem_state__(p_state)

            # Extract output files
            print('Extracting output files')
            for f in model.__get_interface_files__(type='output'):
                model.__set_interface_file__(f, f['name']+f['extension'])

            # Extract output objects
            print('Extracting output objects')
            for o in model.__get_interface_objects__(type='output'):
                o_optmod = scope[o['name']]
                model.__set_interface_object__(o, o_optmod)

        except Exception as e:

            print('ERROR')
            raise e

        finally:

            # Cleanup
            print('Cleaning up local files')
            model.__delete_input_files__()
            model.__delete_input_object_files__()
            model.__delete_output_files__()
