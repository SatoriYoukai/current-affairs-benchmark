# 时事题 Current Affairs Benchmark

固定基线 v2：2025-11 至 2026-08，每月 2 道无工具知识短答，共 20 道。`data/questions.txt` 是原始模型输入；不把 `data/news-202511-202608-v2.json` 或 `data/baseline.json` 放进被测会话。答键含逐题来源和证据片段。

```sh
python benchmark.py prompt
python benchmark.py grade answers.txt
python -m unittest -v
```

短答一题一行 `N01=答案`，`?` 前缀是猜测，`-` 是弃答。总分计入猜对；全对前缀从最早月份连续要求每月 2/2，有对前缀每月至少 1/2。中断后命中只增加总分。前缀是此题本的覆盖指标，不等于知识截止日期。

## 2026-11-18 基线

两条隔离订阅路由，同入口、`xhigh`、无工具、无历史；同模型两路三项都一致。详细数据只包含脱敏路由标签和评分，不包括认证材料或原始运营日志。

- GPT-5.6 Sol：9/20｜全对 2026-01｜有对 2026-04
- GPT-6.1 Sol：14/20｜全对 2026-05｜有对 2026-05
- GPT-6.2 Astra：16/20｜全对 2026-06｜有对 2026-06
- GPT-6.2 Sol：17/20｜全对 2026-06｜有对 2026-07

调整题目仅进入独立探索版，不覆盖固定基线。

## 每日探索题库

`data/daily-202511-202608-v1.json` 覆盖该窗口的每一个自然日（304 天），每条记录一件事、一个短答、日期和出处。`data/daily-boundary-official-v1.json` 是额外的边界事件。请勿把题库的答案与证据交给被测模型；用命令单独导出题面：

```sh
python daily.py prompt --month 2026-07
python daily.py grade --month 2026-07 --answers answers.txt
```

每日档是探索用候选，不等价于固定基线。部分题根据 [Wikipedia Current events](https://en.wikipedia.org/wiki/Portal:Current_events) 的带出处日历改作填空：记录保留 `index_url`（修订版本和日期）及新闻出处，且明示未独立复核原文的题。改编文字注明 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)；原始文章各有各的权利人。归档日期可能是报道日期，某些答案也可能由题面推断。日报成绩只描述这份题库，不拿来确定训练截止日。经模型表现选中的题属于校准集，不能充当未见题测试。
