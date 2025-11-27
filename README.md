# DotMatrixPrometheus

Lightweight terminal graphics for Prometheus metrics visualization. Includes built-in support for multiple performance dashboards from [cloud-bulldozer/performance-dashboards](https://github.com/cloud-bulldozer/performance-dashboards).

## Features

- 📊 Terminal-based ASCII charts using [plotext](https://github.com/piccolomo/plotext)
- 📈 **Multi-metric grid display** - View multiple metrics side by side
- 🕐 Flexible time range selection (last N minutes, or specific date/time ranges)
- 🔥 100+ pre-configured metrics from 7 performance dashboards
- 🎯 Easy to extend with custom metrics
- 🌐 Configurable Prometheus server URL

## Supported Dashboards

Based on [cloud-bulldozer/performance-dashboards](https://github.com/cloud-bulldozer/performance-dashboards):

| Dashboard | Description | List Command |
|-----------|-------------|--------------|
| **ingress-perf** | Ingress/HAProxy performance | `--list-ingress` |
| **k8s-netperf** | Kubernetes network performance | `--list-netperf` |
| **kube-burner** | Cluster stress testing metrics | `--list-kubeburner` |
| **etcd** | Etcd cluster detailed metrics | `--list-etcd` |
| **ocp-performance** | OpenShift cluster performance | `--list-ocp` |
| **ovn-dashboard** | OVN networking metrics | `--list-ovn` |
| **hypershift** | HyperShift hosted clusters | `--list-hypershift` |

## Installation

### Option 1: Using Virtual Environment (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/DotMatrixPrometheus.git
cd DotMatrixPrometheus

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install prometheus-api-client plotext

# Verify installation
python dashboard.py --list
```

### Option 2: System-wide Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/DotMatrixPrometheus.git
cd DotMatrixPrometheus

# Install dependencies system-wide
pip3 install prometheus-api-client plotext

# Verify installation
python3 dashboard.py --list
```

### Dependencies

| Package | Description |
|---------|-------------|
| `prometheus-api-client` | Python client for Prometheus API |
| `plotext` | Terminal plotting library |

## Usage

### Single Metric

```bash
# Show last 60 minutes (default)
python dashboard.py cluster-cpu

# Show last 120 minutes
python dashboard.py etcd-db-size -m 120

# Use a different Prometheus server
python dashboard.py ingress-rps-total --url http://prometheus.example.com:9090
```

### Multi-Metric Grid Display

Display multiple metrics side by side in a grid layout:

```bash
# 4 metrics in a 2x2 grid (auto layout)
python dashboard.py cluster-cpu cluster-memory etcd-cpu etcd-memory

# 6 metrics in a 2x3 grid
python dashboard.py masters-cpu workers-cpu etcd-cpu kube-api-cpu ovn-master-cpu kubelet-cpu

# Specify number of columns manually
python dashboard.py masters-cpu workers-cpu etcd-cpu --cols 3

# Mix different dashboard types
python dashboard.py ingress-rps-total node-net-total tcp-established etcd-keys
```

**Auto Grid Layout:**

| # Metrics | Layout |
|-----------|--------|
| 1 | 1×1 |
| 2 | 1×2 |
| 3-4 | 2×2 |
| 5-6 | 2×3 |
| 7-9 | 3×3 |
| 10-12 | 3×4 |
| 13+ | N×4 |

### Time Range Selection

```bash
# Specific time range: November 13th, 8:00 to 10:00 AM
python dashboard.py ingress-error-rate --from "Nov 13 08:00" --to "Nov 13 10:00"

# Multiple metrics with time range
python dashboard.py cluster-cpu etcd-db-size --from "Nov 13 08:00" --to "Nov 13 10:00"

# Using full date format
python dashboard.py haproxy-cpu --from "2024-11-13 08:00" --to "2024-11-13 10:00"

# From a specific time until now
python dashboard.py ingress-latency-p99 --from "Nov 13 08:00"
```

### Listing Available Metrics

```bash
# List all available metrics
python dashboard.py --list

# List metrics by dashboard type
python dashboard.py --list-ingress      # Ingress-perf metrics
python dashboard.py --list-netperf      # k8s-netperf metrics
python dashboard.py --list-kubeburner   # Kube-burner metrics
python dashboard.py --list-etcd         # Etcd metrics
python dashboard.py --list-ocp          # OCP performance metrics
python dashboard.py --list-ovn          # OVN metrics
python dashboard.py --list-hypershift   # HyperShift metrics
```

### Supported Datetime Formats

| Format | Example |
|--------|---------|
| Full ISO | `2024-11-13 08:00` or `2024-11-13T08:00` |
| Month-day with time | `11-13 08:00` or `11/13 08:00` |
| Named month | `Nov 13 08:00` or `November 13 08:00` |
| Time only (today) | `08:00` |

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--url` | `-u` | Prometheus server URL (default: `http://localhost:9090`) |
| `--from` | `-f` | Start datetime |
| `--to` | `-t` | End datetime |
| `--minutes` | `-m` | Minutes to look back from now (default: 60) |
| `--cols` | `-c` | Number of columns for multi-metric grid |
| `--list` | `-l` | List all available metrics |
| `--list-ingress` | `-li` | List ingress-perf metrics |
| `--list-netperf` | `-ln` | List k8s-netperf metrics |
| `--list-kubeburner` | `-lk` | List kube-burner metrics |
| `--list-etcd` | `-le` | List etcd metrics |
| `--list-ocp` | `-lp` | List OCP performance metrics |
| `--list-ovn` | `-lo` | List OVN metrics |
| `--list-hypershift` | `-lh` | List HyperShift metrics |
| `--help` | `-h` | Show help message |

## Available Metrics

### Ingress-Perf Metrics

| Category | Metrics |
|----------|---------|
| **RPS** | `ingress-rps-edge`, `ingress-rps-passthrough`, `ingress-rps-reencrypt`, `ingress-rps-http`, `ingress-rps-total` |
| **Latency** | `ingress-latency-avg`, `ingress-latency-p99`, `ingress-latency-p90`, `ingress-latency-p50` |
| **HAProxy** | `haproxy-cpu`, `haproxy-cpu-max` |
| **Infrastructure** | `infra-cpu`, `infra-cpu-max` |
| **Connections** | `ingress-connections`, `ingress-conn-rate` |
| **Error/Quality** | `ingress-error-rate`, `ingress-success-rate`, `ingress-backends-down` |
| **Throughput** | `ingress-bytes-in`, `ingress-bytes-out` |
| **Router** | `router-reload`, `router-config-time` |

### k8s-Netperf Metrics

| Category | Metrics |
|----------|---------|
| **Node Network** | `node-net-tx`, `node-net-rx`, `node-net-total` |
| **Pod Network** | `pod-net-tx`, `pod-net-rx`, `pod-net-total` |
| **TCP** | `tcp-established`, `tcp-active-opens`, `tcp-passive-opens`, `tcp-retransmits`, `tcp-segments-tx`, `tcp-segments-rx` |
| **UDP** | `udp-tx`, `udp-rx`, `udp-errors` |
| **Errors/Drops** | `net-drops-tx`, `net-drops-rx`, `net-errors-tx`, `net-errors-rx` |
| **Sockets** | `socket-timewait`, `socket-allocated`, `socket-inuse` |
| **Conntrack** | `conntrack-entries`, `conntrack-usage` |

### Kube-Burner Metrics

| Category | Metrics |
|----------|---------|
| **Cluster Status** | `masters-cpu`, `masters-memory`, `workers-cpu`, `workers-memory` |
| **Node/Pod Status** | `node-count`, `nodes-ready`, `nodes-notready`, `pod-count`, `pods-running`, `pods-pending`, `pods-failed` |
| **API Server** | `kube-api-cpu`, `kube-api-memory`, `kube-api-request-rate`, `kube-api-latency-p99`, `kube-api-latency-p50` |
| **Controller/Scheduler** | `kube-controller-cpu`, `kube-controller-memory`, `kube-scheduler-cpu`, `kube-scheduler-memory`, `scheduling-throughput` |
| **Kubelet/CRI-O** | `kubelet-cpu`, `kubelet-memory`, `crio-cpu`, `crio-memory` |
| **Pod Latency** | `pod-ready-latency-p99`, `pod-ready-latency-p50`, `container-start-latency-p99` |
| **Services** | `service-sync-latency-p99`, `endpoints-count`, `services-count` |
| **Alerts** | `alerts-firing`, `alerts-pending` |
| **Resources** | `deployments-count`, `replicasets-count`, `namespaces-count`, `secrets-count`, `configmaps-count` |

### Etcd Metrics

| Category | Metrics |
|----------|---------|
| **Basic** | `etcd-leader-changes`, `etcd-db-size`, `etcd-cpu`, `etcd-memory` |
| **Disk** | `etcd-disk-writes`, `etcd-disk-reads`, `etcd-wal-sync-p99`, `etcd-backend-commit-p99` |
| **DB Space** | `etcd-db-space-used`, `etcd-db-left-capacity`, `etcd-db-size-limit` |
| **Operations** | `etcd-keys`, `etcd-slow-ops`, `etcd-key-ops`, `etcd-compacted-keys` |
| **Raft/Leader** | `etcd-raft-proposals`, `etcd-failed-proposals`, `etcd-heartbeat-failures`, `etcd-has-leader` |
| **Network** | `etcd-net-tx`, `etcd-net-rx`, `etcd-grpc-traffic`, `etcd-peer-rtt-p99`, `etcd-active-streams`, `etcd-snapshot-duration` |
| **Compaction** | `etcd-compaction-duration`, `etcd-defrag-duration` |

### OCP Performance Metrics

| Category | Metrics |
|----------|---------|
| **Cluster** | `cluster-cpu`, `cluster-memory`, `cluster-memory-total`, `cluster-filesystem` |
| **Container** | `container-cpu-top`, `container-memory-top`, `container-restarts`, `container-oom-kills` |
| **API** | `api-request-duration`, `api-error-rate`, `api-inflight-requests` |

### OVN Metrics

| Category | Metrics |
|----------|---------|
| **Components** | `ovn-master-cpu`, `ovn-master-memory`, `ovn-node-cpu`, `ovn-node-memory`, `ovn-controller-cpu`, `ovn-controller-memory` |
| **Northd/DB** | `ovn-northd-cpu`, `ovn-northd-memory`, `ovn-nbdb-cpu`, `ovn-nbdb-memory`, `ovn-sbdb-cpu`, `ovn-sbdb-memory` |
| **Flows** | `ovn-flow-count`, `ovn-flow-add-rate`, `ovn-pod-latency-p99`, `ovn-pod-latency-p50` |

### HyperShift Metrics

| Category | Metrics |
|----------|---------|
| **Hosted Clusters** | `hosted-cluster-count`, `hosted-clusters-available` |
| **Management** | `management-cluster-cpu`, `management-cluster-memory` |
| **Control Plane** | `control-plane-cpu`, `control-plane-memory`, `hypershift-operator-cpu`, `hypershift-operator-memory` |

## Adding Custom Metrics

Add new metric classes to `my_metrics.py`:

```python
class MyCustomMetric:
    """Description of your metric."""
    title = "My Custom Metric"
    unit = "req/s"
    
    query = '''
        sum(rate(my_custom_metric_total[2m]))
    '''
    
    # Optional: transform function for value conversion
    @staticmethod
    def transform(value):
        return value / 1000  # Convert to thousands
```

Then register it in `dashboard.py`:

```python
AVAILABLE_METRICS = {
    # ... existing metrics ...
    "my-custom": my_metrics.MyCustomMetric,
}
```

## Requirements

- Python 3.7+
- Access to a Prometheus server
- Terminal with Unicode support (for better chart rendering)

## Notes

- Metrics are based on [cloud-bulldozer/performance-dashboards](https://github.com/cloud-bulldozer/performance-dashboards)
- You may need to adjust label selectors in `my_metrics.py` to match your environment
- Connection errors are handled gracefully with helpful error messages

## License

See [LICENSE](LICENSE) file for details.
