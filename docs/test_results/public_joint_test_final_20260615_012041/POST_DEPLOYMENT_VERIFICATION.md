# EduChain 部署后验证记录

## 结论

- 公网九账号主测试：47/47 通过，100%。
- 后端本地回归：32 项通过。
- 整套 Compose 重启后链数据、用户数据、上传文件和元数据均持久保留。
- 钱包交易流水、管理员删除、删除事件审计和资料元数据更新均已恢复。

## 当前服务器状态

- 服务地址：`http://1.95.47.47/`
- 链 ID：1337
- 当前区块高度：44
- 资料数：7
- 下载审计数：7
- 登录账号：8 个学生账号、1 个管理员账号
- 公网开放：80
- 公网未开放：5000、8545

主测试结束时区块高度为 41、下载审计为 6。整套服务重启后该状态完整保留；随后执行了一次资料 A 的下载连续性验证，新增 3 个区块和 1 条审计记录。

## 回退依据

服务器修复前备份位于：

- `/root/educhain_before_fix_20260615_003854_code.tar.gz`
- `/root/educhain_before_fix_20260615_003854_educhain_ganache_data.tar.gz`
- `/root/educhain_before_fix_20260615_003854_educhain_runtime_data.tar.gz`
- `/root/educhain_before_fix_20260615_003854_educhain_upload_data.tar.gz`

这些归档分别覆盖代码、Ganache 链数据、运行时账号与元数据、上传文件，可用于独立回退。

## 证据目录

- `TEST_REPORT.md`：完整用例报告
- `test_cases.csv`：结构化测试用例结果
- `joint_test_results.json`：原始响应、交易哈希和余额快照
- `screenshots/`：12 张浏览器证据截图
- `downloads/`：6 份下载文件样本
