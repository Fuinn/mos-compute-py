import HTTP
import JSON
import Cbc
import Clp
import JuMP
import WebSockets
import MathOptInterface

using Suppressor
using MOSInterface

const MOI = MathOptInterface
correct_url = MOSInterface.correct_url

function model_run(model_id::Int64, model_name::String, caller_id::Int64)

    # Interface
    println("Creating interface")
    interface = MOSInterface.Interface(get_backend_url())

    # Token
    usr, pwd = get_admin_credentials()
    token = get_user_token(interface, usr, pwd)
    set_token!(interface, token)

    # Model
    println("Getting model")
    model = get_model(interface, model_id)

    # Status
    MOSInterface.__set_status__(model, "running")
    push_notification(caller_id, Dict(
        "model_id" => model_id,
        "model_name" => model_name,
        "status" => "running",
    ))

    # Execution log
    io = IOBuffer()

    try

        # Get recipe
        writeln(io, "Getting recipe")
        recipe = IOBuffer()
        MOSInterface.__write__(model, recipe)
        recipe = String(take!(recipe))

        # Download input files
        writeln(io, "Downloading input files")
        MOSInterface.__download_input_files__(model)

        # Download input object files
        writeln(io, "Downloading input object files")
        MOSInterface.__download_input_object_files__(model)

        # Execute recipe in isolated scope
        writeln(io, "Executing model")
        m = Module();
        output = @capture_out begin
            include_string(m, recipe);
            Base.Libc.flush_cstdio()   # Crazy fix
        end
        writeln(io, output)

        # Extract model
        model_jump = getfield(m, Symbol(MOSInterface.__get_problem__(model)["name"]))

        # Flags
        has_values = JuMP.has_values(model_jump)
        has_duals = JuMP.has_duals(model_jump)
        integer_switch = false

        # Extract context objects
        writeln(io, "Extracting contexts objects")
        for o in MOSInterface.__get_helper_objects__(model)
            o_jump = getfield(m, Symbol(o["name"]))
            MOSInterface.__set_helper_object__(model, o, o_jump)
        end

        # Extract variable states
        writeln(io, "Extracting variable states")
        num_vars = 0
        for v in MOSInterface.__get_variables__(model)
            v_jump = getfield(m, Symbol(v["name"]))
            v_labels = isempty(v["labels"]) ? Dict() : getfield(m, Symbol(v["labels"]))

            var_states = Dict{String, Any}[]

            # Scalar
            if typeof(v_jump) <: JuMP.VariableRef

                num_vars = num_vars + 1
                MOSInterface.__set_var_type_and_shape__(model, v, "scalar", nothing)

                if JuMP.has_upper_bound(v_jump)
                    ub = JuMP.upper_bound(v_jump)
                else
                    ub = 1e9
                end
                
                if JuMP.has_lower_bound(v_jump)
                    lb = JuMP.lower_bound(v_jump)
                else
                    lb = -1e9
                end
                
                if JuMP.is_binary(v_jump)
                    lb = 0
                    ub = 1
                    vkind = "binary"
                    integer_switch = true
                elseif JuMP.is_integer(v_jump)
                    vkind = "integer"
                    integer_switch = true
                else
                    vkind = "continuous"
                end
                    
                v_state = Dict(
                    "variable" => correct_url(v["url"], model.interface.url),
                    "owner" => MOSInterface.get_owner_id(model),
                    "index" => nothing,
                    "label" => v["name"],
                    "value" => has_values ? JuMP.value(v_jump) : 0,
                    "kind" => vkind,
                    "upper_bound" => ub,
                    "lower_bound" => lb)
                push!(var_states, v_state)

            # Dict

            # Array
            elseif (typeof(v_jump) <: Array{JuMP.VariableRef,} || 
                    typeof(v_jump) <: JuMP.Containers.DenseAxisArray)
                num_vars = num_vars + length(v_jump)

                vtype = "array"
                vshape = [x for x in size(v_jump)]
                    
                MOSInterface.__set_var_type_and_shape__(model, v, vtype, vshape)

                for i in CartesianIndices(v_jump)

                    if JuMP.has_upper_bound(v_jump[i])
                        ub = JuMP.upper_bound(v_jump[i])
                    else
                        ub = 1e9
                    end
                
                    if JuMP.has_lower_bound(v_jump[i])
                        lb = JuMP.lower_bound(v_jump[i])
                    else
                        lb = -1e9
                    end

                    if JuMP.is_binary(v_jump[i])
                        lb = 0
                        ub = 1
                        vkind = "binary"
                        integer_switch = true
                    elseif JuMP.is_integer(v_jump[i])
                        vkind = "integer"
                        integer_switch = true
                    else
                        vkind = "continuous"
                    end

                    index = length(i.I) == 1 ? i.I[1] : i.I
                    v_state = Dict(
                        "variable" => correct_url(v["url"], model.interface.url),
                        "owner" => get_owner_id(model),
                        "index" => [x for x in i.I],
                        "label" => haskey(v_labels, index) ? v_labels[index] : "",
                        "value" => has_values ? JuMP.value(v_jump[i]) : 0,
                        "kind" => vkind,
                        "upper_bound" => ub,
                        "lower_bound" => lb)
                    push!(var_states, v_state)
                end

            # Unknown
            else
                error("invalid variable type")
            end
            MOSInterface.__add_variable_states__(model, var_states)
        end

        # Extract function states
        writeln(io, "Extracting function states")
        for f in MOSInterface.__get_functions__(model)
            f_jump = getfield(m, Symbol(f["name"]))
            func_states = Dict{String, Any}[]

            # Scalar
            if typeof(f_jump) <: JuMP.GenericAffExpr{Float64,JuMP.VariableRef}
                MOSInterface.__set_function_type_and_shape__(model, f, "scalar", nothing)
                f_state = Dict(
                    "function" => correct_url(f["url"], model.interface.url),
                    "owner" => get_owner_id(model),
                    "index" => nothing,
                    "label" => f["name"],
                    "value" => JuMP.value(f_jump))
                push!(func_states, f_state)
            else
            
            # Array

            # Unknown
                error("only one-dimensional functions supported at this point")
            end
            MOSInterface.__add_function_states__(model, func_states)
        end

        # Constraint helper function
        function get_constr_info(c::JuMP.ConstraintRef)
            f = MOI.get(model_jump, MOI.ConstraintFunction(), c) # just a reference
            s = MOI.get(model_jump, MOI.ConstraintSet(), c)
            fval = has_values ? JuMP.value(c) : 0
            if typeof(c.index) <: MOI.ConstraintIndex{<:Any, <:MOI.EqualTo}
                return "equality", abs(fval-s.value)
            elseif typeof(c.index) <: MOI.ConstraintIndex{<:Any, <:MOI.GreaterThan}
                return "inequality", max(s.lower-fval, 0)
            elseif typeof(c.index) <: MOI.ConstraintIndex{<:Any, <:MOI.LessThan}
                return "inequality", max(fval-s.upper, 0)
            elseif typeof(c.index) <: MOI.ConstraintIndex{<:Any, <:MOI.Interval}
                error("not yet supported")
            else
                error("bad constraint")
            end
        end

        # Extract constraint states
        writeln(io, "Extracting constraint states")
        num_constraints = Int(0)
        for c in MOSInterface.__get_constraints__(model)
            
            c_jump = getfield(m, Symbol(c["name"]))
            c_labels = isempty(c["labels"]) ? Dict() : getfield(m, Symbol(c["labels"]))
            constr_states = Dict{String, Any}[]

            # Single
            if typeof(c_jump) <: JuMP.ConstraintRef
                num_constraints = num_constraints + 1
                MOSInterface.__set_constraint_type_and_shape__(model, c, "scalar", nothing)
                
                type, vio = get_constr_info(c_jump)
                c_state = Dict(
                    "constraint" => correct_url(c["url"], model.interface.url),
                    "owner" => get_owner_id(model),
                    "index" => nothing,
                    "label" => c["name"],
                    "dual" => has_duals ? JuMP.dual(c_jump) : 0.,
                    "kind" => type,
                    "violation" => vio)
                push!(constr_states, c_state)

            # SparseAxisArray
            elseif typeof(c_jump) <: JuMP.Containers.SparseAxisArray
                num_constraints = num_constraints + length(c_jump)
                MOSInterface.__set_constraint_type_and_shape__(model, 
                                                               c, 
                                                               "array", 
                                                               [length(c_jump)])

                for (k, ci) in c_jump.data

                    type, vio = get_constr_info(ci)
                    index = length(k) == 1 ? k[1] : k
                    c_state = Dict(
                        "constraint" => correct_url(c["url"], model.interface.url),
                        "owner" => get_owner_id(model),
                        "index" => [x for x in k],
                        "label" => haskey(c_labels, index) ? c_labels[index] : "",
                        "dual" => has_duals ? JuMP.dual(ci) : 0.,
                        "kind" => type,
                        "violation" => vio)
                    push!(constr_states, c_state)
                end

            # Array and DenseAxisArray
            elseif typeof(c_jump) <: Array || typeof(c_jump) <: JuMP.Containers.DenseAxisArray
                num_constraints = num_constraints + length(c_jump)
                
                ctype = "array"
                cshape = [x for x in size(c_jump)]
                
                MOSInterface.__set_constraint_type_and_shape__(model, c, ctype, cshape)
                for i in CartesianIndices(c_jump)
                    ci = c_jump[i]
                    type, vio = get_constr_info(ci)
                    index = length(i.I) == 1 ? i.I[1] : i.I
                    c_state = Dict(
                        "constraint" => correct_url(c["url"], model.interface.url),
                        "owner" => get_owner_id(model),
                        "index" => [x for x in i.I],
                        "label" => haskey(c_labels, index) ? c_labels[index] : "",
                        "dual" => has_duals ? JuMP.dual(ci) : 0.,
                        "kind" => type,
                        "violation" => vio)
                    push!(constr_states, c_state)
                end

            # Unknown
            else
                error("invalid constraint type")
            end
            MOSInterface.__add_constraint_states__(model, constr_states)
        end

        # Extract problem state
        writeln(io, "Extracting problem state")
        p = MOSInterface.__get_problem__(model)
        linear_switch = true
        ct = JuMP.list_of_constraint_types(model_jump)
        numc = 0
        for i = 1:length(ct)
            numc = numc + JuMP.num_constraints(model_jump,ct[i][1],ct[i][2])
            if ct[i][1] != JuMP.GenericAffExpr{Float64, JuMP.VariableRef}
                if ct[i][1] != JuMP.VariableRef
                    linear_switch = false
                end
            end
        end

        pkind = "unknown"
        objtype = MOI.get(model_jump, MOI.ObjectiveFunctionType())
        if integer_switch == true
            pkind = "mip"
        elseif linear_switch == true
            pkind = "lp"
        end
                 
        if p != nothing
            p_state = Dict(
                "problem" => correct_url(p["url"], model.interface.url),
                "owner" => get_owner_id(model),
                "kind" => pkind,
                "num_constraints" => num_constraints,
                # we will pull number of variables directly from JuMP for 
                # now in case hidden from MOS
                "num_vars" => MOI.get(model_jump, MOI.NumberOfVariables()))
            MOSInterface.__add_problem_state__(model, p_state)
        end

        # Extract solver state
        writeln(io, "Extracting solver state")
        s = MOSInterface.__get_solver__(model)

        iterations = 0
        try
            iterations = iterations + MOI.get(model_jump, MOI.SimplexIterations)
        catch
        end
        try
            iterations = iterations + MOI.get(model_jump, MOI.BarrierIterations)
        catch
        end
        
        s_time = 0
        try
            s_time = s_time + JuMP.solve_time(model_jump)
        catch
        end
            
        s_state = Dict(
            "solver" => correct_url(s["url"], model.interface.url),
            "owner" => get_owner_id(model),
            "name" => JuMP.solver_name(model_jump),
            "status" => JuMP.termination_status(model_jump),
            "iterations" => iterations,
            "time" => s_time,
            "parameters" => Dict())
        MOSInterface.__add_solver_state__(model, s_state)

        # Extract output files
        writeln(io, "Extracting output files")
        for f in MOSInterface.__get_interface_files__(model, "output")
            MOSInterface.__set_interface_file__(model, f, string(f["name"], f["extension"]))
        end

        # Extract output objects
        writeln(io, "Extracting output objects")
        for o in MOSInterface.__get_interface_objects__(model, "output")
            o_jump = getfield(m, Symbol(o["name"]))
            MOSInterface.__set_interface_object__(model, o, o_jump)
        end

        # Execution log
        MOSInterface.__set_execution_log__(model, String(take!(io)))

        # Status
        MOSInterface.__set_status__(model, "success")
        push_notification(caller_id, Dict(
            "model_id" => model_id,
            "model_name" => model_name,
            "status" => "success",
        ))

    catch e

        # Show error
        bt = catch_backtrace()
        msg = sprint(showerror, e, bt)
        writeln(io, msg)

        # Execution log
        MOSInterface.__set_execution_log__(model, String(take!(io)))

        # Status
        MOSInterface.__set_status__(model, "error")
        push_notification(caller_id, Dict(
            "model_id" => model_id,
            "model_name" => model_name,
            "status" => "error",
        ))

    finally

        # Cleanup
        println("Cleaning up local files")
        MOSInterface.__delete_input_files__(model)
        MOSInterface.__delete_input_object_files__(model)
        MOSInterface.__delete_output_files__(model)

    end
end 
