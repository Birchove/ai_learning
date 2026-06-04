本次作业完成: 
借鉴 https://github.com/redis/redis-vl-python 的实现, 
实现:
+  EmbeddingsCache.py
+ SemanticCache.py
+ SemanticMessageHistory.py
+ SemanticRouter.py

下面先给出一些此前不曾了解的知识的补充

### Redis 介绍
> 以下内容部分摘自菜鸟教程[redis介绍](https://www.runoob.com/redis/redis-intro.html)

Redis（Remote Dictionary Server）是一个开源的内存数据库，遵守 BSD 协议，它提供了一个高性能的键值（key-value）存储系统，常用于缓存、消息队列、会话存储等应用场景。

Redis具有以下特点
- 性能极高：Redis 以其极高的性能而著称，能够支持每秒数十万次的读写操作。这使得Redis成为处理高并发请求的理想选择，尤其是在需要快速响应的场景中，如缓存、会话管理、排行榜等。

- 丰富的数据类型：Redis 不仅支持基本的键值存储，还提供了丰富的数据类型，包括字符串、列表、集合、哈希表、有序集合等。这些数据类型为开发者提供了灵活的数据操作能力，使得Redis可以适应各种不同的应用场景。

- 原子性操作：Redis 的所有操作都是原子性的，这意味着操作要么完全执行，要么完全不执行。这种特性对于确保数据的一致性和完整性至关重要，尤其是在高并发环境下处理事务时。

### Redis 与 MySQL 的应用场景区别

数据库理论中, 我们称 MySQL 具有 ACID 特性，而以 Redis 为代表的 NoSQL 数据库，对应的特性概括词叫做 BASE。
> 这个名字其实起得非常有灵性, 在化学中, acid 是酸, 而 base 是碱

Redis 是存在内存中的, 所以速度更快, 但可存的体积更小; MySQL是存在磁盘中的, 所以速度会变慢, 但可以存储海量数据, 其余更多的比较见下

#### Redis

Redis 是一个基于内存的键值（Key-Value）数据库。因为数据都在内存中，所以读写速度极快（单机可达 10W+ QPS），但内存容量有限且成本较高。

##### BASE特性
1. BA - Basically Available（基本可用）
含义： 允许损失部分可用性，但系统绝不能死掉。

遇到大流量或网络故障时，响应可能会变慢（比如平时 2 毫秒，现在变 50 毫秒），或者部分非核心功能暂时不可用，但系统整体依然能给你返回结果，不直接报错。

2. S - Soft State（软状态 / 柔性状态）
含义： 允许数据存在中间状态。

数据的状态不需要像 MySQL 那样时刻保持“绝对正确”。数据的更新允许在不同的服务器节点之间同步时存在一定的时间差（比如主节点数据变了，从节点还没来得及变）。

3. E - Eventual Consistency（最终一致性）
含义： 不追求“实时一致”，只追求“最终一致”。

这是 BASE 的核心。Redis 允许你在修改数据的瞬间，别人读到的是旧数据。但是，经过一段很短的时间（比如几毫秒或几十毫秒）后，数据一定会同步完成，所有人看到的就又是最新且一致的数据了。

##### Redis 应用场景

一句话总结: Redis 适用于高频, 多并发, 小体积的数据查询/处理, 允许少量数据丢失, 追求极致性能, 拥有富的数据结构(如 List, Set, ZSet 排序集), 主要有以下几个应用场景:

1. 高频热点数据缓存 (Caching)：

场景： 电商的商品详情、新闻热点文章、用户信息。

原因： 这些数据经常被成千上万的用户同时访问，但更新频率相对较低。把它们从 MySQL 查出来放到 Redis 里，用户直接读内存，能极大地减轻 MySQL 的压力。

2. 高频更新的计数器与排行榜 (Counter & Leaderboards)：

场景： 微博帖子的点赞数、浏览量；游戏内的实时战力排行榜。

原因： Redis 内部有极其高效的自增命令（INCR）和有序集合（ZSet）。如果用 MySQL 做排行榜，每次点赞都要写一次磁盘，数据库会直接卡死；而 Redis 可以轻松应对每秒几万次的点赞更新并实时排序。

3. 分布式 Session / 登录状态存储：

场景： 用户在 App 或网站登录后的 Token / Session 状态。

原因： 分布式架构下，用户的请求可能会被分发到不同的服务器。把登录状态存在中心化的 Redis 中，所有服务器都能秒级读取。而且 Redis 支持过期时间（TTL），可以让登录状态在 30 分钟不操作后自动失效。

4. 分布式锁 (Distributed Lock)：

场景： 秒杀系统防止超卖、优惠券防止恶意超领。

原因： 当多个并发请求同时要抢购一件商品时，利用 Redis 的原子性操作（如 SETNX）可以实现一把高并发的“全局锁”，确保商品不会被多卖。

5. 轻量级消息队列与发布订阅 (Pub/Sub)：

场景： 异步发送短信验证码、实时聊天室消息分发。

原因： Redis 的 List 结构（配合 BLPOP）或 Stream 结构可以作为轻量级的消息队列，处理不需要绝对可靠、但要求速度极快的异步任务。


#### MySQL

##### ACID特性

1. A - Atomicity（原子性）
字面意思： 原子在传统物理学中是“不可分割的最小单位”。

通俗解释： “要么全做，要么全不做”。

转账例子： 转账包含两个动作：①张三账户减 100 元；②李四账户加 100 元。原子性保证了这两个动作必须绑定在一起。如果张三的钱刚扣完，银行服务器突然断电了，MySQL 会在重启后进行回滚（Rollback），把张三的 100 元退回来。绝不会出现“张三钱扣了，李四没收到”的尴尬情况。

2. C - Consistency（一致性）
字面意思： 数据库在事务前后都必须处于合法的完整性状态。

转账例子： 在转账前，张三和李四的账户总金额是 2000 元。无论中间怎么转、怎么失败、怎么重试，转账结束后，两人的总金额必须还是 2000 元，钱不会凭空变多，也不会凭空消失。另外，如果张三银行卡里只有 50 元，他想转 100 元，一致性检查会直接拒绝这次转账，因为这违反了“余额不能为负数”的业务规则。

3. I - Isolation（隔离性）
字面意思： 多个并发事务之间互相隔离，互不干扰。

转账例子： 假设张三卡里有 1000 元。现在发生两个并发事件：

事务 A：张三给李四转账 100 元。

事务 B：张三的老婆同时从这张卡里取走 500 元。

隔离性保证了这两个事务就像在两个平行宇宙里运行一样。事务 A 无法看到事务 B 刚取了一半的中间状态，它们会排好队，最终卡里正确地剩下 400 元。如果没有隔离性，两个事务同时改一个数字，可能最后余额会变成 900 元或 500 元（算错账）。

4. D - Durability（持久性）
字面意思： 一旦事务提交，它对数据库的改变就是永久性的。

转账例子： 当银行系统提示你“转账成功”的那一秒，这就意味着事务已经成功提交（Commit）。即使银行数据中心故障，只要服务器重新开机，MySQL 就能通过磁盘上的重做日志（Redo Log）把数据恢复回来。张三的钱确实少了，李四的钱确实多了，谁也赖不掉。

##### MySQL应用场景

一句话总结 MySQL 应用场景, 存储海量、长期保存的结构化数据, 追求数据的绝对安全和准确, 支持多表联查

1. 核心业务资产与核心账目数据：

场景： 用户的银行账户余额、电商系统的订单信息、支付流水、用户注册的账号密码。

原因： 这些数据绝对不能丢，也绝对不能错。MySQL 的事务机制能保证“要么全部成功，要么全部失败”。比如转账，A 扣钱和 B 加钱必须同时成功，MySQL 能百分之百保证这种数据的准确性（数据持久化、不丢失）。

2. 具有复杂关系网的数据：

场景： ERP 系统、CRM 客户管理系统、教务管理系统（学生-班级-课程-成绩的多表关联）。

原因： 关系型数据库擅长处理结构化数据。当你需要写复杂的 JOIN 语句，去查询“年龄大于20岁、选修了计算机课程、且期末考试大于80分的男学生信息”时，MySQL 的 SQL 引擎和索引优化是最专业的。

3. 需要严格数据规范（Schema）的场景：

场景： 任何需要严格限制字段类型、长度、非空约束的业务表。

原因： MySQL 会在写入时强制进行格式校验，防止脏数据进入系统。


#### WHY redis-vl-python

Redis 一般使用Java来管理, 针对于Python, 官方开发了redis-py 库, 那为什么redis官方还额外开发了redis-vl-py?

正如官方README给出的, 
```text
Redis Vector Library (RedisVL) is the production-ready(用于生产的) Python client for AI applications built on Redis. 
Lightning-fast vector search meets enterprise-grade reliability.

Perfect for building RAG pipelines with real-time retrieval, AI agents with memory and semantic routing, 
and recommendation systems with fast search and reranking.
```

redis-vl-python 是专门为`AI开发`而推出的新的库, 由于大模型的"语义" 实际上就是向量, 所以为redis做了向量数据库适配, 这样可以在AI开发过程中享受redis的各种功能

其有以下几个优点:

1. 语义化、声明式的索引管理 (Schema Management)

在 AI 应用中，不仅要存向量，还要存元数据（如文章标题、作者、发布时间、分类标签）。
redis-vl-python 允许用户直接用一个简单的 Python 字典（Dict）或者 YAML 文件来定义数据结构：
```yaml
# 用 YAML 直接定义索引结构，包含文本、标签和向量
index:
  name: products
  prefix: prod
fields:
  - name: category
    type: tag
  - name: description_embedding
    type: vector
    attrs:
      dims: 1536
      distance_metric: cosine
      algorithm: hnsw
```

2. 极简的“向量 + 元数据”混合检索 (Hybrid Search)

在做大模型知识检索（RAG）时，我们经常需要进行混合检索, 而redis-vl-py提供了一个极简的书写方式

```python
from redisvl.query import VectorQuery
from redisvl.query.filter import Tag

# 1. 定义过滤条件
filter_expr = Tag("category") == "electronics"

# 2. 构建向量查询
query = VectorQuery(
    vector=[0.12, -0.34, ...], # 你的查询向量
    vector_field_name="description_embedding",
    num_results=3,
    filter_expression=filter_expr
)

# 3. 直接获取结果
results = index.query(query)
```

> 我们先前提到过, 使用Elasticsearch进行的混合检索(BM25文本匹配 + KNN向量检索), 那么这二者应该怎么取舍呢?
下方给出了ChatGPT的一个回复
```PlainText
如果你的目标是做 RAG 的混合检索，这两个方案都能胜任，但定位不一样：RedisVL 更像是基于 Redis 的“轻量统一检索层”，
官方支持在一次查询里把文本检索、向量检索和各种过滤条件组合起来，还支持 RRF 和线性融合；
Elasticsearch 则是更完整的搜索引擎方案，官方重点强调 BM25/lexical + 向量语义检索的融合，
并提供 RRF、retriever、boost、analyzer、rerank 等一整套相关性控制能力。

RedisVL 更适合的场景是：你本来就想用 Redis 承载在线检索，追求架构短、接入快、延迟敏感，
并且希望把向量、元数据、文本过滤放在同一个系统里处理。Redis 官方文档明确说它把向量和元数据存到 hashes 或 JSON 里，
支持向量索引、KNN、元数据过滤以及混合查询；RedisVL 也提供 Hash/JSON 两种存储方式和查询构建器，所以很适合做“RAG 检索中台”的快速落地。
这个选择通常更适合应用内检索、实时问答、语义缓存、以及检索逻辑不想太重的团队。

Elasticsearch 更适合的场景是：你已经在用 ES 做搜索，或者你的 RAG 语料很依赖精确词项匹配、字段权重、同义词、分词器、短语查询、过滤、排序和可解释性。
官方文档把 hybrid search 定义为把 lexical/BM25 和 semantic/vector 合成一个结果列表，并且明确推荐用 RRF；
同时它还强调可以通过 retriever、field boosts、synonyms、analyzers 和多阶段检索来持续调优相关性。
换句话说，ES 更像“搜索平台”，而不只是“向量库 + 混合检索”。

我的推荐很直接：如果你现在主要做的是 RAG 检索能力本身，优先选 RedisVL；
如果你做的是带强搜索属性的产品，优先选 Elasticsearch。 前者更偏“轻、快、简单”，后者更偏“强、全、可调”。
这个判断是基于两边官方文档对能力侧重点的归纳：Redis 强调单系统内的向量/文本/过滤混合查询，Elastic 强调完整搜索栈和更细粒度的 relevance tuning。

更细一点的落地建议是：
1）语料规模不大、团队想快速上线、Python 侧开发为主，选 RedisVL。
2）语料大、查询复杂、以后大概率要做搜索排序和召回实验，选 Elasticsearch。
3）如果你已经有 Redis / ES 其中一个现成基础设施，通常优先复用现有系统，性价比最高。
```

总结就是, 轻便快捷选RedisVL, 全面数据量大选Elasticsearch



