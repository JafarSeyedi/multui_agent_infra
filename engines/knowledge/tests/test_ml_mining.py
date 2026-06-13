from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from engines.knowledge.models.parsers.ml_mining import OnnxParser, PmmlParser
from engines.knowledge.models.writers.ml_mining import OnnxWriter, PmmlWriter
from engines.knowledge.ml_mining import MlMiningEngine
from engines.knowledge.models.ksdm_models import (
    AttributeValue,
    DatasetSplit,
    EvaluationStage,
    FeatureImportance,
    FieldUsageType,
    ImportanceMethod,
    LossFunction,
    MiningField,
    MiningModelType,
    MiningSchema,
    ModelFormat,
    ModelGraph,
    ModelMetric,
    ModelNode,
    ModelParameter,
    ModelResult,
    MlMiningDocument,
    OpType,
    OptimizationAlgorithm,
    OutlierTreatment,
    ParameterName,
    Port,
    RegularizationConfig,
    TrainingConfig,
    TrainingTask,
)
from engines.document.models.msdm_models import Attribute as MsdmAttribute, DataType, ScalarType
from engines.document.models.media_types import MEDIA_TYPES


SAMPLE_PMML = b"""<?xml version="1.0" encoding="UTF-8"?>
<PMML version="4.2" xmlns="http://www.dmg.org/PMML-4_2">
  <MiningModel modelName="IrisClassifier" modelType="decisionTree" functionName="classification">
    <MiningSchema>
      <MiningField name="sepal_length" usageType="active"/>
      <MiningField name="sepal_width" usageType="active"/>
      <MiningField name="petal_length" usageType="active"/>
      <MiningField name="petal_width" usageType="active"/>
      <MiningField name="species" usageType="predicted"/>
    </MiningSchema>
  </MiningModel>
</PMML>"""


_STR = DataType(base=ScalarType.STRING)
_DBL = DataType(base=ScalarType.DOUBLE)


@pytest.fixture
def sample_pmml_doc() -> MlMiningDocument:
    return MlMiningDocument(
        title="test_model",
        document_id="test_model",
        model_type=MiningModelType.DECISION_TREE,
        model_format=ModelFormat.PMML,
        features=[
            MsdmAttribute(name="sepal_length", data_type=_DBL),
            MsdmAttribute(name="sepal_width", data_type=_DBL),
            MsdmAttribute(name="petal_length", data_type=_DBL),
            MsdmAttribute(name="petal_width", data_type=_DBL),
        ],
        target=MsdmAttribute(name="species", data_type=_STR),
        mining_schema=MiningSchema(fields=[
            MiningField(name="sepal_length", usage_type=FieldUsageType.ACTIVE),
            MiningField(name="sepal_width", usage_type=FieldUsageType.ACTIVE),
            MiningField(name="petal_length", usage_type=FieldUsageType.ACTIVE),
            MiningField(name="petal_width", usage_type=FieldUsageType.ACTIVE),
            MiningField(name="species", usage_type=FieldUsageType.PREDICTED),
        ]),
        media_type=MEDIA_TYPES["pmml_xml"],
    )


@pytest.mark.asyncio
async def test_pmml_parse():
    parser = PmmlParser()
    doc = await parser.parse_bytes(SAMPLE_PMML, "test_pmml", "test.pmml")
    assert doc.model_type == MiningModelType.DECISION_TREE
    assert doc.model_format == ModelFormat.PMML
    assert doc.mining_schema is not None
    assert len(doc.mining_schema.fields) == 5
    assert doc.mining_schema.fields[0].name == "sepal_length"
    assert doc.mining_schema.fields[-1].name == "species"
    assert doc.mining_schema.fields[-1].usage_type == FieldUsageType.PREDICTED


@pytest.mark.asyncio
async def test_pmml_write_roundtrip():
    parser = PmmlParser()
    doc = await parser.parse_bytes(SAMPLE_PMML, "test_roundtrip", "test.pmml")
    writer = PmmlWriter()
    output = await writer.write(doc)
    assert b"<PMML" in output
    assert b"TreeModel" in output
    assert b"MiningSchema" in output
    assert b"sepal_length" in output
    assert b"species" in output

    doc2 = await parser.parse_bytes(output, "test_roundtrip2", "test.pmml")
    assert doc2.mining_schema is not None
    assert len(doc2.mining_schema.fields) == 5


