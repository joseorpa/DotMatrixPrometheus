# my_metrics.py

class CPULoadMetric:
    """
    Fetches average CPU usage across all cores.
    Assumes node_exporter is running.
    """
    title = "Cluster CPU Usage (%)"
    unit = "%"
    
    # The actual PromQL query
    # We use 'irate' for high sensitivity to spikes
    query = '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)'

class DeploymentCountMetric:
    """
    Fetches the number of successful deployments.
    (Example uses a hypothetical metric - adjust to your environment)
    """
    title = "Total Deployments (Last Hour)"
    unit = "Count"
    
    # Example: increase in deployment counter over the last hour
    query = 'increase(deployment_events_total[1h])'

class MemoryUsageMetric:
    """
    Fetches Memory Usage.
    """
    title = "Memory Usage (GB)"
    unit = "GB"
    
    # Calculation: Total - Available
    query = 'node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes'
    
    # Optional: A custom transform function to convert Bytes to GB
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)
