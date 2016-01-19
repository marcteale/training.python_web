import socket
import sys
import mimetypes
import os.path


def response_ok(body=b"this is a pretty minimal response", mimetype=b"text/plain"):
    """returns a basic HTTP response"""
    mimetype = b"content-type:" + mimetype
    resp = []
    resp.append(b"HTTP/1.1 200 OK")
    resp.append(mimetype)
    resp.append(b"")
    resp.append(body)
    return b"\r\n".join(resp)


def response_method_not_allowed():
    """returns a 405 Method Not Allowed response"""
    resp = []
    resp.append("HTTP/1.1 405 Method Not Allowed")
    resp.append("")
    return "\r\n".join(resp).encode('utf8')


def response_not_found():
    """returns a 404 Not Found response"""
    return b"HTTP/1.1 404 Not Found"


def parse_request(request):
    first_line = request.split("\r\n", 1)[0]
    try:
        method, uri, protocol = first_line.split()
    # Chrome seems to be sending a zero-length request that breaks the split.
    except ValueError:
        print('The client tried to break me.  Request was: \'{}\''.format(request))
        method = ''
    if method != "GET":
        raise NotImplementedError("We only accept GET")
    return uri


def resolve_uri(uri):
    """Return appropriate content and a mime type"""
    # Return the contents of a file if it exists
    uri = os.getcwd() + uri
    if os.path.isfile(uri):
        mime_type, _ = mimetypes.guess_type(uri)
        mime_type = mime_type.encode('utf8')
        with open(uri, "rb") as content_file:
            f = content_file.read()
            content = bytearray(f)
    # Return an index if a directory is requested
    elif os.path.isdir(uri):
        mime_type = b'text/plain'
        filelist = os.listdir(uri)
        filelist.sort
        content = '\r\n'.join(filelist)
        content = content.encode('utf8')
    else:
        raise NameError
    return content, mime_type


def server(log_buffer=sys.stderr):
    address = ('0.0.0.0', 10000)  # I'm running this from a remote VM
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)  # NOQA
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)
                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')
                    if len(data) < 1024:
                        break

                try:
                    uri = parse_request(request)
                except NotImplementedError:
                    response = response_method_not_allowed()
                else:
                    try:
                        content, mime_type = resolve_uri(uri)
                    except NameError:
                        response = response_not_found()
                    else:
                        response = response_ok(content, mime_type)

                print('sending response', file=log_buffer)
                conn.sendall(response)
            finally:
                conn.close()

    except KeyboardInterrupt:
        sock.close()
        return


if __name__ == '__main__':
    server()
    sys.exit(0)