@pytest.mark.asyncio
async def test_pmml_write_from_unified():
    doc = MlMiningDocument(
        title="manual_model",
        document_id="manual",
        model_type=MiningModelType.REGRESSION,
        features=[
            MsdmAttribute(name="age", data_type=_DBL),
            MsdmAttribute(name="income", data_type=_DBL),
        ],
        target=MsdmAttribute(name="score", data_type=_DBL),
        media_type=MEDIA_TYPES["pmml_xml"],
    )
    writer = PmmlWriter()
    output = await writer.write(doc)
    assert b"<PMML" in output
    assert b"age" in output
    assert b"income" in output
    assert b"score" in output


@pytest.mark.asyncio
async def test_onnx_parse_no_onnx_lib():
    dummy_onnx = b"\x08\x00\x08\x04"
    parser = OnnxParser()
    try:
        await parser.parse_bytes(dummy_onnx, "test_onnx", "test.onnx")
    except ImportError:
        pass
    except Exception:
        pass


@pytest.mark.asyncio
async def test_onnx_write_no_onnx_lib():
    doc = MlMiningDocument(
        title="onnx_test",
        document_id="onnx_test",
        model_type=MiningModelType.ONNX_MODEL,
        model_format=ModelFormat.ONNX,
        model_data=b"dummy onnx data",
        media_type=MEDIA_TYPES["onnx_protobuf"],
    )
    writer = OnnxWriter()
    output = await writer.write(doc)
    assert output == b"dummy onnx data"


def test_can_parse():
    parser = PmmlParser()
    assert parser.can_parse("model.pmml")
    assert parser.can_parse("model.pmml.xml")
    assert not parser.can_parse("model.txt")

    parser2 = OnnxParser()
    assert parser2.can_parse("model.onnx")
    assert parser2.can_parse("model.pb")


@pytest.mark.asyncio
async def test_engine_parse_pmml():
    engine = MlMiningEngine()
    doc = await engine.async_parse(SAMPLE_PMML.decode())
    assert doc.model_type == MiningModelType.DECISION_TREE
    assert doc.model_format == ModelFormat.PMML
    assert doc.mining_schema is not None


@pytest.mark.asyncio
async def test_engine_convert():
    engine = MlMiningEngine()
    await engine.async_parse(SAMPLE_PMML.decode())
    output = await engine.async_convert("pmml")
    assert b"<PMML" in output
    assert b"TreeModel" in output


@pytest.mark.asyncio
async def test_engine_getters():
    doc = MlMiningDocument(
        title="test",
        document_id="test",
        model_type=MiningModelType.SVM,
        model_format=ModelFormat.PMML,
        features=[
            MsdmAttribute(name="feat1", data_type=_DBL),
            MsdmAttribute(name="feat2", data_type=_DBL),
        ],
        target=MsdmAttribute(name="label", data_type=_STR),
        metrics=[ModelMetric(name="accuracy", value=0.95, stage=EvaluationStage.TEST)],
        training_config=TrainingConfig(task=TrainingTask.CLASSIFICATION, epochs=100),
        media_type=MEDIA_TYPES["pmml_xml"],
    )
    engine = MlMiningEngine(doc)
    assert engine.get_model_type() == MiningModelType.SVM
    assert len(engine.get_features()) == 2
    assert engine.get_features()[0].name == "feat1"
    assert engine.get_target() is not None
    assert engine.get_target().name == "label"
    assert len(engine.get_metrics()) == 1
    assert engine.get_metrics()[0].name == "accuracy"
    assert engine.get_training_config() is not None
    assert engine.get_training_config().epochs == 100
    assert engine.get_model_format() == ModelFormat.PMML


def test_model_metric_defaults():
    m = ModelMetric(name="accuracy", value=0.95)
    assert m.stage == EvaluationStage.TEST
    assert m.higher_is_better is True


def test_feature_importance():
    fi = FeatureImportance(feature_name="age", importance=0.42)
    assert fi.feature_name == "age"
    assert fi.importance == 0.42


def test_model_parameter():
    p = ModelParameter(name=ParameterName.MAX_DEPTH, value=10)
    assert p.name == ParameterName.MAX_DEPTH
    assert p.value == 10


