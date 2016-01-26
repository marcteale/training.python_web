#!/usr/bin/python
# import cgitb
from urllib.parse import urlparse

# cgitb.enable()


def parse_path(referer):
    '''
    Parse the path provided and respond with appropriate content. Returns the
    status of the request and content of response.
    '''
    response = ''
    status = '200 OK'

    scheme, netloc, path, params, query, fragment = urlparse(referer)
    baseurl = "{}://{}/".format(scheme, netloc)

    args = path.split('/')
    args.pop(0)  # First element is always a null string, get rid of it

    # We only support paths, return a 501 if we get anything else
    if params or query or fragment != '':
        raise NotImplementedError
    # Send the examples
    if path == '/' or '':
        response = """
        <h1>Instructions for use:</h1>
        <h2>Separate all arguments with slashes.</h2>
        <h3>Multiply</h3>
        <p>Append 'multiply' to the URL string followed by the multiplicands.</p>
        <a href="{0}multiply/3/4">{0}multiply/3/4</a> = 12
        <h3>Divide</h3>
        <p>Append 'divide', then the dividend and divisor.</p>
        Example: <a href="{0}divide/12/4">{0}divide/12/4</a> = 3
        <h3>Add</h3>
        <p>Append 'add', followed by any number of addends.</p>
        Example: <a href="{0}add/23/52">{0}add/23/52</a> = 75
        <h3>Subtract</h3>
        <p>Append 'subtract', followed by the minuend and the subtrahend. (I had no idea those were words before today.)</p>
        Example: <a href="{0}subtract/36/4">{0}subtract/36/4</a> = 12
        """.format(baseurl)
    # Do the math
    elif args[0].lower() == 'multiply' or 'divide' or 'add' or 'subtract':
        response = do_some_math(args)
    # This is supposed to return a NameError when the path doesn't match, but it
    # returns a 500 instead.  I can't figure out why.
    else:
        raise NameError
    return status, response


def do_some_math(args):
    operation = args[0]
    args.pop(0)
    if len(args) > 2:
        raise SyntaxError
    first = float(args[0])
    second = float(args[1])
    if operation == 'subtract':
        operator = '-'
        result = first - second
    elif operation == 'divide':
        if float(second) == 0.0:
            raise ValueError
        operator = '/'
        result = first / second
    elif operation == 'multiply':
        operator = '*'
        result = first * second
    else:
        operator = '+'
        result = first + second
    content = "{} {} {} = {}".format(first, operator, second, result)

    return content


def error_content(status_code, referer):
    '''
    Creates error pages based on an intentionally limited number of HTTP error
    codes. Returns the HTTP error code string and content of the error message.
    '''
    error_codes = {400: '400 Bad request',
                   404: '404 Not Found',
                   500: '500 Internal Server Error',
                   501: '501 Not Implemented'
                   }
    scheme, netloc, path, params, query, fragment = urlparse(referer)
    status_str = error_codes[status_code]
    content = '<h1>{}</h1>Referer was <a href="{}">{}</a>'.format(status_str, referer, referer)
    return status_str, content


def application(environ, start_response):
    header = """<html>
    <head>
    <title>WSGI Calculator</title>
    </head>
    <body>"""
    footer = """
    </body>
    </html>"""

    # I'm sure there was an easier way to get the full request, but I couldn't find it.
    http_host = environ.get('HTTP_HOST', None)
    path = environ.get('PATH_INFO', None)
    query_string = environ.get('QUERY_STRING', None)
    examples = '<p><a href="http://{}/">Examples</a>'.format(http_host)
    if query_string == '':
        request = "http://{}{}".format(http_host, path)
    else:
        request = "http://{}{}?{}".format(http_host, path, query_string)

    try:
        status, content = parse_path(request)
    except SyntaxError or ValueError:
        status, content = error_content(400, request)
    except NameError:
        status, content = error_content(404, request)
    except NotImplementedError:
        status, content = error_content(501, request)
    except Exception:
        status, content = error_content(500, request)

    content = header + content + examples + footer
    response_headers = [('Content-Type', 'text/html'),
                        ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    return[content.encode('utf8')]


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    srv = make_server('0.0.0.0', 8080, application)
    srv.serve_forever()
