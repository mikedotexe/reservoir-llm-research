"""Owned, isolated activation worker. Importing this package never loads a model."""

PROTOCOL_VERSION = "reservoir-activation/1"
MODEL_ID = "mlx-community/Qwen3-4B-4bit"
MODEL_REVISION = "4dcb3d101c2a062e5c1d4bb173588c54ea6c4d25"
HIDDEN_DIM = 2560
STATE_DIM = 32
LAYER_COUNT = 36
TAP_BLOCK_INDEX = 17
GAIN = 0.01
MAX_TOKENS = 1024
DEADLINE_SECONDS = 180.0
