# B1 Real C Make Project Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `fixtures/draft` 制作为具有 C0/C1 两个连续提交的真实 C/Make 项目，并形成可复现的 B1 交接证据。

**Architecture:** C0 使用 `main.c`、`helper.c`、`helper.h` 和 `config.h` 构成依赖完整的基线。C1 只增加并使用 `extra.h`，同时故意不把它加入 `main.o` 的 Makefile 依赖，从而形成唯一的 `MISSING main.o extra.h`。

**Tech Stack:** C11、GNU Make、Git、Docker、BuildKit、Python unittest、SHA256。

## Global Constraints

- 仓库必须为 `https://github.com/llxxy-cn/devops-b09`。
- 项目子目录必须为 `fixtures/draft`。
- 程序必须保持输出 `hello E3`。
- C1 必须是 C0 的直接后继提交。
- 候选镜像必须使用固定 digest 的 DaoCloud Python 基础镜像。
- 候选镜像必须使用清华 Debian 软件源。
- B1 不实现 E12 的 `project_subdir` 适配，不声称完成正式 A/B 联调。
- 修改后必须通过 E8–E10 的14项测试和 E11–E12 的14项测试。

---

### Task 1: 制作依赖完整的 C0

**Files:**

- Modify: `fixtures/draft/main.c`
- Create: `fixtures/draft/helper.c`
- Create: `fixtures/draft/helper.h`
- Create: `fixtures/draft/config.h`
- Modify: `fixtures/draft/Makefile`
- Modify: `fixtures/draft/README.md`
- Preserve: `fixtures/draft/Dockerfile.broken`

**Interfaces:**

- Produces: 可构建、输出 `hello E3`、无缺失依赖的 C0 完整提交 SHA。
- Consumes: 现有 `fixtures/draft` 旧实验目录。

- [ ] **Step 1: 保存修改前状态**

运行：

```bash
git status --short --branch
git log -1 --oneline
find fixtures/draft -maxdepth 1 -type f -printf '%f\n' | sort
```

预期：工作区干净，当前提交为设计和计划提交之后的 HEAD。

- [ ] **Step 2: 写入 C0 源文件**

`config.h`：

```c
#ifndef CONFIG_H
#define CONFIG_H

#define APP_MESSAGE "hello E3"

#endif
```

`helper.h`：

```c
#ifndef HELPER_H
#define HELPER_H

const char *helper_message(void);

#endif
```

`helper.c`：

```c
#include "helper.h"
#include "config.h"

const char *helper_message(void)
{
    return APP_MESSAGE;
}
```

`main.c`：

```c
#include <stdio.h>

#include "helper.h"

int main(void)
{
    puts(helper_message());
    return 0;
}
```

`Makefile`：

```make
CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror
TARGET := app
OBJECTS := main.o helper.o

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $(OBJECTS)

main.o: main.c helper.h
	$(CC) $(CFLAGS) -c main.c

helper.o: helper.c helper.h config.h
	$(CC) $(CFLAGS) -c helper.c

test: $(TARGET)
	@test "$$(./$(TARGET))" = "hello E3"

clean:
	rm -f $(TARGET) $(OBJECTS)
```

- [ ] **Step 3: 验证 C0**

运行：

```bash
make -C fixtures/draft clean
make -C fixtures/draft
make -C fixtures/draft test
test "$(fixtures/draft/app)" = "hello E3"
cc -MM fixtures/draft/main.c -Ifixtures/draft
cc -MM fixtures/draft/helper.c -Ifixtures/draft
```

预期：

- 编译成功。
- 测试成功。
- 输出为 `hello E3`。
- `main.o` 依赖 `main.c helper.h`。
- `helper.o` 依赖 `helper.c helper.h config.h`。

- [ ] **Step 4: 提交 C0**

运行：

```bash
make -C fixtures/draft clean
git add fixtures/draft
git diff --cached --check
git commit -m "feat: prepare B1 real C Make baseline"
git rev-parse HEAD
```

将输出的完整 SHA 记录为 `C0_COMMIT`。

---

### Task 2: 制作具有唯一 MD 的 C1

**Files:**

- Create: `fixtures/draft/extra.h`
- Modify: `fixtures/draft/main.c`
- Preserve without dependency change: `fixtures/draft/Makefile`

**Interfaces:**

- Consumes: Task 1 的 C0。
- Produces: C0 的直接后继 C1，以及唯一预期 `MISSING main.o extra.h`。

- [ ] **Step 1: 创建 `extra.h`**

```c
#ifndef EXTRA_H
#define EXTRA_H

#define OUTPUT_ENABLED 1

#endif
```

- [ ] **Step 2: 修改 `main.c` 使用 `extra.h`**

```c
#include <stdio.h>

#include "extra.h"
#include "helper.h"

int main(void)
{
    if (OUTPUT_ENABLED) {
        puts(helper_message());
    }
    return 0;
}
```

