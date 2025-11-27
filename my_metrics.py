# my_metrics.py
"""
Performance metrics for DotMatrixPrometheus dashboard.

Based on cloud-bulldozer/performance-dashboards:
- ingress-perf.jsonnet
- k8s-netperf.jsonnet
- kube-burner-report-ocp-wrapper.jsonnet
- etcd-on-cluster-dashboard.jsonnet
- hypershift-performance.jsonnet
- ocp-performance.jsonnet
- ovn-dashboard.jsonnet

Repository: https://github.com/cloud-bulldozer/performance-dashboards
"""

# =============================================================================
# INGRESS PERFORMANCE (ingress-perf) METRICS
# =============================================================================

# -----------------------------------------------------------------------------
# RPS (Requests Per Second) Metrics
# -----------------------------------------------------------------------------

class IngressRPSEdgeMetric:
    """
    Requests per second for Edge termination routes.
    Edge termination: TLS is terminated at the router.
    """
    title = "Ingress RPS - Edge Termination"
    unit = "req/s"
    
    query = '''
        sum(rate(haproxy_frontend_http_requests_total{route=~".*edge.*"}[2m]))
    '''


class IngressRPSPassthroughMetric:
    """
    Requests per second for Passthrough termination routes.
    Passthrough: TLS is passed through to the backend pod.
    """
    title = "Ingress RPS - Passthrough Termination"
    unit = "req/s"
    
    query = '''
        sum(rate(haproxy_frontend_http_requests_total{route=~".*passthrough.*"}[2m]))
    '''


class IngressRPSReencryptMetric:
    """
    Requests per second for Reencrypt termination routes.
    Reencrypt: TLS terminated at router, re-encrypted to backend.
    """
    title = "Ingress RPS - Reencrypt Termination"
    unit = "req/s"
    
    query = '''
        sum(rate(haproxy_frontend_http_requests_total{route=~".*reencrypt.*"}[2m]))
    '''


class IngressRPSHttpMetric:
    """
    Requests per second for HTTP (non-TLS) routes.
    """
    title = "Ingress RPS - HTTP (Non-TLS)"
    unit = "req/s"
    
    query = '''
        sum(rate(haproxy_frontend_http_requests_total{route=~".*http.*", route!~".*https.*"}[2m]))
    '''


class IngressRPSTotalMetric:
    """
    Total requests per second across all termination types.
    """
    title = "Ingress RPS - Total"
    unit = "req/s"
    
    query = '''
        sum(rate(haproxy_frontend_http_requests_total[2m]))
    '''


# -----------------------------------------------------------------------------
# Latency Metrics
# -----------------------------------------------------------------------------

class IngressLatencyAvgMetric:
    """
    Average request latency across all ingress routes.
    """
    title = "Ingress Avg Latency"
    unit = "ms"
    
    query = '''
        avg(haproxy_backend_response_time_average_seconds) * 1000
    '''


class IngressLatencyP99Metric:
    """
    99th percentile latency for ingress routes.
    Uses histogram_quantile for accurate percentile calculation.
    """
    title = "Ingress P99 Latency"
    unit = "ms"
    
    query = '''
        histogram_quantile(0.99, 
            sum(rate(haproxy_backend_http_response_time_seconds_bucket[5m])) by (le)
        ) * 1000
    '''


class IngressLatencyP90Metric:
    """
    90th percentile latency for ingress routes.
    """
    title = "Ingress P90 Latency"
    unit = "ms"
    
    query = '''
        histogram_quantile(0.90, 
            sum(rate(haproxy_backend_http_response_time_seconds_bucket[5m])) by (le)
        ) * 1000
    '''


class IngressLatencyP50Metric:
    """
    Median (50th percentile) latency for ingress routes.
    """
    title = "Ingress P50 Latency (Median)"
    unit = "ms"
    
    query = '''
        histogram_quantile(0.50, 
            sum(rate(haproxy_backend_http_response_time_seconds_bucket[5m])) by (le)
        ) * 1000
    '''


# -----------------------------------------------------------------------------
# HAProxy CPU Usage Metrics
# -----------------------------------------------------------------------------

class HAProxyCPUAvgMetric:
    """
    Average CPU usage of HAProxy router pods.
    Corresponds to 'HAProxy avg CPU usage' panel in ingress-perf dashboard.
    """
    title = "HAProxy Avg CPU Usage"
    unit = "%"
    
    query = '''
        avg(
            rate(container_cpu_usage_seconds_total{
                pod=~"router-.*",
                container="router"
            }[5m])
        ) * 100
    '''


class HAProxyCPUMaxMetric:
    """
    Maximum CPU usage across HAProxy router pods.
    Useful for identifying hotspots.
    """
    title = "HAProxy Max CPU Usage"
    unit = "%"
    
    query = '''
        max(
            rate(container_cpu_usage_seconds_total{
                pod=~"router-.*",
                container="router"
            }[5m])
        ) * 100
    '''


# -----------------------------------------------------------------------------
# Infrastructure Nodes CPU Usage
# -----------------------------------------------------------------------------

class InfraNodesCPUAvgMetric:
    """
    Average CPU usage of infrastructure nodes.
    Corresponds to 'Infra nodes CPU usage' panel in ingress-perf dashboard.
    Assumes infra nodes are labeled with node-role.kubernetes.io/infra.
    """
    title = "Infra Nodes Avg CPU Usage"
    unit = "%"
    
    query = '''
        100 - avg(
            rate(node_cpu_seconds_total{
                mode="idle",
                node=~".*infra.*"
            }[5m])
        ) * 100
    '''


class InfraNodesCPUMaxMetric:
    """
    Maximum CPU usage across infrastructure nodes.
    """
    title = "Infra Nodes Max CPU Usage"
    unit = "%"
    
    query = '''
        100 - min(
            rate(node_cpu_seconds_total{
                mode="idle",
                node=~".*infra.*"
            }[5m])
        ) * 100
    '''


# -----------------------------------------------------------------------------
# Connection and Session Metrics
# -----------------------------------------------------------------------------

class IngressActiveConnectionsMetric:
    """
    Current active connections on HAProxy frontends.
    """
    title = "Ingress Active Connections"
    unit = "connections"
    
    query = '''
        sum(haproxy_frontend_current_sessions)
    '''


