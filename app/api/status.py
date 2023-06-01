from fastapi import APIRouter, HTTPException, Path, Query
from pymongo import MongoClient
from datetime import timedelta, datetime
from app.config import logger, settings
import pandas as pd
import pytz

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
                        [{
                                "$group": {
                                        "_id": "$status",
                                        "count": { "$sum": 1 },
                                },
                        }
                        ]
                )
                RUNNING = db.find_one({'status':'RUNNING'})
                result = {}

                for r in aggre_result:
                        result[r['_id'].lower()] = r['count'] 

                if RUNNING:
                        now = datetime.now().astimezone(pytz.utc)
                        start = RUNNING['startRunning'].replace(tzinfo=pytz.utc)
                        logger.debug(RUNNING)
                        logger.debug(f"{RUNNING['startRunning']},{now}")
                        
                        time = (now-start).total_seconds() / 60.0
                        result['running'] = {'runtime_minutes':time}
                TEMPOMEDIO = db.find({'status':'DONE'},{'startRunning':1,'endRunning':1})
                df = pd.DataFrame(TEMPOMEDIO)
                df['time'] = df['endRunning'] - df['startRunning']
                result['mean_running_minutes'] = df['time'].mean() / 60
                result['max_running_minutes'] = df['time'].max() / 60
                result['min_running_minutes'] = df['time'].min() / 60
                return result


