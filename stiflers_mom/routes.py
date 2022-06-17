import pathlib

from aiohttp import web

from stiflers_mom.views import *

PROJECT_PATH = pathlib.Path(__file__).parent


def init_routes(app: web.Application) -> None:
    add_route = app.router.add_route

    add_route('*', '/', index, name='index')

    # POSTs from collectors
    add_route('POST', '/macs_to_localdb', SaveMacsLocaly) # only in clickhouse
    add_route('POST', '/captured_macs', SaveCapturedMacs) #clhouse and bigdata
    add_route('POST', '/collector_stats', CollectorStats)
    #CollectorStats

    # GET
    add_route('GET', '/show_macs', macs_view)
    add_route('GET', '/post_stats', post_stats_view)
    add_route('GET', '/collector_stats', collector_stats_view)
    add_route('GET', '/snif_stats', snif_stats_view)
    #stats_view


    # added static dir
    app.router.add_static(
        '/static/',
        path=(PROJECT_PATH / 'static'),
        name='static',
    )

    # added static temp dir with csv
    app.router.add_static(
        '/csv_files/Locomotive',
        path=(PROJECT_PATH / 'csv_files/Locomotive'),
        name='Locomotive_csv',
        show_index=True,
    )