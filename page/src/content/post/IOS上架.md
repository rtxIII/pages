+++
date = "2023-12-13"
title = "IOS上架"
description = ""
tags = [""]
term = [""]
categories = [""]
+++

# Ionic ios app打包

0. 安装capacitor， 注意起始页面必须在/

```
 4747  pnpm i @capacitor/core
 4748  pnpm i -D @capacitor/cli
 4749  pnpm i  @capacitor/ios
```

* pnpm 和vite如有冲突，通过npm安装依赖

1. 保证capacitor版本一致：

   ```
       "@capacitor/android": "^5.5.1",
       "@capacitor/app": "^5.0.6",
       "@capacitor/haptics": "^5.0.6",
       "@capacitor/ios": "^5.5.1",
       "@capacitor/keyboard": "^5.0.6",
       "@capacitor/status-bar": "^5.0.6"
   ```

2. 使用npx cap add ios增加ios打包

3. 确保配置目录正确：

   ```
   const config: CapacitorConfig = {
     appId: 'com.example.app',
     appName: 'Example-App',
     webDir: './.output/public',
     bundledWebRuntime: false
   };
   ```

3. App connect 中建立app

5.  [图标工场 - 移动应用图标/启动图生成工具，一键生成所有尺寸的应用图标/启动图 (wuruihong.com)](https://icon.wuruihong.com/icon?utm_source=mfywriRO#/ios) 生成appicon

5. [App Tools - Generate icons, images and splashscreens for android and iOS apps (appicononline.com)](http://appicononline.com/) 启动图

10. 注意事项：
 ```
最近大半年上架了 5 个 App ，也踩了不少坑，今天说一下上架的相关问题。

直接不废话，开始内容：

注意点

EULA （最终用户许可协议）。EULA 需要出现在三处地方，有一处是 App Information 页面填写的区域，另外两处分别是 1️⃣ 产品描述的文字部分，2️⃣ App 运行页面中的某处（可以放在设置/关于之类的用户看得到的地方），这是新手上架最容易出问题的地方。

内购。内购分为两种，一种是订阅，一种是非订阅（非订阅包含可消费的（比如游戏道具），和不可被消耗的（比如永久会员））。这些内购必须让用户和 Review 人员知道买了之后是做什么的，如果说明文字隔几秒切换一次说明的那种，一定要让 Review 人员知道这个地方会自己变的，订阅类型必须提供一个可以信服的“持续性的价值”。内购提交有自己的 Notes 和 附件，这个地方可以用截图拼贴说明 Free 用户和付费用户的区别。

注意每次 Review 提交的 Notes 部分，这部分留空也是可以提交 Review 的，但是 Notes 以及附件部分，是 Review 人员不需要和你再次沟通就能获取到信息的地方，这里你可以放入大概的功能说明、技术实现，总之要体现自己人畜无害但是 App 又有独特能力的地方。Review 人员如果有疑问在这里就能解决掉，就不会再次要求你提供信息。

Review 人员经常使用 iPad ，所以 iPad 上运行的时候不要一副低质量的状态。

避免一些歧义词，比如我就提交过“锁屏页面也能使用”之类的文字，想表达锁屏页面的实时活动可以用，结果 Review 人员问锁屏小组件里没有你的东西。

如果只有一个页面且只能展示信息，就会特别难上架，Apple 会觉得你这个服务做成 App 没意义，这种情况建议重新设计功能，添加各种自定义的设置，添加用户的收藏夹之类的有用的功能。

每次提交 Review 都是有可能变更 Review 人员的，所以如果被拒绝了，一定要在回复被拒信息的对话页面重新说明清楚。

善用 ChatGPT 或者类似服务翻译和整理自己想说的内容，说来说去就是为了减少歧义
 ```

8. [Marketing Tools and Resources - Apple Services (applemediaservices.com)](https://tools.applemediaservices.com/)  可以用来生成市场宣传图。
9. 