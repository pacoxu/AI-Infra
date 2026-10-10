---
status: Active
maintainer: pacoxu
last_updated: 2026-10-10
tags: hardware, supernode, vera-rubin, nvl72, vllm, sglang, miles, metax, shanghai-cube, daocloud
canonical_path: docs/hardware/supernode.md
source_urls:
  - https://vllm.ai/blog/2026-10-09-vera-rubin-preview
  - https://www.lmsys.org/blog/2026-10-09-vera-rubin/
  - https://d.run/news/i80bp6njjsg0yhxat1rgbvb7
  - https://github.com/DaoCloud/DaoCloud-docs/blob/main/docs/zh/docs/blogs/2026/optimize-gpu.md
  - https://www.shanghaicube.com/index.html
  - https://www.metax-tech.com/ndetail/12573.html
---

# 超节点（SuperNode）

超节点把几十到上百张加速卡收进同一个 scale-up 域。对训练和推理来说，调度单位不再是
「一台 8 卡服务器」，而是机柜里的 NVLink / Mesh / 交换域：卡落错域，AllReduce、
All2All 和 Expert Parallel 会先打在带宽上。

这一章记录路线图里已经点名的机柜级系统，并补上 2026-10-09 的 NVIDIA Vera Rubin
软件适配，以及 DaoCloud 参与的国产超节点案例 Shanghai Cube（ShanghaiCube）。

## 机柜级系统对照

<!-- markdownlint-disable MD013 -->
| 系统 | 公开规模 | Scale-up | 软件栈信号 |
| --- | --- | --- | --- |
| Huawei CloudMatrix 384 | 384 卡级机柜 | UnifiedBus | 路线图中的华为超节点条目，规格不在本章展开 |
| NVIDIA GB200 NVL72 | 36 颗 Grace CPU + 72 颗 Blackwell GPU，液冷机柜 | 机柜级 NVLink | Vera Rubin 文章里的上一代对照 |
| NVIDIA GB300 NVL72 | Blackwell Ultra 机柜 | NVL72 | Vera Rubin 文章里的近一代对照 |
| NVIDIA Vera Rubin NVL72 | Rubin GPU 机柜，面向 agentic inference | 第六代 NVLink，双向带宽约 1.7x GB200 | vLLM `cu134-nightly`；SGLang / Miles 早期适配 |
| 沐曦耀龙 S8000 G2 | 64 张曦云 C550 | 3D Mesh | 沐曦公开材料：已覆盖 DeepSeek、Qwen、Kimi-K2 |
| Shanghai Cube | 单柜 128 张曦云 C550，液冷 | 产品站写 4 组 TP32；集成材料写 2 个 20U 超节点群组 | DaoCloud 定制操作系统与高密度调度 |
<!-- markdownlint-enable MD013 -->

耀龙 S8000 G2 和 Shanghai Cube 用的是同一代曦云 C550，但产品边界不同。S8000 G2 是
64 卡 3D Mesh 超节点；Shanghai Cube 是 128 卡液冷整柜，沐曦材料里 8 柜并排即可组成
千卡集群。

## NVIDIA Vera Rubin NVL72

2026-10-09，vLLM 与 SGLang / Miles 同一天公开了 Vera Rubin 上的早期结果。两篇都强调：
这是 bring-up 阶段的数字，不是最终性能。

LMSYS 把 Vera Rubin 放在 Blackwell Ultra（GB300 NVL72）之后。做 kernel 时，他们标出的
硬件变化是：每个 CTA 的 shared memory 从 Hopper / Blackwell 的 227 KiB 提到 327 KiB，
节点上有 212 个 SM，互联换成 NVLink 6。

vLLM 文章给出的单卡对照（相对 GB200 NVL72）是：

- NVFP4 推理算力约 5x
- HBM 带宽约 2.4x，显存从 HBM3e 换到 HBM4
- NVLink 双向带宽约 1.7x
- softmax 用的指数吞吐提高：相对 GB200，FP32 约 2x，BF16/FP16 约 4x

机柜不再只有 GPU。vLLM 文章列出的 Vera Rubin 平台有五套机柜级系统：Vera Rubin NVL72、
Vera CPU rack、Groq 3 LPX、Spectrum-6 SPX、BlueField-4 STX Storage。对平台工程，
这意味着 scale-up GPU 域、Arm CPU 沙盒、横向交换和存储节点会同时出现在一个集群里。

### vLLM：Blackwell 内核先能跑

Rubin 仍属于 Blackwell 架构族，编译目标是 `sm107`，但面向 `sm100f` 的 Blackwell
kernel 可以直接跑。所以 vLLM 里偏 GEMM 的 attention 和 MoE kernel 不改就能在 Rubin
上启动。社区据此给出 day-0 模型覆盖：DeepSeek、Kimi、GLM、MiniMax。

