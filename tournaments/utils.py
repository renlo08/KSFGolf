import random
import datetime

from django.utils.text import slugify


def slugify_instance_str(instance, save=False, new_slug=None):
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.__str__())
    Klass = instance.__class__
    qs = Klass.objects.filter(slug=slug).exclude(id=instance.id)
    if qs.exists():
        # auto generate new slug
        rand_int = random.randint(300_000, 500_000)
        slug = f"{slug}-{rand_int}"
        return slugify_instance_str(instance, save=save, new_slug=slug)
    instance.slug = slug
    if save:
        instance.save()
    return instance


def stringify_time_delta(date: datetime.date) -> str:
    current_time = datetime.datetime.now(tz=datetime.timezone.utc)  # This is timezone-aware
    time_difference = current_time - date

    if time_difference < datetime.timedelta(minutes=1):
        return f"less than 1 minute ago."
    elif time_difference < datetime.timedelta(hours=1):
        minutes = int(time_difference.total_seconds() / 60)
        return f"{minutes} minutes ago."
    elif time_difference < datetime.timedelta(days=1):
        hours = int(time_difference.total_seconds() // 3600)
        return f"{hours} hours ago."
    else:
        return f"on {date.strftime('%dd.%mm.%YY')}."
