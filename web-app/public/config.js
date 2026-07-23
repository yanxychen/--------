// 运行时配置
// Vercel版：此处设置 backendUrl 后前端直接调Render后端（绕过Vercel Serverless超时限制）
window.__APP_CONFIG = {
  backendUrl: 'https://npl-backed.onrender.com/api/search'
};
