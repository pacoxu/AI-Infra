---
status: Active
maintainer: pacoxu
last_updated: 2026-01-23
tags: dranet, gke, b200, nccl, rdma, kubernetes, ai-infrastructure
canonical_path: docs/blog/2026-01-23/dranet-gke-b200-nccl-test_zh.md
---

# Part I — 在 GKE 上探索 DRANET：B200 GPU 与 NCCL 测试

本文基于 Google Cloud 博客文章，介绍如何在 Google Kubernetes Engine (GKE)
上使用 DRANET (Dynamic Resource Allocation Network) 部署 NVIDIA B200 GPU
集群并进行 NCCL 性能测试。

**原文链接:** [Part I — Exploring DRANET on GKE with B200 GPUs and NCCL
test](https://medium.com/google-cloud/part-i-exploring-dranet-on-gke-with-b200-gpus-and-nccl-test-c4674ec10659)

## 为什么需要 RDMA

AI 工作负载需要快速的网络连接，这就是远程直接内存访问 (RDMA) 的用武之地。
[Google 提供了这一功能](https://docs.cloud.google.com/vpc/docs/rdma-network-profiles?utm_campaign=CDR_0x78e4a6e6_default_b473040571&utm_medium=external&utm_source=blog)，
以 RDMA over Converged Ethernet v2 和 Falcon 的形式提供，这些是另一个讨论的主题。

部署 RDMA 就绪网络有几种方式：

- [ClusterToolkit](https://docs.cloud.google.com/cluster-toolkit/docs/overview?utm_campaign=CDR_0x78e4a6e6_default_b473040571&utm_medium=external&utm_source=blog)
- [通过脚本/控制台](https://docs.cloud.google.com/ai-hypercomputer/docs/create/gke-ai-hypercompute-custom?utm_campaign=CDR_0x78e4a6e6_default_b473040571&utm_medium=external&utm_source=blog)
- [Cluster Director](https://docs.cloud.google.com/cluster-director/docs/overview?utm_campaign=CDR_0x78e4a6e6_default_b473040571&utm_medium=external&utm_source=blog)

但今天我们关注 [Google Kubernetes Engine 托管的 (GKE)
DRANET](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/allocate-network-resources-dra?utm_campaign=CDR_0x78e4a6e6_default_b473040571&utm_medium=external&utm_source=blog)。

## 为什么选择 DRANET？

我发现 DRANET 特别有趣，因为它利用了原生的 Kubernetes [动态资源分配
(DRA)](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)。
GKE 托管版本基于[开源
DRANET](https://github.com/kubernetes-sigs/dranet)。你只需启用正确的标志，
创建 ResourceClaimTemplate，并附加正确的标签。然后 GKE
会自动为你的节点处理网络资源的分配。

如果这些资源没有正确分配，你昂贵的节点将无法利用高带宽、专用的 GPU NIC。
这会限制 GPU 到 GPU 的流量并严重影响性能。GKE 托管的 DRANET 也支持 TPU。

在本演示中，我们将设置一个 GKE 集群，以便在配备 B200 GPU 的 A4 VM
系列上促进 GPU 通信。

## 阶段 1：环境设置

首先，让我们定义变量。将占位符值替换为你的具体项目详细信息。

**注意：** A4/B200 资源稀缺；你通常需要预留资源

```bash
export PROJECT=$(gcloud config get project)
export REGION="us-central1"           # 替换为你的区域
export ZONE="us-central1-c"           # 替换为你的可用区
export CLUSTER_NAME="dranet-cluster"
export NODE_POOL_NAME="b200-pool"
export GVNIC_NETWORK_PREFIX="dranet-net"
export RESERVATION_NAME="my-reservation"
export BLOCK_NAME="my-block"

# 启用所需的 API
gcloud services enable networkservices.googleapis.com --project=$PROJECT
```

## 阶段 2：网络配置

我们需要一个专用的 VPC，为 Pod 配置特定的辅助范围和一个仅代理子网。

```bash
gcloud compute --project=${PROJECT} \
    networks create ${GVNIC_NETWORK_PREFIX}-main \
    --subnet-mode=custom \
    --mtu=8896

gcloud compute --project=${PROJECT} \
    networks subnets create ${GVNIC_NETWORK_PREFIX}-sub \
    --network=${GVNIC_NETWORK_PREFIX}-main \
    --region=${REGION} \
    --range=172.16.0.0/12 \
    --secondary-range="pods-range=10.4.0.0/14"

gcloud compute --project=${PROJECT} \
    networks subnets create ${GVNIC_NETWORK_PREFIX}-proxy-sub \
    --purpose=REGIONAL_MANAGED_PROXY \
    --role=ACTIVE \
    --region=${REGION} \
    --network=${GVNIC_NETWORK_PREFIX}-main \
    --range=10.129.0.0/23

gcloud compute --project=${PROJECT} firewall-rules create \
    ${GVNIC_NETWORK_PREFIX}-allow-ssh \
    --network=${GVNIC_NETWORK_PREFIX}-main \
    --allow=tcp:22 \
    --source-ranges=0.0.0.0/0 \
    --description="Allow SSH from any source." \
    --direction=INGRESS \
    --priority=1000

gcloud compute --project=${PROJECT} firewall-rules create \
    ${GVNIC_NETWORK_PREFIX}-allow-rdp \
    --network=${GVNIC_NETWORK_PREFIX}-main \
    --allow=tcp:3389 \
    --source-ranges=0.0.0.0/0 \
    --description="Allow RDP from any source." \
    --direction=INGRESS \
    --priority=1000

gcloud compute --project=${PROJECT} firewall-rules create \
    ${GVNIC_NETWORK_PREFIX}-allow-icmp \
    --network=${GVNIC_NETWORK_PREFIX}-main \
    --allow=icmp \
    --source-ranges=0.0.0.0/0 \
    --description="Allow ICMP from any source." \
    --direction=INGRESS \
    --priority=1000

gcloud compute --project=${PROJECT} firewall-rules create \
    ${GVNIC_NETWORK_PREFIX}-allow-internal \
    --network=${GVNIC_NETWORK_PREFIX}-main \
    --allow=all \
    --source-ranges=172.16.0.0/12 \
    --description="Allow all internal traffic within the network." \
    --direction=INGRESS \
    --priority=1000
```

## 阶段 3：集群部署

现在我们部署 GKE 集群。注意我们启用了 Ray Operator
和各种监控工具，以支持开箱即用的 AI 工作负载。

这将部署集群并分配要使用的标准 VPC，并创建一个默认的非 GPU 节点。

```bash
gcloud container clusters create $CLUSTER_NAME \
    --location=$ZONE \
    --num-nodes=1 \
    --machine-type=e2-standard-16 \
    --network=${GVNIC_NETWORK_PREFIX}-main \
    --subnetwork=${GVNIC_NETWORK_PREFIX}-sub \
    --release-channel rapid \
    --enable-dataplane-v2 \
    --enable-ip-alias \
    --addons=HttpLoadBalancing,RayOperator \
    --gateway-api=standard \
    --enable-ray-cluster-logging \
    --enable-ray-cluster-monitoring \
    --enable-managed-prometheus \
    --enable-dataplane-v2-metrics \
    --monitoring=SYSTEM
```

连接到集群：

```bash
gcloud container clusters get-credentials $CLUSTER_NAME \
    --zone $ZONE --project $PROJECT
```

## 阶段 4：A4 节点池 & DRANET

这是关键步骤。我们使用 A4 HighGPU 机器类型（由 NVIDIA B200 驱动）创建节点池。

至关重要的是，我们应用了 `gke-networking-dra-driver` 标签。
此标签告诉 GKE 为动态资源分配准备节点。

```bash
gcloud beta container node-pools create $NODE_POOL_NAME \
  --cluster $CLUSTER_NAME \
  --location $ZONE \
  --node-locations $ZONE \
  --machine-type a4-highgpu-8g \
  --accelerator type=nvidia-b200,count=8,gpu-driver-version=latest \
  --enable-autoscaling --num-nodes=1 \
  --total-min-nodes=1 --total-max-nodes=3 \
  --reservation-affinity=specific \
  --reservation=projects/$PROJECT/reservations/$RESERVATION_NAME/reservationBlocks/$BLOCK_NAME \
  --accelerator-network-profile=auto \
  --node-labels=cloud.google.com/gke-networking-dra-driver=true
```

## 阶段 5：资源声明模板

在 Kubernetes DRA 中，我们需要一个模板来定义我们想要声明的设备。
这里我们请求 `mrdma.google.com` 设备类。

创建一个名为 `all-mrdma-template.yaml` 的文件，然后将以下内容添加到清单中：

```yaml
apiVersion: resource.k8s.io/v1
kind: ResourceClaimTemplate
metadata:
  name: all-mrdma
spec:
  spec:
    devices:
      requests:
      - name: req-mrdma
        exactly:
          deviceClassName: mrdma.google.com
          allocationMode: All
```

应用它：

```bash
kubectl apply -f all-mrdma-template.yaml
```

## 阶段 6：验证（NCCL 测试）

为了验证 RDMA 速度，我们将运行标准的 NCCL 基准测试。

### 1. 创建 SSH 密钥和 Secret

```bash
# 1. 生成新的 SSH 密钥对（无密码短语）
ssh-keygen -t rsa -f ./id_rsa -N ""

# 2. 将密钥上传到集群作为 Kubernetes Secret
kubectl create secret generic mpi-keys \
  --from-file=id_rsa=./id_rsa \
  --from-file=id_rsa.pub=./id_rsa.pub \
  --from-file=authorized_keys=./id_rsa.pub

# 3. 清理本地密钥
rm ./id_rsa ./id_rsa.pub
```

### 2. 部署基准测试工作负载

这个 2 个 Pod 的 StatefulSet 挂载 RDMA 资源声明 (rdma-claim) 和 NVIDIA 驱动。

创建一个名为 `nccl-hybrid-test.yaml` 的文件，然后将以下内容添加到清单中：

```yaml
# --- Headless Service ---
apiVersion: v1
kind: Service
metadata:
  name: nccl-node
  labels:
    app: nccl
spec:
  clusterIP: None
  selector:
    app: nccl
  ports:
  - port: 2222
    name: ssh
---
# --- NCCL Workload ---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: nccl
spec:
  serviceName: "nccl-node"
  replicas: 2
  selector:
    matchLabels:
      app: nccl
  template:
    metadata:
      labels:
        app: nccl
        gke.networks.io/accelerator-network-profile: auto
    spec:
      hostNetwork: false
      
      # 允许在有污点的 GPU 节点上调度
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"

      containers:
      - name: test
        image: us-docker.pkg.dev/gce-ai-infra/gpudirect-gib/nccl-plugin-gib-diagnostic:v1.1.0
        command: ["/bin/bash", "-c"]
        args:
          - |
            # 为 MPI 设置 SSH
            mkdir -p /run/sshd; mkdir -p /root/.ssh
            cp /etc/secret-volume/* /root/.ssh/
            chmod 600 /root/.ssh/id_rsa
            echo "StrictHostKeyChecking no" > /root/.ssh/config
            /usr/sbin/sshd -p 2222
            sleep infinity
            
        securityContext:
          privileged: true
          capabilities:
            add: ["IPC_LOCK", "NET_RAW"]
        
        resources:
          limits:
            nvidia.com/gpu: 8
          # 绑定 RDMA 网络声明
          claims:
            - name: rdma-claim
        
        # 挂载主机驱动（NVML/SMI 访问所需）
        volumeMounts:
        - name: driver-lib
          mountPath: /usr/local/nvidia/lib64
          readOnly: true
        - name: gib
          mountPath: /usr/local/gib
        - name: shared-memory
          mountPath: /dev/shm
        - name: secret-volume
          mountPath: /etc/secret-volume
          readOnly: true
        
        env:
        - name: LD_LIBRARY_PATH
          value: /usr/local/nvidia/lib64
      
      # 将 Pod 链接到网络模板
      resourceClaims:
      - name: rdma-claim
        resourceClaimTemplateName: all-mrdma
      
      volumes:
      - name: driver-lib
        hostPath:
          path: /home/kubernetes/bin/nvidia/lib64
      - name: gib
        hostPath:
          path: /home/kubernetes/bin/gib
      - name: shared-memory
        emptyDir:
          medium: "Memory"
          sizeLimit: 250Gi
      - name: secret-volume
        secret:
          secretName: mpi-keys
          defaultMode: 0400
```

应用它：

```bash
kubectl apply -f nccl-hybrid-test.yaml
```

### 3. 执行测试

粘贴以下内容。这将运行测试并将输出保存到名为 `nccl_linear_test.log` 的文件：

```bash
echo "Starting NCCL Benchmark (Linear 1GB Increments)..."

kubectl exec -it nccl-0 -- /bin/bash -c "
  export LD_LIBRARY_PATH=/third_party/nccl/build/lib:/usr/local/nvidia/lib64
  
  # 1. 解析 IP
  IP1=\$(python3 -c \"import socket; print(socket.gethostbyname('nccl-0.nccl-node'))\")
  IP2=\$(python3 -c \"import socket; print(socket.gethostbyname('nccl-1.nccl-node'))\")

  # 2. 创建 Hostfile
  echo \"\$IP1 slots=8\" > /tmp/hostfile
  echo \"\$IP2 slots=8\" >> /tmp/hostfile

  # 3. 使用线性增量运行 MPI (-i 1G)
  # -b 1G: 从 1GB 开始
  # -e 8G: 到 8GB 结束
  # -i 1G: 每步增加 1GB（线性）而不是倍增
  mpirun --allow-run-as-root \
    --hostfile /tmp/hostfile \
    -mca plm_rsh_args '-p 2222 -o StrictHostKeyChecking=no' \
    -x LD_LIBRARY_PATH \
    -np 16 \
    --bind-to none \
    /third_party/nccl-tests/build/all_gather_perf \
      -b 1G \
      -e 8G \
      -i 1G \
      -g 1
" | tee nccl_linear_test.log
```

## 清理资源

```bash
# 1. 删除 NCCL 工作负载和服务
kubectl delete statefulset nccl
kubectl delete service nccl-node
kubectl delete secret mpi-keys

# 2. 删除 DRA 资源声明模板
kubectl delete resourceclaimtemplate all-mrdma
```

接下来 — 删除附加的两个网络。转到 VPC 网络并搜索已创建的网络。选择并删除两者。

删除这些 VPC 后，继续删除集群：

```bash
gcloud container clusters delete $CLUSTER_NAME \
    --zone $ZONE \
    --project $PROJECT \
    --quiet
```

接下来搜索你的标准 VPC，查看防火墙规则并删除所有规则，
你可能会看到一些自动创建的规则。

然后删除 VPC：

```bash
gcloud compute networks subnets delete ${GVNIC_NETWORK_PREFIX}-sub \
    --region=${REGION} --project=$PROJECT --quiet

gcloud compute networks subnets delete ${GVNIC_NETWORK_PREFIX}-proxy-sub \
    --region=${REGION} --project=$PROJECT --quiet

# 3. 删除 VPC 网络
gcloud compute networks delete ${GVNIC_NETWORK_PREFIX}-main \
    --project=$PROJECT --quiet
```

## 总结

DRANET 目前处于预览状态，也支持 TPU。你可以查看以下文档：

- [为加速器 VM 配置自动化网络](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/config-auto-net-for-accelerators?utm_campaign=CDR_0x78e4a6e6_default_b473040571&utm_medium=external&utm_source=blog)
- [AI Hypercomputer](https://docs.cloud.google.com/ai-hypercomputer/docs/overview?utm_campaign=CDR_0x78e4a6e6_default_b473040571&utm_medium=external&utm_source=blog)

## 相关资源

- [DRANET GitHub 仓库](https://github.com/kubernetes-sigs/dranet)
- [Kubernetes DRA 文档](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
- [GKE DRANET 文档](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/allocate-network-resources-dra)
- [本仓库 DRANET 介绍](../2025-12-17/dranet-kubernetes-network-driver_zh.md)
- [本仓库 DRA 性能测试](../../kubernetes/dra-performance-testing.md)

## 参考资料

- 原文作者：Google Cloud
- 翻译日期：2026-01-23
- 译者：AI-Infra 社区
