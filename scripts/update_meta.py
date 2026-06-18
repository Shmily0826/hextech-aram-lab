"""
生成 data/meta.json — 记录数据最后更新时间、版本号、数据统计
每次数据变更后运行此脚本，然后 push 即可同步到线上。
"""
import json, os, time, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
META = os.path.join(DATA_DIR, "meta.json")

# 数据文件列表
DATA_FILES = [
    "champions.json",
    "augments.json",
    "synergies.json",
    "reports.json",
    "issues.json",
]

PATCH_VERSION = "26.12"


def get_stats():
    """从数据文件中读取条目数量"""
    stats = {}
    for fname in DATA_FILES:
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            key = fname.replace(".json", "")
            if isinstance(data, list):
                stats[key] = len(data)
            elif isinstance(data, dict):
                # champions.json 有嵌套结构
                if "champions" in data:
                    stats["champions"] = len(data["champions"])
                else:
                    stats[key] = len(data)
        except Exception as e:
            print(f"[warn] 读取 {fname} 失败: {e}")
    return stats


def get_latest_mtime():
    """获取所有数据文件中最新的修改时间"""
    latest = 0
    latest_file = ""
    for fname in DATA_FILES:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            mt = os.path.getmtime(fpath)
            if mt > latest:
                latest = mt
                latest_file = fname
    return latest, latest_file


def main():
    ts, src = get_latest_mtime()
    stats = get_stats()

    # ISO 格式时间
    dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
    iso_time = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    meta = {
        "patch": PATCH_VERSION,
        "last_updated": iso_time,
        "last_updated_ts": int(ts),
        "source_file": src,
        "stats": stats,
    }

    with open(META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[meta] 版本: {PATCH_VERSION}")
    print(f"[meta] 最后更新: {iso_time} ({src})")
    print(f"[meta] 数据统计: {json.dumps(stats, ensure_ascii=False)}")
    print(f"[meta] 已写入 {META}")


if __name__ == "__main__":
    main()
