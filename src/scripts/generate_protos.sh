#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------
# Root resolution
# ----------------------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ----------------------------------------
# Output directory
# ----------------------------------------
OUT_DIR="${ROOT_DIR}/apps/generated"

# ----------------------------------------
# External proto roots
# ----------------------------------------
EXTERNAL_PROTO_DIRS=(
  "${ROOT_DIR}/external/equity-flow-auth/protos"
  "${ROOT_DIR}/external/equity-flow-startup/protos"
)

# ----------------------------------------
# Validate
# ----------------------------------------
mkdir -p "${OUT_DIR}"

PROTO_FILES=()
PROTO_INCLUDES=()

for d in "${EXTERNAL_PROTO_DIRS[@]}"; do
  if [[ ! -d "$d" ]]; then
    echo "WARN: proto dir not found: $d" >&2
    continue
  fi

  PROTO_INCLUDES+=(-I "$d")

  while IFS= read -r f; do
    PROTO_FILES+=("$f")
  done < <(find "$d" -type f -name "*.proto")
done

if [[ ${#PROTO_FILES[@]} -eq 0 ]]; then
  echo "ERROR: no .proto files found in external services" >&2
  exit 1
fi

# ----------------------------------------
# Info
# ----------------------------------------
echo "Root:      ${ROOT_DIR}"
echo "Out dir:   ${OUT_DIR}"
echo "Proto roots:"
for i in "${PROTO_INCLUDES[@]}"; do
  echo "  ${i#-I }"
done
echo "Found ${#PROTO_FILES[@]} proto file(s)."

# ----------------------------------------
# Generate code
# ----------------------------------------
python -m grpc_tools.protoc \
  "${PROTO_INCLUDES[@]}" \
  --python_out="${OUT_DIR}" \
  --grpc_python_out="${OUT_DIR}" \
  "${PROTO_FILES[@]}"

# ----------------------------------------
# Make packages importable
# ----------------------------------------
touch "${OUT_DIR}/__init__.py"

while IFS= read -r -d '' d; do
  touch "${d}/__init__.py"
done < <(find "${OUT_DIR}" -type d -print0)

# ----------------------------------------
# Preview
# ----------------------------------------
echo "Protobuf generation complete."
find "${OUT_DIR}" -maxdepth 4 -type f \
  \( -name "*_pb2.py" -o -name "*_pb2_grpc.py" \) \
  | sed "s|${ROOT_DIR}/||" \
  | head -n 50

# find "${OUT_DIR}" -type f -name "*_pb2*.py" \
#   -print0 | xargs -0 sed -i -E \
#   's/^import ([a-zA-Z0-9_]+_pb2) as/from app.generated import \1 as/'
