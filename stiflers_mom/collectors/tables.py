import datetime
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from stiflers_mom.migrations import metadata
#from stiflers_mom.users.enums import UserGender


__all__ = ['macs_captured']


#gender_enum = postgresql.ENUM(UserGender)


macs_captured = sa.Table(
    'macs_captured', metadata,
    sa.Column('id', sa.BigInteger, primary_key=True, index=True),
    sa.Column('snifid', sa.String(12), nullable=False), # 6c3b6b931fed
    sa.Column('mac', sa.String(17)), # dc:8b:28:4f:94:bc
    sa.Column('vendor', sa.Text),
    sa.Column('frames_with_fine_rssi', sa.Integer),
    sa.Column('frames_count', sa.Integer),
    sa.Column('rssi_max', sa.Integer),
    sa.Column('rssi_avg', sa.Integer),
    sa.Column('notified_count', sa.Integer),
    sa.Column('known_from', sa.Integer),
    sa.Column('timestamp', sa.Integer),
    sa.Column('created_at',sa.DateTime, default=datetime.datetime.utcnow)
)
