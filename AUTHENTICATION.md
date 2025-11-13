# TrendRadar MCP Server 密码认证指南

## 📋 概述

TrendRadar MCP Server 现已支持HTTP模式下的密码认证功能，确保您的服务器在网络中的安全访问。

## 🔐 认证机制

### 工作原理

1. **环境变量配置**：从 `MCP_SERVER_PASSWORD` 环境变量读取密码
2. **请求验证**：每个HTTP请求都会在认证中间件中被验证
3. **双通道支持**：支持URL查询参数和HTTP请求头两种密码传递方式
4. **失败处理**：密码错误或缺失时返回 403 Forbidden 错误

### 认证流程

```
客户端请求
    ↓
FastMCP 认证中间件
    ↓
检查 MCP_SERVER_PASSWORD 是否设置
    ↓
    ├─ 未设置 → 允许访问（无认证）
    └─ 已设置 → 验证密码
        ↓
        ├─ 正确 → 继续处理请求
        └─ 错误/缺失 → 返回 403 Forbidden
```

## 🚀 启动方式

### Windows (start-http.bat)

```batch
# 脚本会自动设置 MCP_SERVER_PASSWORD 环境变量
.\start-http.bat
```

**脚本输出示例：**
```
╔════════════════════════════════════════════════════════════════╗
║  TrendRadar MCP Server - HTTP Mode with Authentication       ║
╚════════════════════════════════════════════════════════════════╝

✅ [认证] 密码保护已启用

📋 启动参数:
   - 模式: HTTP (适合远程访问和集成)
   - 地址: http://localhost:3333
   - 端口: 3333

🔐 访问方式:
   1. URL参数方式:
      http://localhost:3333/mcp?pwd=TrendRadar@2025SecurePass

   2. 请求头方式 (推荐):
      curl -H "X-MCP-Password: TrendRadar@2025SecurePass" http://localhost:3333/mcp
```

### macOS/Linux (start-http.sh)

```bash
# 脚本会自动设置 MCP_SERVER_PASSWORD 环境变量
./start-http.sh
```

### 手动启动

```bash
# 设置密码环境变量
export MCP_SERVER_PASSWORD="your_secure_password"

# 启动服务器
uv run python -m mcp_server.server --transport http --port 3333
```

## 📝 配置密码

### 修改默认密码

编辑启动脚本中的密码字符串：

**Windows (start-http.bat):**
```batch
set "MCP_SERVER_PASSWORD=your_new_secure_password"
```

**macOS/Linux (start-http.sh):**
```bash
export MCP_SERVER_PASSWORD="your_new_secure_password"
```

### 密码建议

✅ **强密码特征：**
- 长度至少12个字符
- 包含大小写字母 (A-Z, a-z)
- 包含数字 (0-9)
- 包含特殊符号 (!@#$%^&*)

❌ **避免：**
- 过短的密码 (<8字符)
- 仅使用数字或字母
- 容易猜测的单词
- 项目名称或日期

### 密码示例

```
✅ 好的密码：
   - TrendRadar@2025SecurePass
   - MCP$Server#Pwd123
   - TR_Secure!Pass2025

❌ 不好的密码：
   - 123456
   - password
   - trendradar
   - 2025
```

## 🔗 访问服务器

### 方式 1: URL查询参数（简单）

```bash
# 基础请求
curl "http://localhost:3333/mcp?pwd=TrendRadar@2025SecurePass"

# 使用JSON数据
curl -X POST "http://localhost:3333/mcp?pwd=TrendRadar@2025SecurePass" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

**优点：** 简单易用
**缺点：** 密码在URL中可见，不够安全

### 方式 2: 请求头（推荐）

```bash
# 基础请求
curl -H "X-MCP-Password: TrendRadar@2025SecurePass" http://localhost:3333/mcp

# 使用JSON数据
curl -X POST http://localhost:3333/mcp \
  -H "X-MCP-Password: TrendRadar@2025SecurePass" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'

# 完整示例：调用get_latest_news工具
curl -X POST http://localhost:3333/mcp \
  -H "X-MCP-Password: TrendRadar@2025SecurePass" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_latest_news",
      "arguments": {
        "limit": 10
      }
    },
    "id": 1
  }'
```

**优点：** 密码不在URL中，更安全
**缺点：** 需要支持自定义请求头

### 方式 3: Python 客户端

```python
import requests
import json

# 配置
SERVER_URL = "http://localhost:3333/mcp"
PASSWORD = "TrendRadar@2025SecurePass"

# 方式A：URL参数
response = requests.post(
    f"{SERVER_URL}?pwd={PASSWORD}",
    json={
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }
)