def test_training_config():
    tc = TrainingConfig(
        task=TrainingTask.REGRESSION,
        epochs=50,
        batch_size=32,
        learning_rate=0.001,
        hyperparameters=[
            ModelParameter(name=ParameterName.MAX_DEPTH, value=10),
            ModelParameter(name=ParameterName.N_ESTIMATORS, value=100),
        ],
    )
    assert tc.task == TrainingTask.REGRESSION
    assert tc.epochs == 50
    assert tc.hyperparameters[0].name == ParameterName.MAX_DEPTH
    assert tc.hyperparameters[0].value == 10


def test_dataset_split():
    ds = DatasetSplit(train_ratio=0.7, validation_ratio=0.15, test_ratio=0.15, shuffle=True, random_seed=42)
    assert ds.train_ratio == 0.7
    assert ds.test_ratio == 0.15
    assert ds.random_seed == 42


def test_mining_schema_construction():
    schema = MiningSchema(fields=[
        MiningField(name="x", usage_type=FieldUsageType.ACTIVE, importance=0.8),
    ])
    assert schema.fields[0].importance == 0.8


def test_model_graph_construction():
    graph = ModelGraph(
        name="test_graph",
        nodes=[ModelNode(id="n1", op_type=OpType.RELU, inputs=[Port(name="x")], outputs=[Port(name="y")])],
        inputs=[Port(name="x")],
        outputs=[Port(name="y")],
    )
    assert graph.name == "test_graph"
    assert len(graph.nodes) == 1
    assert graph.nodes[0].op_type == OpType.RELU


def test_unified_document_construction():
    doc = MlMiningDocument(
        title="unified_test",
        document_id="unified_001",
        model_type=MiningModelType.DECISION_TREE,
        model_format=ModelFormat.PMML,
        features=[
            MsdmAttribute(name="f1", data_type=_DBL),
            MsdmAttribute(name="f2", data_type=_DBL),
            MsdmAttribute(name="f3", data_type=_DBL),
        ],
        target=MsdmAttribute(name="target", data_type=_STR),
        media_type=MEDIA_TYPES["pmml_xml"],
    )
    assert doc.title == "unified_test"
    assert doc.model_type == MiningModelType.DECISION_TREE
    assert doc.model_format == ModelFormat.PMML
    assert doc.features[0].name == "f1"
    assert doc.target is not None
    assert doc.target.name == "target"


@pytest.mark.asyncio
async def test_engine_graph_api():
    graph = ModelGraph(
        name="test",
        nodes=[
            ModelNode(id="root", op_type=OpType.TREE, sub_graph=ModelGraph(nodes=[
                ModelNode(id="n1", op_type=OpType.TREE_SPLIT, attributes={"predicate": AttributeValue(string_value="x > 1")}),
                ModelNode(id="n2", op_type=OpType.LEAF, attributes={"score": AttributeValue(float_value=0.5)}),
            ])),
        ],
        inputs=[Port(name="x")],
        outputs=[Port(name="score")],
    )
    doc = MlMiningDocument(
        title="graph_test",
        document_id="graph_test",
        model_type=MiningModelType.DECISION_TREE,
        model_graph=graph,
        media_type=MEDIA_TYPES["pmml_xml"],
    )
    engine = MlMiningEngine(doc)
    assert engine.get_graph() is graph
    assert engine.get_node("n1") is not None
    assert engine.get_node("n1").op_type == OpType.TREE_SPLIT
    assert engine.get_node("n1").attributes["predicate"] == AttributeValue(string_value="x > 1")
    assert engine.get_node("missing") is None

    found = engine.find_nodes(op_type=OpType.LEAF)
    assert len(found) == 1
    assert found[0].id == "n2"


@pytest.mark.asyncio
async def test_engine_traverse():
    leaf1 = ModelNode(id="l1", op_type=OpType.LEAF)
    leaf2 = ModelNode(id="l2", op_type=OpType.LEAF)
    inner = ModelNode(id="inner", op_type=OpType.TREE_SPLIT, sub_graph=ModelGraph(nodes=[leaf1, leaf2]))
    root = ModelNode(id="root", op_type=OpType.TREE, sub_graph=ModelGraph(nodes=[inner]))
    graph = ModelGraph(nodes=[root])
    doc = MlMiningDocument(
        title="traverse_test",
        document_id="traverse_test",
        model_graph=graph,
        media_type=MEDIA_TYPES["pmml_xml"],
    )
    engine = MlMiningEngine(doc)

    flat = list(engine.traverse())
    assert len(flat) == 4
    assert flat[0].id == "root"
    assert flat[1].id == "inner"
    assert flat[2].id == "l1"
    assert flat[3].id == "l2"

    with_depth = list(engine.traverse(yield_depth=True))
    assert len(with_depth) == 4
    assert with_depth[0] == (root, 0)
    assert with_depth[1] == (inner, 1)
    assert with_depth[2] == (leaf1, 2)
    assert with_depth[3] == (leaf2, 2)