class IngressConnectionRateMetric:
    """
    Rate of new connections per second.
    """
    title = "Ingress Connection Rate"
    unit = "conn/s"
    
    query = '''
        sum(rate(haproxy_frontend_connections_total[2m]))
    '''


# -----------------------------------------------------------------------------
# Error and Quality Metrics
# -----------------------------------------------------------------------------

class IngressErrorRateMetric:
    """
    HTTP error rate (4xx and 5xx responses).
    Useful for data quality assessment.
    """
    title = "Ingress HTTP Error Rate"
    unit = "%"
    
    query = '''
        sum(rate(haproxy_frontend_http_responses_total{code=~"4.*|5.*"}[5m])) 
        / 
        sum(rate(haproxy_frontend_http_responses_total[5m])) 
        * 100
    '''


class IngressSuccessRateMetric:
    """
    HTTP success rate (2xx responses).
    Corresponds to data quality metrics in ingress-perf dashboard.
    """
    title = "Ingress Success Rate (Data Quality)"
    unit = "%"
    
    query = '''
        sum(rate(haproxy_frontend_http_responses_total{code=~"2.*"}[5m])) 
        / 
        sum(rate(haproxy_frontend_http_responses_total[5m])) 
        * 100
    '''


class IngressBackendDownMetric:
    """
    Number of backends currently marked as down.
    """
    title = "Ingress Backends Down"
    unit = "count"
    
    query = '''
        sum(haproxy_backend_status{state="DOWN"})
    '''


# -----------------------------------------------------------------------------
# Throughput Metrics
# -----------------------------------------------------------------------------

class IngressBytesInMetric:
    """
    Incoming traffic throughput across all frontends.
    """
    title = "Ingress Bytes In"
    unit = "MB/s"
    
    query = '''
        sum(rate(haproxy_frontend_bytes_in_total[2m]))
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 * 1024)  # Convert to MB/s


class IngressBytesOutMetric:
    """
    Outgoing traffic throughput across all frontends.
    """
    title = "Ingress Bytes Out"
    unit = "MB/s"
    
    query = '''
        sum(rate(haproxy_frontend_bytes_out_total[2m]))
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 * 1024)  # Convert to MB/s


# -----------------------------------------------------------------------------
# OpenShift Router Specific Metrics
# -----------------------------------------------------------------------------

class RouterReloadMetric:
    """
    Rate of router reloads.
    High reload rate may indicate configuration churn.
    """
    title = "Router Reload Rate"
    unit = "reloads/min"
    
    query = '''
        sum(rate(template_router_reload_seconds_count[5m])) * 60
    '''


class RouterWriteConfigMetric:
    """
    Time spent writing router configuration.
    """
    title = "Router Config Write Time"
    unit = "ms"
    
    query = '''
        avg(rate(template_router_write_config_seconds_sum[5m]) 
        / rate(template_router_write_config_seconds_count[5m])) * 1000
    '''


# =============================================================================
# K8S-NETPERF METRICS
# Based on: cloud-bulldozer/performance-dashboards k8s-netperf.jsonnet
# Network performance testing metrics for Kubernetes
# =============================================================================

# -----------------------------------------------------------------------------
# Node Network Throughput (Node to Node)
# -----------------------------------------------------------------------------

class NodeNetworkThroughputTxMetric:
    """
    Node-level network transmit throughput.
    Measures bytes transmitted per second across all network interfaces.
    """
    title = "Node Network TX Throughput"
    unit = "Mbps"
    
    query = '''
        sum(rate(node_network_transmit_bytes_total{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"}[2m])) by (instance)
    '''
    
    @staticmethod
    def transform(value):
        return (value * 8) / (1024 * 1024)  # Convert bytes/s to Mbps


class NodeNetworkThroughputRxMetric:
    """
    Node-level network receive throughput.
    Measures bytes received per second across all network interfaces.
    """
    title = "Node Network RX Throughput"
    unit = "Mbps"
    
    query = '''
        sum(rate(node_network_receive_bytes_total{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"}[2m])) by (instance)
    '''
    
    @staticmethod
    def transform(value):
        return (value * 8) / (1024 * 1024)  # Convert bytes/s to Mbps


class NodeNetworkThroughputTotalMetric:
    """
    Total node-level network throughput (TX + RX).
    """
    title = "Node Network Total Throughput"
    unit = "Mbps"
    
    query = '''
        sum(rate(node_network_transmit_bytes_total{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"}[2m])) 
        + 
        sum(rate(node_network_receive_bytes_total{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"}[2m]))
    '''
    
    @staticmethod
    def transform(value):
        return (value * 8) / (1024 * 1024)  # Convert bytes/s to Mbps


# -----------------------------------------------------------------------------
# Pod Network Throughput (Pod to Pod)
# -----------------------------------------------------------------------------

class PodNetworkThroughputTxMetric:
    """
    Pod-level network transmit throughput.
    Measures container network bytes transmitted.
    """
    title = "Pod Network TX Throughput"
    unit = "Mbps"
    
    query = '''
        sum(rate(container_network_transmit_bytes_total{namespace!="",pod!=""}[2m]))
    '''
    
    @staticmethod
    def transform(value):
        return (value * 8) / (1024 * 1024)  # Convert bytes/s to Mbps


class PodNetworkThroughputRxMetric:
    """
    Pod-level network receive throughput.
    Measures container network bytes received.
    """
    title = "Pod Network RX Throughput"
    unit = "Mbps"
    
    query = '''
        sum(rate(container_network_receive_bytes_total{namespace!="",pod!=""}[2m]))
    '''
    
    @staticmethod
    def transform(value):
        return (value * 8) / (1024 * 1024)  # Convert bytes/s to Mbps


class PodNetworkThroughputTotalMetric:
    """
    Total pod-level network throughput (TX + RX).
    """
    title = "Pod Network Total Throughput"
    unit = "Mbps"
    
    query = '''
        sum(rate(container_network_transmit_bytes_total{namespace!="",pod!=""}[2m])) 
        + 
        sum(rate(container_network_receive_bytes_total{namespace!="",pod!=""}[2m]))
    '''
    
    @staticmethod
    def transform(value):
        return (value * 8) / (1024 * 1024)  # Convert bytes/s to Mbps


# -----------------------------------------------------------------------------
# TCP Metrics
# -----------------------------------------------------------------------------

