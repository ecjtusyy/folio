# Folio: Personal Academic & Project Showcase

这是一个基于 **Next.js + Tailwind CSS** 构建的静态个人站点，专为 **计算机科学与计算力学** 背景设计的学术/技术展示平台。

## 🚀 核心工作流 (Fast Track)

如果你已经在 **GitHub Codespaces** 中打开了本项目，只需执行以下命令：

```bash
# 1. 环境初始化 (首次运行)
npm install

# 2. 启动本地开发服务器
npm run dev

# 3. 生产环境预检查 (提交代码前必做)
npm run typecheck && npm run build

# 4. 部署至生产环境
git add .
git commit -m "feat: update content"
git push origin main
```

---

## 📂 目录结构与配置说明

| 路径 | 功能描述 | 备注 |
| :--- | :--- | :--- |
| `content/posts/` | **文章存储库** | 存放所有 `.md` 格式的技术博客或随笔 |
| `app/papers/` | **论文展示页** | 用于罗列 MPM/FEM 相关 Research Papers |
| `app/projects/` | **项目档案** | 展示 A-share 量化、数值模拟等工程项目 |
| `public/` | **静态资源** | 存放 PDF 论文、图片、简历等文件 |
| `next.config.js` | **站点路由配置** | 已锁定 `basePath: '/folio'`，确保 GitHub Pages 路径正确 |

---

## ✍️ 内容发布指南 (Posts Management)

文章必须遵循标准的 **Front Matter** 格式。在 `content/posts/` 下新建 `.md` 文件：

```markdown
---
title: "基于 MPM-FEM 耦合的数值稳定性分析"
date: "2026-04-15"
slug: "mpm-fem-stability"
summary: "探讨 Explicit Discrete-Continuum 模拟中的脉冲修正映射与能量守恒问题。"
tags: ["Computational Mechanics", "MPM", "Research"]
---

# 核心推导

$$
\mathbf{f}_{int} = -\int_{\Omega} \sigma : \delta \epsilon d\Omega
$$

正文内容...
```

> **Warning**: `slug` 字段必须全局唯一，它决定了文章的访问 URL。

---

## ⚙️ 部署逻辑 (CI/CD)

本项目采用 **GitHub Actions** 进行自动化部署。

1.  **Repository Settings**: 确保仓库名为 `folio`。
2.  **Pages Setup**: 
    * 进入 `Settings -> Pages`。
    * `Build and deployment -> Source` 必须选择 **GitHub Actions**。
3.  **URL Structure**: 部署成功后，访问地址为 `https://ecjtusyy.github.io/folio/`。

---

## 🛠 技术维护 (Maintenance)

* **样式修改**: 采用 Tailwind CSS，全局配置位于 `tailwind.config.ts`。
* **数学公式**: 支持 LaTeX 渲染（通过 `remark-math` / `rehype-katex`）。
* **静态检查**: 在 Push 前务必运行 `npm run typecheck`，确保 TypeScript 类型定义无误，避免 Actions 构建失败。

---

## 📋 TODO
- [ ] 完善 `app/cv/page.tsx` 中的个人履历。
- [ ] 上传最新的数值模拟实验 PDF 到 `public/papers/`。
- [ ] 优化移动端对复杂矩阵公式的显示效果。

---

**Sun Yiyang** *Undergraduate in  Applied Mathematics* *Specializing in Numerical Simulation & Computational Mechanics*

