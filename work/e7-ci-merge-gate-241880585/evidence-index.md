# E7 GitLab CI与合并门禁证据索引

采集日期：2026-10-23

执行人：241880585

项目：`https://git.nju.edu.cn/241880585/devops-e5`

## 关键流程

| 阶段 | Commit | Pipeline | Job | 结论 | 本地证据 |
|---|---|---|---|---|---|
| CI稳定基线 | `eaeddc70` | [343601](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343601) | 686057 | 26项测试及六项gate通过 | GitLab Artifact |
| CI配置MR | `eaeddc70` | [343604](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343604) | — | MR !4通过 | GitLab Pipeline |
| CI首次main | `4cf75df7` | [343605](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343605) | — | main通过 | GitLab Pipeline |
| 故意失败 | `cd88108a8431142f0780b0198e8cea00e32bd2e5` | [343613](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343613) | [686098](https://git.nju.edu.cn/241880585/devops-e5/-/jobs/686098) | `1 failed, 26 passed`，合并被阻止 | `failure/`、截图03 |
| 同MR恢复 | `3fc27ca6e2c3a4d5a1f7131b55548fbabc63c7e1` | [343616](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343616) | [686115](https://git.nju.edu.cn/241880585/devops-e5/-/jobs/686115) | `27 passed`，六项gate通过 | `recovery/`、截图04 |
| 最终main | `523ca700a2f1b7a64347008c57cf3029722dfe3a` | [343619](https://git.nju.edu.cn/241880585/devops-e5/-/pipelines/343619) | [686121](https://git.nju.edu.cn/241880585/devops-e5/-/jobs/686121) | `27 passed`，六项gate通过 | `main-final/`、截图05 |

Merge Requests：

- CI配置：[!4](https://git.nju.edu.cn/241880585/devops-e5/-/merge_requests/4)
- 失败、恢复与最终合并：[!5](https://git.nju.edu.cn/241880585/devops-e5/-/merge_requests/5)

## 精选文件

### failure/

- `commit.txt`：失败提交完整SHA；
- `pipeline-url.txt`、`job-url.txt`：GitLab永久链接；
- `unit-tests.log`：`AssertionError: assert 0 == 1`及`1 failed, 26 passed`；
- `source-scan.log`：失败前的历史密钥扫描通过记录。

### recovery/

- `commit.txt`、`pipeline-url.txt`、`job-url.txt`；
- `unit-tests.log`：`27 passed`；
- `gate-result.json`、`results.csv`：六项gate全部通过；
- `candidate-warm-run.log`：真实运行输出`hello E3`；
- `ci-candidate-sha256.txt`、`ci-candidate-provenance.json`：CI候选完整性和来源。

### main-final/

- `commit.txt`、`pipeline-url.txt`、`job-url.txt`；
- `unit-tests.log`：最终main为`27 passed`；
- `invocation.json`：最终gate执行时间、镜像和构建器；
- `gate-result.json`、`results.csv`：最终main六项gate结果；
- `candidate-warm-run.log`及候选来源记录。

### screenshots/

1. `01-main-protected-branch.png`：main允许Maintainers合并、No one直接推送、禁止强推；
2. `02-pipelines-must-succeed.png`：启用“流水线必须成功”，未把跳过视为成功；
3. `03-failed-pipeline-merge-blocked.png`：Pipeline 343613失败且MR被阻止合并；
4. `04-same-mr-recovered.png`：同一MR最新Pipeline 343616通过并恢复可合并；
5. `05-mr-merged.png`：MR !5已合并，merge commit `523ca700`。

## 原始Artifact归档

本机另保留GitLab下载的完整压缩包：

- `e7-b-evidence-343613-686098.zip`（失败，13个文件）；
- `e7-b-evidence-343616-686115.zip`（恢复，186个文件）；
- `e7-b-evidence-343619-686121.zip`（最终main，186个文件）。

GitLab CI设置的Artifact保留期为14天；本目录收录长期交付所需的精选文本与截图。
