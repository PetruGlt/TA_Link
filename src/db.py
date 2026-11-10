from sqlalchemy import create_engine, MetaData, Column, Integer, Table, ForeignKey, Text, Date
from dotenv import load_dotenv
import os

from sqlalchemy.dialects.postgresql import TIMESTAMP

load_dotenv()

engine = create_engine(os.environ['DATABASE_URL'])

# with engine.connect() as conn:
#     print(conn.execute(text("select * from accounts")).fetchall())

metadata = MetaData()

accounts = Table('accounts', metadata,
                 Column('account_id', Integer, primary_key=True),
                 Column('name', Text, nullable=False),
                 Column('address', Text),
                 )
daily_status = Table('daily_status', metadata,
                     Column('account', Integer),
                     Column('queue', Text),
                     Column('status', Text),
                     Column('changed_datetime', TIMESTAMP(precision=0)),
                     Column('changed_datetime_raw', Text),
                     Column('source_file', Text),
                     Column('file_date', Date),
                     )

monthly_status = Table('monthly_status', metadata,
                       Column('account', Integer, ForeignKey('accounts.account_id')),
                       Column('queue', Text),
                       Column('status', Text),
                       Column('month', Integer, nullable=False),
                       Column('snapshot_ym', Text),
                       Column('snapshot_year', Integer),
                       Column('source_file', Text),
                       )


metadata.create_all(engine)