日常镜像已经按 CUDA 13.4 和 PyTorch 2.15 构建，入口是
`vllm/vllm-openai:cu134-nightly`。Rubin 专用 kernel 正通过 FlashInfer 0.7.0、
`vllm-project/MSA` 和 `vllm-project/humming` 往上游送，已经接上的包括 dense
NVFP4 / MXFP4 GEMM、NVFP4 MoE、FP8 attention、FP8 MSA prefill。

文章附录里的开关：

- NVFP4 dense GEMM：`--linear-backend flashinfer_cutedsl`；MXFP4 用
  `--linear-backend flashinfer_cutlass`。NVFP4 / MXFP4 checkpoint 默认就会走这条路径。
- NVFP4 MoE：`--moe-backend flashinfer_cutedsl`。
- Expert parallel 且 `--all2all-backend deepep_low_latency|nixl_ep` 时，
  `--moe-backend auto|flashinfer_cutedsl` 会落到 batched expert 的 CuTe-DSL masked
  grouped GEMM。
- FP8 attention：`--kv-cache-dtype fp8`（或 checkpoint 自己指定 FP8 KV），再加
  `--attention-backend FLASHINFER|FLASHINFER_MLA`。DeepSeek 风格 MLA prefill 还要
  `-ac.mla_prefill_backend=TRTLLM_RAGGED -ac.use_prefill_query_quantization=true`。
- MiniMax M3 的 FP8 MSA prefill：同样需要 FP8 KV，并设置
  `--attention-config.minimax_m3_msa_decode_backend=cutlass`。

早期性能（vLLM 文章，作者写明还会继续涨）：

<!-- markdownlint-disable MD013 -->
| 基准 | 模型与系统 | 公开结果 |
| --- | --- | --- |
| SemiAnalysis AgentX | vLLM 跑 MiniMax M3 | 匹配交互性时，每 GPU 吞吐最高是 GB200 的 7.84x；150 TPS 约束下是 5.18x |
| MLPerf Inference v6.1 VLM | vLLM 做后端、Dynamo 做前端路由，模型 Qwen3-VL-235B-A22B | 相对 GB300 NVL72，offline / server / interactive 最高约 3.7x |
<!-- markdownlint-enable MD013 -->

接下来他们列的 Rubin 工作包括：把 FlashInfer MegaMoE（`sm107`）接进 vLLM、把
locality domain 铺满 MoE、用 PDL 和 Lamport Sync 找层间重叠、为低延迟做 mega
kernel、为 Kimi K3 优化 KDA / MLA、为 DeepSeek-V4.1-Flash 接 CSA / HCA、补完 MSA
decode，以及接入 CFT counted-write MoE all-to-all。

### Locality domain：一张卡里的 HBM 也不均匀

从 Ampere 起，NVIDIA GPU 的 global memory 访问就不均匀。CUDA 13.4 的 locality
domain 让计算和数据落在同一个域里：SM 读本域 HBM，带宽更高、延迟更低。配合 Green
Context 和 CUDA stream，可以每个域启动一份 kernel。这主要加速访存受限的路径，
vLLM 拿 MoE decode 做了第一刀。

做法是 split-N：FC1 和 FC2 的权重按列切成两半，每半放进一个 locality domain，
该域的 SM 只读自己的那一半。decode 时 activation 很小，输入 X 和输出 C 继续跨域，
开销有限。SM 数不一定能等分。默认创建域时会丢掉无法配平的 SM，他们测到的是两个域
合计 200 个 SM；打开 `cudaDevSmResourceGroupBackfill` 后才能用满 212 个 SM。

以 MiniMax M3 的 MoE shape 为例，locality domain 打开后，小 token 前向的
FC1+FC2 平均约 1.2x，TP2 / TP4 / EP2 / EP4 趋势接近。只用 200 个 SM 的默认模式
也有差不多的收益，因为小 token decode 的时间主要花在读权重。通信时间没有算进去。
文章把这当成起点，不是最终调优结果。

### SGLang：Kimi K3 NVFP4

LMSYS 的早期机器是两台 Vera Rubin、共 8 张 GPU。推理侧把 SGLang 调到 Kimi K3 的
NVFP4 checkpoint 上。K3 是 2.8T 混合模型，上下文 1M。93 层 attention 里，69 层是
KDA 线性 attention，24 层是 MLA，每层输出按 block 做 Attention Residuals。FFN 是
LatentMoE：896 个 expert、top-16、3584 维 latent。服务方式是 RadixArk DSpark 的
block speculative decoding，每步先 draft 再 verify。

Attention 上的改动，都是把 Blackwell 时代的 kernel 按新上限重调：

