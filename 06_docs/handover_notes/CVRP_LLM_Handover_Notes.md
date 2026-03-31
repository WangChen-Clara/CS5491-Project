# CVRP 启发式搜索与 LLM 候选表达式生成项目交接说明

## 1. 项目范围与当前状态
本 notebook 实现了一个面向 CVRP（Capacitated Vehicle Routing Problem，容量约束车辆路径问题）的启发式搜索实验框架。其核心思路是：使用表达式定义客户选择打分规则，对候选表达式进行评估、筛选与迭代扩展，并可通过 LLM 生成新的候选表达式。

当前版本已经完成以下核心工作：

- 环境配置与依赖安装；
- CVRP 实例数据读取，并统一整理为内部 `instance` 格式；
- baseline 求解器与对照流程；
- 基于表达式的启发式构造；
- 单轮候选表达式评估与聚合统计；
- 候选池控制模块，包括重复过滤、复杂度控制、行为签名式 novelty 支持；
- LLM 候选表达式生成接口；
- 外层搜索流程（generation → evaluation → selection → carry-over）；
- 在小规模实例子集上的端到端联调验证。

目前该框架已经可以 **完整运行主流程**。后续工作的重点是：

- 接入新的数据集；
- 扩展到更大的 benchmark；
- 系统执行实验并整理结果；
- 补齐消融实验。

---

## 2. Notebook 结构与功能模块

### 2.1 环境与依赖
前部单元格安装并导入实验所需依赖，主要包括：

- `ortools`
- `vrplib`
- `pandas`
- `numpy`
- `matplotlib`
- `openai`

当前 notebook 主要面向 Colab 环境编写；如果迁移到本地或其他平台，可能需要对安装方式做少量调整。

### 2.2 基础工具函数
notebook 中定义了若干通用的距离与可行性辅助函数，包括：

- `euclidean_distance(a, b)`
- `build_distance_matrix(coords)`
- `route_distance(route, dist_matrix)`
- `total_distance(routes, dist_matrix)`
- `check_feasibility(routes, demands, capacity, depot=0)`

这些函数用于支持：

- 路径长度计算；
- 整体解的总代价计算；
- 容量约束可行性检查。

### 2.3 Baseline 求解器
当前 notebook 中已包含若干 baseline CVRP 求解方式，便于后续实验对照：

- `greedy_cvrp_solver(instance)`
- `ortools_cvrp_solver(instance, time_limit_sec=3)`
- `nearest_neighbor_cvrp_solver(instance)`

此外，还支持基于表达式的启发式构造：

- `nn_score(current, c, instance, remaining, dist_matrix)`
- `make_score_fn_from_expression(expr)`
- `heuristic_cvrp_solver(...)`

其中，表达式驱动的求解器是整个项目的关键桥梁：LLM 生成的表达式最终会被转成 score function，并作用在具体的 CVRP 构造过程中。

### 2.4 数据读取与 instance 标准化
主要数据读取函数为：

- `load_base_instance(json_path)`

该函数会将每个 JSON 实例文件转换为统一的内部 `instance` 对象。当前格式为：

```python
instance = {
    "name": data["instance_id"],
    "depot": 0,
    "coords": coords,
    "demands": demands,
    "capacity": data["vehicle_capacity"],
    "num_nodes": len(coords),
    "distance_matrix": data["distance_matrix"],
    "raw": data,
}
```

需要注意：

- 内部表示中固定使用 `depot = 0`；
- `coords`、`demands`、`distance_matrix` 三者必须严格对齐；
- `raw` 中保留了原始 JSON 的完整字段，可供后续分析使用，例如 `known_opt_cost`、`known_opt_routes`、`set_id` 等。

批量读取由以下函数处理：

- `load_multiple_base_instances(base_dir, limit=None)`

当前为了联调主流程，仅使用 `limit=5` 的小规模子集进行测试。

### 2.5 候选表达式评估与结果汇总
单个表达式在多个实例上的评估由以下函数完成：

- `evaluate_expression_on_instances(instances, expr)`

表达式级别的结果汇总由以下函数完成：

- `summarize_expression_results(df)`

命名求解器（baseline）在多个实例上的批量评估由以下函数完成：

- `evaluate_named_solver_on_instances(instances, solver_name, solver_fn)`

固定候选池下的多表达式搜索由以下函数支持：

- `search_expressions_multi(instances, candidate_expressions, top_k=5)`

这些函数会输出单实例结果以及聚合后的汇总结果，常见指标包括：

