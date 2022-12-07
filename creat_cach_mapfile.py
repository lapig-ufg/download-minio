import os
import pathlib
import pickle
import re
from app.config import logger

import mappyfile

from app.config import logger, settings
from app.model.mapfile import MapFileLayers, Metadata


def remove__type__(obj):
    try:
        obj.pop('__type__')
        return obj
    except:
        return obj


file_ows = f'{settings.CACHE_MAP}{settings.FILE_MAP_CACH}'
listl_layer_ows = f'{settings.CACHE_MAP}{settings.LISTL_LAYER_OWS}'
layer_metata_ows = f'{settings.CACHE_MAP}{settings.LAYER_METATA_OWS}'


if not os.environ.get('LAPIG_ENV') == 'production' and os.path.exists(file_ows):
    logger.debug('Voce ja tem um mapfile')
else:
    map = {}
    file = mappyfile.open(settings.MAPFILE)['layers']


    total = len(file)

    for n, i in enumerate(file, 1):
        porcet = (n * 100) / total
        try:
            d = dict(i)
            regex = r'^(.{0,256} [f|F][r|R][o|O][m|M] )|( [w|W][h|H][e|E][r|R][e|E] .{0,256})$'
            name = d['name']
            # logger.debug(f'Completado: {porcet:.1f}% Camada: {name}')
            data = ''
            for dt in d['data']:
                data = f'{data}{dt}'
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
            elif d['connectiontype'] == 'OGR':
                map[name]['data'] = data
                map[name]['connectiontype'] = {d['connectiontype']: {}}
                map[name]['connectiontype'][d['connectiontype']] = d['connection']
            else:
                map[name]['data'] = data
                table = re.sub(regex, '', data).split(')')[0].split(' ')
                if table[0] == '':
                    map[name]['table'] = table[1]
                else:
                    map[name]['table'] = table[0]

                map[name]['connectiontype'] = {d['connectiontype']: {}}
                for key, value in [
                    tuple(connection.split('='))
                    for connection in d['connection'].split(' ')
                ]:
                    map[name]['connectiontype'][d['connectiontype']][key] = value
        except Exception as e:
            logger.exception(f'Error {i}')



    if os.path.exists(file_ows):
        os.remove(file_ows)
    else:
        logger.debug('The file does not exist')
        
    if os.path.exists(listl_layer_ows):
        os.remove(listl_layer_ows)
    else:
        logger.debug('The file does not exist')
        
    if os.path.exists(layer_metata_ows):
        os.remove(layer_metata_ows)
    else:
        logger.debug('The file does not exist')

    if not os.path.exists(settings.CACHE_MAP):
        os.mkdir(settings.CACHE_MAP)
    else:
        logger.debug('Folder already exists')

    with open(file_ows, 'wb') as f:
        pickle.dump(map, f)

    with open(listl_layer_ows, 'wb') as f:
        dateset = sorted(list(set([name for name in map])))
        pickle.dump(dateset, f)
        
    with open(layer_metata_ows, 'wb') as f:
        all_metada = [
            MapFileLayers(
                name=name,
                projection = map[name]['projection'],
                type = map[name]['type'],
                metadata = Metadata(
                    ows_title=map[name]['metadata']['ows_title'],
                    ows_abstract=map[name]['metadata']['ows_abstract'],
                    gml_exclude_items=map[name]['metadata']['gml_exclude_items'],
                    gml_include_items=map[name]['metadata']['gml_include_items'],
                    gml_geometries=map[name]['metadata']['gml_geometries']
                        )).dict()
                        for name in map]
        pickle.dump(all_metada, f)