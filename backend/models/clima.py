from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Clima(Base):
    __tablename__ = "clima"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ciudad = Column(String(100))
    temperatura = Column(Float)
    humedad = Column(Integer)
    viento = Column(Float)
    descripcion = Column(String(200))
    alerta = Column(String(100))
    fecha_registro = Column(DateTime, default=datetime.now)
