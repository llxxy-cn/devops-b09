# B09 E13 2号异常测试记录

测试代码提交 `1cd48d2ccb92b3a48b169da723bc570bd5dd6fa2`。
A09 项目 Target `ba688c40d13cd8658e554f7544f1546d35b4b397`。
沿用 1 号离线构建配置，候选镜像记录于 C5 验证及 C8 运行证据。

| 用例 | 实际结果 | 证据 |
| --- | --- | --- |
| C4 | 构建超时，外层 FAILED，内层 TIMED_OUT | c4-run、c4-console.log、c4-process-check.log |
| C5 | 错误补丁成功应用后触发编译错误，验证拒绝，源项目完整性检查通过 | c5-case、c5-validation-console.log |
| C7 | 超时后正常任务成功，标识隔离，153 个产物校验通过 | c7-recovery-run、c7-isolation-check.log |
| C8 | 相同键相同输入复用任务，不同输入返回 409，仅一条任务，最终成功，153 个产物校验通过 | c8-http、c8-api-job |

C4 job `job-b8283b04d80141c8b76b6abbb7b718c0`，trace `trace-3a0bf289715a4fd18a56eacc25e2af55`。
C7 job `job-4165b35942be47caa13a2922ebf94a47`，trace `trace-0483959869c245918173182321754f36`。
C8 job `job-1ee21329632445b68c90210b0211d178`，trace `trace-4fd0a8c0d0f94baf996bc0c82037b440`。

C5 直接调用本轮 pipeline.validate_in_draft，在实际候选镜像中验证错误补丁。
该用例保存验证器拒绝记录、沙箱编译日志及源仓库前后提交、文件哈希和工作区状态。
C4 进程检查时未发现对应残留，现场记录见 c4-process-check.log。
C8 专用 API 容器已停止。

上述实测及证据日志扫描已通过。个人分支提交与交接待完成。
E14 四服务环境中的故障恢复复验由 2 号配合 4 号另行执行。
