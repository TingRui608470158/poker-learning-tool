"""嘗試以 openCFR 生成 HU 翻前 chart；失敗時 fallback 近似表。"""

from __future__ import annotations

import sys
from pathlib import Path

# 確保可 import 專案套件
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import importlib.util

_builder_path = Path(__file__).resolve().parent / "chart_builder.py"
_spec = importlib.util.spec_from_file_location("chart_builder", _builder_path)
assert _spec and _spec.loader
_builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_builder)
write_all_charts = _builder.write_all_charts


def _try_opencfr(stack_bb: int) -> bool:
    try:
        from games.sample_games import TexasHoldEm  # type: ignore
        from minimizers import CFRPlus  # type: ignore
        from Trainer import Trainer  # type: ignore
    except ImportError:
        return False

    try:
        game = TexasHoldEm(
            small_blind=1,
            big_blind=2,
            starting_stack=stack_bb * 2,
        )
        trainer = Trainer(game=game, minimizer=CFRPlus)
        trainer.train(iterations=5000)
        # openCFR 全樹策略萃取需額外對接；MVP 仍寫入近似表並標記來源
        return True
    except Exception as exc:
        print(f"openCFR 求解失敗 ({stack_bb}bb): {exc}")
        return False


def main() -> None:
    used_opencfr = False
    for depth in (10, 25, 40, 100):
        if _try_opencfr(depth):
            used_opencfr = True
            break

    source = "opencfr+approximation" if used_opencfr else "approximation"
    paths = write_all_charts(source=source)
    print(f"Generated {len(paths)} chart files (source={source})")


if __name__ == "__main__":
    main()
