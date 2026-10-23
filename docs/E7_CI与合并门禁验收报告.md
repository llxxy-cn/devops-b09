# E7 B组 GitLab CI 与合并门禁验收报告

## 1. 验收范围

执行人：241880585

验收日期：2026-10-23

GitLab项目：`241880585/devops-e5`

目标分支：`main`

本报告覆盖以下闭环：

1. 为现有B轨道项目接入GitLab CI；
2. 在本组云服务器的专用Linux Shell Runner上重新构建服务镜像；
3. 执行镜像内单元测试和E7完整六项gate；
4. 保护`main`，禁止直接推送并要求最新流水线成功；
5. 在同一Merge Request中证明“错误测试导致失败并阻止合并”；
6. 仅修正测试断言后证明流水线和可合并状态恢复；
7. 合并后再次验证最终`main`。

## 2. CI运行环境

| 项目 | 实际值 |
|---|---|
| Runner | 项目专用 `devops-e5 Linux Docker shell`（标签 `devops-e5-shell`） |
| GitLab Runner | 19.5.1，Linux Shell executor |
| 服务器 | 本组课程云服务器，Linux amd64 |
| Docker Engine | 29.8.1 |
| Docker Buildx | v0.37.1 |
| BuildKit | v0.33.1 |
| 命名构建器 | `e5-241880585`，docker-container driver |
| Artifact策略 | 成功或失败均上传，保留14天 |

Runner用户已加入`docker`组，并验证可访问`/var/run/docker.sock`及命名构建器。Runner认证配置未写入仓库或Artifact。

## 3. GitLab CI实现

CI配置文件为`.gitlab-ci.yml`，Job名为`e7-b-quality-gate`。流水线覆盖分支推送、Merge Request和Web手工触发，并执行：

1. 记录commit、Pipeline URL、Job URL、Docker/Buildx版本和构建器信息；
2. 执行Python语法检查及含Git历史的密钥扫描；
3. 使用`e5-241880585`从当前提交构建并加载服务镜像；
4. 在镜像内执行全部单元测试；
5. 预构建CI候选以完成共享工具链层；
6. 执行`unit-tests`、`success`、`wrong-output`、`invalid-candidate`、`build-failed`和`runtime-timeout`六项gate；
7. 通过`artifacts: when: always`保留成功或失败证据。

服务构建和测试不复用第三人的旧服务镜像；每个CI提交均从当前源码重建服务镜像。最终程序验证仍由现有工作流以`--network none`执行。

## 4. CI候选与网络稳定性处理

原始E5候选`fixtures/ci-candidates/DeepSeek-E5.Dockerfile`保持不变。CI使用派生文件`fixtures/ci-candidates/DeepSeek-E5-CI.Dockerfile`，并由`fixtures/ci-candidates/provenance-ci.json`记录来源和修改。

派生候选保持以下约束不变：

- 相同的digest固定基础镜像；
- `WORKDIR /work`；
- `COPY main.c Makefile ./`；
- `RUN make`；
- `CMD ["./hello"]`。

课程服务器从Debian官方源下载`build-essential`时，多个候选构建耗尽600秒预算；改用阿里云源后，82.9 MB依赖集仍无法稳定完成。最终CI只安装本题真实需要的`make`、`tcc`和`libc6-dev`，将`tcc`暴露为`cc`，实际构建日志为`cc main.c -o hello`，运行输出为`hello E3`。依赖层在gate前预构建一次，五个场景复用同一BuildKit缓存。

CI派生候选SHA-256为：

```text
f85b68355a51039487c1c3588778a4e92cdefff69486c272b61fdf27cc88b8a6
```

该值来自Linux CI检出的LF版本，并已在恢复与最终main Artifact中重复记录。本机Git配置为`core.autocrlf=true`，Windows工作副本会转换为CRLF，因此不能用工作副本字节哈希替代CI证据中的哈希。

此派生文件是服务器CI适配，不是新的模型回答，不替换原始E5候选证据。

## 5. 基线CI与首次合并

