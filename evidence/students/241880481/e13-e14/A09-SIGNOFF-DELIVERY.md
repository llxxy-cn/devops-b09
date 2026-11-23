# A09 E13 B1 签收交付

状态：**服务器实测通过，A09 已核验签收**。

- [2026-11-23 A09 签收记录](A09-SIGNOFF-20261123.md)
- [2026-11-23 已签收交付勘误](ERRATA-20261123.md)
- 关联交付提交：`cbf90cce6fcb4950c6326704bd970f9ed80693bb`

已签收回传包及上述固定提交保持不变。服务器原始路径与包内扁平文件名的逐项映射、
包内 CRLF 清单的兼容校验命令见勘误说明。

## 下载与校验

原始回传包 `a09-e13-b09-server-return-20261122-195038.tar.gz` 为 154,556,278 字节，SHA256：

```text
1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33
```

GitHub 普通 Git 对单文件 100 MiB 有硬限制，因此保留 `work/` 下原包不变，并将同一字节流切成 4 个每个不超过 50,000,000 字节的可提交分片：

- [part01](a09-e13-b09-server-return-20261122-195038.tar.gz.part01)
- [part02](a09-e13-b09-server-return-20261122-195038.tar.gz.part02)
- [part03](a09-e13-b09-server-return-20261122-195038.tar.gz.part03)
- [part04](a09-e13-b09-server-return-20261122-195038.tar.gz.part04)
- [SHA256SUMS](SHA256SUMS)

POSIX 重组：

```sh
cat a09-e13-b09-server-return-20261122-195038.tar.gz.part01 \
    a09-e13-b09-server-return-20261122-195038.tar.gz.part02 \
    a09-e13-b09-server-return-20261122-195038.tar.gz.part03 \
    a09-e13-b09-server-return-20261122-195038.tar.gz.part04 \
  > a09-e13-b09-server-return-20261122-195038.tar.gz
sha256sum -c SHA256SUMS
```

PowerShell 重组：

```powershell
$output = [IO.File]::Create('a09-e13-b09-server-return-20261122-195038.tar.gz')
try {
  Get-ChildItem 'a09-e13-b09-server-return-20261122-195038.tar.gz.part*' |
    Sort-Object Name |
    ForEach-Object {
      $input = [IO.File]::OpenRead($_.FullName)
      try { $input.CopyTo($output) } finally { $input.Dispose() }
    }
} finally { $output.Dispose() }
Get-FileHash -Algorithm SHA256 'a09-e13-b09-server-return-20261122-195038.tar.gz'
```

## C1 服务器证据

- B09 job：`job-ec9901a266654aabb0f3c31ecc0fd697`
- B09 trace：`trace-b9ce4c04ed934430815be6d7fc346aff`
- Base：`e825395a5f8006f1c57a115cc25ea5c7802863ee`
- Target：`ba688c40d13cd8658e554f7544f1546d35b4b397`
- 结果：`SUCCEEDED`；最终 `MD=0`、`RD=1`，唯一 RD 为 `REDUNDANT(main.o, unused.h)`。
- 重建验证：6/6 条修复边均 `rebuilt=true` 且 `output_matches=true`。

服务器证据根：
`/root/devops-b09-e13-offline.AXJSHY/work/e13-b1-server-formal-20261122-195038/`

交付产物：

| 文件（服务器完整路径） | SHA256 |
| --- | --- |
| `/root/devops-b09-e13-offline.AXJSHY/work/e13-b1-server-formal-20261122-195038/deliverables/candidate.patch` | `8634d2aa57acc132ddf21ef90fa087aca1a313aca37a7bc74bb9b5ce9bf29c6e` |
| `/root/devops-b09-e13-offline.AXJSHY/work/e13-b1-server-formal-20261122-195038/deliverables/validation.json` | `f9f4d6b0c2bae1dfcf1895a3eb83e6499a239c51f24e692e7d9fa38dcadb55e9` |
| `/root/devops-b09-e13-offline.AXJSHY/work/e13-b1-server-formal-20261122-195038/deliverables/final-recheck.json` | `85fd1aa62fbdbec19b9625e6ef559be8867a698c3541afdffa3e0abade0e2fe1` |

