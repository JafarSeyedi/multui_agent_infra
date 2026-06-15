from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from engines.document.models.base import BaseDocument
from engines.document.models.msdm_models import Attribute as MsdmAttribute, DataType


class MiningModelType(str, Enum):
    NEURAL_NETWORK = "neural_network"
    DECISION_TREE = "decision_tree"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ASSOCIATION_RULES = "association_rules"
    SEQUENCE_CLUSTERING = "sequence_clustering"
    TIME_SERIES = "time_series"
    SVM = "svm"
    NAIVE_BAYES = "naive_bayes"
    GAUSSIAN_PROCESS = "gaussian_process"
    ONNX_MODEL = "onnx_model"
    OTHER = "other"


class FieldUsageType(str, Enum):
    ACTIVE = "active"
    PREDICTED = "predicted"
    SUPPLEMENTARY = "supplementary"
    GROUP = "group"
    ORDER = "order"
    FREQUENCY_WEIGHT = "frequency_weight"
    ANALYSIS_WEIGHT = "analysis_weight"


class OutlierTreatment(str, Enum):
    AS_IS = "as_is"
    AS_MISSING_VALUES = "as_missing_values"
    AS_EXTREME_VALUES = "as_extreme_values"


class EvaluationStage(str, Enum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"
    HOLDOUT = "holdout"
    CROSS_VALIDATION = "cross_validation"


class ImportanceMethod(str, Enum):
    GINI = "gini"
    PERMUTATION = "permutation"
    SHAP = "shap"
    GAIN = "gain"
    COVER = "cover"
    FREQUENCY = "frequency"
    LIME = "lime"


class OptimizationAlgorithm(str, Enum):
    SGD = "sgd"
    ADAM = "adam"
    ADAMW = "adamw"
    RMSPROP = "rmsprop"
    LBFGS = "lbfgs"
    ADAGRAD = "adagrad"
    NADAM = "nadam"


class LossFunction(str, Enum):
    MSE = "mse"
    MAE = "mae"
    CROSS_ENTROPY = "cross_entropy"
    BINARY_CROSSENTROPY = "binary_crossentropy"
    HINGE = "hinge"
    HUBER = "huber"
    LOG_LOSS = "log_loss"
    KL_DIVERGENCE = "kl_divergence"


class ParameterName(str, Enum):
    MAX_DEPTH = "max_depth"
    N_ESTIMATORS = "n_estimators"
    LEARNING_RATE = "learning_rate"
    MIN_SAMPLES_SPLIT = "min_samples_split"
    MIN_SAMPLES_LEAF = "min_samples_leaf"
    MAX_FEATURES = "max_features"
    MAX_LEAF_NODES = "max_leaf_nodes"
    CRITERION = "criterion"
    CCP_ALPHA = "ccp_alpha"
    SUBSAMPLE = "subsample"
    COLSAMPLE_BYTREE = "colsample_bytree"
    COLSAMPLE_BYLEVEL = "colsample_bylevel"
    COLSAMPLE_BYNODE = "colsample_bynode"
    MAX_DELTA_STEP = "max_delta_step"
    REG_ALPHA = "reg_alpha"
    REG_LAMBDA = "reg_lambda"
    MIN_CHILD_WEIGHT = "min_child_weight"
    NUM_LEAVES = "num_leaves"
    MIN_CHILD_SAMPLES = "min_child_samples"
    FEATURE_FRACTION = "feature_fraction"
    RATE_DROP = "rate_drop"
    SKIP_DROP = "skip_drop"
    C_SVM = "C"
    KERNEL = "kernel"
    DEGREE = "degree"
    GAMMA = "gamma"
    COEF0 = "coef0"
    SHRINKING = "shrinking"
    NU = "nu"
    PROBABILITY = "probability"
    HIDDEN_LAYER_SIZES = "hidden_layer_sizes"
    ACTIVATION = "activation"
    SOLVER = "solver"
    BATCH_SIZE = "batch_size"
    WEIGHT_DECAY = "weight_decay"
    MOMENTUM = "momentum"
    NESTEROVS_MOMENTUM = "nesterovs_momentum"
    BETA_1 = "beta_1"
    BETA_2 = "beta_2"
    EPSILON = "epsilon"
    N_HIDDEN = "n_hidden"
    N_EPOCHS = "n_epochs"
    N_BATCH = "n_batch"
    DROPOUT = "dropout"
    WARMUP_STEPS = "warmup_steps"
    LEARNING_RATE_INIT = "learning_rate_init"
    POWER_T = "power_t"
    N_CLUSTERS = "n_clusters"
    N_INIT = "n_init"
    INIT = "init"
    EPS = "eps"
    MIN_SAMPLES = "min_samples"
    METRIC = "metric"
    LINKAGE = "linkage"
    AFFINITY = "affinity"
    DISTANCE_THRESHOLD = "distance_threshold"
    DBSCAN_MIN_SAMPLES = "dbscan_min_samples"
    RANDOM_STATE = "random_state"
    VERBOSE = "verbose"
    N_JOBS = "n_jobs"
    N_ITER = "n_iter"
    MAX_ITER = "max_iter"
    TOL = "tol"
    EARLY_STOPPING_ROUNDS = "early_stopping_rounds"
    VALIDATION_FRACTION = "validation_fraction"
    ALPHA = "alpha"
    L1_RATIO = "l1_ratio"
    N_NEIGHBORS = "n_neighbors"
    PRIORS = "priors"
    VAR_SMOOTHING = "var_smoothing"
    PCA_N_COMPONENTS = "pca_n_components"
    WHITEN = "whiten"
    SVDD_NU = "svdd_nu"
    SIGMA = "sigma"
    AFFINITY_METRIC = "affinity_metric"
    POOLING = "pooling"
    STRIDES = "strides"
    PADS = "pads"
    DILATIONS = "dilations"
    KERNEL_SHAPE = "kernel_shape"
    CUSTOM = "custom"


class OpType(str, Enum):
    TREE = "tree"
    TREE_SPLIT = "tree_split"
    LEAF = "leaf"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ENSEMBLE = "ensemble"
    CELU = "Celu"
    ELU = "Elu"
    GELU = "Gelu"
    HARD_SIGMOID = "HardSigmoid"
    HARD_SWISH = "HardSwish"
    LEAKY_RELU = "LeakyRelu"
    MISH = "Mish"
    PRELU = "PRelu"
    RELU = "Relu"
    SELU = "Selu"
    SIGMOID = "Sigmoid"
    SOFTMAX = "Softmax"
    SOFTPLUS = "Softplus"
    SOFTSIGN = "Softsign"
    SWISH = "Swish"
    TANH = "Tanh"
    THRESHOLDED_RELU = "ThresholdedRelu"
    ABS = "Abs"
    ACOS = "Acos"
    ACOSH = "Acosh"
    ASIN = "Asin"
    ASINH = "Asinh"
    ATAN = "Atan"
    ATANH = "Atanh"
    ADD = "Add"
    CEIL = "Ceil"
    COS = "Cos"
    COSH = "Cosh"
    DIV = "Div"
    ERF = "Erf"
    EXP = "Exp"
    FLOOR = "Floor"
    LOG = "Log"
    MUL = "Mul"
    NEG = "Neg"
    POW = "Pow"
    RECIPROCAL = "Reciprocal"
    ROUND = "Round"
    SIGN = "Sign"
    SIN = "Sin"
    SINH = "Sinh"
    SQRT = "Sqrt"
    SUB = "Sub"
    SUM = "Sum"
    SQUEEZE = "Squeeze"
    TAN = "Tan"
    UNSQUEEZE = "Unsqueeze"
    CONV = "Conv"
    CONV_INTEGER = "ConvInteger"
    CONV_TRANSPOSE = "ConvTranspose"
    GEMM = "Gemm"
    MATMUL = "MatMul"
    MATMUL_INTEGER = "MatMulInteger"
    BATCH_NORMALIZATION = "BatchNormalization"
    INSTANCE_NORMALIZATION = "InstanceNormalization"
    LAYER_NORMALIZATION = "LayerNormalization"
    GROUP_NORMALIZATION = "GroupNormalization"
    RMS_NORMALIZATION = "RMSNormalization"
    LP_NORMALIZATION = "LpNormalization"
    LP_POOL = "LpPool"
    MAX_POOL = "MaxPool"
    AVERAGE_POOL = "AveragePool"
    GLOBAL_AVERAGE_POOL = "GlobalAveragePool"
    GLOBAL_LP_POOL = "GlobalLpPool"
    GLOBAL_MAX_POOL = "GlobalMaxPool"
    MAX_ROI_POOL = "MaxRoiPool"
    MAX_UNPOOL = "MaxUnpool"
    LRN = "LRN"
    DROPOUT = "Dropout"
    FLATTEN = "Flatten"
    SOFTMAX_CROSS_ENTROPY_LOSS = "SoftmaxCrossEntropyLoss"
    NEGATIVE_LOG_LIKELIHOOD_LOSS = "NegativeLogLikelihoodLoss"
    RESHAPE = "Reshape"
    TRANSPOSE = "Transpose"
    CONCAT = "Concat"
    CONCAT_FROM_SEQUENCE = "ConcatFromSequence"
    SPLIT = "Split"
    SPLIT_TO_SEQUENCE = "SplitToSequence"
    SLICE = "Slice"
    PAD = "Pad"
    TILE = "Tile"
    EXPAND = "Expand"
    COMPRESS = "Compress"
    GATHER = "Gather"
    GATHER_ELEMENTS = "GatherElements"
    GATHER_ND = "GatherND"
    SCATTER = "Scatter"
    SCATTER_ELEMENTS = "ScatterElements"
    SCATTER_ND = "ScatterND"
    TENSOR_SCATTER = "TensorScatter"
    TOP_K = "TopK"
    NON_ZERO = "NonZero"
    WHERE = "Where"
    EYE_LIKE = "EyeLike"
    CONSTANT = "Constant"
    CONSTANT_OF_SHAPE = "ConstantOfShape"
    ONE_HOT = "OneHot"
    SHAPE = "Shape"
    SIZE = "Size"
    RANGE = "Range"
    IDENTITY = "Identity"
    CAST = "Cast"
    CAST_LIKE = "CastLike"
    BIT_SHIFT = "BitShift"
    CLIP = "Clip"
    RESIZE = "Resize"
    DEPTH_TO_SPACE = "DepthToSpace"
    SPACE_TO_DEPTH = "SpaceToDepth"
    COL2_IM = "Col2Im"
    DEFORM_CONV = "DeformConv"
    GRID_SAMPLE = "GridSample"
    NON_MAX_SUPPRESSION = "NonMaxSuppression"
    ROI_ALIGN = "RoiAlign"
    REVERSE_SEQUENCE = "ReverseSequence"
    TRILU = "Trilu"
    UNIQUE = "Unique"
    UPSAMPLE = "Upsample"
    CENTER_CROP_PAD = "CenterCropPad"
    AFFINE_GRID = "AffineGrid"
    IMAGE_DECODER = "ImageDecoder"
    ARG_MAX = "ArgMax"
    ARG_MIN = "ArgMin"
    REDUCE_L1 = "ReduceL1"
    REDUCE_L2 = "ReduceL2"
    REDUCE_LOG_SUM = "ReduceLogSum"
    REDUCE_LOG_SUM_EXP = "ReduceLogSumExp"
    REDUCE_MAX = "ReduceMax"
    REDUCE_MEAN = "ReduceMean"
    REDUCE_MIN = "ReduceMin"
    REDUCE_PROD = "ReduceProd"
    REDUCE_SUM = "ReduceSum"
    REDUCE_SUM_SQUARE = "ReduceSumSquare"
    CUM_PROD = "CumProd"
    CUM_SUM = "CumSum"
    EQUAL = "Equal"
    GREATER = "Greater"
    GREATER_OR_EQUAL = "GreaterOrEqual"
    LESS = "Less"
    LESS_OR_EQUAL = "LessOrEqual"
    AND = "And"
    OR = "Or"
    XOR = "Xor"
    NOT = "Not"
    IS_INF = "IsInf"
    IS_NAN = "IsNaN"
    QUANTIZE_LINEAR = "QuantizeLinear"
    DEQUANTIZE_LINEAR = "DequantizeLinear"
    DYNAMIC_QUANTIZE_LINEAR = "DynamicQuantizeLinear"
    QLINEAR_CONV = "QLinearConv"
    QLINEAR_MATMUL = "QLinearMatMul"
    IF = "If"
    LOOP = "Loop"
    SCAN = "Scan"
    SEQUENCE_AT = "SequenceAt"
    SEQUENCE_CONSTRUCT = "SequenceConstruct"
    SEQUENCE_EMPTY = "SequenceEmpty"
    SEQUENCE_ERASE = "SequenceErase"
    SEQUENCE_INSERT = "SequenceInsert"
    SEQUENCE_LENGTH = "SequenceLength"
    SEQUENCE_MAP = "SequenceMap"
    OPTIONAL = "Optional"
    OPTIONAL_GET_ELEMENT = "OptionalGetElement"
    OPTIONAL_HAS_ELEMENT = "OptionalHasElement"
    RANDOM_NORMAL = "RandomNormal"
    RANDOM_NORMAL_LIKE = "RandomNormalLike"
    RANDOM_UNIFORM = "RandomUniform"
    RANDOM_UNIFORM_LIKE = "RandomUniformLike"
    MULTINOMIAL = "Multinomial"
    BERNOULLI = "Bernoulli"
    DFT = "DFT"
    STFT = "STFT"
    BLACKMAN_WINDOW = "BlackmanWindow"
    HAMMING_WINDOW = "HammingWindow"
    HANN_WINDOW = "HannWindow"
    MEL_WEIGHT_MATRIX = "MelWeightMatrix"
    ARRAY_FEATURE_EXTRACTOR = "ArrayFeatureExtractor"
    BINARIZER = "Binarizer"
    CAST_MAP = "CastMap"
    CATEGORY_MAPPER = "CategoryMapper"
    DICT_VECTORIZER = "DictVectorizer"
    FEATURE_VECTORIZER = "FeatureVectorizer"
    IMPUTER = "Imputer"
    LABEL_ENCODER = "LabelEncoder"
    LINEAR_CLASSIFIER = "LinearClassifier"
    LINEAR_REGRESSOR = "LinearRegressor"
    NORMALIZER = "Normalizer"
    ONE_HOT_ENCODER = "OneHotEncoder"
    SCALER = "Scaler"
    SVM_CLASSIFIER = "SVMClassifier"
    SVM_REGRESSOR = "SVMRegressor"
    TREE_ENSEMBLE = "TreeEnsemble"
    TREE_ENSEMBLE_CLASSIFIER = "TreeEnsembleClassifier"
    TREE_ENSEMBLE_REGRESSOR = "TreeEnsembleRegressor"
    TFIDF_VECTORIZER = "TfIdfVectorizer"
    ZIP_MAP = "ZipMap"
    STRING_NORMALIZER = "StringNormalizer"
    STRING_CONCAT = "StringConcat"
    STRING_SPLIT = "StringSplit"
    REGEX_FULL_MATCH = "RegexFullMatch"
    SVM_MODEL = "svm_model"
    NAIVE_BAYES_MODEL = "naive_bayes_model"
    KMEANS = "kmeans"
    LINEAR_REGRESSION_MODEL = "linear_regression_model"
    LOGISTIC_REGRESSION_MODEL = "logistic_regression_model"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTED_TREES = "gradient_boosted_trees"
    ADAGRAD_OP = "Adagrad"
    ADAM_OP = "Adam"
    MOMENTUM_OP = "Momentum"
    GRADIENT = "Gradient"
    EINSUM = "Einsum"
    DET = "Det"
    MAX = "Max"
    MEAN = "Mean"
    MIN = "Min"
    MOD = "Mod"
    HARDMAX = "Hardmax"
    LOG_SOFTMAX = "LogSoftmax"
    LOOP_COUNTER = "LoopCounter"
    MATRIX_MULTIPLY = "MatrixMultiply"
    NEGATIVE_SLOPE = "NegativeSlope"
    PROD = "Prod"
    SEQUENCE_APPEND = "SequenceAppend"
    SEQUENCE_INDEX = "SequenceIndex"
    SEQUENCE_POP = "SequencePop"
    SEQUENCE_PUSH_BACK = "SequencePushBack"
    SHRINK = "Shrink"
    NEURAL_NETWORK = "neural_network"
    TRANSFORMER = "transformer"
    LSTM = "lstm"
    GRU = "gru"
    RNN = "rnn"
    EMBEDDING = "embedding"
    CUSTOM = "custom"


class ModelFormat(str, Enum):
    PMML = "pmml"
    ONNX = "onnx"
    SKLEARN = "sklearn"
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CUSTOM = "custom"


class TrainingTask(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    DIMENSIONALITY_REDUCTION = "dimensionality_reduction"
    ASSOCIATION = "association"
    FORECASTING = "forecasting"
    ANOMALY_DETECTION = "anomaly_detection"
    RANKING = "ranking"
    RECOMMENDATION = "recommendation"
    GENERATION = "generation"


class DatasetSplit(BaseModel):
    train_ratio: float = 0.8
    validation_ratio: float = 0.1
    test_ratio: float = 0.1
    shuffle: bool = True
    random_seed: int | None = None
    stratify: bool = False
    cross_validation_folds: int | None = None


class AttributeValue(BaseModel):
    int_value: int | None = None
    float_value: float | None = None
    string_value: str | None = None
    ints: list[int] = Field(default_factory=list)
    floats: list[float] = Field(default_factory=list)
    strings: list[str] = Field(default_factory=list)
    tensor_shape: list[int] | None = None
    tensor_data: bytes | None = None
    graph_value: ModelGraph | None = None


class Port(BaseModel):
    name: str = ""
    data_type: DataType | None = None
    shape: list[int | str] | None = None
    ref: str | None = None


class RegularizationConfig(BaseModel):
    method: str | None = None
    lambda_1: float | None = None
    lambda_2: float | None = None
    dropout_rate: float | None = None


class ModelResult(BaseModel):
    name: str = ""
    value: float | str | list[float] | None = None
    description: str | None = None


class ModelParameter(BaseModel):
    name: ParameterName = ParameterName.CUSTOM
    value: float | int | str | bool = 0.0


class MiningField(BaseModel):
    name: str = ""
    usage_type: FieldUsageType = FieldUsageType.ACTIVE
    importance: float | None = None
    missing_value_replacement: str | float | None = None
    data_type: DataType | None = None
    outliers: OutlierTreatment | None = None
    low_value: float | None = None
    high_value: float | None = None
    ref: str | None = None


class MiningSchema(BaseModel):
    fields: list[MiningField] = Field(default_factory=list)


class ModelNode(BaseModel):
    id: str = ""
    op_type: OpType = OpType.CUSTOM
    name: str = ""
    inputs: list[Port] = Field(default_factory=list)
    outputs: list[Port] = Field(default_factory=list)
    attributes: dict[str, AttributeValue] = Field(default_factory=dict)
    sub_graph: ModelGraph | None = None
    weight: float | None = None


class ModelGraph(BaseModel):
    name: str = ""
    nodes: list[ModelNode] = Field(default_factory=list)
    inputs: list[Port] = Field(default_factory=list)
    outputs: list[Port] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrainingConfig(BaseModel):
    task: TrainingTask = TrainingTask.CLASSIFICATION
    dataset_name: str | None = None
    dataset_size: int | None = None
    feature_count: int | None = None
    sample_count: int | None = None
    split: DatasetSplit | None = None
    hyperparameters: list[ModelParameter] = Field(default_factory=list)
    epochs: int | None = None
    batch_size: int | None = None
    learning_rate: float | None = None
    optimization_algorithm: OptimizationAlgorithm | None = None
    loss_function: LossFunction | None = None
    early_stopping_rounds: int | None = None
    regularization: RegularizationConfig | None = None


class ModelMetric(BaseModel):
    name: str = ""
    value: float | None = None
    stage: EvaluationStage = EvaluationStage.TEST
    higher_is_better: bool = True


class FeatureImportance(BaseModel):
    feature_name: str = ""
    importance: float = 0.0
    method: ImportanceMethod | None = None


class MlMiningDocument(BaseDocument):
    model_type: MiningModelType = MiningModelType.DECISION_TREE
    model_format: ModelFormat | None = None
    features: list[MsdmAttribute] = Field(default_factory=list)
    target: MsdmAttribute | None = None
    training_config: TrainingConfig | None = None
    metrics: list[ModelMetric] = Field(default_factory=list)
    feature_importances: list[FeatureImportance] = Field(default_factory=list)
    parameters: list[ModelParameter] = Field(default_factory=list)
    model_data: bytes = b""
    model_graph: ModelGraph | None = None
    mining_schema: MiningSchema | None = None
    results: list[ModelResult] = Field(default_factory=list)
    vendor_extensions: dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
