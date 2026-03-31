# 最终保留清单（标准 CVRP：实验验证到落盘）

本清单用于保证两件事：
- 结果可直接交付（含最终图表/表格）；
- 后续可在本项目内复现实验结果。

## 1. 已保留（必要）

### 1.1 数据与原始处理结果
- `01_raw_data/`
- `02_processed_data/classic/`
- `02_processed_data/fresh/`

### 1.2 核心算法与流程代码
- `03_core_algorithm/`
- `05_scripts/run_formal_benchmark.py`
- `05_scripts/run_llm_vs_mock_small.py`
- `05_scripts/build_lite_final_assets.py`
- `05_scripts/process_cvrplib.py`
- `05_scripts/generate_fresh_dataset.py`

### 1.3 可复现实验输出
- `04_experiment_outputs/formal_benchmark/formal_benchmark_runs/`
- `04_experiment_outputs/llm_vs_mock_small/`

### 1.4 最终交付包（保留最终版）
- `07_delivery_packages/cvrp_docs_lite_package/`
- `07_delivery_packages/cvrp_docs_lite_package.zip`
- `07_delivery_packages/classic_cvrp_dataset.zip`
- `07_delivery_packages/fresh_cvrp_dataset.zip`

## 2. 已删除（冗余/中间产物）

- `04_experiment_outputs/formal_benchmark/smoke_test_export/`（测试导出）
- `04_experiment_outputs/formal_benchmark/tmp_plot_test/`（临时绘图）
- `05_scripts/__pycache__/`
- `07_delivery_packages/cvrp_classic_llm_vs_mock_small/`（旧交付包）
- `07_delivery_packages/cvrp_classic_llm_vs_mock_small.zip`（旧交付包）
- `07_delivery_packages/cvrp_experiment_handover_for_docs/`（旧交付包）
- `07_delivery_packages/cvrp_experiment_handover_for_docs.zip`（旧交付包）

## 3. 标准复现命令

在项目根目录执行：

```powershell
python 05_scripts/run_formal_benchmark.py
python 05_scripts/run_llm_vs_mock_small.py
python 05_scripts/build_lite_final_assets.py
```

说明：
- 前两条命令复现“正式 mock 主实验 + 小规模实时 LLM 对照”；
- 第三条命令基于实验输出重建最终精简图表与最终对比表。

## 4. 报告优先引用位置

- 图：`07_delivery_packages/cvrp_docs_lite_package/figures_final/`
- 表：`07_delivery_packages/cvrp_docs_lite_package/tables/`
- 交接说明：`07_delivery_packages/cvrp_docs_lite_package/docs/`