# 方式B：请求头（推荐）
response = requests.post(
    SERVER_URL,
    headers={"X-MCP-Password": PASSWORD},
    json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_latest_news",
            "arguments": {"limit": 10}
        },
        "id": 1
    }
)

print(response.json())
```

## 🧪 测试认证功能

### 测试 1: 密码正确

```bash
# 应该返回200状态和正常响应
curl -i -H "X-MCP-Password: TrendRadar@2025SecurePass" http://localhost:3333/mcp
```

**预期响应：**
```
HTTP/1.1 200 OK
...
{"success": true, ...}
```

### 测试 2: 密码错误

```bash
# 应该返回403状态
curl -i -H "X-MCP-Password: wrong_password" http://localhost:3333/mcp
```

**预期响应：**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json

{"error": "Forbidden", "message": "Invalid or missing password. ..."}
```

### 测试 3: 密码缺失

```bash
# 应该返回403状态
curl -i http://localhost:3333/mcp
```

**预期响应：**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json

{"error": "Forbidden", "message": "Invalid or missing password. ..."}
```

### 测试 4: 无认证模式

```bash
# 当MCP_SERVER_PASSWORD未设置时，请求应该成功
# 不设置环境变量，直接启动服务器
uv run python -m mcp_server.server --transport http --port 3333

# 任何请求都应该返回200（无需密码）
curl http://localhost:3333/mcp
```

## 🔒 安全最佳实践

### 1. 生产环境配置

```bash
# ✅ 使用安全的密码生成工具
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ✅ 使用环境文件（不要提交到版本控制）
# .env.local
MCP_SERVER_PASSWORD=your_very_secure_password_here
```

### 2. 部署建议

- **使用HTTPS**：在生产环境中必须启用HTTPS加密传输
  ```bash
  # 使用反向代理（如nginx）配置HTTPS
  # 参考 Docker 配置或 nginx 配置文件
  ```

- **定期更换密码**：建议每3个月更换一次
- **强密码策略**：使用密码管理工具生成强密码
- **日志审计**：监控认证失败的请求日志

### 3. Docker 部署

```dockerfile
# 设置环境变量在 docker-compose.yml 中
# docker-compose.yml
services:
  trendradar:
    environment:
      MCP_SERVER_PASSWORD: ${MCP_SERVER_PASSWORD}
    ports:
      - "3333:3333"
```

```bash
# 启动时传入密码
MCP_SERVER_PASSWORD="your_password" docker-compose up
```

### 4. GitHub Actions 部署

```yaml
# 使用 GitHub Secrets 存储密码
- name: Run TrendRadar Server
  env:
    MCP_SERVER_PASSWORD: ${{ secrets.MCP_SERVER_PASSWORD }}
  run: ./start-http.sh
```

## 🐛 故障排查

### 问题 1: 无法连接服务器

```bash
# 检查服务器是否运行
netstat -an | grep 3333

# 检查防火墙
# Windows: 检查 Windows Defender 防火墙
# macOS/Linux: sudo ufw status
```

### 问题 2: 密码认证失败

```bash
# 确认密码正确性
echo $MCP_SERVER_PASSWORD  # 查看当前设置的密码

# 检查密码是否包含特殊字符需要转义
# URL中特殊字符需要URL编码
# 例如：@ 编码为 %40
curl "http://localhost:3333/mcp?pwd=TrendRadar%402025SecurePass"
```

### 问题 3: 环境变量未生效

```bash
# 重新启动脚本确保环境变量生效
# Windows: 关闭并重新打开CMD/PowerShell窗口
# macOS/Linux: 运行 source start-http.sh 或 export MCP_SERVER_PASSWORD=...
```

## 📚 相关文档

- [README-MCP-FAQ.md](README-MCP-FAQ.md) - MCP常见问题
- [README-Cherry-Studio.md](README-Cherry-Studio.md) - Cherry Studio 集成指南
- [readme.md](readme.md) - 项目主文档

## ❓ 常见问题

**Q: 如何禁用认证？**
A: 不设置 `MCP_SERVER_PASSWORD` 环境变量即可。启动时脚本会提示认证已关闭。

**Q: 可以同时支持多个密码吗？**
A: 当前版本仅支持单一密码。如需多用户支持，可考虑使用API密钥或OAuth。

**Q: 密码会被记录在日志中吗？**
A: 否。密码仅在中间件中验证，不会被记录。错误消息也不会透露密码信息。

**Q: 可以使用环境变量以外的方式配置密码吗？**
A: 可以。您可以修改 `server.py` 中的 `SERVER_PASSWORD` 变量读取逻辑，从配置文件、数据库等其他来源读取。

## 📞 反馈与支持

如有问题或建议，欢迎提交 Issue 或 Pull Request。
