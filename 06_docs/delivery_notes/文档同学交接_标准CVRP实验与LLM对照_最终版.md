# 文档同学交接说明：标准 CVRP 实验验证与实时 LLM 对照（最终版）

本文件为 `cvrp_docs_lite_package` 的唯一交接文档，整合“classic 主实验（mock）”与“小规模实时 LLM 对照”。

## 1) 统一评估口径

与算法流程一致，统一使用：

- `feasible_rate`
- `avg_cost`
- `avg_runtime_sec`
- `avg_num_routes`
- 分布对比指标（`gap%` 或相对 `gap%`）
- token 消耗（仅 LLM 对照）

## 2) 图文件逐项说明（`figures_final/`）

### 2.1 `final_methods_avg_cost.png`

- **作用**：给出所有方法在同一数据切片上的总体成本对比，是“谁效果更好”的主图。
- **看什么**：柱越低越好；可直接比较 baseline（`ortools/nearest_neighbor/greedy`）和搜索方法（`search_mock/search_llm`）。
- **建议放置**：报告“总体性能对比”小节主文图。

### 2.2 `final_methods_runtime_log.png`

- **作用**：展示各方法运行时间差异，补充成本图，防止只看成本忽略效率。
- **看什么**：纵轴为 log，适合跨量级比较；`ortools` 慢但成本好，启发式快但成本偏高。
- **建议放置**：报告“效率-效果权衡”小节，与 `final_methods_avg_cost.png` 成对出现。

### 2.3 `final_ablation_rows_mean.png`

- **作用**：反映消融配置在搜索过程中“实际评估了多少候选条目”（搜索强度）。
- **看什么**：`rows_mean` 越高，说明该配置探索更充分；可解释为何某些配置耗时或稳定性不同。
- **建议放置**：报告“消融实验机制分析”小节。

### 2.4 `final_ablation_rounds_mean.png`

- **作用**：反映消融配置平均能维持多少有效轮次（搜索持续性）。
- **看什么**：`rounds_mean` 越高，说明搜索更持续；可与 `rows_mean` 联合解释“行为差异而非仅成本差异”。
- **建议放置**：报告“消融实验机制分析”小节（与上一图并排）。

### 2.5 `final_mock_vs_llm_instance_delta.png`

- **作用**：实例级展示 `delta_cost = cost_mock - cost_llm`，是 LLM 对照最关键图。
- **看什么**：  
  - 正值（绿色）= LLM 更优；  
  - 负值（红色）= mock 更优；  
  - 0（灰色）= 持平。  
  图内已给出 `LLM better / Mock better / Tie` 统计。
- **建议放置**：报告“实时 LLM 对照实验”主文图（优先级最高）。

### 2.6 `final_mock_vs_llm_gap_cdf.png`

- **作用**：分布层面对比 mock 与 LLM 的整体表现，避免只看均值。
- **看什么**：曲线整体越靠左越好（gap 更小）；若无已知最优值则采用相对 `gap%` 回退口径。
- **建议放置**：报告“实时 LLM 对照实验”补充图（支撑分布结论）。

## 3) 表文件逐项说明（`tables/`）

### 3.1 `final_methods_comparison.csv`

- **作用**：主汇总表，统一列出 baseline 与搜索方法的核心指标。
- **字段重点**：`feasible_rate`、`avg_cost`、`avg_runtime_sec`、`token_total`。
- **用法建议**：正文主表可直接引用；附录可补充字段解释。

### 3.2 `baseline_summary.csv`

- **作用**：仅 baseline 方法对比（不含搜索方法），用于“传统方法基线”章节。
- **字段重点**：`num_instances`、`feasible_rate`、`avg_cost`、`avg_runtime_sec`。
- **用法建议**：当需要把 baseline 讨论独立成节时使用。

### 3.3 `ablation_aggregate_summary.csv`

- **作用**：消融总结果汇总（跨 seed 聚合），用于回答“各模块是否有贡献”。
- **字段重点**：各配置的聚合成本、可行率、耗时统计。
- **用法建议**：消融结论的主表（和行为表搭配使用）。

### 3.4 `final_ablation_behavior_summary.csv`

- **作用**：消融“行为”汇总表，对应两张行为图（rows/rounds）。
- **字段重点**：`rounds_mean`、`rows_mean`、`runtime_mean`。
- **用法建议**：用于解释“为何成本接近但搜索过程不同”。

### 3.5 `mock_vs_llm_aggregate_summary.csv`

