import itertools
import random
import datetime
import statistics

from django.db.models import QuerySet
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
        return f"less than 1 minute ago"
    elif time_difference < datetime.timedelta(hours=1):
        minutes = int(time_difference.total_seconds() / 60)
        return f"{minutes} minutes ago"
    elif time_difference < datetime.timedelta(days=1):
        hours = int(time_difference.total_seconds() // 3600)
        return f"{hours} hours ago"
    elif time_difference < datetime.timedelta(days=5):
        days = int(time_difference.total_seconds() // (3600 * 24))
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        return f"{date.strftime('%d.%m.%Y')}"


def order_flights_by_handicap(competitors: QuerySet):
    # convert QuerySet to list if competitors is QuerySet
    competitors = list(competitors.order_by('hcp'))

    flights = []
    remainder = len(competitors) % 3

    # If the competitors are not a multiple of 3, create a group of 2 first
    if remainder != 0:
        flights.append(competitors[:2])
        competitors = competitors[2:]  # remaining competitors

    # Divide the rest of the competitors into flights of 3
    for i in range(0, len(competitors), 3):
        flights.append(competitors[i:i + 3])

    return flights


def get_flight_avg(flight):
    hcp_values = [competitor.hcp for competitor in flight]
    return statistics.mean(hcp_values)


def form_basic_high_mid_low_flights(competitors: QuerySet):
    """ Basic strategy to form the 'HML' flights """
    flights = []
    competitors = competitors.order_by('hcp')
    competitors_as_list = list(competitors)

    nr_flights = competitors.count() // 3
    if competitors.count() % 3 != 0:
        nr_flights += 1

        # First flight is constituted of the best hcp player with a mid-hcp player
        first_flight = (competitors_as_list.pop(0), competitors_as_list.pop(competitors.count() // 2))
        flights.append(first_flight)

    while True:
        if len(competitors_as_list) == 3:
            flights.append(tuple(competitors_as_list))
            break
        # collect the remaining best
        first_player = competitors_as_list.pop(0)
        second_player = competitors_as_list.pop(len(competitors_as_list) // 2)
        third_player = competitors_as_list.pop(-1)
        flight = (first_player, second_player, third_player)
        flights.append(flight)
    return flights


def form_high_middle_low_flights(competitors: QuerySet):
    """ Form flights of competitor, each flight should be constituted of high-mid-low handicap players
    :param competitors: The competitors to form flights
    and a mid-field player.
    """

    # Convert QuerySet to list and sort in descending order of `hcp`
    competitors = competitors.order_by('-hcp')

    nr_flights = competitors.count() // 3
    if competitors.count() % 3 != 0:
        nr_flights += 1

    total_flights_combination = []
    if competitors.count() % 3 != 0:  # Number of competitors are not multiple of 3, create a group of 2 first
        total_flights_combination = list(itertools.combinations(competitors, 2))

    total_flights_combination += list(itertools.combinations(competitors, 3))

    # All combinations of tuples
    all_combo_flights = list(itertools.combinations(total_flights_combination, nr_flights))

    # Checking and keeping only those combinations where all numbers are present and each only once
    valid_flight_combo = []
    for combo in all_combo_flights:
        # Extract all the competitors in the combinaison
        competitors_combo = [competitor for flight in combo for competitor in flight]

        # Accept the combination if all the competitor are present in the flights and only once
        if set(competitors_combo) == set(competitors) and len(competitors_combo) == competitors.count():
            flight_avg_hcp = [get_flight_avg(f) for f in combo]
            valid_flight_combo.append((flight_avg_hcp, combo))

    # Select the combo where the flight_avg_hcp are the closest
    _, closest_avg_hcp_combo = min(valid_flight_combo, key=lambda x: max(x[0]) - min(x[0]))

    # Sort each competitor in the flight by ascending order of hcp
    sorted_flights = [sorted(flight, key=lambda competitor: competitor.hcp) for flight in closest_avg_hcp_combo]

    return sorted_flights

