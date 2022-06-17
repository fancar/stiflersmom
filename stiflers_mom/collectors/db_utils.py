from aiopg.sa import SAConnection
from aiopg.sa.result import RowProxy

from datetime import datetime, timedelta

from stiflers_mom.collectors.tables import *




__all__ = ['select_captured_mac_by_id','store_macs_to_clhouse' ]


async def select_captured_mac_by_id(conn: SAConnection, key: int) -> RowProxy:
    query = macs_captured\
        .select()\
        .where(macs_captured.c.id == key)\
        .order_by(macs_captured.c.id)
    cursor = await conn.execute(query)

    return await cursor.fetchone()



async def store_macs_to_psql(conn, data):
    
    for i in data:
        for kwargs in data[i]:
            print("i",i)
            print(kwargs)
            try:
                uid = await conn.scalar(
                    macs_captured.insert().values(snifid=i,**kwargs)
                    )
            except Exception as e:
                return False, str(e)                
            print(f"\ninserted row with uid: {uid}\n\n\n")


    return True, None

async def store_flow(ch,data):
    """ 
    store flow into local Clickhouse
    """
    if type(data) == dict:
        data = [data]
    elif type(data) != list:
        msg = 'data type must be list or dict!'
        print('CLICKHOUSE: ',msg)
        return False, msg

    query = """INSERT INTO snif_flow
    (Channel,
    FramesCount,
    KnownFrom,
    LastSeen,
    MAC,
    NotifiedCount,
    RSSI,
    RSSImax,
    SnifID,
    SnifIP,
    Vendor)
    VALUES
    """
    values = (
        (
        int(d["Channel"]),
        int(d["FramesCount"]),
        datetime.utcfromtimestamp(int(d["KnownFrom"])),
        datetime.utcfromtimestamp(int(d["LastSeen"])),
        int(d["MAC"].translate(str.maketrans('','',':.- ')), 16),
        int(d["NotifiedCount"]),
        int(d["RSSI"]),
        int(d["RSSImax"]),
        int(d["SnifID"].translate(str.maketrans('','',':.- ')), 16),
        int(d["SnifIP"].translate(str.maketrans('','','.')), 16),
         d["Vendor"]
        ) for d in data)

    try:
        await ch.execute(query,*values)
        print(f"CLICKHOUSE: rows inserted: {len(data)} ")
        return True, None
        
    except Exception as e:
        print('CLICKHOUSE: can not insert Data in DB: '+str(e))
        return False, str(e)



async def store_macs_to_clhouse(ch,data):
    """ store from json into our clickhouse sniffed table """

    query = """INSERT INTO sniffed
    (SnifID,
    MAC,
    Vendor,
    FineRssiValue,
    RSSIavg,
    RSSImax,
    FramesWIthFineRssiCount,
    FramesCount,
    NotifiedCount,
    KnownFrom,
    LastSeen,
    CreatedAt)
    VALUES
    """

    try:
        values = ((int(d["SnifID"].translate(str.maketrans('','',':.- ')), 16),
            int(d["MAC"].translate(str.maketrans('','',':.- ')), 16),
            d["Vendor"],
            int(d["FineRssiValue"]),
            int(d["RSSIavg"]),
            int(d["RSSImax"]),
            int(d["FramesWIthFineRssiCount"]),
            int(d["FramesCount"]),
            int(d["NotifiedCount"]),
            datetime.utcfromtimestamp(int(d["KnownFrom"])),      
            datetime.utcfromtimestamp(int(d["LastSeen"])),
            datetime.utcnow()
            ) for d in data)
    except Exception as e:
        print('DB_UTILS: can not insert Data in DB. Lack of keys in json: '+str(e))
        return False, str(e)

    try:
        await ch.execute(query,*values)
        print(f'{len(data)} rows saved in clickhouse ')
        return True, None

    except Exception as e:
        print('DB_UTILS: can not insert Data to clickhouse: '+str(e))
        return False, str(e)




class DBcapturedMAC:
    """ sql queries for table macs_captured"""

    def __init__(self,conn):
            self.conn = conn
            self.t = macs_captured

    async def select_by_time(self,snifs,time=60):
        since = datetime.now() - timedelta(minutes=time)
        t = self.t
        #query = t.select().where(t.c.created_at > since).order_by(t.c.id)
        #print(query)
        snifs_str =  ",".join([f"'{x}'" for x in snifs])
        query = f"""SELECT * FROM {t} as t 
        WHERE t.created_at > '{since}' AND t.snifid IN ({snifs_str})
        ORDER BY t.id
        """

        cursor = await self.conn.execute(query)
        result = [dict(row) async for row in cursor]
        #print(result)
        return result




#this is a DEAD END way
# AttributeError: 'Engine' object has no attribute '_contextual_connect'
# https://github.com/aio-libs/aiomysql/issues/39
# https://github.com/aio-libs/aiopg/issues/19

# мы не можем работать с сессиями ORM в асинк режиме :(

# class DBcapturedMAC:

    
#     """ sql queries for table macs_captured"""
#     def __init__(self,request):
#         Session = sessionmaker()
#         engine = request.app['db']
        
#         Session.configure(bind=engine)
#         self.s = Session()

#     async def select_by_time(self):
#         since = datetime.now() - timedelta(hours=1)
#         s = self.s
#         #query = await s.query(macs_captured).filter(macs_captured.created_at > since).all()
#         query = await s.query(macs_captured).all()
#         return query
#         #cursor = await conn.execute(query)
#         #return await cursor.fetchall()

#     async def commit(self):
#         await self.s.commit()

#     async def __del__(self):
#         await self.s.close()


        