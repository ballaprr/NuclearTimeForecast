from datetime import timedelta
from nrc_data.models import ReactorStatus, ReactorForecast, StubOutage


def detect_sub_outages_for_reactor(reactor_name, threshold_drops=15):
    try:
        reactor = Reactor.objects.get(name=reactor_name)
    except Reactor.DoesNotExist:
        return

    latest_actual = ReactorStatus.objects.filter(unit=reactor_name).order_by('-report_date').first()
    if not latest_actual:
        return

    forecast = ReactorForecast.objects.filter(
        reactor=reactor,
        df=latest_actual.report_date
    ).first()

    if not forecast:
        return

    actual = latest_actual.power
    predicted = forecast.yhat

    drop = predicted - actual
    if drop >= threshold_drops:
        StubOutage.objects.get_or_create(
            reactor=reactor, 
            date_detected=latest_actual.report_date,
            defaults={
                'description': f"Detected {drop:.1f}% drop vs forecast ({predicted:.1f} → {actual:.1f})",
                'auto_detected': True,
                'confirmed': False,
            }
        )