- MLA decode 主要在等 HBM 上的 KV。Blackwell 的 FP8 kernel 用 227 KiB shared
  memory 排了 3 级 K、2 级 V。327 KiB 刚好多一级 K、多两级 V。batch 16、128k
  上下文时 MLA 快 16%，输出 bit-identical。
- 低并发时一份请求的 KV 被拆到很多 CTA，第二个 kernel 做归约。原先逐段 load、
  逐段等。改成先把 load 全部发出去，再在寄存器里累加。batch 1、128k 时完整 FP8
  MLA 快 20%。
- batch 1 的默认 32-way split 喂不饱 212 个 SM。K3 这个 shape 提到 64-way 后，
  FP8 KV 的端到端收益是 1.9%。
- FP8 转换如果不做饱和，编译器不会走打包硬件转换。饱和转换把溢出钳到 ±448，
  准备 kernel 快 2.5x。

MoE 和通信：

- 每层 MoE 结尾都是 finalize、加 shared expert、8 卡 all-reduce、RMSNorm。K3 有
  92 层 MoE，这些小 kernel 的 launch 开销占主导。把四步收进一个 collective
  kernel，每步 decode 少 276 次 launch，端到端 5.9%。
- fused tail 在小 batch 用 push all-reduce，大 batch 用 pull。Rubin 上 push 一直
  快到 256 行，交叉点挪过去之后，32 并发的 decode 吞吐 +3.6%。
- latent up-projection 的时间花在标量 FMA 和 warp shuffle 上。4–8 行改走
  `mma.m16n8k16` 后，decode step 少 1.1%。

KDA：

- verify kernel 大量时间耗在 barrier。原先每个 CTA 把 conv 权重拷进 shared
  memory 再等整块 barrier。现在每个 warp 把自己的权重留在寄存器里，warp 内的
  state 交接不再要 CTA barrier；空出来的 v warp 顺便算 output-norm gate。输出
  仍然 bitwise identical，生产 verify kernel 快 20%。
- KDA 的 gated RMSNorm 要从融合 QKVG 的一列里取 gate。切片不连续时 PyTorch 会
  先拷贝，每次 2.6 µs，一步 69 次。norm kernel 按 stride 直接读 gate 后，decode
  step 少 1.8%。

Cognition 用自己的 SGLang 分支在 Vera Rubin NVL72 上报告，总 token 吞吐相对
GB200 NVL72 最高约 4.8x。LMSYS 注明：这是对方的私有 fork 和对方自己的 benchmark
设置，不能直接当成上游 SGLang 的数字。

### Miles：推理和 RL 在同一张机柜上

Miles 用 SGLang 做 rollout、Megatron 做训练。Rubin enablement 合入之后，单张 tray
（4 GPU）、一个容器镜像就能把 RL 跑通：

- Qwen3-30B-A3B，GSM8K，每轮 256 个 prompt × 8 个 sample，回答最长 1,024 token。
  50 轮 rollout 里奖励大约从 45% 升到 95%，和 GB300 的奖励曲线一致。
- DeepSeek-V4-Flash 的 4 层 FP8 路径，在 GSM8K 上 rollout 和训练都能走完
  （32 prompt × 8 sample，回答最长 256 token）。

Agentic RL 的第一步放在同一张 tray 的 Vera CPU 上。NeMo Gym 的 mini-SWE-agent
给每个 episode 一个沙盒，沙盒跑在 tray 上的 Arm Vera CPU，旁边就是在做
Qwen3.5-35B-A3B 推理和训练的 GPU，同时开 64 个沙盒。任务用 SWE-bench Verified
的预构建 arm64 镜像，打分在这些镜像上验证过。每步从 64 个任务池里抽
8 tasks × 8 attempts，单 episode 最长 64K token。公开曲线是：奖励维持在大约
0.6，episode 大约短 30%，rollout 和 training 保持接近。

这件事和本仓库的 agent sandbox 讨论接在一起：沙盒不再默认放到另一组 CPU 节点，
而是和 GPU tray 放在同一台机器的 Vera CPU 上。规模上去之后，Vera CPU 服务器
才是并发环境数的上限。

## DaoCloud 案例：Shanghai Cube

Shanghai Cube 是 2025-03-21 发布的国产高密度液冷整柜，定位是和 NVIDIA 机柜级
超节点同一类的产品形态。DaoCloud 在其中的角色是定制操作系统，以及面向高密度
国产算力的调度管理，不是 GPU 或 scale-up 交换本身。

联合发布方包括上海模合信息科技、算丰信息、沐曦集成电路、云合智网、道客云、
立讯精密、无限光年、无问芯穹。分工在 DaoCloud 和产品站的公开材料里是：

- 沐曦：曦云 C550 定制 OAM
- 云合智网：国产交换芯片
- 立讯精密：整机量产
- DaoCloud：定制国产操作系统和调度管理
- 无限光年、无问芯穹：软硬件联合优化
- 复旦大学、创智学院：模型调优