class TCPConnectionsEstablishedMetric:
    """
    Number of established TCP connections.
    Useful for understanding network load.
    """
    title = "TCP Established Connections"
    unit = "connections"
    
    query = '''
        sum(node_netstat_Tcp_CurrEstab)
    '''


class TCPConnectionsActiveMetric:
    """
    Rate of active TCP connection openings.
    """
    title = "TCP Active Opens Rate"
    unit = "conn/s"
    
    query = '''
        sum(rate(node_netstat_Tcp_ActiveOpens[2m]))
    '''


class TCPConnectionsPassiveMetric:
    """
    Rate of passive TCP connection openings (incoming connections).
    """
    title = "TCP Passive Opens Rate"
    unit = "conn/s"
    
    query = '''
        sum(rate(node_netstat_Tcp_PassiveOpens[2m]))
    '''


class TCPRetransmitsMetric:
    """
    Rate of TCP segment retransmissions.
    High values may indicate network issues.
    """
    title = "TCP Retransmits Rate"
    unit = "segments/s"
    
    query = '''
        sum(rate(node_netstat_Tcp_RetransSegs[2m]))
    '''


class TCPSegmentsTxMetric:
    """
    Rate of TCP segments transmitted.
    """
    title = "TCP Segments TX Rate"
    unit = "segments/s"
    
    query = '''
        sum(rate(node_netstat_Tcp_OutSegs[2m]))
    '''


class TCPSegmentsRxMetric:
    """
    Rate of TCP segments received.
    """
    title = "TCP Segments RX Rate"
    unit = "segments/s"
    
    query = '''
        sum(rate(node_netstat_Tcp_InSegs[2m]))
    '''


# -----------------------------------------------------------------------------
# UDP Metrics
# -----------------------------------------------------------------------------

class UDPPacketsTxMetric:
    """
    Rate of UDP datagrams transmitted.
    """
    title = "UDP Datagrams TX Rate"
    unit = "packets/s"
    
    query = '''
        sum(rate(node_netstat_Udp_OutDatagrams[2m]))
    '''


class UDPPacketsRxMetric:
    """
    Rate of UDP datagrams received.
    """
    title = "UDP Datagrams RX Rate"
    unit = "packets/s"
    
    query = '''
        sum(rate(node_netstat_Udp_InDatagrams[2m]))
    '''


class UDPErrorsMetric:
    """
    Rate of UDP receive errors.
    High values may indicate buffer issues or network problems.
    """
    title = "UDP Receive Errors Rate"
    unit = "errors/s"
    
    query = '''
        sum(rate(node_netstat_Udp_InErrors[2m]))
    '''


# -----------------------------------------------------------------------------
# Network Errors and Drops
# -----------------------------------------------------------------------------

class NetworkPacketDropsTxMetric:
    """
    Rate of transmitted packets dropped.
    """
    title = "Network TX Packet Drops"
    unit = "drops/s"
    
    query = '''
        sum(rate(node_network_transmit_drop_total{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"}[2m]))
    '''


class NetworkPacketDropsRxMetric:
    """
    Rate of received packets dropped.
    """
    title = "Network RX Packet Drops"
    unit = "drops/s"
    
    query = '''
        sum(rate(node_network_receive_drop_total{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"}[2m]))
    '''


class NetworkErrorsTxMetric:
    """
    Rate of transmit errors.
    """
    title = "Network TX Errors"
    unit = "errors/s"
    
    query = '''
        sum(rate(node_network_transmit_errs_total{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"}[2m]))
    '''


class NetworkErrorsRxMetric:
    """
    Rate of receive errors.
    """
    title = "Network RX Errors"
    unit = "errors/s"
    
    query = '''
        sum(rate(node_network_receive_errs_total{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"}[2m]))
    '''


# -----------------------------------------------------------------------------
# Network Latency (Socket Statistics)
# -----------------------------------------------------------------------------

class SocketTimeWaitMetric:
    """
    Number of sockets in TIME_WAIT state.
    High values may indicate connection churn.
    """
    title = "Sockets in TIME_WAIT"
    unit = "sockets"
    
    query = '''
        sum(node_sockstat_TCP_tw)
    '''


class SocketAllocatedMetric:
    """
    Number of allocated sockets.
    """
    title = "Allocated Sockets"
    unit = "sockets"
    
    query = '''
        sum(node_sockstat_TCP_alloc)
    '''


class SocketInUseMetric:
    """
    Number of TCP sockets currently in use.
    """
    title = "TCP Sockets In Use"
    unit = "sockets"
    
    query = '''
        sum(node_sockstat_TCP_inuse)
    '''


# -----------------------------------------------------------------------------
# Container Network I/O (Per Namespace)
# -----------------------------------------------------------------------------

class ContainerNetworkTxByNamespaceMetric:
    """
    Container network transmit rate by namespace.
    Top 5 namespaces by throughput.
    """
    title = "Container Network TX by Namespace"
    unit = "Mbps"
    
    query = '''
        topk(5, sum(rate(container_network_transmit_bytes_total{namespace!=""}[2m])) by (namespace))
    '''
    
    @staticmethod
    def transform(value):
        return (value * 8) / (1024 * 1024)  # Convert bytes/s to Mbps


class ContainerNetworkRxByNamespaceMetric:
    """
    Container network receive rate by namespace.
    Top 5 namespaces by throughput.
    """
    title = "Container Network RX by Namespace"
    unit = "Mbps"
    
    query = '''
        topk(5, sum(rate(container_network_receive_bytes_total{namespace!=""}[2m])) by (namespace))
    '''
    
    @staticmethod
    def transform(value):
        return (value * 8) / (1024 * 1024)  # Convert bytes/s to Mbps


# -----------------------------------------------------------------------------
# Network Interface Statistics
# -----------------------------------------------------------------------------

class NetworkInterfaceSpeedMetric:
    """
    Network interface speed (if available).
    """
    title = "Network Interface Speed"
    unit = "Mbps"
    
    query = '''
        avg(node_network_speed_bytes{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"})
    '''
    
    @staticmethod
    def transform(value):
        return (value * 8) / (1024 * 1024)  # Convert bytes to Mbps


class NetworkPacketsTxMetric:
    """
    Rate of packets transmitted across all interfaces.
    """
    title = "Network Packets TX Rate"
    unit = "packets/s"
    
    query = '''
        sum(rate(node_network_transmit_packets_total{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"}[2m]))
    '''