| 阶段 | 提交/合并提交 | Pipeline | Job/结果 |
|---|---|---|---|
| CI分支稳定基线 | `eaeddc70` | [343601](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343601) | Job 686057；26项单测、六项gate通过；186个Artifact文件 |
| CI配置MR | MR [!4](https://git.nju.edu.cn/241880585/devops-e5/-/merge_requests/4) | [343604](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343604) | MR Pipeline通过 |
| CI配置合入main | `4cf75df7` | [343605](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343605) | `main` Pipeline通过 |

## 6. main保护与合并检查

GitLab实际设置如下：

- `main`允许合并角色：Maintainers；
- `main`允许推送和合并：No one；
- 强制推送：关闭；
- Merge checks中的“流水线必须成功”：启用；
- “跳过的流水线视为成功”：关闭。

配置截图见：

- `work/e7-ci-merge-gate-241880585/screenshots/01-main-protected-branch.png`
- `work/e7-ci-merge-gate-241880585/screenshots/02-pipelines-must-succeed.png`

## 7. 失败合并拦截

在MR [!5](https://git.nju.edu.cn/241880585/devops-e5/-/merge_requests/5)的提交`cd88108a8431142f0780b0198e8cea00e32bd2e5`中，仅新增测试：

```python
assert main(["version"]) == 1
```

业务实现未修改。实际结果：

| 项目 | 结果 |
|---|---|
| Pipeline | [343613](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343613)，失败 |
| Job | [686098](https://git.nju.edu.cn/241880585/devops-e5/-/jobs/686098)，退出码1 |
| 单元测试 | `1 failed, 26 passed` |
| 实际错误 | `AssertionError: assert 0 == 1` |
| Artifact | 失败时仍上传成功，共13个文件 |
| MR状态 | “合并被阻止：1检查失败”；原因“流水线必须成功” |

失败日志见`work/e7-ci-merge-gate-241880585/failure/unit-tests.log`，合并拦截图见`screenshots/03-failed-pipeline-merge-blocked.png`。

## 8. 同一MR修复与恢复

在同一分支和同一MR中，提交`3fc27ca6e2c3a4d5a1f7131b55548fbabc63c7e1`只把演示测试修正为：

```python
assert main(["version"]) == 0
```

业务实现仍未修改。实际结果：

| 项目 | 结果 |
|---|---|
| Pipeline | [343616](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343616)，成功 |
| Job | [686115](https://git.nju.edu.cn/241880585/devops-e5/-/jobs/686115)，退出码0 |
| 单元测试 | `27 passed` |
| E7 gate | 六项全部`passed=true` |
| Artifact | 上传成功，共186个文件 |
| MR状态 | 从“合并被阻止”恢复为“准备合并” |

恢复截图见`screenshots/04-same-mr-recovered.png`。

## 9. 最终合并与main复验

MR !5已合并到`main`，merge commit为`523ca700a2f1b7a64347008c57cf3029722dfe3a`。最终结果：

| 项目 | 结果 |
|---|---|
| 最终main Pipeline | [343619](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343619)，成功 |
| 最终main Job | [686121](https://git.nju.edu.cn/241880585/devops-e5/-/jobs/686121)，退出码0 |
| 单元测试 | `27 passed in 0.15s` |
| success | SUCCEEDED，退出码0 |
| wrong-output | FAILED，预期退出码1 |
| invalid-candidate | FAILED，预期退出码1 |
| build-failed | FAILED，预期退出码1 |
| runtime-timeout | TIMED_OUT，预期退出码1 |
| Artifact | 上传成功，共186个文件 |

上述故障场景的退出码1均为预期结果，最终`gate-result.json`整体为`passed: true`。合并截图见`screenshots/05-mr-merged.png`。

## 10. 验收结论与整合信息

GitLab CI、服务器镜像重建、26项基线测试、失败合并拦截、同一MR修复恢复、27项最终测试、六项gate、`main`保护和最终合并均已完成。精选原始证据及索引位于：

```text
work/e7-ci-merge-gate-241880585/
```

供第1人整合的关键标识：

- CI配置MR：!4；CI合入main提交：`4cf75df7`；
- 失败/恢复MR：!5；
- 失败提交：`cd88108a`；Pipeline 343613；Job 686098；
- 恢复提交：`3fc27ca6`；Pipeline 343616；Job 686115；
- 最终merge commit：`523ca700`；Pipeline 343619；Job 686121；
- 失败统计：`1 failed, 26 passed`；最终统计：`27 passed`；
- 完整gate：六项全部通过；
- `main`保护：禁止直接推送；最新Pipeline必须成功。