@pytest.mark.asyncio
async def test_engine_mining_schema_api():
    schema = MiningSchema(fields=[
        MiningField(name="f1", usage_type=FieldUsageType.ACTIVE),
        MiningField(name="f2", usage_type=FieldUsageType.ACTIVE),
        MiningField(name="label", usage_type=FieldUsageType.PREDICTED),
    ])
    doc = MlMiningDocument(
        title="schema_test",
        document_id="schema_test",
        mining_schema=schema,
        media_type=MEDIA_TYPES["pmml_xml"],
    )
    engine = MlMiningEngine(doc)
    assert engine.get_mining_schema() == schema
    assert len(engine.get_fields()) == 3
    assert len(engine.get_active_fields()) == 2
    assert engine.get_predicted_field() is not None
    assert engine.get_predicted_field().name == "label"


@pytest.mark.asyncio
async def test_engine_validate():
    doc = MlMiningDocument(
        title="validate_test",
        document_id="validate_test",
        model_graph=ModelGraph(nodes=[
            ModelNode(id="a", op_type=OpType.CUSTOM),
            ModelNode(id="b", op_type=OpType.RELU),
        ]),
        media_type=MEDIA_TYPES["pmml_xml"],
    )
    engine = MlMiningEngine(doc)
    warnings = engine.validate()
    assert len(warnings) == 1
    assert "CUSTOM" in warnings[0]


@pytest.mark.asyncio
async def test_engine_get_parameters_and_importances():
    doc = MlMiningDocument(
        title="params_test",
        document_id="params_test",
        parameters=[ModelParameter(name=ParameterName.MAX_DEPTH, value=10)],
        feature_importances=[FeatureImportance(feature_name="age", importance=0.42)],
        media_type=MEDIA_TYPES["pmml_xml"],
    )
    engine = MlMiningEngine(doc)
    assert len(engine.get_parameters()) == 1
    assert engine.get_parameters()[0].value == 10
    assert len(engine.get_feature_importances()) == 1
    assert engine.get_feature_importances()[0].feature_name == "age"


# ============================================================
# Phase C — Full PMML Coverage Tests
# ============================================================

TREE_PMML = b"""<?xml version="1.0" encoding="UTF-8"?>
<PMML version="4.2" xmlns="http://www.dmg.org/PMML-4_2">
  <Header description="iris tree">
    <Application name="test" version="1.0"/>
  </Header>
  <DataDictionary numberOfFields="2">
    <DataField name="petal_length" dataType="double" optype="continuous"/>
    <DataField name="species" dataType="string" optype="categorical"/>
  </DataDictionary>
  <TreeModel modelName="IrisTree" functionName="classification" splitCharacteristic="binarySplit">
    <MiningSchema>
      <MiningField name="petal_length" usageType="active"/>
      <MiningField name="species" usageType="predicted"/>
    </MiningSchema>
    <Outputs>
      <OutputField name="PredictedSpecies" feature="predictedValue" dataType="string"/>
    </Outputs>
    <Node id="1" score="setosa" recordCount="150">
      <True/>
      <Node id="2" score="setosa" recordCount="50">
        <SimplePredicate field="petal_length" operator="lessOrEqual" value="2.45"/>
      </Node>
      <Node id="3" score="versicolor" recordCount="100">
        <SimplePredicate field="petal_length" operator="greaterThan" value="2.45"/>
        <ScoreDistribution value="setosa" recordCount="5"/>
        <ScoreDistribution value="versicolor" recordCount="95"/>
      </Node>
    </Node>
  </TreeModel>
</PMML>"""