Makefile 中的依赖仍保持：

```make
main.o: main.c helper.h
```

不能加入 `extra.h`。

- [ ] **Step 3: 验证 C1 行为和依赖差异**

运行：

```bash
make -C fixtures/draft clean
make -C fixtures/draft
make -C fixtures/draft test
test "$(fixtures/draft/app)" = "hello E3"
cc -MM fixtures/draft/main.c -Ifixtures/draft
grep -F 'main.o: main.c helper.h' fixtures/draft/Makefile
! grep -E '^main\.o:.*extra\.h' fixtures/draft/Makefile
```

预期：

- 构建和测试成功。
- 编译器发现 `main.o` 实际依赖 `extra.h`。
- Makefile 的 `main.o` 声明没有 `extra.h`。
- 由此形成唯一 MD：`MISSING main.o extra.h`。

- [ ] **Step 4: 提交 C1并确认父子关系**

运行：

```bash
make -C fixtures/draft clean
git add fixtures/draft/main.c fixtures/draft/extra.h
git diff --cached --check
git commit -m "test: add B1 real missing dependency target"
git rev-parse HEAD
git rev-parse HEAD^
```

记录：

- 当前完整 SHA 为 `C1_COMMIT`。
- `HEAD^` 必须等于 `C0_COMMIT`。

---

### Task 3: 验证初始与候选 Dockerfile

**Files:**

- Preserve: `fixtures/draft/Dockerfile.broken`
- Create: `docs/students/241880481/e11-e12/real-project/candidate.Dockerfile`
- Create evidence under: `work/b1-e11e12/real-project/`

**Interfaces:**

- Consumes: Task 2 的 C1。
- Produces: 缺少 make 的失败日志、成功候选镜像、镜像 ID和输出日志。

- [ ] **Step 1: 构建初始 Dockerfile并要求失败**

运行 Docker 构建并保存日志，记录非零退出码。日志必须包含：

```text
make: not found
```

- [ ] **Step 2: 创建候选 Dockerfile**

候选文件内容：

```dockerfile
FROM m.daocloud.io/docker.io/library/python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f

WORKDIR /work

COPY main.c helper.c helper.h config.h extra.h Makefile ./

RUN sed -i \
    -e 's|https\?://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
    -e 's|https\?://security.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
    -e 's|https\?://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' \
    /etc/apt/sources.list.d/debian.sources

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN make clean && make && make test

CMD ["./app"]
```

- [ ] **Step 3: 构建并运行候选镜像**

镜像标签：

```text
b1-real-cmake:241880481
```

验收：

- Docker 构建退出码为0。
- 保存 `docker image inspect`。
- 保存不可变镜像 ID。
- 容器输出严格等于 `hello E3`。

---

### Task 4: 回归、报告与交接

**Files:**

- Create: `docs/students/241880481/e11-e12/real-project/README.md`
- Create: `docs/students/241880481/e11-e12/real-project/candidate.Dockerfile`
- Create: `docs/students/241880481/e11-e12/real-project/handoff.json`
- Preserve raw evidence under: `work/b1-e11e12/real-project/`

**Interfaces:**

- Consumes: C0、C1、Docker 结果和全部原始日志。
- Produces: 2号和3号能够独立复现的 B1 交接材料。

- [ ] **Step 1: 运行两组回归测试**

预期：

```text
E8–E10：Ran 14 tests，OK
E11–E12：Ran 14 tests，OK
```

必须保存完整 OUT 和退出码。

- [ ] **Step 2: 生成交接清单**

`handoff.json` 至少包含：

```json
{
  "student_id": "241880481",
  "repository": "https://github.com/llxxy-cn/devops-b09",
  "project_subdir": "fixtures/draft",
  "base_commit": "<C0完整SHA>",
  "target_commit": "<C1完整SHA>",
  "build_command": "make clean && make",
  "test_command": "make test",
  "run_command": "./app",
  "expected_output": "hello E3",
  "expected_missing": {
    "target": "main.o",
    "dependency": "extra.h"
  },
  "candidate_image": "b1-real-cmake:241880481",
  "candidate_image_id": "<实际镜像ID>"
}
```

尖括号字段必须替换为本次实际值。

- [ ] **Step 3: 生成哈希清单**

对候选 Dockerfile、日志、镜像检查结果、回归测试结果和交接清单执行 SHA256，保存到证据目录。

- [ ] **Step 4: 提交交接文档**

只提交报告、候选 Dockerfile和交接清单，不提交 `work/` 中的构建缓存或临时产物。

提交信息：

```text
docs: add B1 real project handoff
```

- [ ] **Step 5: 最终检查**

运行：

```bash
git diff --check
git status --short --branch
git log --oneline --decorate -10
```

确认：

- C0、C1 是两个独立连续提交。
- 工作区没有意外文件。
- 没有合并到 `main`。
- 没有虚构推送、PR 或 A/B 联调结果。
