+++
date = "2024-01-30"
title = "Devops-持续交付CD"
description = ""
tags = ["devops"]
term = ["CI","CD"]
categories = ["devops"]
+++

# 持续交付

![image](https://ocf.rtx3.com/api/raw?path=/3/assets/devops/cd.png)


## 渐进式交付

渐进式交付是高级部署模式（如金丝雀，功能标记和 A/B 测试）的总称。通过给予应用程序开发人员和 SRE 团队对爆炸半径的细粒度控制，渐进交付技术被用来降低在生产中引入新软件版本的风险。

> 使用金丝雀的好处是能够在生产环境中使用发现问题的安全回滚策略对新版本进行容量测试。通过缓慢增加负载，您可以监视和捕获有关新版本如何影响生产环境的指标


# GitOps 下的 CI/CD 流程

CI/CD 是架构中非常重要的一个组件，在云原生时代，依托于容器化持续集成，改变了以往应用通过 Jar、war 包形式的部署方式，转而制作成镜像，通过集成 GitLab CI、镜像仓库、Kubernetes 、Argo CD 等各类效率、流程系统，对纳管集群进行镜像发布、应用验证、升级，进而实现了自动化和监控贯穿于应用迭代的整个生命周期。

## 什么是 CI/CD

CI（Continuous Intergration，持续集成），强调开发人员不断进行代码提交、单元测试、性能测试、代码扫描等操作，根据测试结果，发现问题及时回滚，并进行反馈。

持续部署 （Continuous Deployment，CD）或者说持续交付（Continuous Delivery，CD），是指在构建和测试完成通过后，通过一系列系统化手段让最新的功能能够尽快地更新到生产环境，并通过运营反馈需求，促进产品进一步迭代。持续部署需要保障整个过程的平滑和安全，通常借助蓝绿发布、金丝雀发布确保过程中的平滑、安全以及降低部署过程出错的概率。

总结来说，持续集成、持续部署与持续交付，是一种通过在应用开发阶段引入自动化，实现频繁交付应用的方法。


## GitOps 下的 CI/CD 流程

鉴于 GitOps 的设计哲学，我们看一下 GitOps 下的 CI/CD 流程，如下图所示：


![image](https://ocf.rtx3.com/api/raw?path=/3/assets/devops/gitops-workflow.webp

- 首先，团队成员都可以 fork 仓库对配置进行更改，然后提交 Pull Request。
- 接下来运行 CI 流水线，进行校验配置文件、执行自动化测试、构建 OCI 镜像、推送到镜像仓库等。
- CI 流水线执行完成后，拥有合并代码权限的人会将 Pull Request 合并到主分支。
- 最后运行 CD 流水线，结合 CD 工具（例如 Argo CD）将变更自动应用到目标集群中。

整个过程中完全自动化且操作透明，通过多人协作和自动化测试来保证了基础设施声明的健壮性。另外由于基础设置配置都存储在 Git 仓库中，当应用出现故障时，也可快速地进行版本回退。


## CI/CD 中的工具链

在 CI/CD 工程实施中，Jenkins 和 Gitlab 已成为流程中的核心工具，其中 Jenkins 。现如今的 CI/CD 中，集合容器技术、镜像仓库、容器编排系统等各类工具链，已成为企业、各类组织效率提升必不可少的基础支撑。


<div  align="center">
	<img src="../assets/cicd-tools.png" width = "600"  align=center />
	<p>图：CI/CD 典型工具链</p>
</div>

目前，CI/CD 典型的工具链包括持续集成、持续交付、持续部署与基础工具类。

### 基础工具

Jenkins 是一个被广泛使用的可扩展的持续集引擎，提供了数以百计的插件来支持自动化构建、测试、部署相关的各类任务，Jenkins 在 2.0 版本中提供的流水线即代码(Pipeline as Code) 能力。贯穿于 CI/CD  整个过程，将原本独立运行与单个或多个节点的任务串联起来，从而实现单个任务难以完成的复杂发布流程。

Prometheus 是新一代的云原生监控系统，它是一个开源的完整监控解决方案，对传统的监控系统测试、告警模型进行了彻底颠覆的重新设计，形成了基于中央化的规则计算、统一分析和告警的新一模型。

为了实现统一的用户管理和权限管理，我们需要引入一套统一的用户管理系统，OpenLDAP 则是目前较为广泛应用的系统。

### 持续集成

典型的源码管理工具是 Gitlab，同时也可以完成代码评审等工作。

代码构建根据编程语言不同而不同，譬如 Java 构建工具包括 Maven、Gradle。单元测试框架 如 JUnit、TestNG 等。

制品仓库代表性产品为 Nexus，Nexus 可以支持多种私有仓库，包括 maven、nuget、docker、npm、bower、pypi、rubygems、go 等。

镜像仓库目前使用最广泛的 是 VMware 开源的 Harbor。Harbor 是一个用于存储和镜像分发的企业级镜像服务端软件，它添加了很多企业必须的功能特性，例如安全、标识和管理等。

代码质量管理使用最广泛的开源工具是 SonarQube， 它可以用代码风格、缺陷、漏洞、以及安全热点等几个维度对源代码进行扫码和分析。


### 持续交付

接口测试可以使用 Python 编写的功能自动化测试框架 RobotFramework，它具备良好的可扩展性，支持关键字驱动，可以同时测试多种类型的客户端和接口，也可以进行分布式测试。

性能测试类工具可以使用 Java 开发的 JMeter，它可以对服务器、网络、或者对象模拟请求负载来测试他们的强度或者分析不同压力下整体性能。

### 持续部署

使用 Kebernetes 的配置功能（configmap、Secret）做配置管理。

可以使用 Helm 打包应用，管理应用的依赖关系，管理应用版本并发布应用到软件仓库。

Operator 是基于 Kebernetes 编写的也定应用程序控制器，它用来创建、配置和管理复杂的有状态应用，如数据库、缓存和监控系统。Operator 是将运维人员对软件操作代码化，同时利用 Kebernetes 强大的抽象来实现应用的生命周期管理。