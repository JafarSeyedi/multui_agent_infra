from engines.document.models.media_types import DocumentFormat, MEDIA_TYPES, MediaTypeRegistry
from engines.document.models.standard import DocumentStandard


def test_bam_standard_exists():
    assert DocumentStandard.BAM == "bam"


def test_bam_formats_exist():
    assert DocumentFormat.BAM_JSON == "bam_json"
    assert DocumentFormat.BAM_YAML == "bam_yaml"


def test_bam_media_types_registered():
    mt_json = MEDIA_TYPES.get("bam_json")
    assert mt_json is not None
    assert mt_json.standard == DocumentStandard.BAM
    assert mt_json.format == DocumentFormat.BAM_JSON
    assert ".bam.json" in mt_json.extensions

    mt_yaml = MEDIA_TYPES.get("bam_yaml")
    assert mt_yaml is not None
    assert mt_yaml.standard == DocumentStandard.BAM
    assert mt_yaml.format == DocumentFormat.BAM_YAML
    assert ".bam.yaml" in mt_yaml.extensions


def test_bam_media_type_registry():
    mt = MediaTypeRegistry.get_by_format(DocumentFormat.BAM_JSON)
    assert mt is not None
    assert mt.mime == "application/json"
