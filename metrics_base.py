# metrics_base.py
from datetime import datetime, timedelta
from prometheus_api_client import PrometheusConnect
from urllib3.exceptions import NewConnectionError, MaxRetryError
from requests.exceptions import ConnectionError, RequestException


class PrometheusConnectionError(Exception):
    """Raised when unable to connect to Prometheus server."""
    pass


def parse_datetime(dt_string, default_year=None):
    """
    Parse a datetime string in various formats.
    
    Supported formats:
        - "2024-11-13 08:00" or "2024-11-13T08:00"
        - "11-13 08:00" or "11/13 08:00" (uses current or specified year)
        - "Nov 13 08:00" or "November 13 8:00"
        - "13-Nov-2024 08:00"
        - "08:00" (uses today's date)
    
    Returns:
        datetime object
    """
    if default_year is None:
        default_year = datetime.now().year
    
    dt_string = dt_string.strip()
    
    # List of formats to try
    formats = [
        # Full datetime formats
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        
        # Date with time (no year - will add current year)
        "%m-%d %H:%M",
        "%m/%d %H:%M",
        "%d-%m %H:%M",
        
        # Named month formats
        "%b %d %H:%M",      # "Nov 13 08:00"
        "%B %d %H:%M",      # "November 13 08:00"
        "%d %b %H:%M",      # "13 Nov 08:00"
        "%d %B %H:%M",      # "13 November 08:00"
        "%b %d %Y %H:%M",   # "Nov 13 2024 08:00"
        "%B %d %Y %H:%M",   # "November 13 2024 08:00"
        "%d-%b-%Y %H:%M",   # "13-Nov-2024 08:00"
        "%d-%B-%Y %H:%M",   # "13-November-2024 08:00"
        
        # Time only (uses today's date)
        "%H:%M",
        "%H:%M:%S",
        
        # Date only (uses 00:00 time)
        "%Y-%m-%d",
        "%m-%d",
        "%m/%d",
        "%b %d",
        "%B %d",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(dt_string, fmt)
            
            # If year is 1900 (default when not specified), use default_year
            if dt.year == 1900:
                dt = dt.replace(year=default_year)
            
            return dt
        except ValueError:
            continue
    
    raise ValueError(
        f"Could not parse datetime: '{dt_string}'\n"
        "Supported formats:\n"
        "  - '2024-11-13 08:00'\n"
        "  - '11-13 08:00' or '11/13 08:00'\n"
        "  - 'Nov 13 08:00' or 'November 13 08:00'\n"
        "  - '08:00' (uses today's date)"
    )


def calculate_step(start_time, end_time):
    """
    Calculate appropriate step size based on time range.
    Returns step as a string suitable for Prometheus.
    """
    duration = end_time - start_time
    total_minutes = duration.total_seconds() / 60
    
    if total_minutes <= 60:          # Up to 1 hour
        return '30s'
    elif total_minutes <= 180:       # Up to 3 hours
        return '1m'
    elif total_minutes <= 720:       # Up to 12 hours
        return '2m'
    elif total_minutes <= 1440:      # Up to 24 hours
        return '5m'
    elif total_minutes <= 4320:      # Up to 3 days
        return '15m'
    elif total_minutes <= 10080:     # Up to 7 days
        return '30m'
    else:                            # More than 7 days
        return '1h'


class MetricFetcher:
    def __init__(self, url):
        self.url = url
        self.prom = PrometheusConnect(url=url, disable_ssl=True)

    def get_data(self, metric_class, minutes=60, start_time=None, end_time=None, step=None):
        """
        Takes a Metric Class (from my_metrics.py), runs the query,
        and returns cleaned X and Y lists.
        
        Args:
            metric_class: A metric class with 'query' attribute
            minutes: Minutes to look back (used if start_time/end_time not provided)
            start_time: Optional datetime for range start
            end_time: Optional datetime for range end
            step: Optional step size (auto-calculated if not provided)
        
        Returns:
            Tuple of (x_labels, y_values) or (None, None) if no data
        
        Raises:
            PrometheusConnectionError: If unable to connect to Prometheus server
        """
        # Determine time range
        if start_time is not None and end_time is not None:
            # Use provided time range
            pass
        elif start_time is not None:
            # Start time provided, end is now
            end_time = datetime.now()
        elif end_time is not None:
            # End time provided, calculate start from minutes
            start_time = end_time - timedelta(minutes=minutes)
        else:
            # Default: last N minutes
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=minutes)
        
        # Auto-calculate step if not provided
        if step is None:
            step = calculate_step(start_time, end_time)

        # Fetch data with error handling
        try:
            result = self.prom.custom_query_range(
                query=metric_class.query,
                start_time=start_time,
                end_time=end_time,
                step=step
            )
        except (ConnectionError, NewConnectionError, MaxRetryError) as e:
            # Extract the root cause message
            error_msg = str(e)
            if hasattr(e, '__cause__') and e.__cause__:
                error_msg = str(e.__cause__)
                if hasattr(e.__cause__, '__cause__') and e.__cause__.__cause__:
                    error_msg = str(e.__cause__.__cause__)
            
            raise PrometheusConnectionError(
                f"Cannot connect to Prometheus at {self.url}\n"
                f"   Error: {error_msg}\n\n"
                f"   Please check:\n"
                f"   • The Prometheus URL is correct\n"
                f"   • The server is running and accessible\n"
                f"   • Network/DNS configuration\n"
                f"   • Firewall settings"
            ) from None
        except RequestException as e:
            raise PrometheusConnectionError(
                f"Request to Prometheus failed at {self.url}\n"
                f"   Error: {e}\n\n"
                f"   Please check:\n"
                f"   • The Prometheus URL is correct\n"
                f"   • The server is running and accessible"
            ) from None

        if not result:
            return None, None

        # Extract the first series found
        # (For more complex dashboards, you might handle multiple series here)
        data_points = result[0]['values']

        # Process X Axis (Time)
        timestamps = [datetime.fromtimestamp(float(x[0])) for x in data_points]
        
        # Determine date format based on time range
        duration = end_time - start_time
        if duration.days > 0:
            # Show date and time for multi-day ranges
            x_labels = [dt.strftime("%m/%d %H:%M") for dt in timestamps]
        else:
            # Show only time for same-day ranges
            x_labels = [dt.strftime("%H:%M") for dt in timestamps]

        # Process Y Axis (Values)
        y_values = []
        for x in data_points:
            val = float(x[1])
            # Check if the metric class has a custom transform function
            if hasattr(metric_class, 'transform'):
                val = metric_class.transform(val)
            y_values.append(val)

        return x_labels, y_values
