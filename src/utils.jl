import JSON
import WebSockets

function get_admin_credentials()::Tuple{String, String}
    
    # Username
    if haskey(ENV, "MOS_ADMIN_USR")
        usr = ENV["MOS_ADMIN_USR"]
    else
        usr = ""
    end

    # Username
    if haskey(ENV, "MOS_ADMIN_PWD")
        pwd = ENV["MOS_ADMIN_PWD"]
    else
        pwd = ""
    end

    return (usr, pwd)
end

function get_backend_url()::String

    # Host
    if haskey(ENV, "MOS_BACKEND_HOST")
        backend_host = ENV["MOS_BACKEND_HOST"]
    else
        backend_host = "localhost"
    end

    # Port
    if haskey(ENV, "MOS_BACKEND_PORT")
        backend_port = ENV["MOS_BACKEND_PORT"]
    else
        backend_port = "8000"
    end

    # Protocol
    if backend_port == "443"
        protocol = "https"
    else
        protocol = "http"
    end
   
    # Url
    return "$protocol://$backend_host:$backend_port/api/"
end

function push_notification(user_id, notification)
 
    # Host
    if haskey(ENV, "MOS_BACKEND_HOST")
        backend_host = ENV["MOS_BACKEND_HOST"]
    else
        backend_host = "localhost"
    end

    # Port
    if haskey(ENV, "MOS_BACKEND_PORT")
        backend_port = ENV["MOS_BACKEND_PORT"]
    else
        backend_port = "8000"
    end

    # Ws
    if backend_port == "443"
        ws = "wss"
    else
        ws = "ws"
    end

    # Uri
    if (backend_port == "80") || (backend_port == "443")
        wsuri = "$ws://$backend_host/ws/notifications/$user_id/"
    else
        wsuri = "$ws://$backend_host:$backend_port/ws/notifications/$user_id/"
    end

    # Websocket
    WebSockets.open(wsuri) do ws
        msg = JSON.json(notification)
        WebSockets.writeguarded(ws, msg)
    end
end

function writeln(io::IOBuffer, s::String)
    println(io, s)
    println(s)
end