class NetworkPacketsRxMetric:
    """
    Rate of packets received across all interfaces.
    """
    title = "Network Packets RX Rate"
    unit = "packets/s"
    
    query = '''
        sum(rate(node_network_receive_packets_total{device!~"lo|veth.*|docker.*|flannel.*|cali.*|cbr.*"}[2m]))
    '''


# -----------------------------------------------------------------------------
# Conntrack (Connection Tracking)
# -----------------------------------------------------------------------------

class ConntrackEntriesMetric:
    """
    Current number of conntrack entries.
    """
    title = "Conntrack Entries"
    unit = "entries"
    
    query = '''
        sum(node_nf_conntrack_entries)
    '''


class ConntrackUsageMetric:
    """
    Conntrack table usage percentage.
    High values may cause connection issues.
    """
    title = "Conntrack Usage"
    unit = "%"
    
    query = '''
        (sum(node_nf_conntrack_entries) / sum(node_nf_conntrack_entries_limit)) * 100
    '''


# =============================================================================
# KUBE-BURNER METRICS
# Based on: cloud-bulldozer/performance-dashboards kube-burner-report-ocp-wrapper.jsonnet
# Cluster performance and stress testing metrics
# =============================================================================

# -----------------------------------------------------------------------------
# Cluster Status - Masters CPU/Memory
# -----------------------------------------------------------------------------

class MastersCPUUtilizationMetric:
    """
    CPU utilization of master nodes.
    Corresponds to 'Masters CPU utilization' panel.
    """
    title = "Masters CPU Utilization"
    unit = "%"
    
    query = '''
        100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle", node=~".*master.*"}[5m])) * 100)
    '''


class MastersMemoryUtilizationMetric:
    """
    Memory utilization of master nodes.
    """
    title = "Masters Memory Utilization"
    unit = "GB"
    
    query = '''
        sum(node_memory_MemTotal_bytes{node=~".*master.*"} - node_memory_MemAvailable_bytes{node=~".*master.*"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class WorkersCPUUtilizationMetric:
    """
    Average CPU utilization of worker nodes.
    """
    title = "Workers CPU Utilization"
    unit = "%"
    
    query = '''
        100 - (avg(rate(node_cpu_seconds_total{mode="idle", node=~".*worker.*"}[5m])) * 100)
    '''


class WorkersMemoryUtilizationMetric:
    """
    Memory utilization of worker nodes.
    """
    title = "Workers Memory Utilization"
    unit = "GB"
    
    query = '''
        sum(node_memory_MemTotal_bytes{node=~".*worker.*"} - node_memory_MemAvailable_bytes{node=~".*worker.*"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


# -----------------------------------------------------------------------------
# Node and Pod Status
# -----------------------------------------------------------------------------

class NodeCountMetric:
    """
    Total number of nodes in the cluster.
    """
    title = "Node Count"
    unit = "nodes"
    
    query = '''
        count(kube_node_info)
    '''


class NodeReadyCountMetric:
    """
    Number of nodes in Ready state.
    """
    title = "Nodes Ready"
    unit = "nodes"
    
    query = '''
        sum(kube_node_status_condition{condition="Ready", status="true"})
    '''


class NodeNotReadyCountMetric:
    """
    Number of nodes not in Ready state.
    """
    title = "Nodes Not Ready"
    unit = "nodes"
    
    query = '''
        sum(kube_node_status_condition{condition="Ready", status="false"})
    '''


class PodCountMetric:
    """
    Total number of pods in the cluster.
    """
    title = "Total Pod Count"
    unit = "pods"
    
    query = '''
        count(kube_pod_info)
    '''


class PodRunningCountMetric:
    """
    Number of pods in Running phase.
    """
    title = "Running Pods"
    unit = "pods"
    
    query = '''
        sum(kube_pod_status_phase{phase="Running"})
    '''


class PodPendingCountMetric:
    """
    Number of pods in Pending phase.
    """
    title = "Pending Pods"
    unit = "pods"
    
    query = '''
        sum(kube_pod_status_phase{phase="Pending"})
    '''


class PodFailedCountMetric:
    """
    Number of pods in Failed phase.
    """
    title = "Failed Pods"
    unit = "pods"
    
    query = '''
        sum(kube_pod_status_phase{phase="Failed"})
    '''


# -----------------------------------------------------------------------------
# Kube API Server Metrics
# -----------------------------------------------------------------------------

class KubeAPIServerCPUMetric:
    """
    CPU usage of kube-apiserver.
    Corresponds to 'Kube-apiserver usage' panel.
    """
    title = "Kube API Server CPU"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{container="kube-apiserver"}[5m])) * 100
    '''


class KubeAPIServerMemoryMetric:
    """
    Memory usage of kube-apiserver.
    """
    title = "Kube API Server Memory"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{container="kube-apiserver"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class KubeAPIRequestRateMetric:
    """
    Rate of API requests to kube-apiserver.
    Corresponds to 'API request rate' panel.
    """
    title = "Kube API Request Rate"
    unit = "req/s"
    
    query = '''
        sum(rate(apiserver_request_total[5m]))
    '''


class KubeAPIRequestLatencyP99Metric:
    """
    99th percentile latency of API requests.
    Corresponds to 'Read Only API request P99 latency' panels.
    """
    title = "Kube API P99 Latency"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb!="WATCH"}[5m])) by (le))
    '''


class KubeAPIRequestLatencyP50Metric:
    """
    Median latency of API requests.
    """
    title = "Kube API P50 Latency"
    unit = "s"
    
    query = '''
        histogram_quantile(0.50, sum(rate(apiserver_request_duration_seconds_bucket{verb!="WATCH"}[5m])) by (le))
    '''


# -----------------------------------------------------------------------------
# Kube Controller Manager and Scheduler
# -----------------------------------------------------------------------------

class KubeControllerManagerCPUMetric:
    """
    CPU usage of kube-controller-manager.
    Corresponds to 'Active Kube-controller-manager usage' panel.
    """
    title = "Kube Controller Manager CPU"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{container="kube-controller-manager"}[5m])) * 100
    '''


class KubeControllerManagerMemoryMetric:
    """
    Memory usage of kube-controller-manager.
    """
    title = "Kube Controller Manager Memory"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{container="kube-controller-manager"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class KubeSchedulerCPUMetric:
    """
    CPU usage of kube-scheduler.
    Corresponds to 'Kube-scheduler usage' panel.
    """
    title = "Kube Scheduler CPU"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{container="kube-scheduler"}[5m])) * 100
    '''


