import io
import numpy as np

from .kernel import ComputeKernel

class CvxpyKernel(ComputeKernel):

    system = 'cvxpy'

    def __run_model__(self):

        import cvxpy
        from cvxpy.expressions.variable import Variable
        from cvxpy.constraints import Equality, Inequality
        from cvxpy.expressions.expression import Expression

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
                o_cvxpy = scope[o['name']]
                if type(o_cvxpy) == np.ndarray:
                    model.__set_helper_object__(o, o_cvxpy.tolist())
                else:
                    if type(o_cvxpy) == list:
                        # Want to check if any elements in list are ndarrays
                        # If they are, want to make those elements JSON serializable
                        for key,item in enumerate(o_cvxpy):
                            if type(item) == np.ndarray:
                                o_cvxpy[key] = item.tolist()
                                
                    model.__set_helper_object__(o, o_cvxpy)
            
            # Extract variable states
            print('Extracting variable states')
            var_states = []
            for v in model.__get_variables__():

                # Extract var from scope
                v_cvxpy = scope[v['name']]
                v_labels = scope[v['labels']] if v['labels'] else {}

                if not isinstance(v_cvxpy,list):
                    if v_cvxpy.is_nonneg():
                        lb = 0
                    else:
                        lb = -1e9
                    ub = 1e9
                    # Kinds (needs to be improved to check each component)
                    if len(v_cvxpy.boolean_idx) > 0:
                        kind_v = 'binary'
                        lb = 0
                        ub = 1
                    elif len(v_cvxpy.integer_idx) > 0:
                        kind_v = 'integer'
                    else:
                        kind_v = 'continuous'

                # Variable scalar
                #################
                if isinstance(v_cvxpy, Variable) and v_cvxpy.is_scalar():

                    # Type and shape
                    model.__set_var_type_and_shape__(v, 'scalar', None)

                    # Value
                    vtemp = v_cvxpy.value.tolist()
                    if isinstance(vtemp, float):
                        vv = v_cvxpy.value.tolist()
                    elif isinstance(vtemp, list):
                        vv = vtemp[0]
                    else:
                        raise ValueError('unable to get scalar variable value')
                        
                    # State
                    var_states.append(dict(
                        variable=v['url'],
                        owner=model.get_owner_id(),
                        index=None,
                        label=v['name'],
                        value=vv,
                        kind=kind_v,
                        upper_bound=ub,
                        lower_bound=lb))

                # Vector
                ########
                elif isinstance(v_cvxpy, Variable) and v_cvxpy.is_vector():

                    # Type and shape
                    model.__set_var_type_and_shape__(v, 'array', [v_cvxpy.size])
                     
                    # States
                    for i in range(v_cvxpy.size):
                        var_states.append(dict(
                            variable=v['url'],
                            owner=model.get_owner_id(),
                            index=[i],
                            label=v_labels[i] if i in v_labels else '',
                            value=v_cvxpy.value[i],
                            kind=kind_v,
                            upper_bound=ub,
                            lower_bound=lb))

                # Matrix 
                ########
                elif isinstance(v_cvxpy, Variable) and v_cvxpy.is_matrix():
                    
                    # Type and shape
                    model.__set_var_type_and_shape__(v, 
                                                     'array',
                                                     list(v_cvxpy.shape))
                    
                    # States
                    for i in range(v_cvxpy.shape[0]):
                        for j in range(v_cvxpy.shape[1]):
                            var_states.append(dict(
                                variable=v['url'],
                                owner=model.get_owner_id(),
                                index=[i,j],
                                label=v_labels[(i,j)] if (i,j) in v_labels else '',
                                kind=kind_v,
                                value=v_cvxpy.value[i][j],
                                upper_bound=ub,
                                lower_bound=lb))


                # List
                ########
                elif isinstance(v_cvxpy,list) and all([isinstance(i, Variable) for i in v_cvxpy]):
                    # Type and shape
                    shape = []
                    for item in v_cvxpy:
                        if item.is_scalar():
                            shape.append(1)
                        else:
                            shape.append(item.size)
                        
                    # Array is closest allowed type to list for now
                    model.__set_var_type_and_shape__(v, 
                                                     'array',
                                                     shape)
                    ub=1e9
                    lb=-1e9
                    kind_v='continuous'
                    for i,item in enumerate(v_cvxpy):
                        v_labels_local = v_labels[i] if i in v_labels else {}
                        if item.is_nonneg():
                            lb = 0
                        if len(item.boolean_idx) > 0:
                            kind_v = 'binary'
                            lb = 0
                            ub = 1
                        elif len(item.integer_idx) > 0:
                            kind_v = 'integer'
                        else:
                            kind_v = 'continuous'
                            
                        if item.is_scalar():
                            var_states.append(dict(
                                variable=v['url'],
                                owner=model.get_owner_id(),
                                index=[i],
                                label=v_labels_local if not isinstance(v_labels,dict) else '',
                                value=item.value,
                                kind=kind_v,
                                upper_bound=ub,
                                lower_bound=lb))                            
                        elif item.is_vector():
                            for j in range(item.size):
                                var_states.append(dict(
                                    variable=v['url'],
                                    owner=model.get_owner_id(),
                                    index=[i,j],
                                    label=v_labels_local[j] if j in v_labels_local else '',
                                    value=item.value[j],
                                    kind=kind_v,
                                    upper_bound=ub,
                                    lower_bound=lb))                                
                        elif item.is_matrix():
                            for j in range(item.size[0]):
                                for k in range(item.size[1]):
                                    var_states.append(dict(
                                        variable=v['url'],
                                        owner=model.get_owner_id(),
                                        index=[i,j,k],
                                        label=v_labels_local[(j,k)] if (j,k) in v_labels_local else '',
                                        value=item.value[j][k],
                                        kind=kind_v,
                                        upper_bound=ub,
                                        lower_bound=lb))                                                        

                # Unknown
                #########
                else:
                    raise TypeError('invalid variable type')

            model.__add_variable_states__(var_states)

            # Extract function states
            print('Extracting function states')
            func_states = []
            for f in model.__get_functions__():

                # Extract cvxpy function from scope
                f_cvxpy = scope[f['name']]
                f_labels = scope[f['labels']] if f['labels'] else {}

                # Expression scalar
                ###################
                if isinstance(f_cvxpy, Expression) and f_cvxpy.is_scalar():
                    model.__set_func_type_and_shape__(f, 'scalar', None)
                    func_states.append(dict(
                        function=f['url'],
                        owner=model.get_owner_id(),
                        index=None,
                        label=f['name'],
                        value=float(f_cvxpy.value)))

                # Expression vector
                ###################
                elif isinstance(f_cvxpy, Expression) and f_cvxpy.is_vector():
                    model.__set_func_type_and_shape__(f, 
                                                      'array',
                                                      [f_cvxpy.size])
                    for i in range(f_cvxpy.size):
                        func_states.append(dict(
                            function=f['url'],
                            owner=model.get_owner_id(),
                            index=[i],
                            label=f_labels[i] if i in f_labels else '',
                            value=float(f_cvxpy.value[i])))

                # Expression matrix
                ###################
                elif isinstance(f_cvxpy, Expression) and f_cvxpy.is_matrix():
                    model.__set_func_type_and_shape__(f, 
                                                      'array',
                                                      list(f_cvxpy.shape))
                    for i in range(f_cvxpy.shape[0]):
                        for j in range(f_cvxpy.shape[1]):
                            func_states.append(dict(
                                function=f['url'],
                                owner=model.get_owner_id(),
                                index=[i,j],
                                label=f_labels[(i,j)] if (i,j) in f_labels else '',
                                value=float(f_cvxpy.value[i][j])))

                # Expression list
                ###################
                elif isinstance(f_cvxpy,list) and all([isinstance(i, Expression) for i in f_cvxpy]):
                    shape = []
                    for item in f_cvxpy:
                        if item.is_scalar():
                            shape.append(1)
                        else:
                            shape.append(item.size)
                    model.__set_func_type_and_shape__(f,'array',shape)

                    for i,item in enumerate(f_cvxpy):
                        f_labels_local = f_labels[i] if i in f_labels else {}

                        if item.is_scalar():
                            func_states.append(dict(
                                function=f['url'],
                                owner=model.get_owner_id(),
                                index=[i],
                                label=f_labels_local if not isinstance(f_labels,dict) else '',
                                value=item.value))
                        elif item.is_vector():
                            for j in range(item.size):
                                func_states.append(dict(
                                    function=f['url'],
                                    owner=model.get_owner_id(),
                                    index=[i,j],
                                    label=f_labels_local[j] if j in f_labels_local else '',
                                    value=item.value[j]))
                        elif item.is_matrix():
                            for j in range(item.shape[0]):
                                for k in range(item.shape[1]):
                                    func_states.append(dict(
                                        function=f['url'],
                                        owner=model.get_owner_id(),
                                        index=[i,j,k],
                                        label=f_labels_local[(j,k)] if (j,k) in f_labels_local else '',
                                        value=item.value[j][k]))
                            
                # Unknown
                #########
                else:
                    raise TypeError('invalid function type')

            model.__add_function_states__(func_states)

            # Extract constraint states
            print('Extracting constraint states')
            constr_states = []
            for c in model.__get_constraints__():

                # Extract cvxpy constraint from scope
                c_cvxpy = scope[c['name']]
                c_labels = scope[c['labels']] if c['labels'] else {}

                if isinstance(c_cvxpy, Equality):
                    kind = 'equality'
                elif isinstance(c_cvxpy, Inequality):
                    kind = 'inequality'
                else:
                    raise ValueError('unsupported constraint type')

                # Constraint scalar
                ###################
                if c_cvxpy.size == 1:

                    if c_cvxpy.dual_value is None:
                        ccdv = 0
                    else:
                        ccdv = c_cvxpy.dual_value

                    viol = c_cvxpy.violation()
                        
                    model.__set_constraint_type_and_shape__(c, 
                                                            'scalar',
                                                            None)

                    constr_states.append(dict(
                        constraint=c['url'],
                        owner=model.get_owner_id(),
                        index=None,
                        label=c['name'],
                        kind=kind,
                        dual=ccdv if type(ccdv) != np.ndarray else ccdv[0],
                        violation=viol if type(viol) != np.ndarray else viol[0]))                        

                # Constraint array 1d
                #####################
                elif len(c_cvxpy.shape) == 1:
                    if c_cvxpy.dual_value is None:
                        ccdv = np.zeros(c_cvxpy.shape)                        
                    elif not c_cvxpy.dual_value.any():
                        ccdv = np.zeros(c_cvxpy.shape)
                    else:
                        ccdv = c_cvxpy.dual_value
                    model.__set_constraint_type_and_shape__(c, 
                                                            'array',
                                                            [c_cvxpy.size])
                                
                    for i in range(c_cvxpy.size):
                        constr_states.append(dict(
                            constraint=c['url'],
                            owner=model.get_owner_id(),
                            index=[i],
                            label=c_labels[i] if i in c_labels else '',
                            kind=kind,
                            dual=ccdv[i],
                            violation=c_cvxpy.violation()[i]))

                # Constraint array 2d
                #####################
                elif len(c_cvxpy.shape) == 2:
                    if c_cvxpy.dual_value is None:
                        ccdv = np.zeros(c_cvxpy.shape)                        
                    elif not c_cvxpy.dual_value.any():
                        ccdv = np.zeros(c_cvxpy.shape)
                    else:
                        ccdv = c_cvxpy.dual_value
 
                    model.__set_constraint_type_and_shape__(c, 
                                                            'array',
                                                            list(c_cvxpy.shape))
                                
                    for j in range(c_cvxpy.shape[0]):
                        for k in range(c_cvxpy.shape[1]):                                
                            constr_states.append(dict(
                                constraint=c['url'],
                                owner=model.get_owner_id(),
                                index=[j,k],
                                label=c_labels[(j,k)] if (j,k) in c_labels else '',
                                kind=kind,
                                dual=ccdv[j][k],
                                violation=c_cvxpy.violation()[j][k]))

                # Unknown
                #########
                else:
                    raise TypeError('unsupported constraint structure')

            model.__add_constraint_states__(constr_states)

            # Extract problem state
            print('Extracting problem state')
            if model.has_problem():
                p = model.__get_problem__()
                p_cvxpy = scope[p['name']]

                metrics = cvxpy.problems.problem.SizeMetrics(p_cvxpy)

                if p_cvxpy.is_mixed_integer():
                    problem_type = 'mip'
                elif p_cvxpy.is_dcp():
                    problem_type = 'convex'
                else:
                    problem_type = 'unknown'

                p_state = dict(problem=p['url'],
                               owner=model.get_owner_id(),
                               kind=problem_type,
                               num_constraints=int(metrics.num_scalar_eq_constr + metrics.num_scalar_leq_constr), 
                               num_vars=int(metrics.num_scalar_variables))
                model.__add_problem_state__(p_state)

            # Extract solver state
            print('Extracting solver state')
            if model.has_solver() and model.has_problem():
                s = model.__get_solver__()
                s_cvxpy = scope[s['name']]
                
                numiters = p_cvxpy.solver_stats.num_iters
                time_recorded = p_cvxpy.solver_stats.solve_time
                    
                s_state = dict(solver=s['url'],
                               owner=model.get_owner_id(),
                               name=s_cvxpy if isinstance(s_cvxpy, str) else 'unknown',
                               status=p_cvxpy.status,
                               message='',
                               iterations=numiters if numiters != None else 0,
                               time=time_recorded if time_recorded != None else 0,
                               parameters={})
                model.__add_solver_state__(s_state)

            # Extract output files
            print('Extracting output files')
            for f in model.__get_interface_files__(type='output'):
                model.__set_interface_file__(f, f['name']+f['extension'])

            # Extract output objects
            print('Extracting output objects')
            for o in model.__get_interface_objects__(type='output'):
                o_cvxpy = scope[o['name']]
                model.__set_interface_object__(o, o_cvxpy)

        except Exception as e:

            print('ERROR')
            raise e
            
        finally:

            # Cleanup
            print('Cleaning up local files')
            model.__delete_input_files__()
            model.__delete_input_object_files__()
            model.__delete_output_files__()
