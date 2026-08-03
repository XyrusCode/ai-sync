---
name: seaborn-visualization
description: charting, plotting, graphing, visualization, seaborn, matplotlib, pandas reports, Chinese chart labels, and data-viz code in Daimon's managed Python runtime. Covers both interactive runs via the Bash tool and Blueprint Automation code execution.
---

# Seaborn Visualization

Use this skill for charting, plotting, graphing, visualization, seaborn, matplotlib, pandas, Chinese chart labels, visual reports, and data-viz code in Daimon's managed Python runtime.

Use pandas DataFrames for tabular data and seaborn for statistical charts. Use matplotlib only for the `Agg` backend, layout, fonts, and saving — never call `plt.show()`. The bundled CJK fonts (`NotoSansSC`) handle Chinese chart labels.

Daimon's managed Python execution passes a context dict to the entry function and expects JSON-serializable data back. From your code, import helpers:

```python
from daimon_runtime import setup_plot, save_figure
```

Call `setup_plot(ctx)` before creating figures. It configures matplotlib `Agg`, the runtime cache, bundled CJK fonts, seaborn defaults, and negative sign rendering.
Call any `sns.set_theme()` or `sns.set_style()` customization before `setup_plot(...)`, never after it: resetting the theme afterward can overwrite the managed CJK font configuration with Arial or another font that lacks Chinese glyphs.

Save figures and other outputs under `ctx["runDir"]`. `save_figure` leaves figures open by default; pass `close=True` (or call `plt.close(fig)`) after saving when a task creates many figures.

When the user requires an exact pixel size or aspect ratio, preserve the fixed canvas: use the requested `figsize` and `dpi`, lay out labels inside that canvas with `constrained_layout` or `subplots_adjust`, and do not pass `bbox_inches="tight"` because tight cropping changes the final dimensions. After saving, inspect the raster dimensions and visual edges before claiming the requested size or ratio. For charts without an exact size or ratio requirement, tight cropping remains acceptable.

## Pick the right caller

There are two callers, distinguished by who is waiting:

- **Interactive - the user asked for a chart now.** Run the managed interpreter
  yourself with the `Bash` tool. Do not create an
  Automation for one-off requests.
- **Blueprint Automation - recurring or scheduled.** Use an `Automation` with
  `execution.kind: "code"` and an `entryRef` owned by the Automation.

### Interactive: run via `Bash`

When the user is waiting on the chart in this conversation, write a script in the workspace and run it with `python` in the `Bash` tool. The managed interpreter is already first on that tool's PATH. Do not hard-code `.venv/bin/python`, because Windows uses a different layout and the runtime root may be customized.

Call `setup_plot()` with no argument — it self-configures the bundled CJK fonts, the `Agg` backend, and `MPLCONFIGDIR` from the install directory — then save the figure to a path you choose and deliver that file to the user:

```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path(sys.executable).parent.parent.parent))
from daimon_runtime import setup_plot
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

setup_plot()
df = pd.DataFrame({"x": [...], "y": [...]})
fig, ax = plt.subplots(figsize=(9, 5))
sns.lineplot(data=df, x="x", y="y", ax=ax)
fig.savefig("chart.png", dpi=220, bbox_inches="tight")
```

```bash
python chart.py
```

After the run, deliver the saved `chart.png` path to the user.

### Blueprint Automation: `execution.kind: "code"`

For scheduled or recurring work, create a Blueprint Automation with `execution.kind: "code"` and
an `entryRef` such as:

```json
{
  "kind": "code",
  "runtime": "python",
  "entryRef": { "kind": "path", "path": "automations/chart.py", "base": "automation" }
}
```

The code must produce one artifact object that matches `result.schema`.

```python
from daimon_runtime import setup_plot, save_figure

def main(ctx):
    setup_plot(ctx)
    # ... build DataFrame, plot ...
    media = save_figure(ctx, fig, "chart.png")
    return {"chart": media, "rows": len(df)}
```

Do not use legacy `cron_output` or agent-local cron code directories for Blueprint work.