@pytest.mark.asyncio
async def test_parse_treemodel():
    parser = PmmlParser()
    doc = await parser.parse_bytes(TREE_PMML, "tree_test", "tree.pmml")
    assert doc.model_type == MiningModelType.DECISION_TREE
    assert doc.model_format == ModelFormat.PMML
    assert doc.mining_schema is not None
    assert len(doc.mining_schema.fields) == 2
    assert doc.model_graph is not None
    assert len(doc.model_graph.nodes) == 1
    root = doc.model_graph.nodes[0]
    assert root.op_type == OpType.TREE
    assert root.attributes["score"].string_value == "setosa"
    assert root.attributes["record_count"].int_value == 150
    assert root.sub_graph is not None
    assert len(root.sub_graph.nodes) == 2
    n2 = root.sub_graph.nodes[0]
    n3 = root.sub_graph.nodes[1]
    assert n2.op_type == OpType.LEAF
    assert n2.attributes["predicate"].string_value == "petal_length lessOrEqual 2.45"
    assert n3.op_type == OpType.LEAF
    assert n3.attributes["predicate"].string_value == "petal_length greaterThan 2.45"
    assert n3.sub_graph is None
    assert n3.attributes["score"].string_value == "versicolor"

    assert doc.vendor_extensions["description"] == "iris tree"
    assert len(doc.features) == 1
    assert doc.features[0].name == "petal_length"
    assert doc.target is not None
    assert doc.target.name == "species"
    assert len(doc.results) == 1
    assert doc.results[0].name == "PredictedSpecies"


@pytest.mark.asyncio
async def test_treemodel_write_roundtrip():
    parser = PmmlParser()
    doc = await parser.parse_bytes(TREE_PMML, "rt", "tree.pmml")
    writer = PmmlWriter()
    output = await writer.write(doc)
    assert b"<PMML" in output
    assert b"TreeModel" in output
    assert b"IrisTree" in output
    assert b"SimplePredicate" in output
    assert b"lessOrEqual" in output
    assert b"ScoreDistribution" in output
    assert b"recordCount" in output
    assert b"PredictedSpecies" in output
    assert b"Header" in output
    assert b"DataDictionary" in output

    doc2 = await parser.parse_bytes(output, "rt2", "tree.pmml")
    assert doc2.model_type == MiningModelType.DECISION_TREE
    assert doc2.model_graph is not None
    assert len(doc2.model_graph.nodes) == 1
    root2 = doc2.model_graph.nodes[0]
    assert root2.op_type == OpType.TREE
    assert root2.attributes["score"].string_value == "setosa"
    assert root2.sub_graph is not None
    assert len(root2.sub_graph.nodes) == 2


REGRESSION_PMML = b"""<?xml version="1.0" encoding="UTF-8"?>
<PMML version="4.2" xmlns="http://www.dmg.org/PMML-4_2">
  <Header description="regression test"/>
  <DataDictionary numberOfFields="3">
    <DataField name="age" dataType="double" optype="continuous"/>
    <DataField name="income" dataType="double" optype="continuous"/>
    <DataField name="score" dataType="double" optype="continuous"/>
  </DataDictionary>
  <RegressionModel modelName="ScoreModel" functionName="regression">
    <MiningSchema>
      <MiningField name="age" usageType="active"/>
      <MiningField name="income" usageType="active"/>
      <MiningField name="score" usageType="predicted"/>
    </MiningSchema>
    <RegressionTable intercept="0.5">
      <NumericPredictor name="age" coefficient="1.2" exponent="1"/>
      <NumericPredictor name="income" coefficient="0.3" exponent="1"/>
    </RegressionTable>
  </RegressionModel>
</PMML>"""


@pytest.mark.asyncio
async def test_parse_regression_model():
    parser = PmmlParser()
    doc = await parser.parse_bytes(REGRESSION_PMML, "reg_test", "reg.pmml")
    assert doc.model_type == MiningModelType.REGRESSION
    assert doc.model_graph is not None
    assert len(doc.model_graph.nodes) == 1
    rt_node = doc.model_graph.nodes[0]
    assert rt_node.op_type == OpType.REGRESSION
    assert rt_node.attributes["intercept"].float_value == 0.5
    assert rt_node.sub_graph is not None
    assert len(rt_node.sub_graph.nodes) == 2
    predictors = {n.name: n for n in rt_node.sub_graph.nodes}
    assert "age" in predictors
    assert predictors["age"].attributes["coefficient"].float_value == 1.2
    assert "income" in predictors
    assert predictors["income"].attributes["coefficient"].float_value == 0.3