class KubeSchedulerMemoryMetric:
    """
    Memory usage of kube-scheduler.
    """
    title = "Kube Scheduler Memory"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{container="kube-scheduler"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class SchedulingThroughputMetric:
    """
    Pod scheduling throughput.
    Corresponds to 'Scheduling throughput' panel.
    """
    title = "Scheduling Throughput"
    unit = "pods/s"
    
    query = '''
        sum(rate(scheduler_pod_scheduling_duration_seconds_count[5m]))
    '''


# -----------------------------------------------------------------------------
# Etcd Metrics
# -----------------------------------------------------------------------------

class EtcdLeaderChangesMetric:
    """
    Rate of etcd leader changes.
    Corresponds to 'Etcd leader changes per day' panel.
    High values may indicate instability.
    """
    title = "Etcd Leader Changes"
    unit = "changes/h"
    
    query = '''
        sum(increase(etcd_server_leader_changes_seen_total[1h]))
    '''


class EtcdDBSizeMetric:
    """
    Size of etcd database.
    """
    title = "Etcd DB Size"
    unit = "GB"
    
    query = '''
        sum(etcd_mvcc_db_total_size_in_bytes)
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class EtcdPeerRTTP99Metric:
    """
    99th percentile etcd peer round-trip time.
    Corresponds to 'Etcd 99th network peer roundtrip time' panel.
    """
    title = "Etcd Peer RTT P99"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(etcd_network_peer_round_trip_time_seconds_bucket[5m])) by (le))
    '''


class EtcdWALSyncDurationP99Metric:
    """
    99th percentile etcd WAL fsync duration.
    """
    title = "Etcd WAL Sync P99"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(etcd_disk_wal_fsync_duration_seconds_bucket[5m])) by (le))
    '''


class EtcdBackendCommitDurationP99Metric:
    """
    99th percentile etcd backend commit duration.
    """
    title = "Etcd Backend Commit P99"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(etcd_disk_backend_commit_duration_seconds_bucket[5m])) by (le))
    '''


class EtcdCPUMetric:
    """
    Etcd CPU usage.
    Corresponds to 'Etcd resource utilization' panel.
    """
    title = "Etcd CPU Usage"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{container="etcd"}[5m])) * 100
    '''


class EtcdMemoryMetric:
    """
    Etcd memory usage.
    """
    title = "Etcd Memory Usage"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{container="etcd"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


# -----------------------------------------------------------------------------
# OVN-Kubernetes Metrics
# -----------------------------------------------------------------------------

class OVNKubeMasterCPUMetric:
    """
    CPU usage of ovnkube-master pods.
    Corresponds to 'ovnkube-master pods CPU usage' panel.
    """
    title = "OVN-Kube Master CPU"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{pod=~"ovnkube-master-.*"}[5m])) * 100
    '''


class OVNKubeMasterMemoryMetric:
    """
    Memory usage of ovnkube-master pods.
    Corresponds to 'ovnkube-master pods Memory usage' panel.
    """
    title = "OVN-Kube Master Memory"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{pod=~"ovnkube-master-.*"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class OVNKubeNodeCPUMetric:
    """
    CPU usage of ovnkube-node pods.
    Corresponds to 'ovnkube-node pods CPU Usage' panel.
    """
    title = "OVN-Kube Node CPU"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{pod=~"ovnkube-node-.*"}[5m])) * 100
    '''


class OVNKubeNodeMemoryMetric:
    """
    Memory usage of ovnkube-node pods.
    Corresponds to 'ovnkube-node pods Memory Usage' panel.
    """
    title = "OVN-Kube Node Memory"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{pod=~"ovnkube-node-.*"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class OVNControllerCPUMetric:
    """
    CPU usage of ovn-controller.
    Corresponds to 'ovn-controller CPU Usage' panel.
    """
    title = "OVN Controller CPU"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{container="ovn-controller"}[5m])) * 100
    '''


# -----------------------------------------------------------------------------
# Kubelet and CRI-O Metrics
# -----------------------------------------------------------------------------

class KubeletCPUMetric:
    """
    CPU usage of kubelet process.
    Corresponds to 'Top 5 Kubelet process by CPU usage' panel.
    """
    title = "Kubelet CPU Usage"
    unit = "%"
    
    query = '''
        avg(rate(process_cpu_seconds_total{service="kubelet"}[5m])) * 100
    '''


class KubeletMemoryMetric:
    """
    Memory (RSS) usage of kubelet.
    Corresponds to 'Top 5 Kubelet RSS by memory usage' panel.
    """
    title = "Kubelet Memory RSS"
    unit = "GB"
    
    query = '''
        avg(process_resident_memory_bytes{service="kubelet"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class CRIOCPUMetric:
    """
    CPU usage of CRI-O process.
    Corresponds to 'Top 5 CRI-O process by CPU usage' panel.
    """
    title = "CRI-O CPU Usage"
    unit = "%"
    
    query = '''
        avg(rate(process_cpu_seconds_total{service="crio"}[5m])) * 100
    '''


class CRIOMemoryMetric:
    """
    Memory (RSS) usage of CRI-O.
    Corresponds to 'Top 5 CRI-O RSS by memory usage' panel.
    """
    title = "CRI-O Memory RSS"
    unit = "GB"
    
    query = '''
        avg(process_resident_memory_bytes{service="crio"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


# -----------------------------------------------------------------------------
# Pod Latency Metrics
# -----------------------------------------------------------------------------

class PodReadyLatencyP99Metric:
    """
    99th percentile pod ready latency.
    Time from pod creation to Ready condition.
    Corresponds to 'Average pod latency' and 'Pod latencies summary' panels.
    """
    title = "Pod Ready Latency P99"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(kubelet_pod_start_duration_seconds_bucket[5m])) by (le))
    '''


class PodReadyLatencyP50Metric:
    """
    Median pod ready latency.
    """
    title = "Pod Ready Latency P50"
    unit = "s"
    
    query = '''
        histogram_quantile(0.50, sum(rate(kubelet_pod_start_duration_seconds_bucket[5m])) by (le))
    '''


class ContainerStartLatencyP99Metric:
    """
    99th percentile container start latency.
    Corresponds to 'Top 10 Container runtime network setup latency' panel.
    """
    title = "Container Start Latency P99"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(kubelet_container_runtime_start_duration_seconds_bucket[5m])) by (le))
    '''


