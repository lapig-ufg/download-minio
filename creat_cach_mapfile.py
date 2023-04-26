import os
import pathlib
import pickle
import re

import mappyfile
from pymongo import MongoClient

from app.config import logger, settings
from app.model.mapfile import MapFileLayers, Metadata


def remove__type__(obj):
    try:
        obj.pop('__type__')
        return obj
    except:
        return obj


def remove_error(text):
    while True:
        palavra = re.search(r'(\[\w+_\w+\])+', text)
        if not palavra is None:
            palavra = palavra.group()
            text = text.replace(palavra, palavra.replace('_', ''))
        else:
            break
    return text


file_ows = f'{settings.CACHE_MAP}{settings.FILE_MAP_CACH}'
listl_layer_ows = f'{settings.CACHE_MAP}{settings.LISTL_LAYER_OWS}'
layer_metata_ows = f'{settings.CACHE_MAP}{settings.LAYER_METATA_OWS}'


if not os.environ.get('LAPIG_ENV') == 'production' and os.path.exists(
    file_ows
):
    logger.debug('Voce ja tem um mapfile')
else:
    logger.info('Lendo description')
    with MongoClient(settings.MONGODB_URL) as client:
        db = client.ows
        tmp = db.layers.find(
            {
                'layertypes.valueType': {'$exists': True},
                'layertypes.origin.sourceService': 'internal',
                '_id': {'$ne': 'basemaps'},
                '_id': {'$ne': 'basemaps'},
            }
        )
        traducao = db.languages.find_one({'_id': 'pt'})
        new_layers = {}
        lista_layers = []
        for layers in tmp:
            layertype = layers['_id']

            tra_tmp = traducao['layertype']
            for obj in layers['layertypes']:
                layer = obj['valueType']
                metadata = {}

                old_metadata = obj['metadata']

                try:
                    filters = [f['valueFilter'] for f in obj['filters']]
                except:
                    filters = None
                for name in obj['metadata']:
                    try:
                        if old_metadata[name] == 'translate':
                            metadata[name] = tra_tmp[layer]['metadata'][name]
                        else:
                            metadata[name] = old_metadata[name]
                    except:
                        metadata[name] = old_metadata[name]

                tmp = {
                    'layer': layer,
                    'layertype': layertype,
                    'metadata': metadata,
                    'fileType': [
                        x
                        for x in obj['download']
                        if obj['download'][x] is True
                    ],
                }
                if not filters is None:
                    tmp['filters'] = filters
                new_layers[layer] = tmp
                lista_layers.append(layer)

    logger.info('Lendo mapfile')

    with open(settings.MAPFILE, 'r') as file:
        _map = file.read()
        _map = remove_error(_map)

    map = {}
    file = mappyfile.loads(_map)['layers']

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
                map[name]['connectiontype'][d['connectiontype']] = d[
                    'connection'
                ]
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
                    map[name]['connectiontype'][d['connectiontype']][
                        key
                    ] = value
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
        pickle.dump(lista_layers, f)

    with open(layer_metata_ows, 'wb') as f:
        pickle.dump(new_layers, f)