@pytest.mark.asyncio
async def test_regression_write_roundtrip():
    parser = PmmlParser()
    doc = await parser.parse_bytes(REGRESSION_PMML, "rt", "reg.pmml")
    writer = PmmlWriter()
    output = await writer.write(doc)
    assert b"<PMML" in output
    assert b"RegressionModel" in output
    assert b"ScoreModel" in output
    assert b"RegressionTable" in output
    assert b"NumericPredictor" in output
    assert b"coefficient" in output

    doc2 = await parser.parse_bytes(output, "rt2", "reg.pmml")
    assert doc2.model_type == MiningModelType.REGRESSION
    assert doc2.model_graph is not None
    assert len(doc2.model_graph.nodes) == 1
    assert doc2.model_graph.nodes[0].op_type == OpType.REGRESSION


CLUSTERING_PMML = b"""<?xml version="1.0" encoding="UTF-8"?>
<PMML version="4.2" xmlns="http://www.dmg.org/PMML-4_2">
  <Header description="clustering test"/>
  <DataDictionary numberOfFields="2">
    <DataField name="x" dataType="double" optype="continuous"/>
    <DataField name="y" dataType="double" optype="continuous"/>
  </DataDictionary>
  <ClusteringModel modelName="ClusterModel" functionName="clustering">
    <MiningSchema>
      <MiningField name="x" usageType="active"/>
      <MiningField name="y" usageType="active"/>
    </MiningSchema>
    <Cluster id="c1" size="50" name="A">
      <KohonenMap coord1="1.0" coord2="2.0"/>
    </Cluster>
    <Cluster id="c2" size="30" name="B"/>
  </ClusteringModel>
</PMML>"""


@pytest.mark.asyncio
async def test_parse_clustering_model():
    parser = PmmlParser()
    doc = await parser.parse_bytes(CLUSTERING_PMML, "clust_test", "clust.pmml")
    assert doc.model_type == MiningModelType.CLUSTERING
    assert doc.model_graph is not None
    assert len(doc.model_graph.nodes) == 2
    c1 = doc.model_graph.nodes[0]
    assert c1.op_type == OpType.CLUSTERING
    assert c1.id == "c1"
    assert c1.attributes["size"].int_value == 50
    assert c1.attributes["coords"].floats == [1.0, 2.0]
    c2 = doc.model_graph.nodes[1]
    assert c2.op_type == OpType.CLUSTERING
    assert c2.id == "c2"
    assert c2.attributes["size"].int_value == 30


@pytest.mark.asyncio
async def test_clustering_write_roundtrip():
    parser = PmmlParser()
    doc = await parser.parse_bytes(CLUSTERING_PMML, "rt", "clust.pmml")
    writer = PmmlWriter()
    output = await writer.write(doc)
    assert b"<PMML" in output
    assert b"ClusteringModel" in output
    assert b"ClusterModel" in output
    assert b"Cluster" in output
    assert b"KohonenMap" in output
    assert b"coord1" in output

    doc2 = await parser.parse_bytes(output, "rt2", "clust.pmml")
    assert doc2.model_type == MiningModelType.CLUSTERING
    assert doc2.model_graph is not None
    assert len(doc2.model_graph.nodes) == 2


TARGETS_OUTPUTS_PMML = b"""<?xml version="1.0" encoding="UTF-8"?>
<PMML version="4.2" xmlns="http://www.dmg.org/PMML-4_2">
  <DataDictionary numberOfFields="2">
    <DataField name="x" dataType="double" optype="continuous"/>
    <DataField name="y" dataType="double" optype="continuous"/>
  </DataDictionary>
  <RegressionModel modelName="TargetModel" functionName="regression">
    <MiningSchema>
      <MiningField name="x" usageType="active"/>
      <MiningField name="y" usageType="predicted"/>
    </MiningSchema>
    <Targets>
      <Target field="y" rescaleConstant="0.0" rescaleFactor="1.0"/>
    </Targets>
    <Outputs>
      <OutputField name="PredictedY" feature="predictedValue"/>
    </Outputs>
    <RegressionTable intercept="0.0"/>
  </RegressionModel>
</PMML>"""


