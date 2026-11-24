# 最终 main 与 CI 核对

最终验收 main：3e2af528054822c45e9c2463d82ca60d23d3b58e
专项实测基线：298ff1366cdd2f4314cce625492fa813f484893f

PR #23 已合并，B4 最终集成记录已入 main。
已比较 labs/、scripts/、.github/、run_e11e12.py、run_lab.py。
专项基线与最终 main、当前交付分支的上述路径均无差异。
各次原始测试证据继续保留实际被测 SHA。

## 最终 main CI

以下五类工作流对应最终 main 提交，均为 success。

| 工作流 | 运行记录 |
|---|---|
| E7 B quality gate | https://github.com/llxxy-cn/devops-b09/actions/runs/45356981798 |
| E8–E10 teaching validation | https://github.com/llxxy-cn/devops-b09/actions/runs/45356981695 |
| E11–E12 integration | https://github.com/llxxy-cn/devops-b09/actions/runs/45356981484 |
| E13 person3 security gate | https://github.com/llxxy-cn/devops-b09/actions/runs/45356981533 |
| E13–E14 integration gate | https://github.com/llxxy-cn/devops-b09/actions/runs/45356981444 |

## 门禁结论

C1–C8、三个教师项目、扫描及集成验收技术结论为通过。
此前核对时开放 Issue 为 0，Issue #18 已关闭。
本次推送后等待 PR #24 最新 CI 全绿和组员复审。

A09 已签收原交付，新回归是否需额外复核由 B1 继续协调。
候选发布仓库和提交由组内确认。

## 完整证据包

/root/devops-submissions/241880585/e13-gate-298ff136-Fdh9Zq.tar.gz

SHA256：
03a4f592dd4ef17b45c15feb92cd2cb947b935eef82982ac0083bc4b7cdae891

校验结果为 OK。原包保持不变，本记录为打包后的补充文件。
