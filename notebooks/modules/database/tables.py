from sqlalchemy import Table, MetaData, Column, String, Text

meta_obj = MetaData()
iot_export_status_table = Table(
    "iot_export_status",
    meta_obj,
    Column("tenant_id", String(64), primary_key=True),
    Column("thing_type", String(100), primary_key=True),
    Column("property_set_type", String(100), primary_key=True),
    Column("start_date", String(20), primary_key=True),
    Column("end_date", String(20), primary_key=True),
    Column("status", Text),
    Column("message", Text),
    Column("request_id", String(64)),
)
