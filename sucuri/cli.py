import click
import json
import os
import runpy
import sys
from sucuri.rendering import template

@click.group()
def cli():
    """Sucuri Template Engine CLI"""
    pass

@cli.command()
@click.argument('template_file', type=click.Path(exists=True))
@click.option('--context', '-c', help='JSON string or path to JSON file containing the context data.')
@click.option('--output', '-o', help='Path to output HTML file. If not provided, prints to stdout.')
def build(template_file, context, output):
    """Compiles a Sucuri template into HTML."""
    context_data = {}
    
    if context:
        if os.path.exists(context):
            with open(context, 'r', encoding='utf-8') as f:
                try:
                    context_data = json.load(f)
                except json.JSONDecodeError as e:
                    click.echo(f"Error parsing JSON file '{context}': {e}", err=True)
                    sys.exit(1)
        else:
            try:
                context_data = json.loads(context)
            except json.JSONDecodeError:
                click.echo("Error: Context must be a valid JSON string or a valid path to a JSON file.", err=True)
                sys.exit(1)

    try:
        html_output = template(template_file, context_data)
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(html_output)
            click.echo(f"Successfully compiled '{template_file}' to '{output}'.")
        else:
            click.echo(html_output)
    except Exception as e:
        click.echo(f"Error compiling template: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()


@cli.command()
@click.argument('app_file', type=click.Path(exists=True))
@click.option('--port', '-p', default=None, type=int, help='Port to listen on (default: 8080).')
@click.option('--host', default=None, help='Host to bind to (default: 127.0.0.1).')
@click.option('--public', is_flag=True, default=False, help='Disable token protection on non-GET endpoints.')
def serve(app_file, port, host, public):
    """Start the Sucuri live server for a given app file.

    The app file should define a SucuriApp instance and call app.run().
    Use --port / --host to override values set inside the file.

    Example:

        sucuri serve main.py --port 3000
    """
    if port:
        os.environ['SUCURI_PORT'] = str(port)
    if host:
        os.environ['SUCURI_HOST'] = host
    if public:
        os.environ['SUCURI_PUBLIC'] = '1'
    runpy.run_path(app_file, run_name='__main__')


@cli.command()
@click.argument('app_file', type=click.Path(exists=True))
@click.option('--port', '-p', default=8080, type=int, help='Port to listen on (default: 8080).')
@click.option('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1).')
@click.option('--title', default='Sucuri App', help='Window title.')
@click.option('--width', default=1024, type=int, help='Window width in pixels.')
@click.option('--height', default=768, type=int, help='Window height in pixels.')
def desktop(app_file, port, host, title, width, height):
    """Open the application as a native desktop window.

    Starts the Sucuri server in a background thread and opens a native
    WebView window pointing to it. The server stops when the window closes.

    Example:

        sucuri desktop main.py --title "My App" --port 8080
    """
    try:
        import webview
    except ImportError:
        click.echo(
            "Error: pywebview is not installed.\n"
            "Install it with: pip install sucuri[desktop]",
            err=True,
        )
        sys.exit(1)

    import threading
    from sucuri.server import _wait_for_port

    os.environ['SUCURI_PORT'] = str(port)
    os.environ['SUCURI_HOST'] = host

    server_thread = threading.Thread(
        target=runpy.run_path,
        args=(app_file,),
        kwargs={'run_name': '__main__'},
        daemon=True,
    )
    server_thread.start()

    if not _wait_for_port(host, port):
        click.echo(f"Error: server did not start on {host}:{port} within 5 seconds.", err=True)
        sys.exit(1)

    webview.create_window(title, f'http://{host}:{port}', width=width, height=height)
    webview.start()
