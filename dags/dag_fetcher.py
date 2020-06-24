"""
Code that goes along with the Airflow tutorial located at:
https://github.com/apache/airflow/blob/master/airflow/example_dags/tutorial.py
"""
import sys
import os
import datetime 
import logging
import importlib

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.utils import dates
from airflow.utils.dates import cron_presets

from etl_server.pipelines.models import Models as PipelineModels

etl_models = PipelineModels(os.environ['ETLS_DATABASE_URL'])

default_args = {
    'owner': 'Airflow',
    'depends_on_past': False,
    'start_date': dates.days_ago(1),
    'is_paused_upon_creation': False
}

for pipeline in etl_models.all_pipelines():
    dag_id = pipeline['id']
    logging.info('Initializing DAG %s', dag_id)

    schedule = pipeline['schedule']
    if isinstance(schedule, str):
        if schedule not in cron_presets:
            if len(schedule.split()) not in (5, 6):
                if '@' + schedule in cron_presets:
                    schedule = '@' + schedule
                else:
                    schedule = None
    else:
        schedule = None

    try:
        dag = DAG(dag_id, default_args=default_args, schedule_interval=schedule)

        kind = pipeline['kind']
        operator = importlib.import_module('.' + kind, package='operators').operator

        t1 = PythonOperator(task_id=dag_id,
                            python_callable=operator,
                            op_args=[pipeline['name'], pipeline['params']],
                            dag=dag)
        globals()[dag_id] = dag
    except Exception as e:
        logging.error(f'Failed to create a DAG with id {dag_id}, schedule {schedule} because {e}')


try:
    task_id = '_clean_scheduler_logs' 
    dag_id = task_id + '_dag'
    schedule = '0 * * * *'
    dag = DAG(dag_id, default_args=default_args,
              schedule_interval=schedule)
    clean_scheduler_logs = BashOperator(task_id=task_id,
                                        bash_command='cd /app/airflow/logs/scheduler/ && rm -rf * && echo cleaned',
                                        dag=dag)
    globals()[dag_id] = dag
except Exception as e:
    logging.error(f'Failed to create a DAG with id {dag_id}, schedule {schedule} because {e}')
