# app/tasks/celery_app.py
from celery import Celery

celery_app = Celery(
    "app", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)

# Включаем JSON
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

# Для asyncio нужно явно использовать event loop
celery_app.conf.worker_pool = "solo"  # solo или asyncio

celery_app.autodiscover_tasks(["app.tasks"])
