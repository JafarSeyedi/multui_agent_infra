import importlib.util
from pathlib import Path
from typing import Any, BinaryIO

from engines.document.parsers.base import BaseDocumentParser, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.ksdm_models import MiningModelType, MlMiningDocument

ONNX_AVAILABLE = importlib.util.find_spec('onnx') is not None


class OnnxParser(BaseDocumentParser):
    supported_format = MEDIA_TYPES["onnx_proto"]

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith(('.onnx', '.pb')):
            return True
        try:
            data = Path(source).read_bytes()[:8] if Path(source).exists() else b""
            return b"onnx" in data[:4].lower() or len(data) >= 8
        except Exception:
            return False

    def parse(self, source: str | Path | BinaryIO, **options: Any) -> ParseResult:
        if not ONNX_AVAILABLE:
            raise Exception("ONNX parsing requires 'onnx' package. Install with: pip install onnx")
        try:
            import onnx
            if isinstance(source, (str, Path)):
                model = onnx.load(str(source))
            elif hasattr(source, 'read'):
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(suffix='.onnx', delete=False) as f:
                    f.write(source.read())
                    tmp_path = f.name
                try:
                    model = onnx.load(tmp_path)
                finally:
                    os.unlink(tmp_path)
            else:
                raise Exception("Unsupported source type")
            opset = {}
            for entry in model.opset_import:
                opset[entry.domain or 'ai.onnx'] = entry.version
            doc = MlMiningDocument(
                model_type=MiningModelType.ONNX_MODEL,
                model_data=b'',
                onnx_model=None,
                title=str(Path(source).stem) if isinstance(source, (str, Path)) else "Untitled",
                document_id=str(Path(source).stem) if isinstance(source, (str, Path)) else "unknown",
                media_type=MEDIA_TYPES["onnx_proto"]
            )
            return ParseResult(document=doc)
        except ImportError:
            raise Exception("ONNX parsing requires 'onnx' package. Install with: pip install onnx")
        except Exception as e:
            raise Exception(f"ONNX parse failed: {e}")
