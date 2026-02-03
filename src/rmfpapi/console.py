"""CLI entrypoints for fake product integration api"""

import asyncio
import logging
import json

import click
from libadvian.logging import init_logging
import aiohttp

from rmfpapi import __version__
from rmfpapi.app import get_app


LOGGER = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.pass_context
@click.option("-l", "--loglevel", help="Python log level, 10=DEBUG, 20=INFO, 30=WARNING, 40=CRITICAL", default=30)
@click.option("-v", "--verbose", count=True, help="Shorthand for info/debug loglevel (-v/-vv)")
def cli_group(ctx: click.Context, loglevel: int, verbose: int) -> None:
    """CLI helpers for developers"""
    if verbose == 1:
        loglevel = 20
    if verbose >= 2:
        loglevel = 10

    LOGGER.setLevel(loglevel)
    ctx.ensure_object(dict)


@cli_group.command(name="healthcheck")
@click.option("--host", default="localhost", help="The host to connect to")
@click.option("--port", default=8001, help="The port to connect to")
@click.option("--timeout", default=2.0, help="The timeout in seconds")
@click.pass_context
def do_http_healthcheck(ctx: click.Context, host: str, port: int, timeout: float) -> None:
    """
    Do a GET request to the healthcheck api and dump results to stdout
    """

    async def doit() -> int:
        """The actual work"""
        nonlocal host, port, timeout
        if "://" not in host:
            host = f"http://{host}"
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(f"{host}:{port}/api/v1/healthcheck") as resp:
                if resp.status != 200:
                    return resp.status
                payload = await resp.json()
                click.echo(json.dumps(payload))
                if not payload["healthy"]:
                    return 1
        return 0

    ctx.exit(asyncio.get_event_loop().run_until_complete(doit()))


@cli_group.command(name="openapi")
@click.pass_context
def dump_openapi(ctx: click.Context) -> None:
    """
    Dump autogenerate openapi spec as JSON
    """
    app = get_app()
    click.echo(json.dumps(app.openapi()))
    ctx.exit(0)


def rmfpapi_cli() -> None:
    """rmfpapi"""
    init_logging(logging.WARNING)
    cli_group()  # pylint: disable=no-value-for-parameter
