from dataclasses import dataclass


@dataclass
class HNSWConfig:

    m: int = 16
    ef_construction: int = 200
    ef_search: int = 50


@dataclass
class IVFConfig:

    nlist: int = 100
    nprobe: int = 10