# -----------------------------------------------------------------------------
# Service and Kubeproxy Metrics
# -----------------------------------------------------------------------------

class ServiceSyncLatencyP99Metric:
    """
    99th percentile service sync latency in kube-proxy.
    Corresponds to 'Service sync latency' panel.
    """
    title = "Service Sync Latency P99"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(kubeproxy_sync_proxy_rules_duration_seconds_bucket[5m])) by (le))
    '''


class EndpointsCountMetric:
    """
    Total number of endpoints in the cluster.
    """
    title = "Endpoints Count"
    unit = "endpoints"
    
    query = '''
        count(kube_endpoint_info)
    '''


class ServicesCountMetric:
    """
    Total number of services in the cluster.
    """
    title = "Services Count"
    unit = "services"
    
    query = '''
        count(kube_service_info)
    '''


# -----------------------------------------------------------------------------
# Alerts and Events
# -----------------------------------------------------------------------------

class AlertsFiringCountMetric:
    """
    Number of currently firing alerts.
    Corresponds to 'Alerts' panel.
    """
    title = "Firing Alerts"
    unit = "alerts"
    
    query = '''
        count(ALERTS{alertstate="firing"})
    '''


class AlertsPendingCountMetric:
    """
    Number of pending alerts.
    """
    title = "Pending Alerts"
    unit = "alerts"
    
    query = '''
        count(ALERTS{alertstate="pending"})
    '''


# -----------------------------------------------------------------------------
# Workload Resources
# -----------------------------------------------------------------------------

class DeploymentsCountMetric:
    """
    Total number of deployments.
    """
    title = "Deployments Count"
    unit = "deployments"
    
    query = '''
        count(kube_deployment_created)
    '''


class ReplicaSetsCountMetric:
    """
    Total number of replicasets.
    """
    title = "ReplicaSets Count"
    unit = "replicasets"
    
    query = '''
        count(kube_replicaset_created)
    '''


class NamespacesCountMetric:
    """
    Total number of namespaces.
    """
    title = "Namespaces Count"
    unit = "namespaces"
    
    query = '''
        count(kube_namespace_created)
    '''


class SecretsCountMetric:
    """
    Total number of secrets.
    """
    title = "Secrets Count"
    unit = "secrets"
    
    query = '''
        count(kube_secret_info)
    '''


class ConfigMapsCountMetric:
    """
    Total number of configmaps.
    """
    title = "ConfigMaps Count"
    unit = "configmaps"
    
    query = '''
        count(kube_configmap_info)
    '''


# =============================================================================
# ETCD DETAILED METRICS (from etcd-on-cluster-dashboard.jsonnet)
# More granular etcd monitoring metrics
# =============================================================================

# -----------------------------------------------------------------------------
# Etcd Disk I/O
# -----------------------------------------------------------------------------

class EtcdDiskWritesMetric:
    """
    Etcd container disk write rate.
    Corresponds to 'Etcd container disk writes' panel.
    """
    title = "Etcd Disk Writes"
    unit = "B/s"
    
    query = '''
        sum(rate(container_fs_writes_bytes_total{container="etcd"}[5m]))
    '''


class EtcdDiskReadsMetric:
    """
    Etcd container disk read rate.
    """
    title = "Etcd Disk Reads"
    unit = "B/s"
    
    query = '''
        sum(rate(container_fs_reads_bytes_total{container="etcd"}[5m]))
    '''


# -----------------------------------------------------------------------------
# Etcd Compaction and Defrag
# -----------------------------------------------------------------------------

class EtcdCompactionDurationMetric:
    """
    Etcd compaction duration.
    Corresponds to 'Compaction Duration sum' panel.
    """
    title = "Etcd Compaction Duration"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(etcd_debugging_mvcc_db_compaction_pause_duration_milliseconds_bucket[5m])) by (le)) / 1000
    '''


