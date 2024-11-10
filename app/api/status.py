from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytz
from fastapi import APIRouter, HTTPException, Path, Query
from pymongo import MongoClient

from app.config import logger, settings
from app.util.functions import number2text

router = APIRouter()


@router.get(
    '/jobs',
    name='Get Jobs',
    response_description='Get status do Lapig Jobs',
)
async def get_status_jobs():
    with MongoClient(settings.MONGODB_URL) as client:
        db = client['lapig-jobs'].jobs
        aggre_result = db.aggregate(
            [
                {
                    '$group': {
                        '_id': '$status',
                        'count': {'$sum': 1},
                    },
                }
            ]
        )
        RUNNING = db.find_one({'status': 'RUNNING'})
        result = {}

        for r in aggre_result:
            result[r['_id'].lower()] = r['count']

        if RUNNING:
            now = datetime.now().astimezone(pytz.utc)
            start = RUNNING['startRunning'].replace(tzinfo=pytz.utc)
            time = (now - start).total_seconds() / 60.0
            result['running'] = {'runtime_minutes': time}
        TEMPOMEDIO = db.find(
            {'status': 'DONE'}, {'startRunning': 1, 'endRunning': 1}
        )
        df = pd.DataFrame(TEMPOMEDIO)
        df['time'] = df['endRunning'] - df['startRunning']
        result['mean_running_minutes'] = df['time'].mean() / 60
        result['max_running_minutes'] = df['time'].max() / 60
        result['min_running_minutes'] = df['time'].min() / 60
        return result


@router.get(
    '/access',
    name='Get access',
    response_description='Get status access',
)
async def get_status_access():
    with MongoClient(settings.MONGODB_URL) as client:
        db = client.analytics.dowloadMinioProd
        date = datetime.now() - timedelta(30)
        result = db.aggregate(
            [
                {'$match': {'created_at': {'$gte': date}}},
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'date': '$created_at',
                                'format': '%Y-%m-%d',
                            }
                        },
                        'value': {'$sum': 1},
                    }
                },
                {'$sort': {'_id': 1}},
            ]
        )
        x = []
        y = []
        for c in result:
            x.append(c['_id'])
            y.append(c['value'])

        ymax = int(np.mean([np.percentile(y, 80), np.percentile(y, 25)])) + 5
        annotations = []
        texts = [number2text(i) for i in y]
        for i, text in enumerate(texts):
            annotations.append(
                {
                    'x': x[i],
                    'y': 5,
                    'text': text,
                    'showarrow': False,
                    'font': {'color': '#000000', 'size': 12},
                }
            )

        return {
            'date': [{'x': x, 'y': y, 'type': 'bar'}],
            'layout': {
                'annotations': annotations,
                'yaxis': {
                    'range': [0, ymax],
                },
            },
        }
