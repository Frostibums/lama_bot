from celery import Celery
from celery.schedules import crontab

redis_host = 'redis://redis:6379/0'
celery_app = Celery(main='bot', broker=redis_host)
celery_app.conf.broker_url = redis_host
celery_app.conf.result_backend = redis_host
celery_app.autodiscover_tasks()

celery_app.conf.update(result_expires=3600, enable_utc=True, timezone='UTC')

# celery beat tasks
celery_app.conf.beat_schedule = {
    'notify_about_subscription_expiration': {
        'task': 'bot.tasks.notify_about_subscription_expiration',
        'schedule': crontab(hour='20', minute='45')
    },
    'kick_users_with_exp_sub': {
        'task': 'bot.tasks.kick_users_with_exp_sub',
        'schedule': crontab(hour='21', minute='00')
    },
}