- cost
- runtime
- feasible
- num_routes

### 2.6 候选池控制模块
当前 notebook 中已经实现了三类候选池控制机制。

#### （1）重复过滤
- `dedup_expressions(candidate_expressions)`

该模块用于做表达式字符串级别去重，避免完全相同的候选被重复评估。

#### （2）复杂度控制
- `expression_complexity(expr)`
- `filter_expressions_by_complexity(expressions, max_complexity=None)`

当前复杂度定义基于表达式字符串长度与运算符数量，是一个轻量级复杂度估计，用于：

- 过滤过于复杂的候选；
- 在排序时作为辅助指标。

#### （3）基于行为签名的 novelty 支持
- `make_behavior_signature_from_summary_row(...)`
- `add_novelty_columns(summary_df, archive_signatures=None)`
- `update_archive_signatures(summary_df, archive_signatures=None, only_novel=True)`

novelty 的实现基于聚合行为统计（如平均 cost、平均路线数、可行率等）构成的离散签名，而不是符号表达式本身的精确等价判定。

表达式汇总结果的排序由以下函数处理：

- `sort_expression_summary(summary_df)`

当前的排序优先级为：

1. 可行率更高；
2. 平均 cost 更低；
3. 平均路线数更少；
4. complexity 更低。

### 2.7 候选生成
当前支持两类候选表达式生成方式。

#### 模拟生成（用于本地测试）
- `generate_mock_expression_variants(seed_expr, n=8)`
- `generate_mock_candidates_from_top_expressions(...)`

#### LLM 生成
- `build_expression_generation_prompt(...)`
- `try_parse_json_object(text)`
- 若干表达式合法性检查辅助函数；
- `call_openai_for_expressions_chat(...)`
- `generate_candidates_with_llm(...)`

LLM 被要求返回如下 JSON 结构：

```json
{"expressions": ["expr1", "expr2", "..."]}
```

随后仅保留满足变量范围与表达式格式约束的候选。

### 2.8 外层搜索流程
外层搜索主流程由以下函数实现：

- `evaluate_expression_list_on_instances(instances, expressions)`
- `run_one_search_round(...)`
- `search_expressions_outer_loop(...)`

这部分是整个实验框架的核心。在每一轮中，系统依次完成：

1. 对候选表达式做去重与过滤；
2. 在选定实例集上评估所有候选；
3. 汇总、排序并选出 top 表达式；
4. 更新 novelty archive；
5. 使用 mock 或 LLM 方式生成下一轮候选；
6. 进入下一轮 outer loop。

---

## 3. 输入输出约定

### 3.1 Route 格式
单条 route 使用节点下标列表表示，例如：

```python
[0, 3, 5, 0]
```

其中 `0` 表示 depot。一个完整解使用 route 列表表示，即：

```python
[[0, 3, 5, 0], [0, 2, 4, 0]]
```

### 3.2 表达式格式
候选表达式应为单行 Python 算术表达式，例如：

```python
dist_matrix[current][c] - instance['demands'][c]
```

表达式最终会被转为如下接口的 score function：

```python
score_fn(current, c, instance, remaining, dist_matrix)
```

约定为：**分数越小，优先级越高**。

### 3.3 评估输出
当前评估流程至少会记录以下字段：

- `instance`
- `expression`
- `cost`
- `runtime_sec`
- `feasible`
- `num_routes`

聚合后的汇总结果通常包含：

- `num_instances`
- `feasible_rate`
- `avg_cost`
- `avg_runtime_sec`
- `avg_num_routes`
- `complexity`
- novelty 相关字段（若启用）

---

## 4. 当前已经验证通过的部分
目前以下内容已经在小规模实例子集上完成联调验证：

- 数据读取与 instance 标准化；
- baseline 求解器运行；
- 表达式解析与启发式构造；
- 多实例上的候选表达式评估；
- 单轮与多轮搜索执行；
- OpenAI API 接口与候选表达式生成。


---

## 5. 后续工作建议分工
后续工作可以较清晰地拆分为以下两部分。

### 5.1 当前 notebook 已基本完成的部分
以下内容可以视为当前版本的稳定主干：

- instance 读取与标准化；
- baseline 评估；
- 表达式驱动的启发式求解流程；
- LLM 候选生成接口；
- 单轮搜索与 outer loop 主逻辑；
- 重复过滤、复杂度控制、novelty 支持模块。