`final-recheck.json` 是从 C1 最终全量复检的 `c1/run/final-full/findings.json` 原样复制而来。另有两个容易混淆但均已保留的流水线文件：

- `c1/run/validation/recheck.json`：`d7952718fbb581067f6af4e860a571876cf56c7f10b912e856f755fa57d065a8`
- `c1/run/recheck.json`（阶段信封）：`24b8c344cde10243c6ac2f6fa1db6598177d0cb297ee965d20e3d58caf288ed8`

修复 bundle 已通过 `git bundle verify`，记录完整历史：

- 修复提交：`74eff064e1eae3e244b0acf80880c92fb4635e26`
- 父提交：`ba688c40d13cd8658e554f7544f1546d35b4b397`
- 提交说明：`fix: declare observed Make dependencies`

## C2、C3 与恢复

- C2：退出码 1，`STALE_REPORT`；未生成 `candidate.patch`，未创建验证 sandbox，项目 HEAD/Makefile 保持不变。job/trace：`job-0c0a865d138f4249b2ef1c7f3e7791da` / `trace-99fd2dbb1b0a4bd084ab4d551e81dd7a`。
- C3：退出码 1，`ARTIFACT_HASH_MISMATCH`；未生成 `candidate.patch`，未创建验证 sandbox，项目 HEAD/Makefile 保持不变。job/trace：`job-19d998dafff0457d8fa862b7bc784360` / `trace-828731512d364995b7f6b3af1e040014`。
- 恢复：恢复正确输入并在新目录运行，`SUCCEEDED`。job/trace：`job-d7ff2505c71b4406aa8334467e5fb24a` / `trace-e0ac2f893d5c46018f124a3467682932`。

## handoff 哈希差异结论

服务器实际请求 `inputs/request-c1.json` 指向并校验的是服务器现场重新生成的：

```text
/root/devops-b09-e13-offline.AXJSHY/work/e13-b1-server-formal-20261122-195038/inputs/fixed-md-a09.json
SHA256 c19a6b11675b86bd5f2bfe348b3faeb65151b4c57681a54103510f642845e5cf
bytes  2825
```

流水线把它逐字节保存为 `c1/run/fixed-md-input.json`；两文件字节完全相同，后者才是实际消费留痕。它由 `labs/e13e14/handoff_a_to_b.py` 从服务器安全解包并验证的 A09 `result.json` 和 `incremental-check.json` 生成。

A09 原件为：

```text
work/e13-b1-formal-20261122-121914/materials/handoff/fixed-md-a09-project.json
SHA256 623e6854cb99904eb20e49e72436a182a83446a1e68e2218741971bca1f618a2
bytes  2806
```

逐字段比较结果：两者 `data` 完全相等，`source_report` 的 job、trace、URI、SHA256 也完全相等；重新生成的服务器信封只比 A09 原件多一个 `source_report.bytes = 3052` 字段。删除这个新增字段后，两个 JSON 对象整体相等。因此这是兼容信封重新生成时补齐已验证字节数导致的字节哈希变化，不是业务数据、来源或关联错误，无需修改旧证据。

保留的来源身份为：

- job：`job-131c4b1d8c34469aaa31f9e2a9da1736`
- trace：`trace-c224eaab92394b91bedfc2dea14ebc61`
- URI：`artifact://job-131c4b1d8c34469aaa31f9e2a9da1736/incremental-check.json`
- 原始 incremental-check SHA256：`504a3c505c1479c990f59143926247a2deb7415375de5d957a2d4938aefff224`
- 原始 incremental-check 字节数：3052

包内名为 `fixed-md-a09.json` 的 2,832 字节文件（SHA256 `a37c47c17807ae16d6042f29cbb48d460bd9c5ddea611e6aefea3f01146c644b`）是 C1 流水线生成的 `fixed-md` 阶段输出，含新的 B09 job/trace 和对 `fixed-md-input.json` 的 artifact 引用；它不是 A09 原件，也不是请求实际读取的 2,825 字节输入信封。
