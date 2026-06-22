from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio
import logging
import requests
from database import SessionLocal, engine
from models.clima import Clima, Base
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger('meteo-wanka')

app = FastAPI(
    title='Meteo Wanka API',
    version='1.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

Base.metadata.create_all(bind=engine)

# Modelo Pydantic para actualizar registros
class ClimaUpdate(BaseModel):
    temperatura: float
    humedad: int
    viento: float

scheduler = BackgroundScheduler(
    job_defaults={'coalesce': True, 'max_instances': 1},
    daemon=True,
)

API_KEY = 'cfec75adb170c3c81902d5a470680553'
WEATHER_URL = (
    'https://api.openweathermap.org/data/2.5/weather'
    '?q=Huancayo,PE'
    '&appid={api_key}'
    '&units=metric'
    '&lang=es'
)


def obtener_y_guardar_clima():
    url = WEATHER_URL.format(api_key=API_KEY)
    logger.info('Solicitando datos de OpenWeather: %s', url)

    try:
        respuesta = requests.get(url, timeout=15)
        respuesta.raise_for_status()
        datos = respuesta.json()
    except requests.RequestException as err:
        logger.error('Error al obtener datos de OpenWeather: %s', err)
        raise

    temperatura = datos['main']['temp']
    humedad = datos['main']['humidity']
    viento = datos['wind']['speed']
    descripcion = datos['weather'][0]['description']
    icono = datos['weather'][0]['icon']

    if temperatura <= 2:
        alerta = 'ALTO RIESGO DE HELADA'
    elif temperatura <= 5:
        alerta = 'RIESGO MODERADO DE HELADA'
    else:
        alerta = 'SIN RIESGO DE HELADA'

    try:
        with SessionLocal() as db:
            nuevo_registro = Clima(
                ciudad='Huancayo',
                temperatura=temperatura,
                humedad=humedad,
                viento=viento,
                descripcion=descripcion,
                alerta=alerta,
            )
            db.add(nuevo_registro)
            db.commit()
    except Exception as err:
        logger.error('Error al guardar registro en la base de datos: %s', err)
        raise

    return {
        'ciudad': 'Huancayo',
        'temperatura': temperatura,
        'humedad': humedad,
        'viento': viento,
        'descripcion': descripcion,
        'icono': icono,
        'alerta': alerta,
        'hora_consulta': str(datetime.now()),
    }


async def run_in_thread(fn, *args, **kwargs):
    return await asyncio.to_thread(fn, *args, **kwargs)


@app.on_event('startup')
def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            obtener_y_guardar_clima,
            'interval',
            minutes=20,
            id='obtener_y_guardar_clima',
            replace_existing=True,
        )
        scheduler.start()
        logger.info('Scheduler iniciado')


@app.on_event('shutdown')
def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info('Scheduler detenido')


@app.get('/')
def inicio():
    return {
        'proyecto': 'Meteo Wanka',
        'estado': 'Backend funcionando',
    }


@app.get('/clima')
async def obtener_clima():
    return await run_in_thread(obtener_y_guardar_clima)


@app.get('/clima/historico')
async def obtener_historico():
    def leer_historico():
        with SessionLocal() as db:
            registros = (
                db.query(Clima)
                .order_by(Clima.fecha_registro)
                .all()
            )
            return [
                {
                    'id': r.id,
                    'ciudad': r.ciudad,
                    'temperatura': r.temperatura,
                    'humedad': r.humedad,
                    'viento': r.viento,
                    'descripcion': r.descripcion,
                    'alerta': r.alerta,
                    'fecha': str(r.fecha_registro),
                }
                for r in registros
            ]
    return await run_in_thread(leer_historico)


@app.delete('/clima/{id}')
def eliminar_registro(id: int):
    """Elimina un registro de clima por ID"""
    def borrar():
        with SessionLocal() as db:
            registro = db.query(Clima).filter(Clima.id == id).first()
            
            if not registro:
                raise HTTPException(status_code=404, detail=f'Registro {id} no encontrado')
            
            db.delete(registro)
            db.commit()
            
            return {
                'mensaje': f'Registro {id} eliminado correctamente',
                'id': id
            }
    
    try:
        return asyncio.run(run_in_thread(borrar))
    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error al eliminar registro: %s', e)
        raise HTTPException(status_code=500, detail=str(e))


@app.put('/clima/{id}')
def actualizar_registro(id: int, datos: ClimaUpdate):
    """Actualiza temperatura, humedad y viento de un registro"""
    def actualizar():
        with SessionLocal() as db:
            registro = db.query(Clima).filter(Clima.id == id).first()
            
            if not registro:
                raise HTTPException(status_code=404, detail=f'Registro {id} no encontrado')
            
            registro.temperatura = datos.temperatura
            registro.humedad = datos.humedad
            registro.viento = datos.viento
            
            db.commit()
            db.refresh(registro)
            
            return {
                'mensaje': 'Registro actualizado correctamente',
                'id': id,
                'temperatura': registro.temperatura,
                'humedad': registro.humedad,
                'viento': registro.viento
            }
    
    try:
        return asyncio.run(run_in_thread(actualizar))
    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error al actualizar registro: %s', e)
        raise HTTPException(status_code=500, detail=str(e))
