# B09 B2 统一基线服务器专项复跑

实测代码提交 `298ff1366cdd2f4314cce625492fa813f484893f`。
项目 Base `e825395a5f8006f1c57a115cc25ea5c7802863ee`，Target `ba688c40d13cd8658e554f7544f1546d35b4b397`。
消费报告 SHA256 `c19a6b11675b86bd5f2bfe348b3faeb65151b4c57681a54103510f642845e5cf`。
A09 报告来源身份见 request-normal.json 的 expected_source_report。

| 用例 | 结果 | 证据 |
| --- | --- | --- |
| C4 | 构建超时，外层 FAILED，内层 TIMED_OUT，进程检查时未发现对应残留 | c4-run、c4-process-check.log、c4-exit.txt |
| C5 | 错误补丁触发编译失败，accepted=false，源项目完整性检查通过 | c5-case、c5-validation-console.log |
| C7 | 超时后新任务成功，job/trace 隔离，153 个产物校验通过 | c7-recovery-run、c7-isolation-check.log |
| C8 | 相同输入复用同一 job，不同输入返回 409，仅创建一条任务，最终成功 | c8-http、c8-api-job |

C4 job `job-581481c504dc41d6b6f92f7b0ecda00e`，trace `trace-d278cfb76f6a4045becd164ab974ad13`。
C7 job `job-27f57e8a40914a2f9b9ef29adb20ec2a`，trace `trace-b246111f3b0f4df18d5ff6827c70dec8`。
C8 job `job-c8ada5349d3247a4aced3b35b9307904`，trace `trace-3436f679dab44ba99f94998e577235d2`。
C8 已校验 153 个产物的哈希和大小。

C5 直接调用本基线 pipeline.validate_in_draft，在实际候选镜像中验证错误补丁。
源项目验证前后的 HEAD、文件哈希和工作区状态均一致。
本轮使用既有离线镜像，实际镜像标识见运行结果及 c8-api-container.json。
C8 专用 API 容器已停止。
证据扫描结果见 runtime-scan.log 和 runtime-scan-exit.txt。

本记录供 B3 汇总统一基线下的 E13 门禁。
E14 四服务故障恢复验证另行记录。
