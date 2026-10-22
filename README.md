# B-draft 云主机实验

本目录是可运行的教学参考实现，已合并 E6/E7 代码，未包含助教门禁演示测试。
请先阅读实验包 docs/00_开始与目录.md，再按 03_B轨道操作指南.md 完成步骤。
统一入口：`python3 scripts/lab_cloud.py --help`。
不需要 Windows、WSL、Docker Desktop，不使用助教的学号、代理地址或宿主机目录。
仓库旧 Makefile/Compose 属于 E4 环境接口；本次优先使用 lab_cloud.py，避免镜像标签混用。

## B 轨道命名 Buildx 构建器

课程服务器若已配置命名 Buildx 实例，可在 B 轨道 E6/E7 使用可选的
`--builder NAME`。入口会先执行 `docker buildx inspect NAME`，仅把
`~/.docker/buildx` 只读挂载到服务容器暂存路径，再复制到容器内可写的
`/tmp/.docker/buildx`，并设置 `BUILDX_BUILDER`；不会挂载
`~/.docker/config.json`。可写副本只保存于一次性服务容器。不传该参数时保持
默认 Docker 构建行为。

第 2 人 E6 服务器命令：

```bash
python3 scripts/lab_cloud.py e6 \
  --builder e5-241880585 \
  --candidate work/candidate/Dockerfile \
  --out work/e6-own-241880481-02 \
  --build-timeout 600
```