@pytest.mark.asyncio
async def test_parse_targets_outputs():
    parser = PmmlParser()
    doc = await parser.parse_bytes(TARGETS_OUTPUTS_PMML, "to_test", "to.pmml")
    assert len(doc.results) == 1
    assert doc.results[0].name == "PredictedY"
    targets = doc.vendor_extensions.get("targets", [])
    assert len(targets) == 1
    assert targets[0]["field"] == "y"
    assert targets[0]["rescale_constant"] == 0.0
    assert targets[0]["rescale_factor"] == 1.0


@pytest.mark.asyncio
async def test_data_dictionary_type_inference():
    parser = PmmlParser()
    doc = await parser.parse_bytes(REGRESSION_PMML, "dd_test", "dd.pmml")
    assert doc.features[0].data_type.base.value == "double"
    assert doc.target is not None
    assert doc.target.data_type.base.value == "double"


@pytest.mark.asyncio
async def test_pmml_writer_no_training_config():
    doc = MlMiningDocument(
        title="no_tc",
        document_id="no_tc",
        model_type=MiningModelType.REGRESSION,
        features=[MsdmAttribute(name="x", data_type=DataType(base=ScalarType.DOUBLE))],
        media_type=MEDIA_TYPES["pmml_xml"],
    )
    writer = PmmlWriter()
    output = await writer.write(doc)
    assert b"RegressionModel" in output
    assert b"functionName" in output


@pytest.mark.asyncio
async def test_parse_minimal_mining_model():
    parser = PmmlParser()
    doc = await parser.parse_bytes(SAMPLE_PMML, "minimal", "minimal.pmml")
    assert doc.model_type == MiningModelType.DECISION_TREE
    assert doc.mining_schema is not None
    assert len(doc.mining_schema.fields) == 5
    assert doc.model_graph is not None


@pytest.mark.asyncio
async def test_graph_populated_on_parse():
    parser = PmmlParser()
    doc = await parser.parse_bytes(TREE_PMML, "gp", "tree.pmml")
    assert doc.model_graph is not None
    assert len(doc.model_graph.nodes) > 0
    engine = MlMiningEngine(doc)
    assert engine.get_graph() is not None
    assert engine.get_node("1") is not None
    assert engine.get_node("2") is not None
    assert engine.get_node("3") is not None

    nodes = list(engine.traverse())
    assert len(nodes) == 3


try:
    import onnx  # noqa: F401
    from onnx import helper, TensorProto, numpy_helper
    import numpy as np
    _ONNX_AVAILABLE = True
except ImportError:
    _ONNX_AVAILABLE = False


@pytest.mark.skipif(not _ONNX_AVAILABLE, reason="onnx package not installed")
@pytest.mark.asyncio
async def test_onnx_parse_simple_model():
    X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, 4])
    Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [None, 3])

    w_np = np.ones((4, 3), dtype=np.float32)
    b_np = np.zeros(3, dtype=np.float32)
    w_init = numpy_helper.from_array(w_np, "W")
    b_init = numpy_helper.from_array(b_np, "B")

    matmul = helper.make_node("MatMul", ["X", "W"], ["Y_mid"], name="matmul1")
    add = helper.make_node("Add", ["Y_mid", "B"], ["Y"], name="add1")

    graph = helper.make_graph([matmul, add], "test_graph", [X], [Y], [w_init, b_init])
    model_proto = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 18)])
    model_bytes = model_proto.SerializeToString()

    parser = OnnxParser()
    doc = await parser.parse_bytes(model_bytes, "onnx_test", "test.onnx")

    assert doc.model_type == MiningModelType.ONNX_MODEL
    assert doc.model_format == ModelFormat.ONNX
    assert doc.model_graph is not None
    assert doc.model_graph.name == "test_graph"

    node_map = {n.id: n for n in doc.model_graph.nodes}

    assert "matmul1" in node_map
    assert node_map["matmul1"].op_type == OpType.MATMUL

    assert "add1" in node_map
    assert node_map["add1"].op_type == OpType.ADD

    assert len(doc.model_graph.inputs) == 1
    assert doc.model_graph.inputs[0].name == "X"
    assert doc.model_graph.inputs[0].data_type is not None
    assert doc.model_graph.inputs[0].shape == [-1, 4]

    assert len(doc.model_graph.outputs) == 1
    assert doc.model_graph.outputs[0].name == "Y"

    # initializer should produce CONSTANT nodes
    constant_nodes = [n for n in doc.model_graph.nodes if n.op_type == OpType.CONSTANT]
    assert len(constant_nodes) >= 2

    # value_info metadata present
    assert "value_info" in doc.model_graph.metadata
    assert "ir_version" in doc.model_graph.metadata


