#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  TrendRadar MCP Server - HTTP Mode with Authentication       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ [错误] 虚拟环境未找到"
    echo "请先运行 ./setup-mac.sh 进行部署"
    echo ""
    exit 1
fi

# ==================== 密码配置 ====================
# 在这里设置您的服务器密码
# 建议使用强密码：至少12个字符，包含大小写字母、数字和特殊符号
# 示例密码需要修改为实际的安全密码
export MCP_SERVER_PASSWORD="TrendRadar@2025SecurePass"

# 验证密码是否为空
if [ -z "$MCP_SERVER_PASSWORD" ]; then
    echo "⚠️  [警告] 未设置MCP_SERVER_PASSWORD，服务器将以无认证模式运行"
    echo ""
else
    echo "✅ [认证] 密码保护已启用"
fi

echo ""
echo "📋 启动参数:"
echo "   - 模式: HTTP (适合远程访问和集成)"
echo "   - 地址: http://localhost:3333"
echo "   - 端口: 3333"
echo ""
echo "🔐 访问方式:"
echo "   1. URL参数方式:"
echo "      http://localhost:3333/mcp?pwd=$MCP_SERVER_PASSWORD"
echo ""
echo "   2. 请求头方式 (推荐):"
echo "      curl -H \"X-MCP-Password: $MCP_SERVER_PASSWORD\" http://localhost:3333/mcp"
echo ""
echo "💡 提示:"
echo "   - 按 Ctrl+C 停止服务"
echo "   - 请妥善保管密码，不要在公开场所暴露"
echo "   - 建议在生产环境中使用HTTPS"
echo ""

uv run python -m mcp_server.server --transport http --host 0.0.0.0 --port 3333
