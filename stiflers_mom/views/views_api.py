from datetime import datetime
from time import time,strftime,localtime
from typing import Dict

import aiohttp_jinja2
import markdown2
from aiohttp import web,ClientSession
from aiochclient import ChClient
#from aiojobs.aiohttp import atomic
import json
import sys

from stiflers_mom.constants import PROJECT_DIR
from stiflers_mom.collectors.db_utils import DBcapturedMAC,store_macs_to_clhouse,store_flow
#from stiflers_mom.cron import save_csv

#timeout sec | after we mark stats as outdated
TIMELIFE = 120

@aiohttp_jinja2.template('index.html')
async def index(request: web.Request) -> Dict[str, str]:
    with open(PROJECT_DIR / 'README.md') as f:
        text = markdown2.markdown(f.read())

    return {"text": text}




async def post_json(data,url):
    t = strftime("%d%m%y %H:%M:%S", localtime())
    msg = ''
    size = sys.getsizeof(data)
    result = False
    try:
        async with ClientSession() as session:
            async with session.post(url, json=data) as resp:
                if resp:
                    if resp.status in range(200,300):
                        print(f"\n[{t}] {url} POST {size} bytes, response status: {resp.status}")
                        #print(f"\n[{t}] {url} POST {resp.status} data: {data}\n")
                        return True, f"code:{resp.status}"

                    rt = await resp.text()
                    
                    print(f"\n[{t}] {url}  POST {size} bytes, response status: {r.status}")
                    #print(f"\n{t} {url} POST {resp.status} data: {data}\n")
                    if rt: msg = f"code:{r.status}, {rt}"
                else:
                    m = "POST no response"
                    print(f"[{t}] {m}")
                    msg = m

    except Exception as e:
        msg = str(e)
        print(f"[{t}] {url} POST {size} bytes, could not store: {msg}")

    return result, msg




########################################## POST STATISTICS | FOR COLLECTORS

#/collector_stats
async def CollectorStats(request):
    """ /collector_stats endpoint recieve statistics from collectors """
    if request.body_exists and request.content_type == 'application/json':
        data = await request.json()
        data["main"]["status"] = "online"

        peername = request.transport.get_extra_info('peername')
        if peername is not None:
            host, port = peername

            if 'stats' not in request.app: request.app['stats'] = {}
            if 'clctrs' not in request.app['stats']: request.app['stats']['clctrs'] = {}
            if 'snifs' not in request.app['stats']: request.app['stats']['snifs'] = {}

            if 'snifs' in data:
                for s in data['snifs']:
                    data['snifs'][s]["collector"] = host
                    ut = data['snifs'][s]["ts_last"]
                    #data['snifs'][s]["ts_last"] = int(ut // 1e9) #1000000000
                    data['snifs'][s]["ts_last"] = int(ut) #1000000000
                    if data['snifs'][s]["ts_last"] + TIMELIFE < time():
                        data['snifs'][s]["status"] = "offline"
                    else:
                        data['snifs'][s]["status"] = "online"

                request.app['stats']['snifs'].update(data['snifs'])
                del data['snifs']

            request.app['stats']['clctrs'][host] = data["main"]

        return web.HTTPAccepted(text='stats stored\n')
    else:
        return web.HTTPForbidden(text='only json allowed\n')


# /macs_to_localdb
# @atomic
async def SaveMacsLocaly(request): # /captured_macs
    """ recieve from collectors and put to local db some MACs  """
    data = await request.json()   

    bigdata_stored = False
    clkhs_stored = False
    clkhs_msg = 'success'

    try:
        ch: ChClient = request.app['ch']        
        is_alive = await ch.is_alive()
    except Exception as e:
        clkhs_msg = 'Could Not connect: '+str(e)
    else:
        if ch:
            is_alive = await ch.is_alive()
            if is_alive:
                clkhs_stored,err = await store_flow(ch,data) 
                if not clkhs_stored: clkhs_msg = err
            else:
                print('could not save new row in Clickhouse!')
                clkhs_msg = 'Could not connect. Session is not alive'

    peername = request.transport.get_extra_info('peername')
    if peername is not None:
        host, _ = peername
        if 'stats' not in request.app:
            request.app['stats'] = {}
        if 'posts' not in request.app['stats']:
            request.app['stats']['posts'] = {}
        d = {
        "ClickHouse" : clkhs_stored,
        "ClickHouseMsg" : clkhs_msg,
        "macs_sent" : len(data),
        "posttime" : int(time()),
        "status" : "ok",
        }

        if clkhs_stored:
            d["status"] = "success"
            request.app['stats']['posts'][host] = d
            return web.HTTPAccepted(text='data stored localy\n')
        else:
            error = f"CLICKHOUSE: {clkhs_msg}"
            d["status"] = error
            print(error)
            request.app['stats']['posts'][host] = d
            return web.HTTPServiceUnavailable(
                text='could not save into local db: '+error)
    return web.HTTPForbidden(text='peername is None\n')
        
    