首套样机（计算、管理、存储、网络）放在复旦大学上海张江校区。DaoCloud 公开写法是：
这套系统已经跑通 DeepSeek 671B 满血版推理，并支持其他主流模型的训练和微调。
算丰把「丰收一号 / 二号 / 三号」上累计超过 3,000 卡国产 GPU 的运营经验做进了设计。

机柜形态，产品站和后续系统集成材料可以合在一起看：

- 单柜 128 卡，冷板液冷。产品站写的是 47U、4 组 TP32。
- 系统集成材料进一步把整柜拆成 2 个 20U 超节点群组。每组 8 台 2U 计算节点、
  1 台供电模块、4 台 1U scale-up 交换机。计算节点是双路海光或 Intel 第四代 /
  第五代至强，加 8 张 OAM 2.0；柜内 54V 直流汇流排，CPU 和 GPU 走冷板。
- 每组 8 节点支持 32/64 卡 scale-up，整柜 16 个计算节点共 128 卡。公开目标是
  从单柜私有化部署扩到万卡。
- 同一篇集成材料给出的系统指标是：相对传统节点式交付效率提升约 50%，PUE 可到
  1.15。这是系统集成方公布的数字。

和耀龙 S8000 G2 放在一条产品线上理解：S8000 G2 解决 64 卡 Mesh 超节点，
Shanghai Cube 解决 128 卡整柜交付。8 柜并排是沐曦材料里的千卡集群组法。
下一代公开方向包括光互连和国产高速网卡。

对 DaoCloud 平台，这个案例说明国产超节点要过的三层和 NVIDIA 机柜是同一类问题：

1. 设备能被 Kubernetes 认出来（驱动、Device Plugin、HAMi 已经覆盖沐曦）。
2. 推理栈能吃到卡的算子（MXMACA、vLLM-MetaX，以及 MLA / MoE / Attention kernel）。
3. 调度要看见超节点拓扑，而不是只看见「有几张 GPU」。TP / EP 落在不同
   scale-up 组里，通信路径会直接变。

DaoCloud 自己的异构 GPU 文章把 Shanghai Cube 写成从「硬件可用」到「生产级规模化」
的例子，并把它放在 HAMi、拓扑感知和统一 GPU 管理这条线上。

## 平台侧要跟着变的地方

超节点把三层局部性叠在一起，调度和镜像都要能说清楚任务落在哪一层：

1. **机柜 scale-up 域**。GB200 / GB300 / Vera Rubin 的 NVL72，耀龙的 64 卡 Mesh，
   Shanghai Cube 的 TP32 或 20U 群组，都是这一层。放错域，专家并行和集合通信先受损。
2. **卡内 locality domain**。这是 Vera Rubin 新暴露出来的一层。CUDA 13.4 允许按域
   切 MoE 权重。它不是 NVLink 域，Kubernetes 今天也还没有对应的资源属性。
3. **同 tray 的 CPU**。Miles 把 SWE 沙盒放在 Vera CPU 上，和 GPU 训练 / 推理并排。
   Agent 工作负载要同时申请 GPU scale-up 域和旁边的 Arm CPU 沙盒容量。

软件跟进也分成两条：

- NVIDIA 路径目前是「Blackwell 内核先跑，Rubin 内核再换」。`sm100f` 的 vLLM
  kernel 能在 Rubin 上启动；要吃到 HBM4、NVLink 6 和 327 KiB shared memory，
  需要 CUDA 13.4 的 nightly 镜像和 FlashInfer / SGLang 里那些 Rubin 专用 kernel。
- 国产路径以 Shanghai Cube 为例：操作系统和调度先把 128 卡液冷柜收成可交付单元，
  再靠 MXMACA 和 vLLM 插件把模型性能补上。拓扑感知仍然是没做完的部分。

## 参考

- [vLLM Support for NVIDIA Vera Rubin NVL72](https://vllm.ai/blog/2026-10-09-vera-rubin-preview)
  （2026-10-09）
- [SGLang and Miles on NVIDIA Vera Rubin](https://www.lmsys.org/blog/2026-10-09-vera-rubin/)
  （2026-10-09）
- [Shanghai Cube 发布](https://d.run/news/i80bp6njjsg0yhxat1rgbvb7)（DaoCloud，2025-03-21）
- [异构 GPU 优化实践](https://github.com/DaoCloud/DaoCloud-docs/blob/main/docs/zh/docs/blogs/2026/optimize-gpu.md)
- [Shanghai Cube 产品站](https://www.shanghaicube.com/index.html)
- [沐曦：超节点技术体系与耀龙 / Shanghai Cube 产品布局](https://www.metax-tech.com/ndetail/12573.html)
