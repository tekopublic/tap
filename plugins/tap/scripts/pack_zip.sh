#!/usr/bin/env bash
# pack_zip.sh — Đóng gói plugin tap thành file zip chuẩn để upload lên Cowork
# Sử dụng: bash scripts/pack_zip.sh [version] [release-dir]
# Ví dụ:   bash scripts/pack_zip.sh 2.0.0 ../release

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-2.0.0}"
OUTPUT_NAME="tap-${VERSION}.zip"
RELEASE_DIR="${2:-$(dirname "${PLUGIN_DIR}")/release}"
OUTPUT_PATH="${RELEASE_DIR}/${OUTPUT_NAME}"

echo "📦 Đóng gói plugin tap v${VERSION}..."
echo "   Nguồn    : ${PLUGIN_DIR}"
echo "   Đích     : ${OUTPUT_PATH}"
echo ""

MANIFEST_VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "${PLUGIN_DIR}/.claude-plugin/plugin.json")"
if [ "${VERSION}" != "${MANIFEST_VERSION}" ]; then
  echo "❌ Version package (${VERSION}) không khớp manifest (${MANIFEST_VERSION})"
  exit 1
fi

# Kiểm tra cấu trúc tối thiểu
if [ ! -f "${PLUGIN_DIR}/.claude-plugin/plugin.json" ]; then
  echo "❌ Lỗi: Không tìm thấy .claude-plugin/plugin.json"
  exit 1
fi

# Chạy check_contract trước khi đóng gói
echo "🔍 Chạy kiểm tra hợp đồng (check_contract.py)..."
python3 "${PLUGIN_DIR}/scripts/check_contract.py" \
  --plugin-dir "${PLUGIN_DIR}"

echo "🧪 Chạy kiểm tra orchestration..."
python3 "${PLUGIN_DIR}/scripts/test_orchestration.py"

echo ""
echo "✔ Hợp đồng OK. Tiến hành đóng gói..."

mkdir -p "${RELEASE_DIR}"
# Xóa file release cùng version nếu có
[ -f "${OUTPUT_PATH}" ] && rm -f "${OUTPUT_PATH}"

# Tạo zip từ thư mục cha, trỏ đúng thư mục tap/
(
  cd "$(dirname "${PLUGIN_DIR}")"
  zip -r "${OUTPUT_PATH}" tap \
    -x "tap/evals/results/*" \
    -x "tap/.DS_Store" \
    -x "tap/**/.DS_Store" \
    -x "tap/**/__pycache__/*" \
    -x "tap/**/*.pyc" \
    -x "tap/.tap-work-items/*"
)

echo ""
echo "✅ Đóng gói thành công: ${OUTPUT_PATH}"
echo "   Kích thước: $(du -sh "${OUTPUT_PATH}" | cut -f1)"
echo ""
echo "📤 Các bước tiếp theo:"
echo "   1. Mở Anthropic Cowork"
echo "   2. Customize > Plugins > Add > Upload plugin"
echo "   3. Chọn file: ${OUTPUT_PATH}"
