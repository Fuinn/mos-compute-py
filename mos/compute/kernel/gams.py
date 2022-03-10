import os
import io
import math

from .kernel import ComputeKernel

class GamsKernel(ComputeKernel):

    system = 'gams'

    def __run_model__(self):

        import gams
        import json
        import requests
        import math

        # Locals
        model = self.model

        try:

            #ws = gams.GamsWorkspace(os.getcwd(),'/home/ubuntu/Downloads/gams30.2_linux_x64_64_sfx/',debug=1)
            ws = gams.GamsWorkspace(os.getcwd(),debug=1)
            
            # Get recipe
            print('Getting recipe')
            recipe = io.StringIO()
            model.__write__(recipe, base_path=os.getcwd())

            # Download input files
            print('Downloading input files')
            model.__download_input_files__()

            #print('recipe')
            #model.show_recipe()

            # Execute recipe in isolated scope
            print('Executing model')
            t1 = ws.add_job_from_string(recipe.getvalue())

            # we may want to allow solver designation, feature not finished yet
            newsolver = False
            for item in model.__get_interface_objects__(type='input'):
                if item['name'] == 'solver_designation':
                    r=requests.get(item['data'])
                    opt = ws.add_options()
                    opt.all_model_types = json.loads(r.content)
                    newsolver = True
            if newsolver == True:
                t1.run(opt)
            else:
                t1.run()

            # pull some information from gams listing file
            t1f = t1._file_name
            t1f = t1f.replace('.gms','.lst')
            capture = []
            f = open(t1f,'r')
            for i in range(10000):
                j=f.readline()
                if 'S O L V E' in j:
                    capture.append(j)
                    for k in range(10):
                        capture.append(f.readline())
                    break
            f.close()

            ptype = capture[3].split()[1]
            psolver = capture[4].split()[1]

            # Extract context objects
            # need to distinguish below between gams parameters and sets
            print('Extracting context objects')
            for o in model.__get_helper_objects__():
                tmp = []
                o_gams = t1.out_db[o['name']]
                if isinstance(o_gams, gams.database.GamsParameter):
                    for i in o_gams:
                        tmp.append(str(i.keys)+': '+str(i.value))
                elif isinstance(o_gams, gams.database.GamsSet):
                    for i in o_gams:
                        tmp.append(str(i.keys))
                else:
                    print('unknown helper object')

                model.__set_helper_object__(o, tmp)
            
            # Extract variable states
            print('Extracting variable states')
            var_states = []
            for v in model.__get_variables__():
                
                # Extract gams var from gams python api
                v_gams = t1.out_db[v['name']]

                if isinstance(v_gams, gams.database.GamsVariable):
                    if v_gams.dimension == 0:
                        vtype = 'scalar'
                        vshape = None
                    elif v_gams.dimension == 1:
                        vtype = 'array'
                        vshape = [len(v_gams)]
                    elif v_gams.dimension == 2:
                        vtype = 'array'
                        vd = [len(v_gams.domains[0]), len(v_gams.domains[1])]                                  
                        if vd[0]*vd[1] == len(v_gams):
                            vshape = [vd[0],vd[1]]
                        else:
                            vshape = [len(v_gams)]
                    else:
                        vtype = 'array'
                        vshape = [len(v_gams)]
                        
                    model.__set_var_type_and_shape__(v, vtype, vshape)

                    if v_gams.vartype == 1:
                        kind_v = 'binary'
                    elif v_gams.vartype == 2:
                        kind_v = 'integer'
                    elif 3 <= v_gams.vartype <= 5:
                        kind_v = 'continuous'
                    else:
                        kind_v = 'unknown'

                    
                    for i in enumerate(v_gams):
                        if v_gams.dimension == 0:
                            ind = None
                        elif v_gams.dimension == 2:
                            if vd[0]*vd[1] == len(v_gams):
                                floor = math.floor(i[0]/vd[1])
                                ind = [floor, i[0]-floor*vd[1]]
                            else:
                                ind = i[0]
                        else:
                            ind = i[0]

                        label = str(i[1].keys) if len(v_gams) > 1 else v['name']
                        if str(i[1].upper)=='inf':
                            ub=1e9
                        else:
                            ub=i[1].upper
                        if str(i[1].lower)=='-inf':
                            lb=-1e9
                        else:
                            lb=i[1].lower
                        var_states.append(dict(
                            variable=v['url'],
                            owner=model.get_owner_id(),
                            index=ind,
                            label=label,
                            kind=kind_v,
                            value=i[1].level,
                            upper_bound=ub,   
                            lower_bound=lb))
                        
                # Unknown
                else:
                    raise TypeError('invalid variable type')
            model.__add_variable_states__(var_states)

            # Extract function states from gams python api
            print('Extracting function states')
            func_states = []
            for f in model.__get_functions__():
                # Extract gams functions
                f_gams = t1.out_db[f['name']]
                if f_gams.dimension == 0:
                    ftype = 'scalar'
                    fshape = None
                elif f_gams.dimension == 1:
                    ftype = 'array'
                    fshape = [len(f_gams)]
                elif f_gams.dimension == 2:
                    ftype = 'array'
                    fd = [len(f_gams.domains[0]), len(f_gams.domains[1])]
                    if fd[0] * fd[1] == len(f_gams):
                           fshape = [fd[0], fd[1]]
                    else:
                           fshape = [len(f_gams)]
                else:
                    ftype = 'array'
                    fshape = [len(f_gams)]
                           
                    
                model.__set_func_type_and_shape__(f, ftype, fshape)                


                # Expression
                if isinstance(f_gams, gams.database.GamsParameter):
                    for i in enumerate(f_gams):

                        if f_gams.dimension == 0:
                            ind = None
                        elif f_gams.dimension == 2:
                            if fd[0]*fd[1] == len(f_gams):
                                floor = math.floor(i[0]/fd[1])
                                ind = [floor, i[0]-floor*fd[1]]
                            else:
                                ind = i[0]
                        else:
                            ind = i[0]
                        
                        label = str(i[1].keys) if len(f_gams) > 1 else f['name']
                        
                        func_states.append(dict(
                            function=f['url'],
                            owner=model.get_owner_id(),
                            index=ind,
                            label=label, 
                            value=i[1].value))
                else:
                    print('unknown function type in GAMS kernel')
                    raise TypeError('invalid function type')

            model.__add_function_states__(func_states)               

            # Extract constraint states
            print('Extracting constraint states')
            constr_states = []
            for c in model.__get_constraints__():

                # Extract gams constraint from scope
                c_gams = t1.out_db[c['name']]
                if c_gams.dimension==0:
                    ctype = 'scalar'
                    cshape = None
                elif c_gams.dimension==1:
                    ctype = 'array'
                    cshape = [len(c_gams)]
                elif c_gams.dimension==2:
                    ctype = 'array'
                    cd = [len(c_gams.domains[0]), len(c_gams.domains[1])]
                    if cd[0] * cd[1] == len(c_gams):
                        cshape = [cd[0], cd[1]]
                    else:
                        cshape = [len(c_gams)]
                else:
                        ctype = 'array'
                        cshape = [len(c_gams)]                    
                    
                model.__set_constraint_type_and_shape__(c, ctype ,cshape)                
                if isinstance(c_gams, gams.database.GamsEquation):
                    for i in enumerate(c_gams):
                        
                        if c_gams.dimension == 0:
                            ind = None
                        elif c_gams.dimension == 2:
                            if cd[0]*cd[1] == len(c_gams):
                                floor = math.floor(i[0]/cd[1])
                                ind = [floor, i[0]-floor*cd[1]]
                            else:
                                ind = i[0]
                        else:
                            ind = i[0]
                        
                        label = str(i[1].keys) if len(c_gams) > 1 else c['name']
                        
                        ckind = 'equality' if c_gams._equtype == 0 else 'inequality'
                        
                        constr_states.append(dict(
                            constraint=c['url'],
                            owner=model.get_owner_id(),
                            index=ind,
                            label=label,
                            dual=i[1].marginal,
                            kind=ckind,
                            violation=0)) # NEED TO FIX
                else:
                    raise TypeError('invalid constraint type')

            model.__add_constraint_states__(constr_states)

            
            # Extract problem state
            print('Extracting problem state')
            if model.has_problem():
                num_rows = 0
                num_columns = 0
                for i in t1.out_db:
                    if isinstance(i, gams.database.GamsVariable):
                        num_columns += i.get_number_records()
                    elif isinstance(i,gams.database.GamsEquation):
                        num_rows += i.get_number_records()
                
                p = model.__get_problem__()

                p_value = t1.out_db['solver'].find_record('objective').value
                p_state = dict(problem=p['url'],
                               owner=model.get_owner_id(),
                               kind=ptype.lower(),
                               num_constraints=num_rows,
                               num_vars=num_columns)
                model.__add_problem_state__(p_state)

            # Extract solver state
            if model.has_solver() and model.has_problem():
                s = model.__get_solver__()
                s_gams = t1.out_db['solver']
                if math.isnan(s_gams.find_record('iterations').value):
                    checkiter = 0
                else:
                    checkiter = s_gams.find_record('iterations').value
                    
                s_state = dict(solver=s['url'],
                           name = psolver,
                           owner=model.get_owner_id(),    
                           #status=s_gams.find_record('status').value,
                           status=capture[7].split()[4],
                           time=s_gams.find_record('time').value,
                           iterations=checkiter)
            model.__add_solver_state__(s_state)

            # Extract output files
            # For now we will not deal with output GDX files
            print('Extracting output files')
            for f in model.__get_interface_files__(type='output'):
                model.__set_interface_file__(f, f['name']+f['extension'])
            
            # Extract output objects
            print('Extracting output objects')
            for o in model.__get_interface_objects__(type='output'):
                tmp = []
                o_gams = t1.out_db[o["name"]]
                for i in o_gams:
                    tmp.append(str(i.keys)+': '+str(i.value))
                model.__set_interface_object__(o, tmp)
    
        except Exception as e:

            print('ERROR')
            raise e

        finally:

            # Cleanup
            print('Cleaning up local files')
            model.__delete_input_files__()
            model.__delete_output_files__()
            