class EtcdDefragDurationMetric:
    """
    Etcd defragmentation duration.
    Corresponds to 'Defrag Duration sum' panel.
    """
    title = "Etcd Defrag Duration"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(etcd_debugging_mvcc_db_compaction_total_duration_milliseconds_bucket[5m])) by (le)) / 1000
    '''


# -----------------------------------------------------------------------------
# Etcd DB Space
# -----------------------------------------------------------------------------

class EtcdDBSpaceUsedPercentMetric:
    """
    Percentage of etcd DB space used.
    Corresponds to '% DB Space Used' panel.
    """
    title = "Etcd DB Space Used"
    unit = "%"
    
    query = '''
        (sum(etcd_mvcc_db_total_size_in_bytes) / sum(etcd_server_quota_backend_bytes)) * 100
    '''


class EtcdDBLeftCapacityMetric:
    """
    Etcd DB remaining capacity.
    Corresponds to 'DB Left capacity' panel.
    """
    title = "Etcd DB Left Capacity"
    unit = "GB"
    
    query = '''
        sum(etcd_server_quota_backend_bytes) - sum(etcd_mvcc_db_total_size_in_bytes)
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class EtcdDBSizeLimitMetric:
    """
    Etcd DB size limit (quota).
    Corresponds to 'DB Size Limit' panel.
    """
    title = "Etcd DB Size Limit"
    unit = "GB"
    
    query = '''
        sum(etcd_server_quota_backend_bytes)
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


# -----------------------------------------------------------------------------
# Etcd Keys and Operations
# -----------------------------------------------------------------------------

class EtcdKeysCountMetric:
    """
    Total number of keys in etcd.
    Corresponds to 'Keys' panel.
    """
    title = "Etcd Keys Count"
    unit = "keys"
    
    query = '''
        sum(etcd_debugging_mvcc_keys_total)
    '''


class EtcdSlowOperationsMetric:
    """
    Rate of slow etcd operations.
    Corresponds to 'Slow Operations' panel.
    """
    title = "Etcd Slow Operations"
    unit = "ops/s"
    
    query = '''
        sum(rate(etcd_server_slow_apply_total[5m]))
    '''


class EtcdKeyOperationsMetric:
    """
    Rate of key operations (put/delete).
    Corresponds to 'Key Operations' panel.
    """
    title = "Etcd Key Operations"
    unit = "ops/s"
    
    query = '''
        sum(rate(etcd_mvcc_put_total[5m])) + sum(rate(etcd_mvcc_delete_total[5m]))
    '''


class EtcdCompactedKeysMetric:
    """
    Total compacted keys in etcd.
    Corresponds to 'Compacted Keys' panel.
    """
    title = "Etcd Compacted Keys"
    unit = "keys"
    
    query = '''
        sum(etcd_debugging_mvcc_db_compaction_keys_total)
    '''


# -----------------------------------------------------------------------------
# Etcd Raft and Leader
# -----------------------------------------------------------------------------

class EtcdRaftProposalsMetric:
    """
    Rate of raft proposals.
    Corresponds to 'Raft Proposals' panel.
    """
    title = "Etcd Raft Proposals"
    unit = "proposals/s"
    
    query = '''
        sum(rate(etcd_server_proposals_committed_total[5m]))
    '''


class EtcdFailedProposalsMetric:
    """
    Total number of failed raft proposals.
    Corresponds to 'Total number of failed proposals seen' panel.
    """
    title = "Etcd Failed Proposals"
    unit = "proposals"
    
    query = '''
        sum(etcd_server_proposals_failed_total)
    '''


class EtcdHeartbeatFailuresMetric:
    """
    Rate of etcd heartbeat failures.
    Corresponds to 'Heartbeat Failures' panel.
    """
    title = "Etcd Heartbeat Failures"
    unit = "failures/s"
    
    query = '''
        sum(rate(etcd_server_heartbeat_send_failures_total[5m]))
    '''


class EtcdHasLeaderMetric:
    """
    Whether etcd cluster has a leader (1=yes, 0=no).
    Corresponds to 'Etcd has a leader?' panel.
    """
    title = "Etcd Has Leader"
    unit = "bool"
    
    query = '''
        max(etcd_server_has_leader)
    '''


# -----------------------------------------------------------------------------
# Etcd Network
# -----------------------------------------------------------------------------

class EtcdNetworkTrafficTxMetric:
    """
    Etcd container network transmit rate.
    Corresponds to 'Container network traffic' panel.
    """
    title = "Etcd Network TX"
    unit = "B/s"
    
    query = '''
        sum(rate(container_network_transmit_bytes_total{pod=~"etcd-.*"}[5m]))
    '''


class EtcdNetworkTrafficRxMetric:
    """
    Etcd container network receive rate.
    """
    title = "Etcd Network RX"
    unit = "B/s"
    
    query = '''
        sum(rate(container_network_receive_bytes_total{pod=~"etcd-.*"}[5m]))
    '''


class EtcdGRPCTrafficMetric:
    """
    Etcd gRPC network traffic.
    Corresponds to 'gRPC network traffic' panel.
    """
    title = "Etcd gRPC Traffic"
    unit = "B/s"
    
    query = '''
        sum(rate(etcd_network_client_grpc_received_bytes_total[5m])) + sum(rate(etcd_network_client_grpc_sent_bytes_total[5m]))
    '''


class EtcdActiveStreamsMetric:
    """
    Number of active gRPC streams.
    Corresponds to 'Active Streams' panel.
    """
    title = "Etcd Active Streams"
    unit = "streams"
    
    query = '''
        sum(grpc_server_started_total{grpc_service=~"etcdserverpb.*"}) - sum(grpc_server_handled_total{grpc_service=~"etcdserverpb.*"})
    '''


class EtcdSnapshotDurationMetric:
    """
    Etcd snapshot save duration.
    Corresponds to 'Snapshot duration' panel.
    """
    title = "Etcd Snapshot Duration"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(etcd_debugging_snap_save_total_duration_seconds_bucket[5m])) by (le))
    '''


# =============================================================================
# OCP PERFORMANCE METRICS (from ocp-performance.jsonnet)
# OpenShift cluster performance metrics
# =============================================================================

# -----------------------------------------------------------------------------
# Cluster Overview
# -----------------------------------------------------------------------------

class ClusterCPUUsageMetric:
    """
    Total cluster CPU usage percentage.
    """
    title = "Cluster CPU Usage"
    unit = "%"
    
    query = '''
        (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))) * 100
    '''


class ClusterMemoryUsageMetric:
    """
    Total cluster memory usage.
    """
    title = "Cluster Memory Usage"
    unit = "GB"
    
    query = '''
        sum(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class ClusterMemoryTotalMetric:
    """
    Total cluster memory capacity.
    """
    title = "Cluster Memory Total"
    unit = "GB"
    
    query = '''
        sum(node_memory_MemTotal_bytes)
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class ClusterFilesystemUsageMetric:
    """
    Cluster filesystem usage percentage.
    """
    title = "Cluster Filesystem Usage"
    unit = "%"
    
    query = '''
        (1 - sum(node_filesystem_avail_bytes{mountpoint="/"}) / sum(node_filesystem_size_bytes{mountpoint="/"})) * 100
    '''


# -----------------------------------------------------------------------------
# Container Resources
# -----------------------------------------------------------------------------

class ContainerCPUUsageTopMetric:
    """
    Top containers by CPU usage.
    """
    title = "Top Containers CPU Usage"
    unit = "%"
    
    query = '''
        topk(10, sum(rate(container_cpu_usage_seconds_total{container!="",container!="POD"}[5m])) by (namespace, pod, container)) * 100
    '''


