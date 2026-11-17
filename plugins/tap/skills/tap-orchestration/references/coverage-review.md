# B2.5 Rà soát độ phủ + rà độc lập ở B3 (plugin 3.3.1)

Chi tiết cho `SKILL.md` mục B2.5 và B3. Mẫu in ra chat: `tap-core/references/gate-templates.md` (Mẫu B2.5, Mẫu ma trận phủ).

## 1. B2.5 — Rà soát độ phủ yêu cầu

Mục tiêu: bảng B3 phủ **toàn bộ** yêu cầu của người dùng, không chỉ phần mockup vẽ.

1. `set-phase REQUIREMENT_CONFIRMATION`. Đọc lại nguyên văn yêu cầu gốc (issue / mô tả / file người dùng đưa), câu trả lời B1, đề xuất B2, live probe và mockup đã đồng ý.
2. Tách thành danh sách **mục yêu cầu** có mã `R1, R2…`: mỗi gạch đầu dòng / tiêu chí nghiệm thu / ràng buộc của issue là một mục; tách nhỏ khi một câu chứa nhiều ý. Ghi nguồn (`issue`, `chat`, `mockup`, `probe`). Không gộp cho gọn; thà thừa còn hơn sót.
3. In danh sách R ra chat, kèm câu hỏi làm rõ **tối đa 5 câu** trong đúng một message, theo **Khung hỏi** (mục 2b). Ưu tiên hỏi chỗ ảnh hưởng tới số case: trạng thái dữ liệu (rỗng / một / nhiều / hết hàng / chưa đăng nhập), nhánh lỗi và từ chối, wait point, đường đi của nút trong chat (`[Bấm · Chat]` hay `[Chip · AI]`), scope (trong lần này hay `Proposed`). Câu hỏi dạng PO tự quyết theo [usecase-rules.md](usecase-rules.md) mục 7. Yêu cầu đã đủ rõ thì không hỏi, ghi `noQuestionReason`.
4. Hợp nhất câu trả lời (không trả lời thì dùng phương án đề xuất, ghi vào assumptions), cập nhật danh sách R, rồi `record-coverage --file` với JSON `{"items":[{"id":"R1","text":"...","source":"issue"}],"questions":[{"q","options","recommended","reason","answer"}],"noQuestionReason"?}`.
5. Chỉ một lượt hỏi ở B2.5. Câu phát sinh sau đó mà PO tự quyết được: ghi thành giả định dưới bảng B3.

## 2. B3 — Rà độc lập (bắt buộc trước khi hỏi Xác nhận)

Sau `record-requirement`, giao một **sub-agent mới** (Agent tool, không fork, không chia sẻ ngữ cảnh) rà bảng. Chỉ đưa đầu vào thô, không đưa lập luận hay kết luận của gateway (tránh xác nhận theo):

1. nguyên văn yêu cầu gốc (issue / mô tả người dùng) và câu trả lời B1, B2.5;
2. danh sách R đã chốt ở B2.5;
3. đường dẫn `skills/tap-orchestration/references/usecase-rules.md`;
4. bảng 9 cột + ma trận phủ vừa ghi;
5. danh sách transition `T<n>` của mockup.

Prompt mẫu cho sub-agent:

> Bạn là người rà độc lập bảng Requirement. Đọc `usecase-rules.md` và đầu vào kèm theo. Tìm: (a) mục R chưa có case hoặc case chỉ phủ hời hợt (thiếu trạng thái dữ liệu, nhánh lỗi/từ chối, nhánh wait point); (b) ý trong yêu cầu gốc chưa thành mục R; (c) case vi phạm usecase-rules (Điều kiện trước thiếu trạng thái, Pass rate sai mức, "nếu… ngược lại…", mô tả UI tĩnh, tên kỹ thuật, `Như`/`Sau` trỏ sai); (d) case thừa/trùng. Không sửa bảng, không viết lại bảng. Trả **chỉ** JSON: `{"reviewer":"subagent","inputs":[<tên các đầu vào đã nhận>],"findings":[{"ref":"<ID dòng | R<n> | TABLE>","severity":"block|warn","issue":"...","suggestion":"..."}]}`. `block` khi thiếu phủ, sai Pass rate, sai quy tắc làm test chấm sai; còn lại `warn`.

Gateway ghi nguyên kết quả bằng `record-independent-review --file`. Còn `block`: sửa bảng → `record-requirement` lại → rà lại bằng sub-agent mới. Tối đa **2 vòng**; sau vòng 2 còn `block` thì vẫn được hỏi Xác nhận nhưng phải in khối **Rà độc lập còn tồn** (ref | lỗi | đề xuất) dưới bảng. `warn` in dưới bảng để người dùng thấy. Script từ chối `confirm-requirement` khi chưa rà đúng bảng hiện tại hoặc còn `block` trong vòng 1.
