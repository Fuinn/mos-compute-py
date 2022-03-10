import io
import numpy as np

from .kernel import ComputeKernel

class PyomoKernel(ComputeKernel):

    system = 'pyomo'

    def __run_model__(self):

        import pyomo.environ as pyo

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

            instance = scope['instance']
            
            # Extract helper objects
            print('Extracting helper objects')
            for o in model.__get_helper_objects__():

                helper = eval('instance.' + o['name'])

                try:
                    if helper.is_parameter_type():
                        o_pyomo = pyo.value(helper)
                    elif helper.is_indexed():
                        d = helper.extract_values()
                        o_pyomo = {str(key): value for key, value in d.items()}
                    else:
                        o_pyomo = helper.data()
                    model.__set_helper_object__(o,o_pyomo)
                except:
                    print(o['name'], 'is a currently unsupported helper object type')


            # Extract variable states
            print('Extracting variable states')
            var_states = []
            for v in model.__get_variables__():

                variable = eval('instance.' + v['name'])
                
                v_labels = scope[v['labels']] if v['labels'] else {}
                
                if variable.dim() == 0:
                    vtype = 'scalar'
                    vshape = None

                    model.__set_var_type_and_shape__(v, vtype, vshape)
                    var_states.append(dict(
                        variable=v['url'],
                        owner=model.get_owner_id(),
                        index=None,
                        label=v['name'],
                        value=variable.expr()
                        ))
                    
                else:
                    variable_dict = variable.get_values()
                    vtype = 'array'
                    vshape = [len(variable_dict)]
                    

                    if variable.dim() == 2:
                        indices = list(variable_dict.keys())
                        vd = []
                        for j in range(2):
                            vd.append(len(set([i[j] for i in indices])))
                        if vd[0]*vd[1] == len(variable_dict):
                            vshape = [vd[0],vd[1]]
                        else:
                            vshape = [len(variable_dict)]
                        
                    model.__set_var_type_and_shape__(v, vtype, vshape)

                    v_lb = variable._bounds_init_value[0] if variable._bounds_init_value != None else -1e9
                    v_ub = variable._bounds_init_value[1] if variable._bounds_init_value != None else 1e9
                
                    for key in variable_dict:
                        vdomain = eval('instance.'+v['name']+'['+str(key)+'].domain')
                        vkind = 'unknown'
                        if vdomain.to_string() == 'Reals':
                            vkind = 'continuous'
                        elif vdomain.to_string() == 'Binary':
                            vkind = 'binary'
                            v_lb = 0
                            v_ub = 1
                        
                        var_states.append(dict(
                            variable=v['url'],
                            owner=model.get_owner_id(),
                            index=key,
                            label=v_labels[key] if key in v_labels else '',
                            value=variable_dict[key],
                            kind = vkind,
                            upper_bound=v_ub,
                            lower_bound=v_lb
                        ))
                        
            model.__add_variable_states__(var_states)


            # Extract function states
            print('Extracting function states')
            func_states = []
            for f in model.__get_functions__():

                # Extract pyomo function 
                f_pyomo = eval('instance.' + f['name'])
                f_labels = scope[f['labels']] if f['labels'] else {}

                # Expression scalar
                ###################
                if f_pyomo.dim() == 0:
                    ftype = 'scalar'
                    fshape = None
                    model.__set_func_type_and_shape__(f, ftype, fshape)
                    func_states.append(dict(
                        function=f['url'],
                        owner=model.get_owner_id(),
                        index=None,
                        label=f['name'],
                        value=(f_pyomo.expr())
                    ))

                    
                #TODO add array and matrix function capabilities
                        
            model.__add_function_states__(func_states)

            # Extract constraint states
            print('Extracting constraint states')
            constr_states = []
    
            for c in model.__get_constraints__():

                c_labels = scope[c['labels']] if c['labels'] else {}

                c_pyomo = eval('instance.'+c['name'])
                
                if c_pyomo.dim() == 0:
                    ctype = 'scalar'
                    cshape = None
                                
                    try:
                        instance.dual[c_pyomo]
                        exist_dual = True
                    except:
                        exist_dual = False

                    constr_states.append(dict(
                        constraint=c['url'],
                        owner=model.get_owner_id(),
                        index=None,
                        label=c['name'],
                        kind='equality' if c_pyomo.equality else 'inequality',
                        dual=instance.dual[c_pyomo] if exist_dual else 0,
                        violation=0)) # NEED TO FIX

                else:
                    ctype = 'array'
                    cshape = [len(c_pyomo)]
                    
                    if c_pyomo.dim() == 2:
                        indices_c = list(c_pyomo.keys())
                        cd = []
                        for j in range(2):
                            cd.append(len(set([i[j] for i in indices_c])))
                        if cd[0]*cd[1] == len(indices_c):
                            cshape = [cd[0],cd[1]] 

                    for key in c_pyomo:

                        try:
                            instance.dual[c_pyomo[key]]
                            exist_dual = True
                        except:
                            exist_dual = False

                        
                        constr_states.append(dict(
                            constraint=c['url'],
                            owner=model.get_owner_id(),
                            index=key,
                            label=c_labels[key] if key in c_labels else '',
                            kind='equality' if c_pyomo[key].equality else 'inequality',
                            dual=instance.dual[c_pyomo[key]] if exist_dual else 0,
                            violation=0)) # NEED TO FIX

                            
                model.__set_constraint_type_and_shape__(c, ctype, cshape)

            model.__add_constraint_states__(constr_states)


            # Extract problem state
            print('Extracting problem state')

            p = model.__get_problem__()
            
            p_state = dict(problem=p['url'],
                           owner=model.get_owner_id(),
                           num_constraints=instance.nconstraints(),
                           num_vars=instance.nvariables())
            model.__add_problem_state__(p_state)


            # Extract solver state
            print('Extracting solver state')

            s = model.__get_solver__()
            
            s_state = dict(solver=s['url'],
                           owner=model.get_owner_id(),
                           name=scope[s['name']],
                           status=instance.solutions.solutions[0]._metadata['status'],
                           message='',
                           iterations=scope[p['name']]['Solver'][0]['Statistics']['Black box']['Number of iterations'],
                           time=scope[p['name']]['Solver'][0]['Time'],
                           parameters={}
                           )
            
            model.__add_solver_state__(s_state)
            

            
        except Exception as e:

            print('ERROR')
            raise e
            
        finally:

            # Cleanup
            print('Cleaning up local files')
            model.__delete_input_files__()
            model.__delete_input_object_files__()
            model.__delete_output_files__()
            
            