#/captured_macs
#@atomic
async def SaveCapturedMacs(request): # /captured_macs
    """ recieve and put to db mac addresses from collectors """
    #try:
    if request.body_exists and request.content_type == 'application/json':

        try:
            data = await request.json()
        except json.decoder.JSONDecodeError:
            raise web.HTTPBadRequest(text='json decode error\n')
        except Exception as e:
            return web.HTTPBadRequest(text=str(e))       

        bigdata_stored = False
        clkhs_stored = False
        clkhs_msg = 'success'
        
        url = request.app['config']['bigdata']['url']
        
        bigdata_stored, bigdata_msg = await post_json(data,url)
        #bigdata_stored, bigdata_msg = True, 'Commented during tests'

        try:
            ch: ChClient = request.app['ch']        
            is_alive = await ch.is_alive()
        except Exception as e:
            clkhs_msg = 'Could Not connect: '+str(e)
        else:
            if ch:
                is_alive = await ch.is_alive()
                if is_alive:
                    #clkhs_stored,err = await store_macs_to_clhouse(ch,data) 
                    #clkhs_stored, err = True, 'Commented during tests'
                    clkhs_stored,err = await store_flow(ch,data) 
                    if not clkhs_stored: clkhs_msg = err

                else:
                    print('could not save new row in Clickhouse!')
                    clkhs_msg = 'Could not connect. Session is not alive'

        peername = request.transport.get_extra_info('peername')
        if peername is not None:
            host, _ = peername
            if 'stats' not in request.app:
                request.app['stats'] = {}
            if 'posts' not in request.app['stats']:
                request.app['stats']['posts'] = {}
            d = {
            "Bigdata" : bigdata_stored,
            "ClickHouse" : clkhs_stored,
            "BigdataMsg" : bigdata_msg,
            "ClickHouseMsg" : clkhs_msg,
            "macs_sent" : len(data),
            "posttime" : int(time()),
            "status" : "ok",
            }

            if all([bigdata_stored,clkhs_stored]):
                d["status"] = "success"
                request.app['stats']['posts'][host] = d
                return web.HTTPAccepted(text='data stored\n')
            else:
                error = f"BIGDATA: {bigdata_msg}| CLICKHOUSE: {clkhs_msg}"
                d["status"] = "not clear"
                print(error)
                request.app['stats']['posts'][host] = d
                return web.HTTPServiceUnavailable(
                    text='could not save into db: '+error)
        return web.HTTPForbidden(text='peername is None\n')
    else:
        return web.HTTPForbidden(text='only json allowed\n')
    # except Exception as e:
    #     print(e)
    #     web.HTTPServiceUnavailable(text=str(e))



############################## GET STATISTICS | FOR ZABBIX MONITORING

async def macs_view(request): # /show_macs
    """ show_macs """
    async with request.app['db'].acquire() as conn:
        data = await DBcapturedMAC(conn).select_by_time()

    return web.HTTPAccepted(text=f'ok query: {len(data)}\n')


async def post_stats_view(request): # /post_stats
    """
        returns json with general statistics
        
    """
    if 'stats' in request.app:
        if 'posts' in request.app['stats']:
            res = request.app['stats']['posts']

            for i in res:
                if "posttime" in res[i]:
                    if int(res[i]["posttime"]) + TIMELIFE < time():
                        res[i]["status"] = "Outdated!"
            
            return web.json_response(res)
    
    return web.HTTPServiceUnavailable(text="no statistics in main loop yet")


async def collector_stats_view(request): # /collector_stats
    """
        returns json with collector statistics
        
    """
    if 'stats' in request.app:
        if 'clctrs' in request.app['stats']:
            res = request.app['stats']['clctrs']
            for i in res:
                if "last_ts" in res[i]:
                    if int(res[i]["last_ts"]) + TIMELIFE < time():
                        res[i]["status"] = "offline"

            return web.json_response(res)
    
    return web.HTTPServiceUnavailable(text="no statistics for collectors yet")    
    

async def snif_stats_view(request): # /collector_stats
    """
        returns json with sniffer statistics
        
    """
    def check_status(d):
        if "update_time" in d:
            if int(d["ts_last"]) + TIMELIFE < time():
                d["status"] = "offline"
            else:
                d["status"] = "online"
        return d

    snifid = None
    if 'stats' in request.app:
        if 'snifs' in request.app['stats']:
            res = request.app['stats']['snifs']

            if 'id' in request.rel_url.query:
                snifid = request.rel_url.query['id']
                snifid = snifid.lower().replace(":","")

                if snifid:
                    if snifid in res:
                        result = check_status(res[snifid])
                        return web.json_response(result)
                    else:
                        return web.HTTPNotFound()

            for i in res: res[i] = check_status(res[i])
 
            return web.json_response(res)
    
    return web.HTTPServiceUnavailable(text="no statistics for collectors yet")