- **作用**：原始 LLM 对照聚合结果（按 mode：`mock/llm`）。
- **字段重点**：`best_avg_cost_mean`、`best_feasible_rate_mean`、`best_avg_runtime_sec_mean`、`llm_total_tokens`。
- **用法建议**：报告中如果强调“实验原始输出”，优先引用此表。

### 3.6 `final_mock_vs_llm_aggregate.csv`

- **作用**：最终精简包保留的 LLM 对照聚合副本（便于最终包内引用）。
- **字段重点**：与 `mock_vs_llm_aggregate_summary.csv` 一致。
- **用法建议**：仅在不想引用“原始命名表”时使用；两者内容口径相同。

### 3.7 `final_mock_vs_llm_instance_delta.csv`

- **作用**：实例级对照数据源，直接支撑 `final_mock_vs_llm_instance_delta.png`。
- **字段重点**：`cost_llm`、`cost_mock`、`delta_cost`、`rel_gap_pct_llm`、`rel_gap_pct_mock`。
- **用法建议**：附录/答辩问答时用于逐实例举例说明。

### 3.8 `llm_token_summary.json`

- **作用**：记录实时 LLM token 使用量与成本量级，支持“成本可控”结论。
- **字段重点**：总 token（本次为 6170）及相关统计。
- **用法建议**：放在“实验成本与可复现性”小节，给出资源开销依据。

## 4) 主实验（classic + mock）结论（可直接用于报告）

- OR-Tools 在成本上最优但耗时最高；
- 搜索方法相对简单启发式有改进，但与 OR-Tools 仍有差距；
- 消融在成本均值上接近，但在搜索行为（轮次/评估条数）上存在可解释差异。

## 5) 实时 LLM 对照（mock vs llm）结论（本次设置）

- 相同参数下，LLM 的最佳成本优于 mock（约 7.6%）；
- 两者可行率均为 1.0；
- 本次 LLM token 总量 6170，成本可控；
- 差异在实例级更明显，优先展示实例差值图而非仅均值柱状图。

### 5.1 范围与后续扩展说明（请在报告中保留）

- 当前实时 LLM 对照属于**小规模实验**，目标是前期流程验证与方法可行性确认（参数、落盘、图表链路是否正确）。
- 后续计划转为**更大规模实时 LLM 实验**（更多实例、更多 seed、更多轮次）以获得更稳健结论。
- 因实验规模与随机性来源扩大，后续结果（成本差距、实例级胜负分布、token 消耗）可能与当前小规模结果不同，属于预期现象。
- 报告建议表述为“当前结果为阶段性验证结论，最终结论以大规模实时 LLM 复现实验为准”。

### 5.2 mock 与实时 LLM 的区别及双实验必要性（可直接写入报告）

#### （1）两者本质区别

- `mock`：候选启发式由规则/模板模拟生成，不依赖外部模型调用，结果稳定、可控、成本低。
- `实时 LLM`：候选启发式由在线大模型生成，具备更强表达能力与创新空间，但有 token 成本与随机性。

#### （2）为什么要做 mock 实验

- 用于**流程验证**：先验证搜索-评估-落盘-可视化链路是否正确，避免在高成本阶段排查基础错误。
- 用于**可复现消融**：固定生成机制后，便于比较 dedup/complexity/novelty 等模块贡献。
- 用于**建立基准线**：给出“在不依赖实时 LLM 时系统能达到的水平”，作为后续对照参考。

#### （3）为什么要做实时 LLM 实验

- 用于验证**真实能力增益**：检验 LLM 生成是否能在同口径评估下带来成本改进。
- 用于评估**实用可行性**：同时衡量效果与 token 开销，判断方案在资源预算下是否可用。
- 用于支撑项目主题：项目核心是 LLM 参与启发式搜索，实时实验是关键证据。

#### （4）为什么两种都要做（而不是二选一）

- 只做 `mock`：可复现但无法证明“LLM 本身带来的收益”。
- 只做实时 LLM：能看收益但难定位问题来源，也不利于稳定消融与流程验收。
- 两者结合形成分层证据链：  
  `mock` 负责“系统正确且稳定” + `实时 LLM` 负责“能力增益与成本评估”，结论更完整、更可信。

## 6) 报告优先使用路径

- 图：`07_delivery_packages/cvrp_docs_lite_package/figures_final/`
- 表：`07_delivery_packages/cvrp_docs_lite_package/tables/`
