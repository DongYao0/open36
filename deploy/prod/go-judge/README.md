# go-judge 沙箱镜像

## 背景

HOJ 判题依赖 `go-judge` 沙箱执行用户提交的代码。历史方案使用本地手工构建的
未固定版本的本地 `go-judge-with-compilers` 镜像，该镜像未发布到任何 registry，无法在干净的
Linux 生产机上复现。

本目录提供**可复现**构建方式：

- `FROM criyle/go-judge:v1.12.0`（官方发布、固定 tag，Docker Hub 可拉取）
- 其上安装 HOJ `language.yml` 所需的语言运行时。

已核实：历史 `go-judge-with-compilers` 的 go-judge 层 digest 与
`criyle/go-judge:v1.12.0` 完全一致（`sha256:3af6806b4f58deeecb0cc64a8cde04138106372abfe8e6dd7acb525c3aee2e14`），
说明历史镜像即「该官方镜像 + 编译器层」。

## 在目标 Linux 上构建 / 导入

### 方式 A：联网构建（推荐）

```bash
docker build -t open436/go-judge:v1.12.0 ./deploy/prod/go-judge
```

### 方式 B：离线导入（目标机无 Docker Hub 访问）

在能联网的机器上：

```bash
docker build -t open436/go-judge:v1.12.0 ./deploy/prod/go-judge
docker save open436/go-judge:v1.12.0 -o open436-go-judge-v1.12.0.tar
```

将 tar 拷贝到目标 Linux 后：

```bash
docker load -i open436-go-judge-v1.12.0.tar
```

生产 Compose 中 `go-judge` 服务的 `image` 已设为 `open436/go-judge:v1.12.0`，
与上述 tag 一致。

## 语言运行时覆盖

| language.yml 引用 | 运行时 | 本镜像 |
|---|---|---|
| `/usr/bin/gcc` / `g++` | C / C++ | ✅ gcc/g++ |
| `/usr/bin/python3` | Python3 | ✅ python3（Debian trixie 提供） |
| `/usr/bin/php` | PHP | ✅ php-cli |
| `/usr/bin/ruby` | Ruby | ✅ ruby |
| `/usr/bin/node` | JavaScript Node | ✅ nodejs |
| `/usr/bin/java` | Java | ✅ openjdk-21 |
| `/usr/bin/go` | Golang | ✅ golang-go |
| `/usr/bin/rustc` | Rust | ❌ 未装（历史语言，按需补充） |
| `/usr/bin/mono` / `mcs` | C# | ❌ 未装（历史语言，按需补充） |

> 注：`python3.7` 与 `pypy`（PyPy2）为历史解释器版本，Debian trixie 已不提供；
> 生产请使用 Python3。如需 PyPy2/PyPy3/Rust/C#，请在 Dockerfile 中补充对应安装步骤。