class ContainerMemoryUsageTopMetric:
    """
    Top containers by memory usage.
    """
    title = "Top Containers Memory"
    unit = "GB"
    
    query = '''
        topk(10, sum(container_memory_working_set_bytes{container!="",container!="POD"}) by (namespace, pod, container))
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class ContainerRestartsTotalMetric:
    """
    Total container restarts.
    """
    title = "Container Restarts Total"
    unit = "restarts"
    
    query = '''
        sum(kube_pod_container_status_restarts_total)
    '''


class ContainerOOMKillsMetric:
    """
    Containers killed due to OOM.
    """
    title = "Container OOM Kills"
    unit = "kills"
    
    query = '''
        sum(kube_pod_container_status_last_terminated_reason{reason="OOMKilled"})
    '''


# -----------------------------------------------------------------------------
# API Server Performance
# -----------------------------------------------------------------------------

class APIServerRequestDurationAvgMetric:
    """
    Average API server request duration.
    """
    title = "API Request Duration Avg"
    unit = "s"
    
    query = '''
        sum(rate(apiserver_request_duration_seconds_sum{verb!="WATCH"}[5m])) / sum(rate(apiserver_request_duration_seconds_count{verb!="WATCH"}[5m]))
    '''


class APIServerRequestErrorRateMetric:
    """
    API server error rate (4xx and 5xx).
    """
    title = "API Request Error Rate"
    unit = "%"
    
    query = '''
        sum(rate(apiserver_request_total{code=~"4.*|5.*"}[5m])) / sum(rate(apiserver_request_total[5m])) * 100
    '''


class APIServerInFlightRequestsMetric:
    """
    Current in-flight API requests.
    """
    title = "API In-Flight Requests"
    unit = "requests"
    
    query = '''
        sum(apiserver_current_inflight_requests)
    '''


# =============================================================================
# OVN METRICS (from ovn-dashboard.jsonnet)
# Open Virtual Network performance metrics
# =============================================================================

# -----------------------------------------------------------------------------
# OVN Controller Metrics
# -----------------------------------------------------------------------------

class OVNControllerMemoryMetric:
    """
    OVN controller memory usage.
    """
    title = "OVN Controller Memory"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{container="ovn-controller"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class OVNNorthdCPUMetric:
    """
    OVN northd CPU usage.
    """
    title = "OVN Northd CPU"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{container="northd"}[5m])) * 100
    '''


class OVNNorthdMemoryMetric:
    """
    OVN northd memory usage.
    """
    title = "OVN Northd Memory"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{container="northd"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class OVNNbdbCPUMetric:
    """
    OVN nbdb (Northbound DB) CPU usage.
    """
    title = "OVN NBDB CPU"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{container="nbdb"}[5m])) * 100
    '''


class OVNNbdbMemoryMetric:
    """
    OVN nbdb memory usage.
    """
    title = "OVN NBDB Memory"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{container="nbdb"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class OVNSbdbCPUMetric:
    """
    OVN sbdb (Southbound DB) CPU usage.
    """
    title = "OVN SBDB CPU"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{container="sbdb"}[5m])) * 100
    '''


class OVNSbdbMemoryMetric:
    """
    OVN sbdb memory usage.
    """
    title = "OVN SBDB Memory"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{container="sbdb"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


# -----------------------------------------------------------------------------
# OVN Flow Metrics
# -----------------------------------------------------------------------------

class OVNFlowCountMetric:
    """
    Total number of OVN flows.
    """
    title = "OVN Flow Count"
    unit = "flows"
    
    query = '''
        sum(ovn_controller_integration_bridge_openflow_total)
    '''


class OVNFlowAddRateMetric:
    """
    Rate of OVN flow additions.
    """
    title = "OVN Flow Add Rate"
    unit = "flows/s"
    
    query = '''
        sum(rate(ovnkube_controller_pod_creation_latency_seconds_count[5m]))
    '''


# -----------------------------------------------------------------------------
# OVN Network Metrics
# -----------------------------------------------------------------------------

class OVNPodCreationLatencyP99Metric:
    """
    99th percentile OVN pod creation latency.
    """
    title = "OVN Pod Creation Latency P99"
    unit = "s"
    
    query = '''
        histogram_quantile(0.99, sum(rate(ovnkube_controller_pod_creation_latency_seconds_bucket[5m])) by (le))
    '''


class OVNPodCreationLatencyP50Metric:
    """
    Median OVN pod creation latency.
    """
    title = "OVN Pod Creation Latency P50"
    unit = "s"
    
    query = '''
        histogram_quantile(0.50, sum(rate(ovnkube_controller_pod_creation_latency_seconds_bucket[5m])) by (le))
    '''


# =============================================================================
# HYPERSHIFT METRICS (from hypershift-performance.jsonnet)
# HyperShift hosted cluster performance metrics
# =============================================================================

# -----------------------------------------------------------------------------
# Hosted Cluster Status
# -----------------------------------------------------------------------------

class HostedClusterCountMetric:
    """
    Number of hosted clusters.
    Corresponds to 'Number of HostedCluster' panel.
    """
    title = "Hosted Cluster Count"
    unit = "clusters"
    
    query = '''
        count(hypershift_hostedclusters)
    '''


class HostedClusterAvailableMetric:
    """
    Number of available hosted clusters.
    """
    title = "Hosted Clusters Available"
    unit = "clusters"
    
    query = '''
        sum(hypershift_hostedclusters{condition="Available",status="True"})
    '''


# -----------------------------------------------------------------------------
# Management Cluster Resources
# -----------------------------------------------------------------------------

class ManagementClusterCPUMetric:
    """
    Management cluster CPU usage.
    """
    title = "Management Cluster CPU"
    unit = "%"
    
    query = '''
        100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
    '''


class ManagementClusterMemoryMetric:
    """
    Management cluster memory usage.
    """
    title = "Management Cluster Memory"
    unit = "GB"
    
    query = '''
        sum(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


# -----------------------------------------------------------------------------
# Control Plane Resources (per hosted cluster)
# -----------------------------------------------------------------------------

class ControlPlaneCPUTotalMetric:
    """
    Total CPU usage of all control plane components.
    """
    title = "Control Plane CPU Total"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{namespace=~".*-.*",container=~"kube-apiserver|etcd|kube-controller-manager|kube-scheduler"}[5m])) * 100
    '''


class ControlPlaneMemoryTotalMetric:
    """
    Total memory usage of all control plane components.
    """
    title = "Control Plane Memory Total"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{namespace=~".*-.*",container=~"kube-apiserver|etcd|kube-controller-manager|kube-scheduler"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB


class HyperShiftOperatorCPUMetric:
    """
    HyperShift operator CPU usage.
    """
    title = "HyperShift Operator CPU"
    unit = "%"
    
    query = '''
        sum(rate(container_cpu_usage_seconds_total{namespace="hypershift",container="operator"}[5m])) * 100
    '''


class HyperShiftOperatorMemoryMetric:
    """
    HyperShift operator memory usage.
    """
    title = "HyperShift Operator Memory"
    unit = "GB"
    
    query = '''
        sum(container_memory_working_set_bytes{namespace="hypershift",container="operator"})
    '''
    
    @staticmethod
    def transform(value):
        return value / (1024 ** 3)  # Convert to GB