### 5.2 适合后续同学接手的部分
#### A. 新生鲜/新数据集接入
- 将新数据适配为相同的 `instance` schema；
- 确保 `coords`、`demands`、`capacity`、`distance_matrix` 字段正确对齐；
- 验证新实例无需修改主流程即可进入现有评估框架。

#### B. 大规模 benchmark 实验执行
- 将当前小规模测试实例替换为更大的 benchmark 集；
- 批量运行 baseline 与 outer loop 搜索实验；
- 保存中间结果表与最终结果表；
- 在更多实例、更多轮次上比较不同方法表现。

#### C. 实验分析与结果整理
- 汇总各项性能指标；
- 比较 baseline、表达式搜索、LLM 增强搜索的差异；
- 分析 feasible rate、cost、route 数、complexity、novelty 等趋势；
- 准备最终报告所需的表格与图。

---

## 6. 不建议随意修改的部分
以下约定在 notebook 中被多处默认使用，如需修改，应先检查下游影响。

### 6.1 Depot 编号约定
当前内部约定为：

- `depot index = 0`

该约定会影响 route 表示、需求求和、距离访问等多个部分。

### 6.2 Instance schema
当前 solver 与 evaluation 代码都依赖前述标准化后的 `instance` 格式。若接入新数据，建议映射到该 schema，而不是直接修改后续函数接口。

### 6.3 表达式接口
生成的表达式默认只能使用允许的局部变量，并输出一个标量 score。若修改 score function 接口，会同时影响：

- 候选生成；
- 表达式验证；
- 求解器调用；
- outer loop。

### 6.4 排序逻辑
当前排序逻辑默认优先保证可行性，再比较代价。这是有意设计的实验目标，不建议在未说明理由的情况下随意改动。

---

## 7. 已实现但尚未系统测试的部分（To-do）
### 7.1 搜索增强模块的消融实验
原计划需要对若干搜索增强模块做系统性消融实验。目前这些模块 **已经实现并接入当前 pipeline**，但 **尚未在更大 benchmark 上系统测试**。

当前已实现的模块包括：

1. **重复过滤（duplicate filtering）**
   - 已实现表达式级去重；
   - 目的：避免完全相同候选被重复评估。

2. **复杂度控制（complexity-aware filtering / ranking）**
   - 已实现复杂度计算；
   - 已支持基于复杂度的过滤与排序辅助；
   - 目的：抑制过于复杂的表达式，并兼顾可解释性与搜索效率。

3. **基于行为签名的 novelty 支持（novelty-based tracking / filtering）**
   - 已实现行为签名构造；
   - 已实现 archive-based novelty 标记；
   - 在对应参数开启时，可将 novelty 作为过滤条件使用；
   - 目的：鼓励行为多样性，减少对等价或近似等价启发式的重复探索。

#### 当前仍需完成的工作
需要在更大 benchmark 上补做系统性的消融实验，用于量化上述模块各自的贡献。建议至少考虑如下实验配置：

- 基础搜索流程；
- 基础搜索 + 重复过滤；
- 基础搜索 + 复杂度控制；
- 基础搜索 + novelty 过滤；
- 三者全部开启的完整版本。

如果后续实验资源允许，也可进一步细分 complexity filtering 与 complexity-aware ranking 的作用。

### 7.2 Benchmark 规模扩展
当前验证规模仍较小，尚未覆盖完整 benchmark。需要在更大实例集上重复实验，以支持最终结论。

### 7.3 候选安全性与鲁棒性
尽管目前已经有表达式过滤与合法性检查，LLM 仍可能生成低质量或不可用候选。若后续实验中发现问题，可继续增强过滤规则与异常处理。

### 7.4 与已知最优解的对比分析
原始 JSON 数据已保存在 `instance["raw"]` 中，后续如需分析 gap、对比 known optimal cost 或 known routes，可直接从该字段中提取信息。

---

## 8. 后续接手建议顺序
若后续同学在当前 notebook 基础上继续推进，建议按以下顺序进行：

1. **先原样运行当前 notebook**，确认环境与依赖正常；
2. **先不要改主流程**，优先做数据扩展或新数据接入；
3. **保持当前 `instance` 内部格式不变**；
4. 使用现有入口函数继续推进实验：
   - `run_one_search_round(...)`
   - `search_expressions_outer_loop(...)`
5. 在大规模运行稳定后，再继续进行：
   - 结果保存；
   - 汇总表整理；
   - 图表制作；
   - 消融实验执行；
   - 最终报告撰写。