@pytest.mark.skipif(not _ONNX_AVAILABLE, reason="onnx package not installed")
@pytest.mark.asyncio
async def test_onnx_write_roundtrip():
    X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [1, 4])
    Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1, 3])

    w_np = np.ones((4, 3), dtype=np.float32)
    w_init = numpy_helper.from_array(w_np, "W")

    matmul = helper.make_node("MatMul", ["X", "W"], ["Y"], name="matmul1")
    graph = helper.make_graph([matmul], "rt_graph", [X], [Y], [w_init])
    model_proto = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 18)])
    model_bytes = model_proto.SerializeToString()

    parser = OnnxParser()
    doc = await parser.parse_bytes(model_bytes, "rt_onnx", "rt.onnx")

    writer = OnnxWriter()
    output = await writer.write(doc)

    assert len(output) > 0
    assert output != b"dummy onnx data"

    model2 = onnx.load_model_from_string(output)
    assert model2.graph.name == "rt_graph"
    assert len(model2.graph.node) >= 1

    found_matmul = any(n.op_type == "MatMul" for n in model2.graph.node)
    assert found_matmul


@pytest.mark.skipif(not _ONNX_AVAILABLE, reason="onnx package not installed")
@pytest.mark.asyncio
async def test_onnx_full_roundtrip():
    X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, 4])
    Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [None, 2])

    w1_np = np.random.randn(4, 8).astype(np.float32)
    b1_np = np.zeros(8, dtype=np.float32)
    w2_np = np.random.randn(8, 2).astype(np.float32)
    b2_np = np.zeros(2, dtype=np.float32)

    w1_init = numpy_helper.from_array(w1_np, "W1")
    b1_init = numpy_helper.from_array(b1_np, "B1")
    w2_init = numpy_helper.from_array(w2_np, "W2")
    b2_init = numpy_helper.from_array(b2_np, "B2")

    mm1 = helper.make_node("MatMul", ["X", "W1"], ["h"], name="fc1/mm")
    add1 = helper.make_node("Add", ["h", "B1"], ["H"], name="fc1/add")
    relu = helper.make_node("Relu", ["H"], ["r"], name="relu1")
    mm2 = helper.make_node("MatMul", ["r", "W2"], ["y"], name="fc2/mm")
    add2 = helper.make_node("Add", ["y", "B2"], ["Y"], name="fc2/add")

    graph = helper.make_graph(
        [mm1, add1, relu, mm2, add2],
        "two_layer_net",
        [X],
        [Y],
        [w1_init, b1_init, w2_init, b2_init],
    )
    model_proto = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 18)])
    model_bytes = model_proto.SerializeToString()

    parser = OnnxParser()
    doc = await parser.parse_bytes(model_bytes, "full_rt", "full.onnx")

    writer = OnnxWriter()
    output = await writer.write(doc)

    model2 = onnx.load_model_from_string(output)

    assert model2.graph.name == "two_layer_net"
    assert len(model2.graph.node) >= 5

    found_relu = any(n.op_type == "Relu" for n in model2.graph.node)
    assert found_relu

    found_matmul = sum(1 for n in model2.graph.node if n.op_type == "MatMul")
    assert found_matmul == 2

    onnx.checker.check_model(model2)


@pytest.mark.skipif(not _ONNX_AVAILABLE, reason="onnx package not installed")
@pytest.mark.asyncio
async def test_onnx_domain_and_metadata():
    domain = "ai.onnx.contrib"
    X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [1, 2])
    Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1, 2])
    relu = helper.make_node("Relu", ["X"], ["Y"], name="relu1")
    relu.domain = domain

    graph = helper.make_graph([relu], "domain_test", [X], [Y])
    model_proto = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 18)])
    model_bytes = model_proto.SerializeToString()

    parser = OnnxParser()
    doc = await parser.parse_bytes(model_bytes, "domain_test", "domain.onnx")

    assert doc.model_graph is not None
    relu_node = next((n for n in doc.model_graph.nodes if n.id == "relu1"), None)
    assert relu_node is not None

    writer = OnnxWriter()
    output = await writer.write(doc)

    model2 = onnx.load_model_from_string(output)
    n = model2.graph.node[0]
    assert n.domain == domain



