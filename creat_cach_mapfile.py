import mappyfile
import pathlib
import os

from app.config import settings, logger
import re
import pickle

map = {}
file=mappyfile.open(settings.MAPFILE)['layers']

def remove__type__(obj):
    try:
        obj.pop('__type__')
        return obj
    except:
        return obj
    

total = len(file)

for n, i in enumerate(file,1):
    porcet = (n * 100)/total
    try:
        d = dict(i)
        regex = r'^(.{0,256} [f|F][r|R][o|O][m|M] )|( [w|W][h|H][e|E][r|R][e|E] .{0,256})$'
        name = d['name']
        #logger.debug(f'Completado: {porcet:.1f}% Camada: {name}')
        data = ''
        for dt in d['data']:
            data = f"{data}{dt}"
        map[name] = {}
        try:
            map[name]['projection'] = d['projection']
        except:
            logger.warning(f'camada: {name} projection')
        try:
            map[name]['type'] = d['type']
        except:
            logger.warning(f'camada: {name} type')
        try:
            map[name]['metadata'] = remove__type__(d['metadata'])
        except:
            logger.warning(f'camada: {name} metadata')
        
        if '.tif' in data or '.tiff' in data or '.shp' in data:
            map[name]['file'] = data
        elif d["connectiontype"] == 'OGR':
            map[name]['data'] = data
            map[name]["connectiontype"] =  {d["connectiontype"]:{}}
            map[name]["connectiontype"][d["connectiontype"]] = d["connection"]
        else:
            map[name]['data'] = data
            map[name]['table'] = re.sub(regex, '',data)
            map[name]["connectiontype"] =  {d["connectiontype"]:{}}
            for key, value in [tuple(connection.split('=')) for connection in  d["connection"].split(' ')]:
                map[name]["connectiontype"][d["connectiontype"]][key] = value
    except Exception as e:
        logger.exception(f'Error {i}')
    

path_cach_ows = 'app/data/'
file_ows = f'{path_cach_ows}ows.map.cache.lgobj'
if os.path.exists(file_ows):
  os.remove(file_ows)
else:
  logger.debug("The file does not exist")

if not os.path.exists(path_cach_ows):
    os.mkdir(path_cach_ows)
else:
    logger.debug("Folder already exists")
    
with open(file_ows, 'wb') as f:
    pickle.dump(map, f)

os.system("gunicorn -k  uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 -w 4 -t 0 app.server:app")